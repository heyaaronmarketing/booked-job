#!/usr/bin/env python3
"""Track where booked-job.com/reviews ranks for each review's target keyword.
DataForSEO SERP (creds ~/.dataforseo). Saves a dated snapshot to
content/review_ranks.json so we can watch the Reviews Desk climb. Run weekly.

  python3 scripts/review_rank_tracker.py
"""
import base64, datetime as dt, json, os, urllib.request

CRED = open(os.path.expanduser("~/.dataforseo")).read().split()
AUTH = base64.b64encode(f"{CRED[0]}:{CRED[1]}".encode()).decode()
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STORE = os.path.join(ROOT, "content", "review_ranks.json")

# keyword -> the review slug we built for it (we own a page for each)
TARGETS = {
    "is angi worth it": "is-angi-worth-it-for-contractors",
    "angi leads review": "is-angi-worth-it-for-contractors",
    "is thumbtack worth it": "is-thumbtack-worth-it-for-contractors",
    "is homeadvisor worth it": "is-homeadvisor-worth-it-for-contractors",
    "homeadvisor review": "is-homeadvisor-worth-it-for-contractors",
    "jobber review": "jobber-review",
    "jobber vs housecall pro": "jobber-vs-housecall-pro",
    "housecall pro review": "housecall-pro-review",
    "servicetitan review": "servicetitan-review",
    "workiz review": "workiz-review",
    "best field service software": "jobber-vs-housecall-pro",
    "is an ai receptionist worth it": "is-an-ai-receptionist-worth-it",
    "best ai receptionist for contractors": "best-ai-receptionist-for-contractors",
    "smith.ai review": "smith-ai-review",
    "rosie ai review": "rosie-ai-review",
    "goodcall review": "goodcall-review",
    "ai receptionist for plumbers": "ai-receptionist-for-plumbers",
}


def serp(keyword):
    body = json.dumps([{"keyword": keyword, "location_code": 2840, "language_code": "en", "depth": 100}]).encode()
    req = urllib.request.Request("https://api.dataforseo.com/v3/serp/google/organic/live/advanced",
                                 data=body, headers={"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"})
    res = json.loads(urllib.request.urlopen(req, timeout=90).read())
    task = res["tasks"][0]
    items = (task.get("result") or [{}])[0].get("items") or []
    pos = None
    for it in items:
        if it.get("type") == "organic" and "booked-job.com" in (it.get("url") or ""):
            pos = it.get("rank_absolute"); break
    return pos, task.get("cost", 0)


def main():
    import sys
    today = dt.date.today().isoformat()
    # Weekly self-gate: this costs DataForSEO per sweep, so when called from the hourly
    # run_all it only actually runs if the last snapshot is 7+ days old. --force overrides.
    if "--force" not in sys.argv and os.path.exists(STORE):
        try:
            hist0 = json.load(open(STORE))
            last = max(hist0) if hist0 else None
            if last and (dt.date.today() - dt.date.fromisoformat(last)).days < 7:
                print(f"skip: last rank sweep {last} (<7 days). --force to override."); return
        except Exception:
            pass
    rows, cost = {}, 0.0
    for kw, slug in TARGETS.items():
        try:
            pos, c = serp(kw); cost += c
        except Exception as e:
            pos = None; print(f"  !! {kw}: {str(e)[:80]}")
        rows[kw] = {"slug": slug, "pos": pos}
        print(f"  {('#'+str(pos)) if pos else 'not in top 100':>14}  {kw}")
    hist = json.load(open(STORE)) if os.path.exists(STORE) else {}
    hist[today] = rows
    json.dump(hist, open(STORE, "w"), indent=2)
    ranked = sum(1 for r in rows.values() if r["pos"])
    print(f"\n{today}: {ranked}/{len(TARGETS)} keywords ranking in top 100  (DataForSEO cost ${cost:.2f})")
    print(f"saved -> {os.path.relpath(STORE)}")


if __name__ == "__main__":
    main()
