#!/usr/bin/env python3
"""
Autonomous GitHub Pages syndication (launchd, weekly). Mirrors each blog article
to the booked-job-articles GitHub Pages repo as a FULL page with rel=canonical
back to booked-job.com (so it builds authority + a dofollow link without
cannibalizing our own SEO). Root-relative asset/links are rewritten to absolute
booked-job.com URLs so the mirror renders standalone.

Reuses content/syndication_queue.json (source HTML at site/blog/<id>/index.html).
State: content/ghpages_state.json. Log: content/ghpages.log. Gated until connected.
"""
import argparse, datetime as dt, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)

QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
STATE = os.path.join(ROOT, "content", "ghpages_state.json")
LOG = os.path.join(ROOT, "content", "ghpages.log")


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def load(p, d):
    return json.load(open(p)) if os.path.exists(p) else d


def mirror_html(slug):
    src = os.path.join(ROOT, "site", "blog", slug, "index.html")
    if not os.path.exists(src):
        return None
    html = open(src).read()
    # make root-relative paths absolute so the page renders off-site
    html = re.sub(r'(href|src)="/(?!/)', r'\1="https://booked-job.com/', html)
    # belt-and-suspenders: ensure a canonical to the original exists
    if "rel=\"canonical\"" not in html:
        html = html.replace("</head>",
                            f'<link rel="canonical" href="https://booked-job.com/blog/{slug}/" />\n</head>')
    return html


INDEX = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Booked Job — Articles for the Trades</title>
<link rel="canonical" href="https://booked-job.com/blog/">
<style>body{font-family:system-ui,sans-serif;background:#0e2235;color:#fff;text-align:center;padding:60px 22px}
a{color:#a62d1a}h1{font-family:Impact,sans-serif;text-transform:uppercase}</style></head>
<body><h1>BOOKED<span style="color:#a62d1a">JOB</span></h1>
<p>Real talk for service pros — plumbers, roofers, HVAC, electricians.</p>
<p><a href="https://booked-job.com/">Read everything at booked-job.com →</a></p></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()

    items = load(QUEUE, {"items": []})["items"]
    state = load(STATE, {"done": []})
    done = set(state["done"])

    if a.status:
        print(json.dumps({"done": len(done), "remaining": [i["id"] for i in items if i["id"] not in done]}, indent=2)); return

    if not os.path.exists(os.path.join(ROOT, "secrets", "github.env")):
        log("GitHub Pages not connected yet (no secrets/github.env) — skipping."); return

    import github_pages_publish
    if not state.get("pages_enabled"):
        github_pages_publish.put_file("index.html", INDEX, "init: index")
        log("pages: " + github_pages_publish.enable_pages())
        state["pages_enabled"] = True
        json.dump(state, open(STATE, "w"), indent=2)

    import post_cadence
    if not a.force and not post_cadence.due(state, 8):
        log("skip: GitHub Pages cadence gate (~3/day)"); return
    nxt = next((i for i in items if i["id"] not in done), None)
    if not nxt:
        log("syndication queue empty — nothing new for GitHub Pages."); return

    html = mirror_html(nxt["id"])
    if not html:
        log(f"no source article for '{nxt['id']}' (site/blog/{nxt['id']}/index.html) — skip."); return
    url = github_pages_publish.put_file(f"{nxt['id']}/index.html", html, f"syndicate: {nxt['id']}")
    done.add(nxt["id"]); state["done"] = list(done); post_cadence.stamp(state)
    json.dump(state, open(STATE, "w"), indent=2)
    log(f"SYNDICATED '{nxt['id']}' to GitHub Pages -> {url}")
    try:
        import log_change
        log_change.add("site", f"Syndicated to GitHub Pages (canonical backlink): {nxt['title']}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
