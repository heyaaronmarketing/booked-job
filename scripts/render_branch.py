#!/usr/bin/env python3
"""
Render + wire Branch Series articles into the machine — OR stage them to drip
in gradually instead of publishing all at once.

  python3 scripts/render_branch.py live clean          # render+publish the fact-check-passed ones NOW
  python3 scripts/render_branch.py live slug1 slug2     # publish specific slugs NOW
  python3 scripts/render_branch.py stage clean 2        # STAGE clean ones to go live 2/day (drip)
  python3 scripts/render_branch.py stage all 3 2026-07-02   # stage all, 3/day, starting a date

Staged articles live in content/staged/<slug>.json + content/schedule.json;
scripts/blog_drip_runner.py (launchd, daily) promotes the due ones.
"""
import json, os, re, sys, html, datetime

ROOT = os.path.join(os.path.dirname(__file__), "..")
BLOG = os.path.join(ROOT, "site", "blog")
RESULT = os.path.join(ROOT, "content", "_branch_result.json")
SYND = os.path.join(ROOT, "content", "syndication_queue.json")
VAR = os.path.join(ROOT, "content", "channel_variants.json")
SITEMAP = os.path.join(ROOT, "site", "sitemap.xml")
IDX = os.path.join(ROOT, "site", "blog", "index.html")
QUEUE = os.path.join(ROOT, "content", "queue.json")
STAGED = os.path.join(ROOT, "content", "staged")
SCHEDULE = os.path.join(ROOT, "content", "schedule.json")
TODAY = datetime.date.today().isoformat()   # real publish date for sitemap lastmod (was hardcoded stale)
B = "https://booked-job.com"


CAPTURE_BLOCK = '''<div class="capture">
  <div class="cap-eyebrow">Free · For owners who'd rather be on the tools</div>
  <h3>Get the honest math — straight to your inbox</h3>
  <p>The real contractor-marketing numbers, one short email at a time: what leads actually cost, how many reviews it takes to rank, why answering the phone beats the ad budget. No fluff, no selling your info.</p>
  <form class="capform" action="/api/subscribe" method="post">
    <input type="email" name="email" placeholder="you@yourshop.com" required aria-label="Email address" />
    <button type="submit">Send me the good stuff &rarr;</button>
  </form>
  <div class="capnote">Join contractors reading the numbers nobody else will show them. Unsubscribe anytime.</div>
</div>'''

# Agency CTA (Aaron 2026-09-10): every page directly promotes Hey Aaron! Marketing (aaron.chat).
# Inline-styled so it renders identically on all 141 existing pages regardless of CSS.
AGENCY_CTA = '''<div class="agency-cta" style="background:#15171A;border:2px solid #FFD23F;border-radius:14px;padding:26px;margin:34px 0">
  <div style="color:#FFD23F;font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:.6px">Rather just have it done right?</div>
  <h3 style="color:#fff;margin:10px 0 6px;font-size:23px;line-height:1.25">Hey Aaron builds honest websites for contractors.</h3>
  <p style="color:#c7ccd3;margin:0 0 18px;font-size:15px;line-height:1.55">Flat <b style="color:#fff">$500</b>. No monthly games, no runaround &mdash; a site that does the four things that actually book jobs. Get found, get picked, get booked.</p>
  <a href="https://aaron.chat" style="display:inline-block;background:#FF6A00;color:#fff;font-weight:800;text-decoration:none;padding:13px 26px;border-radius:8px;font-size:15px">See aaron.chat &rarr;</a>
</div>'''


