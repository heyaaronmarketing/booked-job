#!/usr/bin/env python3
"""
Pull live Booked Job stats from the Graph API + local state and write
site/dashboard/data.json (read by the dashboard; no token ever in the client).
Run by launchd a few times a day.
"""
import datetime as dt, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
GRAPH = "https://graph.facebook.com/v21.0"


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "fb.env")):
        if "=" in line:
            k, v = line.strip().split("=", 1); e[k] = v
    return e


GOAL_SIGNUPS = 1000  # 90-day newsletter goal (ICP service pros)


def _signup_stats():
    """Total signups + top-converting pages, from the worker's /ops/signups (KV)."""
    try:
        req = urllib.request.Request("https://booked-job.com/ops/signups", headers={"User-Agent": "curl/8.4"})
        d = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
        top = sorted((d.get("by_source") or {}).items(), key=lambda x: -x[1])[:6]
        return {"total": d.get("total", 0), "goal": GOAL_SIGNUPS,
                "pct": round(100 * d.get("total", 0) / GOAL_SIGNUPS, 1),
                "top_sources": [{"page": p, "n": n} for p, n in top]}
    except Exception:
        return {"total": 0, "goal": GOAL_SIGNUPS, "pct": 0, "top_sources": []}


def _search_stats():
    """Real organic search traffic for the dashboard: Google (GSC) + Bing (Webmaster).
    Each returns None when its creds aren't set, so the panel degrades gracefully."""
    out = {}
    for name, mod in (("google", "gsc_stats"), ("bing", "bing_search_stats")):
        try:
            sys.path.insert(0, HERE); m = __import__(mod)
            s = m.stats()
            if s is not None:
                out[name] = s
        except Exception as e:
            out[name] = {"error": str(e)[:120]}
    # Cloudflare zone-level pageviews (real site traffic, no beacon needed).
    try:
        sys.path.insert(0, HERE); cf = __import__("cf_analytics")
        import datetime as _dt
        month_start = _dt.date.today().replace(day=1).isoformat()
        w = cf.windows(month_start)
        if w is not None:
            out["cloudflare"] = {"pageviews_daily": w["daily"], "pageviews_weekly": w["weekly"],
                                 "pageviews_monthly": w["monthly"]}
    except Exception as e:
        out["cloudflare"] = {"error": str(e)[:120]}
    tot_c = sum(v.get("clicks", 0) for v in out.values() if isinstance(v, dict) and "clicks" in v)
    tot_i = sum(v.get("impressions", 0) for v in out.values() if isinstance(v, dict) and "impressions" in v)
    out["total_clicks"] = tot_c; out["total_impressions"] = tot_i
    out["configured"] = any(k in out for k in ("google", "bing", "cloudflare"))
    return out


def _buffer_stats():
    """Per-channel engagement for Buffer-routed channels (TikTok/LinkedIn/Pinterest).
    Buffer's aggregated metrics only return ~30 days reliably. None when not configured."""
    try:
        sys.path.insert(0, HERE); b = __import__("buffer_publish")
        if not b.env():
            return None
        out = {}
        for c in b.channels():
            if c.get("isDisconnected"):
                continue
            m = b.metrics([c["id"]], 30)
            out[c["service"]] = {
                "name": c.get("displayName", c["service"]),
                "posts": m.get("postCount", 0), "views": m.get("views", 0),
                "reactions": m.get("reactions", 0), "comments": m.get("comments", 0),
                "engagement_rate": m.get("engagementRate", 0),
            }
        return out or None
    except Exception as e:
        return {"error": str(e)[:120]}


