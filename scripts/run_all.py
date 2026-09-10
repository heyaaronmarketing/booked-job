#!/usr/bin/env python3
"""
Dispatcher for the GitHub Actions host. Runs every Booked Job agent once. Each
agent self-gates on its own schedule/window (posting days, time windows, gap
checks), so running this hourly reproduces the old launchd cadence without
replicating 35 schedules. Failures are isolated — one bad agent never kills the
run. The workflow does a single git commit+push after this finishes.

  python3 scripts/run_all.py            # run all
  python3 scripts/run_all.py --light    # skip the media-generating agents
"""
import os, subprocess, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
LOG = os.path.join(ROOT, "content", "run_all.log")

# order: fresh stats -> build -> publish -> syndicate -> visual formats -> engage -> drip -> review
AGENTS = [
    ("fetch_stats.py", []),
    ("discover_communities.py", []), ("build_tasks.py", []), ("newsletter_build.py", []),
    ("publisher.py", []), ("ig_runner.py", []),
    ("reel_runner.py", []), ("reel_story_runner.py", []), ("story_runner.py", []),
    ("video_pool_runner.py", []),
    ("blogger_runner.py", []), ("tumblr_runner.py", []), ("telegraph_runner.py", []), ("github_pages_runner.py", []),
    ("bluesky_runner.py", []), ("mastodon_runner.py", []), ("threads_runner.py", []),
    ("buffer_runner.py", []), ("buffer_tiktok_runner.py", []),
    ("buffer_carousel_runner.py", []), ("buffer_tiktok_carousel_runner.py", []),
    ("fb_carousel_runner.py", []), ("ig_carousel_runner.py", []),
    ("image_pool_runner.py", []),
    ("pinterest_buffer_runner.py", []), ("email_drip_runner.py", []),
    # ("backlink_outreach.py", []),  # PAUSED 2026-09-10 (Aaron: stop email outreach) — sender OFF
    ("outreach_inbox.py", []),      # surface replies to hello@booked-job.com (read-only; sends nothing)
    # ("outreach_reply.py", []),    # PAUSED 2026-09-10 (Aaron: stop email outreach) — autonomous replier OFF
    ("bluesky_feed_refresh.py", []), ("yt_runner.py", []),
    ("podcast_runner.py", []),  # video→YouTube long-form (own queue: podcast_video_queue.json)
    ("bluesky_engage.py", []), ("threads_engage.py", []), ("fb_engage.py", []),
    ("ig_engage.py", []), ("youtube_engage.py", []), ("ig_dm_inbox.py", []),
    ("fb_report.py", []),
    ("build_recent.py", []),
    ("blog_drip_runner.py", []),
    ("build_llms_full.py", []),   # AEO: full-content file for AI engines, refreshed after drip
    ("nightly_review.py", ["--no-fetch"]),
    ("health_alert.py", []),
    ("founder_digest.py", []),   # emails Aaron a status rollup ~every 2h + on major events
]
MEDIA = {"reel_runner.py", "reel_story_runner.py", "story_runner.py", "buffer_carousel_runner.py",
         "buffer_tiktok_carousel_runner.py", "fb_carousel_runner.py", "ig_carousel_runner.py",
         "pinterest_buffer_runner.py"}
# agents that accept --force (post the next queued item now, bypassing time-window gates).
# Excludes blog_drip (must stay date-gated) and the build/engage/fetch scripts.
FORCE_OK = {"publisher.py", "ig_runner.py", "reel_runner.py", "reel_story_runner.py", "story_runner.py",
            "blogger_runner.py", "tumblr_runner.py", "telegraph_runner.py", "github_pages_runner.py",
            "bluesky_runner.py", "mastodon_runner.py", "threads_runner.py",
            "buffer_runner.py", "buffer_tiktok_runner.py",
            "buffer_carousel_runner.py", "buffer_tiktok_carousel_runner.py", "fb_carousel_runner.py",
            "ig_carousel_runner.py", "pinterest_buffer_runner.py", "yt_runner.py", "video_pool_runner.py",
            "image_pool_runner.py", "podcast_runner.py"}


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line, flush=True); open(LOG, "a").write(line + "\n")


def main():
    light = "--light" in sys.argv
    force = "--force" in sys.argv or bool(os.environ.get("FORCE"))
    if force:
        log("FORCE MODE — pushing the next queued item to every channel, bypassing time gates.")
    ok = fail = skip = 0
    hp = os.path.join(ROOT, "content", "agent_health.json")
    try:
        health = __import__("json").load(open(hp))
    except Exception:
        health = {}
    for script, args in AGENTS:
        if light and script in MEDIA:
            skip += 1; continue
        p = os.path.join(HERE, script)
        if not os.path.exists(p):
            continue
        a = list(args)
        if force and script in FORCE_OK and "--force" not in a:
            a.append("--force")
        rc = None
        try:
            r = subprocess.run([sys.executable, p, *a], cwd=ROOT, timeout=900, capture_output=True, text=True)
            rc = r.returncode
            tail = (r.stdout.strip().splitlines() or [""])[-1][:140]
            log(f"{script}: rc={rc} {tail}")
            ok += 1 if rc == 0 else 0
            fail += 0 if rc == 0 else 1
            if rc != 0 and r.stderr.strip():
                log(f"   stderr: {r.stderr.strip().splitlines()[-1][:160]}")
        except subprocess.TimeoutExpired:
            fail += 1; log(f"{script}: TIMEOUT")
        except Exception as e:
            fail += 1; log(f"{script}: ERROR {str(e)[:140]}")
        # per-agent consecutive-failure tracking (feeds health_alert.py)
        health[script] = 0 if rc == 0 else health.get(script, 0) + 1
    __import__("json").dump(health, open(hp, "w"), indent=2)
    log(f"run_all done — {ok} ok, {fail} failed, {skip} skipped")


if __name__ == "__main__":
    main()
