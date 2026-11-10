#!/usr/bin/env python3
"""
Cloudflare traffic connector. Pulls daily page views for booked-job.com from the
Cloudflare GraphQL Analytics API (zone-level — works for any proxied domain, no
beacon/code needed). Feeds the website-traffic goal in the nightly review.

Needs secrets/cloudflare.env:
  CLOUDFLARE_API_TOKEN=...        (a token with Zone → Analytics → Read)
  CLOUDFLARE_ZONE_ID=...          (booked-job.com zone id, from the CF dashboard)

  python3 scripts/cf_analytics.py --test     # print the last 7 days of page views
"""
import datetime as dt, json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
ENV = os.path.join(ROOT, "secrets", "cloudflare.env")


def env():
    if not os.path.exists(ENV):
        return None
    e = {}
    for l in open(ENV):
        l = l.strip()
        if "=" in l and not l.startswith("#"):
            k, v = l.split("=", 1); e[k.strip()] = v.strip()
    # Prefer a dedicated Analytics:Read token; fall back to the deploy token.
    e["_CF_TOKEN"] = e.get("CLOUDFLARE_ANALYTICS_TOKEN") or e.get("CLOUDFLARE_API_TOKEN")
    return e if e.get("_CF_TOKEN") and e.get("CLOUDFLARE_ZONE_ID") else None


def daily_pageviews(days=35):
    """Return {date: pageViews} for the last `days`, or None if not configured."""
    e = env()
    if not e:
        return None
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    q = ("query($zone:String!,$since:Date!){viewer{zones(filter:{zoneTag:$zone}){"
         "httpRequests1dGroups(limit:60,filter:{date_geq:$since},orderBy:[date_ASC]){"
         "dimensions{date} sum{pageViews}}}}}")
    body = json.dumps({"query": q, "variables": {"zone": e["CLOUDFLARE_ZONE_ID"], "since": since}}).encode()
    req = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", data=body, method="POST",
                                 headers={"Authorization": f"Bearer {e['_CF_TOKEN']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    if d.get("errors"):
        raise RuntimeError(str(d["errors"])[:200])
    groups = d["data"]["viewer"]["zones"][0]["httpRequests1dGroups"]
    return {g["dimensions"]["date"]: int(g["sum"]["pageViews"]) for g in groups}


def windows(period_start, today=None):
    """Return (daily, weekly, monthly) page-view totals, or None if not configured."""
    pv = daily_pageviews()
    if pv is None:
        return None
    today = today or dt.date.today()
    def total(since):
        return sum(v for d, v in pv.items() if d >= since)
    return {
        "daily": pv.get((today - dt.timedelta(days=1)).isoformat(), pv.get(today.isoformat(), 0)),
        "weekly": total((today - dt.timedelta(days=7)).isoformat()),
        "monthly": total(period_start),
    }


def main():
    if "--test" in sys.argv:
        try:
            pv = daily_pageviews(7)
            if pv is None:
                print("Cloudflare not configured — add secrets/cloudflare.env (TOKEN + ZONE_ID)."); return
            for d, v in sorted(pv.items()):
                print(f"  {d}: {v} page views")
            print(f"  7-day total: {sum(pv.values())}")
        except Exception as e:
            print(f"failed: {e}")


if __name__ == "__main__":
    main()
