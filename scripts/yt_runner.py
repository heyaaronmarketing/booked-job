#!/usr/bin/env python3
"""
Autonomous YouTube Shorts runner (launchd, ~3x/week). Generates the next queued
Short with the faceless pipeline (ElevenLabs voice + synced captions) and uploads
it via the Data API. YouTube was the strongest single AI-citation signal in our
research, so this is a core organic channel — not an afterthought.

State: content/yt_state.json. Log: content/youtube.log.
Flags: --force, --dry-run, --status.
"""
import argparse, datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import make_reel, yt_upload

QUEUE = os.path.join(ROOT, "content", "yt_queue.json")
STATE = os.path.join(ROOT, "content", "yt_state.json")
LOG = os.path.join(ROOT, "content", "youtube.log")
OUTDIR = os.path.join(ROOT, "content", "shorts")

POST_DAYS = {0, 1, 2, 3, 4, 5, 6}   # DAILY (2026-11-12, Aaron): YouTube Shorts is the top channel
WINDOW = (8, 20)                     # (ER 2.59% vs FB 0.09%) and had 64 pre-rendered Shorts queued and
GAP_HOURS = 10                       # starved at 3/wk. Unthrottled to ~1-2/day — queue = ~5-6 wks runway.


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    shorts = load(QUEUE, {"shorts": []})["shorts"]
    state = load(STATE, {"done": [], "last_iso": None})
    done = set(state["done"])

    if a.status:
        rem = [s["id"] for s in shorts if s["id"] not in done]
        print(json.dumps({"done": len(done), "remaining": rem}, indent=2)); return

    if not os.path.exists(os.path.join(ROOT, "secrets", "youtube.env")) and not a.dry_run:
        log("YouTube not connected yet (no secrets/youtube.env) — skipping."); return

    nxt = next((s for s in shorts if s["id"] not in done), None)
    if not nxt:
        log("YouTube queue empty — refill content/yt_queue.json"); return

    now = dt.datetime.now()
    if not a.force:
        if now.weekday() not in POST_DAYS:
            log(f"skip: {now:%A} not a Shorts day"); return
        if not (WINDOW[0] <= now.hour < WINDOW[1]):
            log(f"skip: outside window {WINDOW}"); return
        if state.get("last_iso"):
            gap = (now - dt.datetime.fromisoformat(state["last_iso"])).total_seconds() / 3600
            if gap < GAP_HOURS:
                log(f"skip: only {gap:.0f}h since last Short (gap {GAP_HOURS}h)"); return

    out = os.path.join(OUTDIR, f"{nxt['id']}.mp4")
    pre = nxt.get("video")
    if pre:   # pre-rendered clip (e.g. Remotion reels) — upload as-is, no re-render
        src = pre if os.path.isabs(pre) else os.path.join(ROOT, pre)
        if not os.path.exists(src):
            log(f"PRE-RENDERED MISSING '{nxt['id']}': {src}"); return
        out = src
        log(f"using pre-rendered video '{nxt['id']}' -> {out}")
    else:
        log(f"building Short '{nxt['id']}' …")
        try:
            make_reel.build(nxt["hook"], nxt["script"], out, backend="elevenlabs")
        except SystemExit as e:
            log(f"BUILD FAILED '{nxt['id']}': {e}"); return

    if a.dry_run:
        log(f"DRY-RUN built {out}, not uploading"); return

    import cta
    res = yt_upload.publish(out, nxt["title"], cta.append(nxt["description"], "youtube"), nxt["tags"], privacy="public")
    vid = res.get("id")
    if vid and nxt.get("thumbnail"):
        tp = nxt["thumbnail"] if os.path.isabs(nxt["thumbnail"]) else os.path.join(ROOT, nxt["thumbnail"])
        try:
            yt_upload.set_thumbnail(vid, tp); log(f"set custom thumbnail for {vid}")
        except Exception as e:
            log(f"thumbnail set FAILED for {vid}: {str(e)[:140]}")
    done.add(nxt["id"])
    state["done"] = list(done); state["last_iso"] = now.isoformat(timespec="seconds")
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"PUBLISHED Short '{nxt['id']}' -> https://youtu.be/{vid}")
    try:
        import log_change
        log_change.add("reel", f"Published YouTube Short: {nxt['title'].split('#')[0].strip()}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
