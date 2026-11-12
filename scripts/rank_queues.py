#!/usr/bin/env python3
"""Close the engagement feedback loop.

engagement_tracker.py measures what actually earns engagement (content/engagement_insights.json)
but nothing consumed it — the signal was dead. This reorders the VIDEO queues so the
content that matches proven winners posts FIRST, instead of blind FIFO.

The data (2026-11): YouTube Shorts is the only channel that engages, and every top post is a
VERDICT + HARD NUMBER on a tool/lead-mill topic ("Angi costs $542/job", "FTC fined HomeAdvisor
$7.2M", "Answer in 5 minutes", "Yelp: worth it?"). So we score each unposted item's hook by:
  - contains a number / dollar amount          (verdict content leads with the number)
  - tool/lead-mill/review topic terms          (the subjects that win)
  - verdict/curiosity hook words               ("worth it", "vs", "scam", "truth", "stop", "fix")
  - words lifted LIVE from the current top-performing captions (self-updating as winners change)

Then stable-sorts each queue by score (desc). Runners still pop "next unposted by id", so the
best-matching item is simply next. All items are preserved — nothing dropped or duplicated.

  python3 scripts/rank_queues.py            # reorder in place
  python3 scripts/rank_queues.py --dry-run  # show the new top of each queue, write nothing
"""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
INSIGHTS = os.path.join(ROOT, "content", "engagement_insights.json")
QUEUES = [  # (file, list-key, item text fields to score)
    ("content/yt_queue.json", "shorts", ("hook", "title", "description")),
    ("content/reels_queue.json", "reels", ("hook", "description")),
]

# Static winner lexicon drawn from the engagement data. Weighted.
TOPICS = ["angi", "thumbtack", "homeadvisor", "home advisor", "yelp", "nextdoor", "google",
          "lead", "leads", "review", "reviews", "star", "ftc", "ai receptionist", "receptionist",
          "bot", "missed call", "missed-call", "speed", "5 minute", "five minute", "map pack",
          "lsa", "local service", "booked", "cost per", "shared lead"]
VERDICT = ["worth it", " vs ", "vs.", "costs", "cost ", "scam", "truth", "stop", "fix", "really",
           "actually", "why ", "lie", "wrong", "don't", "dont", "beats", "waste", "rip"]
NUM_RE = re.compile(r"\$\s?\d|\b\d{2,}\b|\b\d+\s?(x|%|star|min|minute|review|dollar|pro|job)")


def load_signal():
    """Return a set of significant words lifted from the current top-performing captions,
    so the ranking self-updates as the winners change. Empty set if no insights yet."""
    try:
        d = json.load(open(INSIGHTS))
    except Exception:
        return set()
    words = set()
    for p in d.get("top", [])[:12]:
        for w in re.findall(r"[a-z]{4,}", (p.get("caption", "") or "").lower()):
            words.add(w)
    stop = {"your", "that", "this", "with", "from", "they", "what", "when", "here", "shorts",
            "contractor", "contractors", "booked", "free", "episode", "about", "them", "their"}
    return words - stop


def score(item, fields, signal):
    text = " ".join(str(item.get(f, "")) for f in fields).lower()
    s = 0
    if NUM_RE.search(text):
        s += 3
    s += 2 * min(3, sum(1 for t in TOPICS if t in text))
    s += 1 * min(3, sum(1 for v in VERDICT if v in text))
    s += 1 * min(4, sum(1 for w in signal if w in text))
    return s


def main():
    dry = "--dry-run" in sys.argv
    signal = load_signal()
    for rel, key, fields in QUEUES:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        items = d.get(key) if isinstance(d, dict) else d
        if not isinstance(items, list) or not items:
            continue
        before = [it.get("id") for it in items[:5]]
        # stable sort: higher score first, original order preserved within equal scores
        ranked = sorted(items, key=lambda it: -score(it, fields, signal))
        if isinstance(d, dict):
            d[key] = ranked
        else:
            d = ranked
        after = [(it.get("id"), score(it, fields, signal)) for it in ranked[:5]]
        print(f"{rel}: {len(items)} items | new top-5: {after}")
        if before != [a[0] for a in after]:
            print(f"   (was: {before})")
        if not dry:
            json.dump(d, open(path, "w"), ensure_ascii=False, indent=2)
    if dry:
        print("\n(dry-run — nothing written)")


if __name__ == "__main__":
    main()