def render(a):
    slug = a["slug"]; url = f"{B}/blog/{slug}/"
    h1 = html.unescape(a["h1"])
    plain_h1 = re.sub("<[^>]+>", "", h1).replace("&amp;", "&")
    faq_ld = ",".join('{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
                      % (json.dumps(f["q"]), json.dumps(f["a"])) for f in a["faq"])
    secs = ""
    for s in a["body"]:
        ans = html.unescape(s.get("answer", "") or "")
        abox = f'<div class="answer">{ans}</div>' if ans.strip() else ""
        secs += f"\n  <h2>{html.unescape(s['h2'])}</h2>{abox}\n  {html.unescape(s['html'])}"
    faq_html = "".join(f'\n  <h3>{f["q"]}</h3>\n  <p>{f["a"]}</p>' for f in a["faq"])
    lead = re.sub("<[^>]+>", "", a["body"][0]["html"]) if a["body"] else ""
    lead = html.unescape(lead).strip()
    lead = (lead[:300].rsplit(".", 1)[0] + ".") if len(lead) > 300 else lead
    big, lab = a["statBig"], a["statLabel"]
    # IMAGE GUARANTEE: generate a per-article stat card so every link share (Bluesky,
    # Threads, FB, LinkedIn, etc.) renders with the article's headline number as og:image.
    og_img = f"{B}/assets/og-default.png"
    try:
        import make_statcard
        sd = os.path.join(ROOT, "site", "blog", slug); os.makedirs(sd, exist_ok=True)
        msrc = re.search(r'\[([^\]]+)\]', lab)
        src = (msrc.group(1) if msrc else "Booked Job").strip()
        make_statcard.render({"value": big, "metric": re.sub(r'\s*\[[^\]]*\]', '', lab).split('·')[0].strip()[:80],
                              "source_name": src[:28], "date": TODAY}, "sq", os.path.join(sd, "card.png"))
        og_img = f"{url}card.png"
    except Exception:
        pass
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{a['title']}</title>
<meta name="description" content="{a['meta']}" />
<link rel="canonical" href="{url}" />
<meta property="og:type" content="article" /><meta property="og:title" content="{a['title']}" />
<meta property="og:description" content="{a['meta']}" /><meta property="og:url" content="{url}" />
<meta property="og:image" content="{og_img}" /><meta property="og:image:width" content="1080" /><meta property="og:image:height" content="1080" />
<meta name="twitter:card" content="summary_large_image" /><meta name="twitter:image" content="{og_img}" />
<meta name="theme-color" content="#15171A" />
<link rel="stylesheet" href="/assets/article.css" />
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[
{{"@type":"Article","headline":{json.dumps(plain_h1)},"description":{json.dumps(a['meta'])},
"datePublished":"{TODAY}","dateModified":"{TODAY}",
"author":{{"@type":"Person","name":"Aaron Phillips","jobTitle":"Founder, Booked Job","url":"https://booked-job.com/about/"}},
"publisher":{{"@type":"Organization","name":"Booked Job","url":"https://booked-job.com/"}},
"mainEntityOfPage":"{url}"}},
{{"@type":"BreadcrumbList","itemListElement":[
{{"@type":"ListItem","position":1,"name":"Booked Job","item":"https://booked-job.com/"}},
{{"@type":"ListItem","position":2,"name":"Blog","item":"https://booked-job.com/blog/"}},
{{"@type":"ListItem","position":3,"name":{json.dumps(plain_h1)},"item":"{url}"}}]}},
{{"@type":"FAQPage","mainEntity":[{faq_ld}]}}]}}
</script></head><body>
<header><div class="nav">
  <a class="logo" href="/"><span class="mark">B</span><b>BOOKED<span>JOB</span></b></a>
  <a class="cta" href="https://www.facebook.com/bookedjob" target="_blank" rel="noopener">Follow</a>
</div></header><div class="tape"></div>
<article class="wrap">
  <p class="crumb"><a href="/">Home</a> › <a href="/blog/">Blog</a> › {plain_h1}</p>
  <h1>{h1}</h1>
  <div class="meta"><span class="av">AP</span> By Aaron Phillips · Booked Job · Updated June 2026</div>
  <div class="answer"><b>Short answer:</b> {a['short']}</div>
  <p class="lead">{lead}</p>
  <div class="stat"><div class="big">{big}</div><div class="lab">{lab}</div></div>{secs}
  <h2>Frequently asked questions</h2>{faq_html}
  {AGENCY_CTA}
  {CAPTURE_BLOCK}
  <p class="answer" style="font-size:14px">More free tools: the <a href="https://booked-job.com/tools/">contractor calculators</a> and the <a href="https://booked-job.com/">Marketing 101 course</a>.</p>
