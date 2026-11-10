#!/usr/bin/env python3
"""Engagement-rate tracker — the self-improvement signal for Booked Job social.

For every recent post on the channels we keep (FB Reels, Instagram Reels, YouTube
Shorts, plus TikTok at the channel level via Buffer), pull reach/views + the real
engagements (likes/reactions + comments + shares), compute an engagement rate, rank
every post, and surface which hooks/captions actually earn a reaction.

  ER = (reactions + comments + shares) / max(views, 1)

Writes two files:
  content/engagement_insights.json  — current ranked signal, consumed by the content
                                       engine to bias new posts toward what works.
  content/engagement_history.json   — a dated snapshot each run, for trend tracking.

Usage:
  python3 scripts/engagement_tracker.py            # refresh insights + history
  python3 scripts/engagement_tracker.py --report   # human-readable top/bottom posts
"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
GRAPH = "https://graph.facebook.com/v21.0"
MIN_VIEWS = 20          # ignore tiny-denominator noise when ranking by rate
INSIGHTS = os.path.join(ROOT, "content", "engagement_insights.json")
HISTORY = os.path.join(ROOT, "content", "engagement_history.json")


def _env(name):
    p = os.path.join(ROOT, "secrets", f"{name}.env")
    if not os.path.exists(p):
        return {}
    e = {}
    for l in open(p):
        l = l.strip()
        if "=" in l and not l.startswith("#"):
            k, v = l.split("=", 1); e[k.strip()] = v.strip()
    return e


def _get(url, hdr=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdr or {}), timeout=25) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_err": str(e)[:160]}


def _graph(path, params, tok):
    params = dict(params); params["access_token"] = tok
    return _get(f"{GRAPH}/{path}?" + urllib.parse.urlencode(params))


def _post(ch, pid, caption, views, reactions, comments, shares=0, date=""):
    eng = reactions + comments + shares
    return {"channel": ch, "id": pid, "caption": (caption or "").strip()[:140],
            "views": views, "reactions": reactions, "comments": comments, "shares": shares,
            "engagements": eng, "er": round(100 * eng / max(views, 1), 2), "date": date}


# ── per-channel collectors (each returns a list of post dicts, never raises) ──
def fb_reels(limit=25):
    e = _env("fb"); page = e.get("FB_PAGE_ID"); tok = e.get("FB_PAGE_TOKEN") or e.get("FB_ACCESS_TOKEN") or e.get("FB_TOKEN")
    if not (page and tok):
        return []
    d = _graph(f"{page}/video_reels", {"fields": "id,description,created_time,views,"
               "likes.summary(true),comments.summary(true)", "limit": limit}, tok)
    out = []
    for it in d.get("data", []) if isinstance(d, dict) else []:
        out.append(_post("FB Reels", it.get("id"), it.get("description"), int(it.get("views", 0) or 0),
                         (it.get("likes", {}) or {}).get("summary", {}).get("total_count", 0),
                         (it.get("comments", {}) or {}).get("summary", {}).get("total_count", 0),
                         date=(it.get("created_time", "") or "")[:10]))
    return out


def ig_reels(limit=25):
    e = _env("fb"); ig = e.get("FB_IG_ID"); tok = e.get("FB_PAGE_TOKEN") or e.get("FB_ACCESS_TOKEN") or e.get("FB_TOKEN")
    if not (ig and tok):
        return []
    d = _graph(f"{ig}/media", {"fields": "id,caption,media_type,timestamp,like_count,comments_count,"
               "insights.metric(reach,plays)", "limit": limit}, tok)
    out = []
    for it in d.get("data", []) if isinstance(d, dict) else []:
        reach = 0
        for m in (it.get("insights", {}) or {}).get("data", []):
            if m.get("name") in ("plays", "reach") and m.get("values"):
                reach = max(reach, int(m["values"][0].get("value", 0) or 0))
        out.append(_post("IG Reels", it.get("id"), it.get("caption"), reach,
                         int(it.get("like_count", 0) or 0), int(it.get("comments_count", 0) or 0),
                         date=(it.get("timestamp", "") or "")[:10]))
    return out


def yt_shorts(limit=25):
    e = _env("youtube")
    if not (e.get("YT_REFRESH_TOKEN") and e.get("YT_CLIENT_ID") and e.get("YT_CLIENT_SECRET")):
        return []
    body = urllib.parse.urlencode({"client_id": e["YT_CLIENT_ID"], "client_secret": e["YT_CLIENT_SECRET"],
                                   "refresh_token": e["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=body), timeout=20) as r:
            tok = json.loads(r.read()).get("access_token")
    except Exception:
        return []
    H = {"Authorization": f"Bearer {tok}"}
    ch = _get("https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true", H)
    its = ch.get("items", []) if isinstance(ch, dict) else []
    if not its:
        return []
    up = its[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    pl = _get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails,snippet&playlistId={up}&maxResults={limit}", H)
    ids, titles, dates = [], {}, {}
    for i in pl.get("items", []):
        vid = i["contentDetails"]["videoId"]; ids.append(vid)
        titles[vid] = i["snippet"].get("title", ""); dates[vid] = (i["contentDetails"].get("videoPublishedAt", "") or "")[:10]
    if not ids:
        return []
    vs = _get(f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={','.join(ids)}", H)
    out = []
    for v in vs.get("items", []):
        s = v["statistics"]; vid = v["id"]
        out.append(_post("YT Shorts", vid, titles.get(vid), int(s.get("viewCount", 0) or 0),
                         int(s.get("likeCount", 0) or 0), int(s.get("commentCount", 0) or 0), date=dates.get(vid, "")))
    return out


def tiktok_channel():
    """TikTok only exposes channel-level aggregate via Buffer (no per-post). One summary row."""
    try:
        sys.path.insert(0, HERE); b = __import__("buffer_publish")
        if not b.env():
            return []
        for c in b.channels():
            if c.get("service") == "tiktok" and not c.get("isDisconnected"):
                m = b.metrics([c["id"]], 30)
                v = int(m.get("views", 0) or 0); eng = int(m.get("reactions", 0) or 0) + int(m.get("comments", 0) or 0)
                return [{"channel": "TikTok", "id": "aggregate-30d", "caption": f"{m.get('postCount',0)} posts (channel aggregate, no per-post data)",
                         "views": v, "reactions": int(m.get("reactions", 0) or 0), "comments": int(m.get("comments", 0) or 0),
                         "shares": 0, "engagements": eng, "er": round(100 * eng / max(v, 1), 2), "date": ""}]
    except Exception:
        pass
    return []


def collect():
    posts = []
    for fn in (fb_reels, ig_reels, yt_shorts, tiktok_channel):
        try:
            posts += fn()
        except Exception:
            pass
    return posts


def build():
    posts = collect()
    # per-channel rollup
    channels = {}
    for p in posts:
        c = channels.setdefault(p["channel"], {"posts": 0, "views": 0, "engagements": 0})
        c["posts"] += 1; c["views"] += p["views"]; c["engagements"] += p["engagements"]
    for c in channels.values():
        c["er"] = round(100 * c["engagements"] / max(c["views"], 1), 2)
    # rank only posts with enough reach to trust the rate; aggregate rows excluded from per-post ranking
    rankable = [p for p in posts if p["views"] >= MIN_VIEWS and p["id"] != "aggregate-30d"]
    rankable.sort(key=lambda p: (p["er"], p["engagements"]), reverse=True)
    insights = {
        "generated": dt.datetime.now().isoformat(timespec="minutes"),
        "min_views_for_rank": MIN_VIEWS,
        "channels": channels,
        "post_count": len(posts),
        "top": rankable[:8],
        "bottom": rankable[-8:][::-1] if len(rankable) > 8 else [],
        "note": "ER = (reactions+comments+shares)/views, %. 'top' = hooks that earned a reaction when seen; "
                "feed these patterns into new posts. Everything near 0 = reach without resonance (content problem).",
    }
    json.dump(insights, open(INSIGHTS, "w"), indent=2)
    # append a trend snapshot
    hist = []
    if os.path.exists(HISTORY):
        try:
            hist = json.load(open(HISTORY))
        except Exception:
            hist = []
    snap = {"date": dt.date.today().isoformat(),
            "channels": {k: {"views": v["views"], "engagements": v["engagements"], "er": v["er"]} for k, v in channels.items()}}
    hist = [h for h in hist if h.get("date") != snap["date"]] + [snap]
    json.dump(hist[-120:], open(HISTORY, "w"), indent=2)
    return insights


def report(ins):
    print(f"── Engagement rate by channel (recent posts, ER = eng/views) ──")
    for ch, c in sorted(ins["channels"].items(), key=lambda x: -x[1]["er"]):
        print(f"  {ch:11} {c['posts']:>3} posts · {c['views']:>6} views · {c['engagements']:>4} eng · ER {c['er']}%")
    print(f"\n── Top hooks by engagement rate (≥{ins['min_views_for_rank']} views) ──")
    for p in ins["top"] or []:
        print(f"  ER {p['er']:>5}%  [{p['channel']}] {p['views']}v/{p['engagements']}e  “{p['caption'][:80]}”")
    if not ins["top"]:
        print("  (no posts cleared the view threshold yet — baseline is near-zero engagement everywhere)")


if __name__ == "__main__":
    ins = build()
    report(ins)
    print(f"\nwrote {os.path.relpath(INSIGHTS)} + {os.path.relpath(HISTORY)}")
