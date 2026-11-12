#!/usr/bin/env python3
"""Render a trade-specific custom asset on demand (the negotiator's deliverable).
Writes site/tools/<slug>/index.html + adds it to the sitemap, returns the live URL.
Only produces the two safe, on-brand asset kinds: a cost-per-booked-job calculator
or a sourced stats snippet — both reuse our approved numbers, nothing invented."""
import html, os, re, xml.dom.minidom

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TOOLSDIR = os.path.join(ROOT, "site", "tools")
SITEMAP = os.path.join(ROOT, "site", "sitemap.xml")
B = "https://booked-job.com"

HEAD = """<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title} | Booked Job</title>
<meta name="description" content="{meta}" />
<link rel="canonical" href="{url}" />
<meta property="og:type" content="website" /><meta property="og:title" content="{ogt}" />
<meta property="og:description" content="{meta}" /><meta property="og:url" content="{url}" />
<meta property="og:image" content="https://booked-job.com/assets/og-default.png" />
<meta name="theme-color" content="#15171A" />
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet" />
<link rel="stylesheet" href="/assets/article.css" />
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebApplication","name":"{ogt}","url":"{url}",
"applicationCategory":"BusinessApplication","operatingSystem":"Web",
"offers":{{"@type":"Offer","price":"0","priceCurrency":"USD"}},
"publisher":{{"@type":"Organization","name":"Booked Job","url":"https://booked-job.com/"}}}}
</script>
<style>
.tool{{background:#1D2025;border:1px solid #2E3238;border-radius:16px;padding:28px;margin:26px 0}}
.tool label{{display:block;font-weight:700;margin:16px 0 6px;font-size:15px}}
.tool input{{width:100%;max-width:280px;padding:12px 14px;font-size:18px;font-weight:700;background:#15171A;color:#F4F2EE;border:2px solid #3A3F46;border-radius:10px;font-family:'JetBrains Mono',monospace}}
.tool input:focus{{border-color:#FF6A00;outline:none}}
.res{{margin-top:26px;padding:22px;border-radius:12px;background:rgba(255,106,0,.10);border:2px solid #FF6A00}}
.res .big{{font-family:Anton,sans-serif;font-size:52px;color:#FF6A00;line-height:1}}
.res .lab{{color:#A8A29E;margin-top:6px;font-size:15px}}
.bench{{margin-top:14px;font-size:15px;color:#CFCAC4}}.bench b{{color:#FFD23F}}
.linkbox{{background:#15171A;border:1px dashed #3A3F46;border-radius:10px;padding:14px;font-family:'JetBrains Mono',monospace;font-size:13px;color:#A8A29E;margin-top:28px;word-break:break-all}}
.credit{{color:#888;font-size:13px;margin-top:10px}}
</style></head><body>
<header><div class="nav"><a class="logo" href="/"><span class="mark">B</span><b>BOOKED<span>JOB</span></b></a>
<a class="cta" href="/tools/">All free tools</a></div></header><div class="tape"></div>
<article class="wrap">
<p class="crumb"><a href="/">Home</a> › <a href="/tools/">Tools</a> › {ogt}</p>
"""

FOOT = """<div class="answer"><b>Next step:</b> Free contractor-marketing math + tools at <a href="https://booked-job.com/">booked-job.com</a>.</div>
</article><footer style="text-align:center;padding:40px;color:#888;font-size:14px">© Booked Job · <a href="https://booked-job.com/">booked-job.com</a></footer>{script}</body></html>"""

CALC_BODY = """<h1>{trade} <em>Cost Per Booked Job</em> Calculator</h1>
<div class="answer"><b>Why this number:</b> cost per lead hides your close rate. Cost per booked job — lead price ÷ close rate — is what a {trade_l} customer actually costs. It's the only fair way to compare Angi vs Google vs referrals.</div>
<div class="tool">
  <label for="cpl">What you pay per {trade_l} lead ($)</label><input id="cpl" type="number" value="35" min="0" step="1" />
  <label for="close">Of every 10 of these leads, how many do you win?</label><input id="close" type="number" value="2" min="0" max="10" step="0.5" />
  <div class="res"><div class="big" id="out">$175</div><div class="lab">your real cost per <b>booked {trade_l} job</b></div>
  <div class="bench">Benchmarks per booked job: <b>Google LSA ≈ $168</b> · <b>Thumbtack ≈ $250</b> · <b>Angi ≈ $542</b> — <a href="/blog/contractor-marketing-statistics/">sourced</a>.</div></div>
</div>
<p>A "$35 lead" you win 2 in 10 is a <b>$175</b> customer; at 1-in-12 it's $420. For {trade_l} shops, shared leads (sold to a dozen pros) are usually the most expensive customers you can buy. More: <a href="/blog/cost-per-lead-vs-cost-per-booked-job/">cost per lead vs cost per booked job</a>.</p>
<h2>Embed this calculator</h2><p>Free to embed{partner} — keep the credit line:</p>
<div class="linkbox">&lt;iframe src="{url}" style="width:100%;height:620px;border:1px solid #ddd;border-radius:12px" loading="lazy" title="{ogt}"&gt;&lt;/iframe&gt;&lt;br&gt;&lt;a href="{url}"&gt;{ogt} by Booked Job&lt;/a&gt;</div>
<p class="credit">Built for {trade_l} pros by Booked Job.</p>
"""
CALC_SCRIPT = """<script>function c(){var a=+document.getElementById('cpl').value||0,b=+document.getElementById('close').value||0,r=b/10,v=r>0?a/r:0;document.getElementById('out').textContent=v>0?'$'+Math.round(v).toLocaleString():'—';}document.querySelectorAll('.tool input').forEach(function(i){i.addEventListener('input',c)});c();</script>"""


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:40] or "trade"


def add_to_sitemap(url):
    sm = open(SITEMAP).read()
    if url in sm:
        return
    row = f'  <url><loc>{url}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'
    open(SITEMAP, "w").write(sm.replace("</urlset>", row + "</urlset>"))
    xml.dom.minidom.parse(SITEMAP)


def make(trade, kind="calculator", partner_domain=None):
    """Render the asset, return its public URL. kind: 'calculator' (only kind wired)."""
    trade = re.sub(r"[^A-Za-z0-9 &/-]", "", (trade or "Contractor")).strip()[:30] or "Contractor"
    tl = trade.lower()
    slug = f"cost-per-booked-job-calculator-{slugify(trade)}"
    url = f"{B}/tools/{slug}/"
    ogt = f"{trade} Cost Per Booked Job Calculator"
    partner = f" on {html.escape(partner_domain)}" if partner_domain else ""
    body = CALC_BODY.format(trade=html.escape(trade), trade_l=html.escape(tl), url=url, ogt=html.escape(ogt), partner=partner)
    page = HEAD.format(title=ogt, ogt=html.escape(ogt), url=url,
                       meta=f"Free {tl} cost-per-booked-job calculator: turn cost per lead and close rate into your real cost per booked job, vs Angi/Thumbtack/Google LSA benchmarks.") \
        + body + FOOT.format(script=CALC_SCRIPT)
    d = os.path.join(TOOLSDIR, slug); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w").write(page)
    add_to_sitemap(url)
    return url


if __name__ == "__main__":
    import sys
    print(make(sys.argv[1] if len(sys.argv) > 1 else "HVAC",
               partner_domain=sys.argv[2] if len(sys.argv) > 2 else None))