</article>
<footer style="text-align:center;padding:40px;color:#888;font-size:14px">© Booked Job · Honest marketing for the trades · <a href="https://booked-job.com/">booked-job.com</a></footer>
<script src="/assets/capture.js" defer></script>
</body></html>"""


def wire_articles(picks):
    """Render each article live + wire into syndication, variants, sitemap, blog index, FB/IG queue."""
    synd = json.load(open(SYND)); sids = {i["id"] for i in synd["items"]}
    cv = json.load(open(VAR))
    sm = open(SITEMAP).read(); idx = open(IDX).read()
    new_cards = ""; new_sm = ""; built = []
    for a in picks:
        slug = a["slug"]; url = f"{B}/blog/{slug}/"
        d = os.path.join(BLOG, slug); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w").write(render(a)); built.append(slug)
        if slug not in sids:
            synd["items"].append({"id": slug, "title": a["title"], "labels": a["labels"],
                                  "short_title": a["_series"], "blurb": a["short"], "url": url, "posted": {}})
        cv[slug] = a["variants"]
        if f"/blog/{slug}/" not in sm:
            new_sm += f'  <url><loc>{url}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'
        new_cards += (f'\n    <a class="post" href="/blog/{slug}/">\n      <span class="tag">{a["_series"]}</span>'
                      f'\n      <h2>{html.unescape(a["title"])}</h2>\n      <p>{a["short"][:160]}</p>\n    </a>')
        # NOTE (pure-engagement pivot 2026-07-17): we intentionally NO LONGER push
        # branch-series link posts into the FB engagement queue (content/queue.json).
        # The FB feed is 100% native engagement (seed_content.py); blog articles are
        # syndicated for SEO/backlinks via syndication_queue.json (added above) only.
    json.dump(synd, open(SYND, "w"), indent=2)
    json.dump(cv, open(VAR, "w"), indent=1, ensure_ascii=False)
    open(SITEMAP, "w").write(sm.replace("</urlset>", new_sm + "</urlset>"))
    open(IDX, "w").write(idx.replace('<div class="grid">', '<div class="grid">' + new_cards, 1))
    import xml.dom.minidom; xml.dom.minidom.parse(SITEMAP)
    return built


def stage_articles(picks, per_day, start):
    """Save article data + a staggered go-live date; the drip runner publishes when due."""
    os.makedirs(STAGED, exist_ok=True)
    sched = json.load(open(SCHEDULE)) if os.path.exists(SCHEDULE) else {"items": []}
    have = {it["slug"] for it in sched["items"]}
    n = 0
    for i, a in enumerate([p for p in picks if p["slug"] not in have]):
        json.dump(a, open(os.path.join(STAGED, f"{a['slug']}.json"), "w"), ensure_ascii=False)
        go = start + datetime.timedelta(days=i // per_day)
        sched["items"].append({"slug": a["slug"], "series": a.get("_series", ""),
                               "go_live": go.isoformat(), "status": "pending"})
        n += 1
    json.dump(sched, open(SCHEDULE, "w"), indent=2)
    return n, sched


def pick(arts, sel):
    if sel == ["clean"]:
        return [a for a in arts if a.get("_verdict", {}).get("allNumbersSourced")]
    if sel == ["all"]:
        return arts
    return [a for a in arts if a["slug"] in sel]


def main():
    args = sys.argv[1:]
    mode = args[0] if args and args[0] in ("live", "stage") else "live"
    rest = args[1:] if mode in ("live", "stage") else args
    arts = json.load(open(RESULT))["articles"]
    if mode == "stage":
        per_day = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 2
        start = (datetime.date.fromisoformat(rest[2]) if len(rest) > 2 and re.match(r"\d{4}-", rest[2])
                 else datetime.date.today() + datetime.timedelta(days=1))
        sel = [rest[0]] if rest and rest[0] in ("clean", "all") else (rest or ["clean"])
        sel = [s for s in sel if not s.isdigit() and not re.match(r"\d{4}-", s)] or ["clean"]
        picks = pick(arts, sel)
        n, sched = stage_articles(picks, per_day, start)
        last = sched["items"][-1]["go_live"] if sched["items"] else "?"
        print(f"staged {n} articles · {per_day}/day starting {start} · last goes live {last}")
    else:
        sel = rest or ["clean"]
        built = wire_articles(pick(arts, sel))
        print(f"published {len(built)} articles now: {', '.join(built)}")


if __name__ == "__main__":
    main()
