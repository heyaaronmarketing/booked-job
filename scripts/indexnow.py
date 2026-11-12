#!/usr/bin/env python3
"""IndexNow pings — tell IndexNow-participating engines about new/updated URLs the
moment they publish, instead of waiting days for a crawl. The key is PUBLIC by
protocol design (served at the site root as proof of ownership), so it lives here.

By protocol, submitting to ANY one participating endpoint shares the URLs with the
whole IndexNow network. We POST to several and count success if ANY accepts, so one
engine rejecting doesn't fail the ping. CONFIRMED 2026-07-21: Yandex accepts (202)
and the URLs then show up in Bing Webmaster Tools -> IndexNow as Source: Self — i.e.
they DO reach Bing via the shared network. Bing's own direct endpoint still returns
403 UserForbiddedToAccessSite for direct POSTs of this key (its direct-submit key
check is stricter than its network ingestion), but that's cosmetic: the pings land.
booked-job.com (apex) is verified in Bing Webmaster Tools.

  python3 scripts/indexnow.py --all          # submit every URL in the sitemap
  python3 scripts/indexnow.py URL [URL ...]  # submit specific URLs

`submit(urls)` is importable — blog_drip_runner calls it after each publish."""
import json, os, re, sys, urllib.request, urllib.error

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
KEY = "bd9118e55980402a869f0d965da0b71c"          # public — also served at /<KEY>.txt
HOST = "booked-job.com"
# Yandex first (accepts today); api.indexnow.org fans out to the rest incl. Bing.
ENDPOINTS = ["https://yandex.com/indexnow", "https://api.indexnow.org/indexnow"]


def submit(urls):
    """POST to each endpoint; return the count that accepted (2xx). Never raises —
    a single engine's 403/4xx is logged, not fatal (IndexNow shares across the net)."""
    if not urls:
        return 0
    body = json.dumps({"host": HOST, "key": KEY,
                       "keyLocation": f"https://{HOST}/{KEY}.txt",
                       "urlList": urls[:10000]}).encode()
    accepted = 0
    for ep in ENDPOINTS:
        req = urllib.request.Request(ep, data=body, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8",
                                              "User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                if 200 <= r.status < 300:
                    accepted += 1
        except urllib.error.HTTPError as e:
            reason = ""
            try:
                reason = json.loads(e.read()).get("errorCode", "")
            except Exception:
                pass
            # 403 UserForbiddedToAccessSite = this key isn't claimed at that engine yet
            # (Bing/api-aggregator need booked-job.com verified in Bing Webmaster Tools → IndexNow).
            # Expected + non-fatal: Yandex accepts and fans the URLs across the IndexNow network.
            if not (e.code == 403 and reason == "UserForbiddedToAccessSite"):
                print(f"  {ep} -> {e.code} {reason}".rstrip())
        except Exception as e:
            print(f"  {ep} -> {str(e)[:80]}")
    return accepted


def sitemap_urls():
    sm = open(os.path.join(ROOT, "site", "sitemap.xml")).read()
    return re.findall(r"<loc>(.*?)</loc>", sm)


if __name__ == "__main__":
    urls = sitemap_urls() if "--all" in sys.argv else [a for a in sys.argv[1:] if a.startswith("http")]
    n = submit(urls)
    print(f"IndexNow: {len(urls)} URLs accepted by {n}/{len(ENDPOINTS)} endpoint(s)")