def get(path, params, tok):
    params["access_token"] = tok
    try:
        with urllib.request.urlopen(f"{GRAPH}/{path}?" + urllib.parse.urlencode(params), timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_err": str(e)}


def jload(p, d):
    try:
        return json.load(open(os.path.join(ROOT, p)))
    except Exception:
        return d


# --- Self-updating agent list: derived from the worker/*.plist files, so any
# --- new channel/agent automatically appears on the dashboard. (SOP: add a
# --- channel -> add its com.bookedjob.<x>.plist -> it shows up here for free.)
WEEKDAY = {0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
AGENT_NAMES = {
    "publisher": "Posts", "reels": "FB Reels", "youtube": "YouTube Shorts",
    "instagram": "Instagram Reels", "engage": "Engage", "report": "Weekly Report",
    "stats": "Stats Refresh", "blogger": "Blogger", "tumblr": "Tumblr",
    "pinterest": "Pinterest", "newsletter": "Newsletter",
    "telegraph": "Telegraph", "bluesky": "Bluesky", "mastodon": "Mastodon",
    "threads": "Threads", "telegram": "Telegram", "ghpages": "GitHub Pages",
    "blueskyengage": "Bluesky Engage", "youtubeengage": "YouTube CTA",
    "threadsengage": "Threads Surfacing", "igengage": "IG Inbound",
    "buffer": "LinkedIn (Buffer)", "buffertiktok": "TikTok (Buffer)", "telegrampoll": "Telegram Polls", "emaildrip": "Email Drip", "buffercarousel": "LinkedIn Carousels", "blueskyfeed": "Bluesky Feed", "igcarousel": "IG Carousels", "fbcarousel": "FB Carousels", "story": "IG+FB Stories", "tiktokcarousel": "TikTok Carousels", "reelstory": "Reel Stories",
    "tasks": "Daily Task List", "discovery": "Community Discovery",
}
AGENT_CATS = {
    "publisher": "Publishing", "reels": "Publishing", "youtube": "Publishing", "instagram": "Publishing",
    "blogger": "Publishing", "tumblr": "Publishing", "telegraph": "Publishing", "telegram": "Publishing",
    "threads": "Publishing", "bluesky": "Publishing", "mastodon": "Publishing", "ghpages": "Publishing",
    "newsletter": "Publishing", "buffer": "Publishing", "buffertiktok": "Publishing", "pinterest": "Publishing",
    "igcarousel": "Visual formats", "fbcarousel": "Visual formats", "buffercarousel": "Visual formats",
    "tiktokcarousel": "Visual formats", "story": "Visual formats", "reelstory": "Visual formats",
    "engage": "Engagement", "blueskyengage": "Engagement", "youtubeengage": "Engagement",
    "threadsengage": "Engagement", "igengage": "Engagement", "telegrampoll": "Engagement",
    "discovery": "Engagement", "tasks": "Engagement",
    "emaildrip": "Funnel", "blueskyfeed": "Funnel",
    "report": "Ops", "stats": "Ops",
}


def _sched(sci):
    if not sci:
        return "scheduled"
    items = sci if isinstance(sci, list) else [sci]
    days, times = set(), []
    for it in items:
        if "Weekday" in it:
            days.add(int(it["Weekday"]))
        times.append(f"{int(it.get('Hour', 0))}:{int(it.get('Minute', 0)):02d}")
    daystr = ", ".join(WEEKDAY[d] for d in sorted(days)) if days else "Daily"
    return f"{daystr} · {' / '.join(sorted(set(times)))}"


def enumerate_agents():
    import glob, plistlib
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "worker", "com.bookedjob.*.plist"))):
        try:
            d = plistlib.load(open(p, "rb"))
        except Exception:
            continue
        key = d.get("Label", "").split(".")[-1]
        out.append({"name": AGENT_NAMES.get(key, key.title()),
                    "schedule": _sched(d.get("StartCalendarInterval")), "on": True,
                    "cat": AGENT_CATS.get(key, "Other")})
    return out


def readenv(fname):
    p = os.path.join(ROOT, "secrets", fname)
    e = {}
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1); e[k] = v
    return e


def _jget(url, headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {}


def social_followers():
    """Best-effort follower/subscriber counts for channels with no scoreboard card."""
    f = {}
    bs = readenv("bluesky.env")
    if bs.get("BLUESKY_HANDLE"):
        d = _jget(f"https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?actor={bs['BLUESKY_HANDLE']}")
        if "followersCount" in d:
            f["Bluesky"] = d["followersCount"]
    ms = readenv("mastodon.env")
    if ms.get("MASTODON_TOKEN") and ms.get("MASTODON_INSTANCE"):
        d = _jget(f"{ms['MASTODON_INSTANCE'].rstrip('/')}/api/v1/accounts/verify_credentials",
                  {"Authorization": f"Bearer {ms['MASTODON_TOKEN']}"})
        if "followers_count" in d:
            f["Mastodon"] = d["followers_count"]
    th = readenv("threads.env")
    if th.get("THREADS_USER_ID") and th.get("THREADS_TOKEN"):
        d = _jget(f"https://graph.threads.net/v1.0/{th['THREADS_USER_ID']}/threads_insights?metric=followers_count&access_token={th['THREADS_TOKEN']}")
        try:
            f["Threads"] = d["data"][0]["total_value"]["value"]
        except Exception:
            pass
    tg = readenv("telegram.env")
    if tg.get("TELEGRAM_BOT_TOKEN") and tg.get("TELEGRAM_CHAT_ID"):
        d = _jget(f"https://api.telegram.org/bot{tg['TELEGRAM_BOT_TOKEN']}/getChatMemberCount?chat_id={tg['TELEGRAM_CHAT_ID']}")
        if d.get("ok"):
            f["Telegram"] = d.get("result")
    return f


def social_engagement():
    """Best-effort likes for channels that expose engagement but have no views concept.
    Bluesky: sum likeCount over recent author posts. Mastodon: sum favourites over recent
    statuses. (Telegram channels don't expose per-post views to BOT tokens — that needs
    the MTProto client API — so Telegram stays Posts + Followers.)"""
    eng = {}
    bs = readenv("bluesky.env")
    if bs.get("BLUESKY_HANDLE"):
        try:
            d = _jget(f"https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor={bs['BLUESKY_HANDLE']}&limit=100")
            eng["Bluesky"] = sum(int((it.get("post") or {}).get("likeCount", 0)) for it in d.get("feed", []))
        except Exception:
            pass
    ms = readenv("mastodon.env")
    if ms.get("MASTODON_TOKEN") and ms.get("MASTODON_INSTANCE"):
        try:
            base = ms["MASTODON_INSTANCE"].rstrip("/"); hdr = {"Authorization": f"Bearer {ms['MASTODON_TOKEN']}"}
            aid = _jget(f"{base}/api/v1/accounts/verify_credentials", hdr).get("id")
            if aid:
                sts = _jget(f"{base}/api/v1/accounts/{aid}/statuses?limit=40", hdr)
                eng["Mastodon"] = sum(int(s.get("favourites_count", 0)) for s in (sts if isinstance(sts, list) else []))
        except Exception:
            pass
    return eng


def _grade(value, t):
    """Letter grade from thresholds t=[D,C,B,A]."""
    if value >= t[3]: return "A"
    if value >= t[2]: return "B"
    if value >= t[1]: return "C"
    if value >= t[0]: return "D"
    return "F"


def mafia_summary(overall, posts, audience, clicks, live_ch):
    """Brutally honest read keyed off the overall grade."""
    if overall == "F":
        return (f"Brutal truth: we're basically invisible right now. {posts} posts are out the door across {live_ch} live "
                f"channels, but the audience is {audience} and almost nobody's seen them yet. That's an F — and honestly "
                f"normal for a brand that started at zero. The whole machine is built; what's missing is VOLUME and TIME. "
                f"The fix: the weekly strategist writes more articles (each fans out to every channel), the Bluesky daemon "
                f"keeps drip-pulling real followers, and we convert the Pinterest + Google Business approvals the moment "
                f"they land to open two more reach channels. Nothing's broken — it's a cold engine. Grades climb as the "
                f"numbers do; check back weekly.")
    if overall == "D":
        return (f"On the board, barely. {posts} posts, {audience} in the audience, {clicks} clicks toward Consent Resolve — "
                f"real, but small. A D means the foundation works and the first signs of life are showing. To push to a C: "
                f"more content volume (the single biggest lever), keep the engagement daemon running, and switch on the "
                f"gated channels (Pinterest/GBP) the moment they're approved.")
    if overall == "C":
        return (f"Respectable for an early-stage brand. {posts} posts, {audience} audience, {clicks} CR clicks — the flywheel "
                f"is turning. To reach a B: double down on whatever's driving the most engagement, lean harder into video "
                f"(the reach engine), and tighten the email nurture so more of this audience converts.")
    if overall == "B":
        return (f"Strong. {audience} audience and {clicks} clicks to Consent Resolve — this is working. To hit an A: scale the "
                f"winning channels, push reach (ads + video), and fix the funnel's weakest stage.")
    return (f"Elite. Firing across reach, audience, and conversion — {audience} audience, {clicks} CR clicks. Now defend the "
            f"lead: keep volume high, put budget behind what converts, and protect the owned audience.")


def channels(email_subs=0, followers=None):
    """Distribution panel: every channel with connection status + activity."""
    followers = followers or {}
    # (name, secret file, state file, state key, unit, kind-when-connected)
    reg = [
        ("Facebook", "fb.env", "state.json", "posted", "posts", "live"),
        ("Instagram", "fb.env", "ig_state.json", "done", "posts", "live"),
        ("YouTube", "youtube.env", "yt_state.json", "done", "shorts", "live"),
        ("Blogger", "blogger.env", "blogger_state.json", "done", "posts", "live"),
        ("Tumblr", "tumblr.env", "tumblr_state.json", "done", "posts", "live"),
        ("Telegraph", "telegraph.env", "telegraph_state.json", "done", "posts", "live"),
        ("Bluesky", "bluesky.env", "bluesky_state.json", "done", "posts", "live"),
        ("Mastodon", "mastodon.env", "mastodon_state.json", "done", "posts", "live"),
        ("Threads", "threads.env", "threads_state.json", "done", "posts", "live"),
        ("Telegram", "telegram.env", "telegram_state.json", "done", "posts", "live"),
        ("GitHub Pages", "github.env", "ghpages_state.json", "done", "mirrors", "live"),
    ]
    out = []
    for name, sec, stf, key, unit, kind in reg:
        connected = os.path.exists(os.path.join(ROOT, "secrets", sec))
        cnt = len(jload(os.path.join(ROOT, "content", stf), {}).get(key, [])) if connected else 0
        entry = {"name": name, "status": kind if connected else "off", "count": cnt, "unit": unit}
        if followers.get(name) is not None:
            entry["followers"] = followers[name]
        out.append(entry)
    # Reels + carousels are posts too — fold them into each platform's count so
    # "Posts" reflects everything published there (they were previously uncounted).
    # A reel fans out to FB + IG + TikTok. Stories are ephemeral (24h) -> excluded.
    def _n(fname, key="done"):
        return len(jload(os.path.join(ROOT, "content", fname), {}).get(key, []))
    reels = _n("reels_state.json")
    add = {"Facebook": reels + _n("fb_carousel_state.json"),
           "Instagram": reels + _n("ig_carousel_state.json")}
    for e in out:
        if e["name"] in add and e["status"] == "live":
            e["count"] += add[e["name"]]
    # Blog (always live — it's our own site); count = published articles
    arts = len(jload(os.path.join(ROOT, "content", "syndication_queue.json"), {}).get("items", []))
    out.insert(0, {"name": "Blog", "status": "live", "count": arts, "unit": "articles"})
    # Podcast — Get Booked, Not F***ed (RSS-hosted; episodes = files in site/podcast)
    import glob
    eps = len(glob.glob(os.path.join(ROOT, "site", "podcast", "ep*.mp3")))
    out.insert(1, {"name": "Podcast", "status": "live", "count": eps, "unit": "episodes"})
    # Email (Resend)
    em = os.path.exists(os.path.join(ROOT, "secrets", "resend.env"))
    out.append({"name": "Email", "status": "live" if em else "off", "count": email_subs, "unit": "subs"})
    # LinkedIn + TikTok via Buffer (interim) — with engagement metrics from Buffer
    buf = os.path.exists(os.path.join(ROOT, "secrets", "buffer.env"))
    bs = jload(os.path.join(ROOT, "content", "buffer_state.json"), {})
    li_m = tt_m = pin_m = {}
    if buf:
        try:
            sys.path.insert(0, HERE); import buffer_publish as BP
            be = BP.env()
            li_m = BP.metrics([be["BUFFER_LINKEDIN_CHANNEL"]])
            tt_m = BP.metrics([be["BUFFER_TIKTOK_CHANNEL"]])
            if be.get("BUFFER_PINTEREST_CHANNEL"):
                pin_m = BP.metrics([be["BUFFER_PINTEREST_CHANNEL"]])
        except Exception:
            pass
    li = {"name": "LinkedIn", "status": "live" if buf else "pending",
          "count": len(bs.get("linkedin", [])) + len(bs.get("linkedin_carousel", [])), "unit": "posts (Buffer)"}
    if li_m:
        li["stat"] = f"{int(li_m.get('reach', 0))} reach · {int(li_m.get('reactions', 0))} reactions"
        li["views"] = int(li_m.get("views", 0))
        li["likes"] = int(li_m.get("reactions", 0))
    out.append(li)
    tt = {"name": "TikTok", "status": "live" if buf else "off",
          "count": len(bs.get("tiktok", [])) + len(bs.get("tiktok_carousel", [])) + reels, "unit": "videos (Buffer)"}
    if tt_m:
        tt["stat"] = f"{int(tt_m.get('views', 0))} views · {int(tt_m.get('reactions', 0))} reactions"
        tt["views"] = int(tt_m.get("views", 0))
        tt["likes"] = int(tt_m.get("reactions", 0))
    out.append(tt)
    # Pinterest via Buffer — pins posted from pinterest_buffer_state; stats from Buffer
    pin = {"name": "Pinterest", "status": "live" if buf else "off", "unit": "pins (Buffer)",
           "count": len(jload(os.path.join(ROOT, "content", "pinterest_buffer_state.json"), {}).get("done", []))}
    if pin_m:
        pin["views"] = int(pin_m.get("impressions", 0))   # Pinterest reports impressions, not views
        pin["likes"] = int(pin_m.get("reactions", 0))
        pin["stat"] = f"{int(pin_m.get('impressions', 0))} impressions · {int(pin_m.get('saves', 0))} saves"
    out.append(pin)
    # Pending channels (built/ready, waiting on an external gate)
    out.append({"name": "Google Business", "status": "pending", "count": 0, "unit": "verifying"})
    content = {"Blog", "Podcast", "Blogger", "Tumblr", "Telegraph", "GitHub Pages", "Email"}
    for e in out:
        e["grade"] = "—" if e["status"] in ("pending", "off") else _grade(e.get("followers", e["count"]), [1, 10, 50, 200])
        e["group"] = "content" if e["name"] in content else "social"
    return out


def coverage():
    """Full post-type coverage per network: what we produce (live+count), what the
    platform supports but we don't do yet (gap -> highlighted), and long-form video
    (soon -> tracked as a separate project, not a gap). Counts come from state files."""
    def n(f, k="done"):
        return len(jload(os.path.join(ROOT, "content", f), {}).get(k, []))
    bs = jload(os.path.join(ROOT, "content", "buffer_state.json"), {})
    reels = n("reels_state.json")
    stories = n("story_state.json") + n("reel_story_state.json")
    L = lambda t, c: {"type": t, "status": "live", "count": c}
    gap = lambda t: {"type": t, "status": "gap"}
    soon = lambda t: {"type": t, "status": "soon"}
    vps = jload(os.path.join(ROOT, "content", "video_pool_state.json"), {})   # per-platform video-pool distribution
    vp = lambda plat: len(vps.get(plat, {}).get("posted", []))
    return {
        "Facebook": [L("Posts", n("state.json", "posted")), L("Carousels", n("fb_carousel_state.json")),
                     L("Reels", reels), L("Stories", stories), gap("Polls"), soon("Long video")],
        "Instagram": [L("Posts", n("ig_state.json")), L("Carousels", n("ig_carousel_state.json")),
                      L("Reels", reels), L("Stories", stories), soon("Long video")],
        "YouTube": [L("Shorts", n("yt_state.json")), gap("Community posts"), soon("Long video")],
        "TikTok": [L("Videos", len(bs.get("tiktok", [])) + reels), L("Photo carousels", len(bs.get("tiktok_carousel", []))),
                   gap("Stories"), soon("Long video")],
        "LinkedIn": [L("Posts", len(bs.get("linkedin", []))), L("Documents", len(bs.get("linkedin_carousel", []))),
                     L("Native video", vp("linkedin")), gap("Articles"), gap("Newsletter"), gap("Polls")],
        "Pinterest": [L("Pins", n("pinterest_buffer_state.json")), L("Video pins", vp("pinterest"))],
        "Bluesky": [L("Posts", n("bluesky_state.json")), L("Video", vp("bluesky"))],
        "Mastodon": [L("Posts", n("mastodon_state.json")), gap("Video"), gap("Polls")],
        "Threads": [L("Posts", n("threads_state.json")), gap("Video"), gap("Polls")],
        "Telegram": [L("Posts", n("telegram_state.json")), L("Polls", n("telegram_poll_state.json")), L("Video", vp("telegram"))],
        "Tumblr": [L("Posts", n("tumblr_state.json")), L("Video", vp("tumblr"))],
    }


def runway():
    """Content runway per queue: how many days of content remain at the current
    cadence. Powers the dashboard's low-content alert."""
    import glob
    def rem(qf, key, sf, sk="done"):
        try:
            q = jload(os.path.join(ROOT, "content", qf), {}).get(key, [])
            st = set(jload(os.path.join(ROOT, "content", sf), {}).get(sk, []))
            return len([i for i in q if (i.get("id") if isinstance(i, dict) else i) not in st])
        except Exception:
            return 0
    staged = len(glob.glob(os.path.join(ROOT, "content", "staged", "*.json")))
    pool = len(jload(os.path.join(ROOT, "content", "video_pool.json"), {}).get("videos", []))
    # (label, remaining, per_day, evergreen?) — evergreen queues cycle, so "low" = thin rotation
    rows = [
        ("Facebook posts", rem("queue.json", "posts", "state.json", "posted"), 2, False),
        ("Reels — fresh renders", rem("reels_queue.json", "reels", "reels_state.json"), 1, False),
        ("YouTube/IG shorts", rem("yt_queue.json", "shorts", "yt_state.json"), 2, False),
        ("Blog articles (drip)", staged, 2, False),
        ("Video pool (evergreen)", pool, 0, True),
    ]
    out = []
    for label, n, per, ever in rows:
        if ever:
            days = None
            status = "red" if n < 6 else "amber" if n < 10 else "green"
        else:
            days = round(n / per, 1) if per else None
            status = "red" if days is not None and days < 3 else "amber" if days is not None and days < 7 else "green"
        out.append({"label": label, "remaining": n, "per_day": per, "days": days, "status": status})
    return out


def main():
    E = env()
    page, ptok, stok = E["FB_PAGE_ID"], E["FB_PAGE_TOKEN"], E.get("FB_SYSTEM_TOKEN", E["FB_LONGLIVED_USER_TOKEN"])
    acct = E.get("FB_AD_ACCOUNT", "")

    pi = get(page, {"fields": "name,fan_count,followers_count"}, ptok)
    posts = get(f"{page}/posts", {"fields": "shares,reactions.summary(true),comments.summary(true)", "limit": 50}, ptok)
    rx = cm = sh = 0
    pdata = posts.get("data", [])
    for p in pdata:
        rx += p.get("reactions", {}).get("summary", {}).get("total_count", 0)
        cm += p.get("comments", {}).get("summary", {}).get("total_count", 0)
        sh += p.get("shares", {}).get("count", 0)

    # queues
    q = jload("content/queue.json", {"posts": []})["posts"]
    st = jload("content/state.json", {"posted": []})
    rq = jload("content/reels_queue.json", {"reels": []})["reels"]
    rst = jload("content/reels_state.json", {"done": []})

    # ads insights
    ads = {"status": "—", "daily_budget": None, "spend": "0", "impressions": 0, "reach": 0, "video_views": 0}
    if acct:
        camps = get(f"{acct}/campaigns", {"fields": "name,effective_status,daily_budget", "limit": 5}, stok).get("data", [])
        if camps:
            c = camps[0]
            ads["status"] = c.get("effective_status", "—")
        ins = get(f"{acct}/insights", {"fields": "spend,impressions,reach,actions", "date_preset": "maximum"}, stok).get("data", [])
        if ins:
            i = ins[0]
            ads["spend"] = i.get("spend", "0"); ads["impressions"] = int(i.get("impressions", 0) or 0)
            ads["reach"] = int(i.get("reach", 0) or 0)
            for a in i.get("actions", []):
                if "video_view" in a.get("action_type", ""):
                    ads["video_views"] = int(float(a.get("value", 0)))
        # daily budget from active adset
        asets = get(f"{acct}/adsets", {"fields": "daily_budget,effective_status", "limit": 5}, stok).get("data", [])
        for a in asets:
            if a.get("daily_budget"):
                ads["daily_budget"] = int(a["daily_budget"]) / 100
                break

    # YouTube stats (if connected)
    yt = {"connected": False, "subscribers": 0, "views": 0, "videos": 0}
    yp = os.path.join(ROOT, "secrets", "youtube.env")
    if os.path.exists(yp):
        try:
            ye = {}
            for line in open(yp):
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1); ye[k] = v
            tbody = urllib.parse.urlencode({
                "client_id": ye["YT_CLIENT_ID"], "client_secret": ye["YT_CLIENT_SECRET"],
                "refresh_token": ye["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
            at = json.loads(urllib.request.urlopen(urllib.request.Request(
                "https://oauth2.googleapis.com/token", data=tbody), timeout=30).read().decode())["access_token"]
            def yapi(path):
                r = urllib.request.Request("https://www.googleapis.com/youtube/v3/" + path)
                r.add_header("Authorization", f"Bearer {at}")
                return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())
            ch = yapi("channels?part=statistics,contentDetails&mine=true")["items"][0]
            stt = ch["statistics"]
            # channels.viewCount EXCLUDES Shorts views — sum per-video views instead so
            # Shorts are counted (paged through the uploads playlist).
            uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
            vids, tok_, pages = [], "", 0
            while pages < 6:
                pl = yapi(f"playlistItems?part=contentDetails&maxResults=50&playlistId={uploads}" + (f"&pageToken={tok_}" if tok_ else ""))
                vids += [i["contentDetails"]["videoId"] for i in pl.get("items", [])]
                tok_ = pl.get("nextPageToken"); pages += 1
                if not tok_:
                    break
            total_views = total_likes = 0
            for i in range(0, len(vids), 50):
                for v in yapi("videos?part=statistics&id=" + ",".join(vids[i:i + 50])).get("items", []):
                    total_views += int(v["statistics"].get("viewCount", 0))
                    total_likes += int(v["statistics"].get("likeCount", 0))
            yt = {"connected": True, "subscribers": int(stt.get("subscriberCount", 0)),
                  "views": total_views, "likes": total_likes, "videos": int(stt.get("videoCount", 0))}
        except Exception:
            pass
    yt_done = len(jload("content/yt_state.json", {"done": []}).get("done", []))

    # Instagram stats (if connected)
    ig = {"connected": False, "followers": 0, "media": 0}
    if E.get("FB_IG_ID"):
        d = get(E["FB_IG_ID"], {"fields": "followers_count,media_count"}, stok)
        if "followers_count" in d or "media_count" in d:
            ig = {"connected": True, "followers": int(d.get("followers_count", 0)),
                  "media": int(d.get("media_count", 0))}

    # Email subscribers (Resend)
    email_subs = 0
    rp = os.path.join(ROOT, "secrets", "resend.env")
    if os.path.exists(rp):
        try:
            re_env = {}
            for line in open(rp):
                if "=" in line:
                    k, v = line.strip().split("=", 1); re_env[k] = v
            req = urllib.request.Request(
                f"https://api.resend.com/audiences/{re_env['RESEND_AUDIENCE_ID']}/contacts")
            req.add_header("Authorization", f"Bearer {re_env['RESEND_API_KEY']}")
            req.add_header("User-Agent", "curl/8.4.0")
            email_subs = len(json.loads(urllib.request.urlopen(req, timeout=30).read().decode()).get("data", []))
        except Exception:
            pass

    eng_total = rx + cm + sh
    reels_done = len(rst.get("done", []))
    posts_done = len(st.get("posted", [])) + 1

    # ---- project the upcoming schedule from the real posting rules ----
    created = dt.date.fromisoformat(st.get("page_created", dt.date.today().isoformat()))
    remaining_posts = [p for p in q if p["id"] not in set(st.get("posted", []))]
    remaining_reels = [r for r in rq if r["id"] not in set(rst.get("done", []))]
    upcoming, pi_, ri_ = [], 0, 0
    d = dt.date.today() + dt.timedelta(days=1)
    for _ in range(45):
        age = (d - created).days
        post_days = {1, 2, 3} if age < 14 else {0, 1, 2, 3, 4}
        if d.weekday() in post_days and pi_ < len(remaining_posts):
            p = remaining_posts[pi_]; pi_ += 1
            upcoming.append({"date": d.isoformat(), "type": "post", "icon": "📝",
                             "title": p["caption"][:60].split("\n")[0],
                             "sub": p["archetype"].replace("-", " ")})
        if d.weekday() in {1, 4} and ri_ < len(remaining_reels):
            r = remaining_reels[ri_]; ri_ += 1
            upcoming.append({"date": d.isoformat(), "type": "reel", "icon": "🎬",
                             "title": r["hook"], "sub": "Reel"})
        if pi_ >= len(remaining_posts) and ri_ >= len(remaining_reels):
            break
        d += dt.timedelta(days=1)
    upcoming.sort(key=lambda x: (x["date"], x["type"]))
    upcoming = upcoming[:12]

    # ---- goals vs target with pace ----
    goals_cfg = jload("content/goals.json", {"period": {}, "targets": []})
    per = goals_cfg.get("period", {})
    today = dt.date.today()
    actuals = {"followers": pi.get("followers_count", 0), "likes": pi.get("fan_count", 0),
               "engagement": eng_total, "posts_published": posts_done,
               "reels_published": reels_done, "video_views": ads["video_views"],
               "yt_shorts": max(yt_done, yt["videos"]), "yt_subscribers": yt["subscribers"],
               "yt_views": yt["views"], "ig_followers": ig["followers"],
               "email_subscribers": email_subs}
    g_items = []
    try:
        gs = dt.date.fromisoformat(per["start"]); ge = dt.date.fromisoformat(per["end"])
        total_days = max(1, (ge - gs).days); elapsed = max(0, min(total_days, (today - gs).days))
        days_left = max(0, (ge - today).days)
    except Exception:
        total_days, elapsed, days_left = 30, 0, 30
    for t in goals_cfg.get("targets", []):
        cur = actuals.get(t["key"], 0); tgt = t["target"] or 1
        pct = min(100, round(100 * cur / tgt))
        expected = tgt * elapsed / total_days
        g_items.append({"label": t["label"], "icon": t["icon"], "current": cur, "target": t["target"],
                        "pct": pct, "on_track": cur >= expected})

    # ---- funnel (reach -> engagement -> audience -> CR) + week-over-week trends ----
    foll = social_followers()
    total_aud = (pi.get("followers_count", 0) + ig["followers"] + yt["subscribers"]
                 + foll.get("Bluesky", 0) + foll.get("Mastodon", 0) + foll.get("Threads", 0)
                 + foll.get("Telegram", 0) + email_subs)
    cr_clicks = 0
    try:
        creq = urllib.request.Request("https://booked-job.com/cr/count", headers={"User-Agent": "curl/8.4.0"})
        cr_clicks = json.loads(urllib.request.urlopen(creq, timeout=15).read().decode()).get("clicks", 0)
    except Exception:
        pass
    funnel = {"reach": ads["reach"] or ads["video_views"], "engagement": eng_total,
              "audience": total_aud, "cr_clicks": cr_clicks}
    snap = {"date": today.isoformat(), "audience": total_aud, "engagement": eng_total,
            "email": email_subs, "reach": funnel["reach"]}
    days = [x for x in jload("content/metric_history.json", {"days": []}).get("days", []) if x.get("date") != snap["date"]]
    days = (days + [snap])[-90:]
    json.dump({"days": days}, open(os.path.join(ROOT, "content", "metric_history.json"), "w"), indent=2)

    def _delta(m):
        prior = next((x[m] for x in reversed(days[:-1]) if (today - dt.date.fromisoformat(x["date"])).days >= 7), None)
        return snap[m] - prior if prior is not None else 0
    trends = {m: _delta(m) for m in ("audience", "engagement", "email", "reach")}

    # ---- Mafia Mode: 6 plain-English metrics, letter-graded, + brutal summary ----
    chs = channels(email_subs, foll)
    # attach views + real follower counts where the platform exposes them
    ch_views = {"YouTube": yt["views"]}
    th_likes = {}
    thv = readenv("threads.env")
    if thv.get("THREADS_USER_ID") and thv.get("THREADS_TOKEN"):
        dv = _jget(f"https://graph.threads.net/v1.0/{thv['THREADS_USER_ID']}/threads_insights?metric=views,likes&access_token={thv['THREADS_TOKEN']}")
        try:
            for row in dv.get("data", []):
                if row.get("name") == "views":
                    ch_views["Threads"] = row["total_value"]["value"]
                elif row.get("name") == "likes":
                    th_likes["Threads"] = row["total_value"]["value"]
        except Exception:
            pass
    try:
        fv = get(f"{page}/insights", {"metric": "page_video_views", "period": "days_28"}, ptok)
        ch_views["Facebook"] = fv["data"][0]["values"][-1]["value"]
    except Exception:
        pass
    # Instagram — account-level views over the last 30 days (combines reels + posts +
    # stories, per the metric's own definition). Needs instagram_manage_insights.
    if E.get("FB_IG_ID"):
        try:
            _until = int(dt.datetime.now().timestamp()); _since = _until - 30 * 86400
            iv = get(f"{E['FB_IG_ID']}/insights",
                     {"metric": "views", "period": "day", "metric_type": "total_value",
                      "since": _since, "until": _until}, stok)
            ch_views["Instagram"] = iv["data"][0]["total_value"]["value"]
        except Exception:
            pass
    ch_foll = {"Facebook": pi.get("followers_count", 0), "Instagram": ig["followers"], "YouTube": yt["subscribers"]}
    ch_likes = {"Facebook": rx, "YouTube": yt.get("likes", 0), **th_likes, **social_engagement()}  # LinkedIn/TikTok from Buffer above
    for c in chs:
        if c["name"] in ch_views:
            c["views"] = ch_views[c["name"]]
        if c["name"] in ch_foll and "followers" not in c:
            c["followers"] = ch_foll[c["name"]]
        if c["name"] in ch_likes and "likes" not in c:
            c["likes"] = ch_likes[c["name"]]
    # ---- ORGANIC reach: sum every platform view/impression we can read + IG unique
    # reach + ad reach. Replaces the old ads-only value that read ~0 with no ad spend. ----
    total_impr = sum(int(c.get("views") or 0) for c in chs)
    ig_reach = 0
    if E.get("FB_IG_ID"):
        try:
            _u = int(dt.datetime.now().timestamp()); _s = _u - 30 * 86400
            rr = get(f"{E['FB_IG_ID']}/insights", {"metric": "reach", "period": "day",
                     "metric_type": "total_value", "since": _s, "until": _u}, stok)
            ig_reach = int(rr["data"][0]["total_value"]["value"])
        except Exception:
            pass
    funnel["reach"] = int(ads["reach"]) + int(ads["video_views"]) + total_impr + ig_reach
    snap["reach"] = funnel["reach"]                         # snap is days[-1] — updates history too
    json.dump({"days": days}, open(os.path.join(ROOT, "content", "metric_history.json"), "w"), indent=2)
    trends["reach"] = _delta("reach")
    total_posts = sum(c.get("count", 0) for c in chs)
    GR = [
        ("Total Views", yt["views"] + ads["video_views"], [50, 500, 5000, 50000]),
        ("Total Clicks", cr_clicks, [3, 20, 100, 500]),
        ("Total Posts", total_posts, [10, 30, 80, 200]),
        ("Total Reach", ads["reach"] + ads["impressions"], [100, 1000, 10000, 100000]),
        ("Audience Size", total_aud, [10, 50, 250, 1000]),
        ("Engagement", eng_total, [5, 25, 100, 500]),
    ]
    m_metrics = [{"label": k, "value": v, "grade": _grade(v, t)} for k, v, t in GR]
    gpts = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}
    avg = sum(gpts[m["grade"]] for m in m_metrics) / len(m_metrics)
    overall = "A" if avg >= 3.5 else "B" if avg >= 2.5 else "C" if avg >= 1.5 else "D" if avg >= 0.5 else "F"
    live_ch = sum(1 for c in chs if c["status"] == "live")
    mafia = {"metrics": m_metrics, "overall": overall,
             "summary": mafia_summary(overall, total_posts, total_aud, cr_clicks, live_ch)}

    data = {
        "updated": dt.datetime.now().isoformat(timespec="minutes"),
        "goals": {"label": per.get("label", "Sprint"), "end": per.get("end", ""),
                  "days_left": days_left, "rationale": goals_cfg.get("rationale", ""), "items": g_items},
        "strategist": jload("content/strategist.json", {}),
        "upcoming": upcoming,
        "page": {"name": pi.get("name", "Booked Job"),
                 "followers": pi.get("followers_count", 0), "likes": pi.get("fan_count", 0)},
        "content": {
            "posts_published": len(st.get("posted", [])) + 1,  # +1 manual intro
            "reactions": rx, "comments": cm, "shares": sh,
            "reels_published": len(rst.get("done", [])),
            "posts_remaining": max(0, len(q) - len(st.get("posted", []))),
            "reels_remaining": max(0, len(rq) - len(rst.get("done", []))),
        },
        "ads": ads,
        "youtube": {**yt, "shorts": max(yt_done, yt["videos"])},
        "instagram": ig,
        "email": {"subscribers": email_subs},
        "signups": {**_signup_stats(), "total": email_subs, "pct": round(100 * email_subs / GOAL_SIGNUPS, 1)},
        "search": _search_stats(),
        "buffer": _buffer_stats(),
        "agents": enumerate_agents(),
        "channels": chs,
        "coverage": coverage(),
        "runway": runway(),
        "funnel": funnel,
        "trends": trends,
        "mafia": mafia,
    }
    out = os.path.join(ROOT, "site", "dashboard", "data.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(data, open(out, "w"), indent=2)
    print(f"wrote {os.path.relpath(out)} — followers={data['page']['followers']} likes={data['page']['likes']} "
          f"posts={data['content']['posts_published']} reels={data['content']['reels_published']} spend=${ads['spend']}")


if __name__ == "__main__":
    main()
