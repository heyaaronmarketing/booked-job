#!/usr/bin/env python3
"""Booked Job — Lead Review production engine.
Turns a research-filled page spec (JSON) into the LOCKED "field report" design:
rubber-stamp verdict, bullshit-detector, verbatim field-note quotes (with real
permalinks), line-item estimate, Work Order CTA (aaron.chat), affiliate ledger.
Light + dark (paper/blueprint) + toggle, WCAG-AA contrast, Article+FAQ+Breadcrumb
schema. One spec in -> one on-brand page out at site/reviews/<slug>/index.html.

  python3 scripts/review_render.py content/reviews/<slug>.json   # render one
  python3 scripts/review_render.py --all                          # render all specs
"""
import glob, html, json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SPECS = os.path.join(ROOT, "content", "reviews")
OUT = os.path.join(ROOT, "site", "reviews")
B = "https://booked-job.com"

CSS = r"""
:root{--desk:#d7ccb0;--paper:#f2ebd9;--panel:#e9e0c9;--ink:#211c12;--muted:#655c45;--rule:#c3b894;
--stamp:#a62d1a;--link:#8a3a1f;--check:#2f6b3a;--grid:transparent;
--display:'Bricolage Grotesque',system-ui,sans-serif;--body:'Newsreader',Georgia,serif;--mono:'Courier Prime',ui-monospace,monospace;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--desk:#071220;--paper:#0e2235;--panel:#13293f;--ink:#e4ecf5;--muted:#8aa4c1;--rule:#2c4e73;--stamp:#ff6a45;--link:#ff9270;--check:#4fd083;--grid:rgba(120,180,230,.05);color-scheme:dark;}}
:root[data-theme="dark"]{--desk:#071220;--paper:#0e2235;--panel:#13293f;--ink:#e4ecf5;--muted:#8aa4c1;--rule:#2c4e73;--stamp:#ff6a45;--link:#ff9270;--check:#4fd083;--grid:rgba(120,180,230,.05);color-scheme:dark;}
*{box-sizing:border-box}
body{margin:0;background:var(--desk);color:var(--ink);font-family:var(--body);font-size:18px;line-height:1.62;background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);background-size:26px 26px;-webkit-font-smoothing:antialiased;padding-left:max(0px,env(safe-area-inset-left,0px));padding-right:max(0px,env(safe-area-inset-right,0px))}
.report{max-width:748px;margin:0 auto;background:var(--paper);border:2px solid var(--ink);padding-left:max(22px,env(safe-area-inset-left,0px));padding-right:max(22px,env(safe-area-inset-right,0px))}
@media(min-width:800px){.report{outline:1px solid var(--rule);outline-offset:5px}}
a{color:var(--link);text-underline-offset:3px}
b,strong{font-weight:600}
.mast{border-bottom:3px solid var(--ink);padding-block:16px 12px}
.mast .top{display:flex;justify-content:space-between;align-items:center;gap:12px;font-family:var(--mono);font-size:.64rem;color:var(--muted);text-transform:uppercase;letter-spacing:.18em}
#themeToggle{font-family:var(--mono);font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;color:var(--ink);background:transparent;border:1px solid var(--ink);padding:5px 10px;cursor:pointer}
#themeToggle:hover{background:var(--ink);color:var(--paper)}
.mast h1.brand{font-family:var(--display);font-weight:800;font-size:clamp(2.4rem,9vw,3.6rem);margin:8px 0 0;letter-spacing:-.02em;line-height:.92}
.filing{display:flex;flex-wrap:wrap;gap:4px 22px;margin-top:12px;font-family:var(--mono);font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;border-top:1px solid var(--rule);padding-top:10px}
.filing b{color:var(--ink);font-weight:700}
.head{padding-block:28px 6px}
.head .sec{font-family:var(--mono);font-size:.7rem;color:var(--stamp);text-transform:uppercase;letter-spacing:.16em;font-weight:700}
.head h2.title{font-family:var(--display);font-weight:800;font-size:clamp(2rem,6.4vw,3rem);margin:12px 0 0;letter-spacing:-.02em;line-height:1.02}
.head h2 em{font-style:italic;font-family:var(--body);font-weight:600}
.dek{font-size:1.12rem;margin:16px 0 0;max-width:63ch}
.stamp{display:inline-block;font-family:var(--mono);font-weight:700;color:var(--stamp);border:3px solid var(--stamp);padding:9px 15px 7px;text-transform:uppercase;letter-spacing:.08em;line-height:1.1;transform:rotate(-3.5deg);box-shadow:inset 0 0 0 2px var(--paper),inset 0 0 0 3px var(--stamp);opacity:.92}
@media (prefers-color-scheme:light){:root:not([data-theme="dark"]) .stamp{mix-blend-mode:multiply}}
.verdictrow{display:flex;gap:22px;align-items:center;flex-wrap:wrap;margin-top:26px;padding:18px 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.stamp.big{font-size:1.15rem;padding:12px 18px 10px}
.verdictrow p{margin:0;flex:1;min-width:240px;font-size:1.02rem}
.finding{padding-block:26px;border-bottom:1px solid var(--rule)}
.finding .no{font-family:var(--mono);font-size:.72rem;color:var(--muted);letter-spacing:.14em;text-transform:uppercase}
.finding h3{font-family:var(--display);font-weight:700;font-size:clamp(1.4rem,4.4vw,1.85rem);margin:6px 0 0;letter-spacing:-.01em}
.finding p{margin:14px 0}
.lede::first-letter{font-family:var(--display);font-weight:800;font-size:3.1em;float:left;line-height:.72;padding:.06em .09em 0 0;color:var(--stamp)}
.claimbox{position:relative;background:var(--panel);border:1px solid var(--rule);padding:22px 20px;margin:18px 0}
.claimbox .claim{font-family:var(--display);font-weight:700;font-size:1.25rem;max-width:70%}
.claimbox .reject{position:absolute;right:14px;top:-12px;font-family:var(--mono);font-weight:700;color:var(--stamp);border:2.5px solid var(--stamp);padding:5px 10px;text-transform:uppercase;letter-spacing:.1em;font-size:.82rem;transform:rotate(7deg);background:var(--paper)}
.claimbox small{display:block;color:var(--muted);margin-top:12px;font-size:.92rem;line-height:1.55}
.src{font-family:var(--mono);font-size:.72rem;color:var(--muted);letter-spacing:.04em}
.note{border-left:4px solid var(--stamp);padding:4px 0 4px 18px;margin:14px 0}
.note .tag{font-family:var(--mono);font-size:.66rem;color:var(--stamp);text-transform:uppercase;letter-spacing:.14em;font-weight:700}
.note p{margin:6px 0 0;font-size:1.06rem;font-style:italic}
.note .who{font-family:var(--mono);font-size:.68rem;color:var(--muted);font-style:normal;display:block;margin-top:6px;letter-spacing:.03em}
.note .who a{color:var(--muted)}
.estimate{margin-top:18px;border:2px solid var(--ink)}
.estimate .cap{display:flex;justify-content:space-between;gap:10px;background:var(--ink);color:var(--paper);font-family:var(--mono);font-size:.68rem;text-transform:uppercase;letter-spacing:.14em;padding:8px 12px}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;min-width:540px}
th,td{text-align:left;padding:13px 13px;border-bottom:1px solid var(--rule);vertical-align:top;font-size:.95rem}
th{font-family:var(--mono);font-size:.64rem;color:var(--muted);text-transform:uppercase;letter-spacing:.12em;border-bottom:1.5px solid var(--ink)}
td .item{font-family:var(--display);font-weight:700;font-size:1.08rem}
td .cost{font-family:var(--mono);font-weight:700;white-space:nowrap}
tr .v{font-family:var(--mono);font-weight:700;text-transform:uppercase;font-size:.82rem;letter-spacing:.06em}
.v.yes{color:var(--check)}.v.no{color:var(--stamp)}
tbody tr.rec td{background:color-mix(in srgb,var(--check) 12%,transparent)}
.ops{background:var(--panel);border:1px solid var(--rule);padding:22px;margin-top:18px}
.ops ol{margin:12px 0 0;padding-left:0;list-style:none;counter-reset:step}
.ops li{position:relative;padding:10px 0 10px 44px;border-bottom:1px dashed var(--rule);counter-increment:step}
.ops li:last-child{border:0}
.ops li::before{content:counter(step);position:absolute;left:0;top:9px;font-family:var(--mono);font-weight:700;color:var(--paper);background:var(--stamp);width:28px;height:28px;display:grid;place-items:center;font-size:.9rem}
.workorder{margin:30px 0 0;border:2px solid var(--ink);background:var(--paper)}
.workorder .cap{display:flex;justify-content:space-between;align-items:center;background:var(--stamp);color:var(--paper);font-family:var(--mono);font-size:.68rem;text-transform:uppercase;letter-spacing:.14em;padding:9px 14px;font-weight:700}
.workorder .body{padding:22px}
.workorder h3{font-family:var(--display);font-weight:800;font-size:clamp(1.5rem,5vw,2.1rem);margin:0;letter-spacing:-.01em}
.workorder p{margin:12px 0 0;max-width:54ch}
.wo-foot{display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between;border-top:2px solid var(--ink);margin-top:20px;padding-top:18px}
.price{font-family:var(--mono)}
.price b{font-family:var(--display);font-weight:800;font-size:1.9rem;color:var(--ink);display:block;line-height:1}
.btn{font-family:var(--mono);font-weight:700;font-size:.92rem;text-transform:uppercase;letter-spacing:.08em;text-decoration:none;background:var(--ink);color:var(--paper);padding:14px 22px;border:2px solid var(--ink)}
.btn:hover{background:var(--paper);color:var(--ink)}
.ledger{margin-top:26px;border-top:1px solid var(--rule);padding-top:20px}
.ledger h4{font-family:var(--mono);font-size:.72rem;text-transform:uppercase;letter-spacing:.14em;color:var(--muted);margin:0 0 10px}
.ledger ul{list-style:none;padding:0;margin:0}
.ledger li{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;padding:11px 0;border-bottom:1px dotted var(--rule);font-size:.96rem}
.ledger li .k b{font-family:var(--display);font-weight:700}
.ledger .disc{font-family:var(--mono);font-size:.74rem;color:var(--muted);line-height:1.7;margin-top:16px}
.faqs{padding-block:26px;border-top:1px solid var(--rule)}
.faqs h3{font-family:var(--display);font-weight:700;font-size:1.5rem;margin:0 0 6px}
.faqs dt{font-family:var(--display);font-weight:700;margin-top:16px}
.faqs dd{margin:6px 0 0}
footer{padding-block:26px 40px;font-family:var(--mono);font-size:.72rem;color:var(--muted);line-height:1.8;letter-spacing:.03em}
@media (max-width:560px){.claimbox .claim{max-width:100%}.claimbox .reject{position:static;display:inline-block;transform:rotate(-3deg);margin-bottom:12px}}
"""

TOGGLE = """<script>(function(){var r=document.documentElement,b=null;function sd(){try{return matchMedia('(prefers-color-scheme: dark)').matches}catch(e){return false}}function c(){var t=r.getAttribute('data-theme');return t||(sd()?'dark':'light')}function l(){if(b)b.textContent=(c()==='dark'?'Paper':'Blueprint')}try{var s=localStorage.getItem('bj-theme');if(s)r.setAttribute('data-theme',s)}catch(e){}function i(){b=document.getElementById('themeToggle');if(!b)return;l();b.addEventListener('click',function(){var n=c()==='dark'?'light':'dark';r.setAttribute('data-theme',n);try{localStorage.setItem('bj-theme',n)}catch(e){}l()})}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',i);else i()})();</script>"""

A = lambda s: html.escape(str(s or ""), quote=True)      # attribute-safe
T = lambda s: html.escape(str(s or ""), quote=False)      # text-safe (body html passed through raw)


def block_html(bk):
    t = bk.get("type")
    no = f'<div class="no">Finding {T(bk.get("no",""))}</div>' if bk.get("no") else ""
    h = f'<h3>{T(bk.get("h",""))}</h3>' if bk.get("h") else ""
    if t == "prose":
        cls = ' class="lede"' if bk.get("lede") else ""
        body = bk.get("html","")
        # first paragraph gets the drop-cap when lede
        if bk.get("lede") and body.startswith("<p>"):
            body = body.replace("<p>", f'<p{cls}>', 1)
        return f'<section class="finding">{no}{h}{body}</section>'
    if t == "bs":
        return (f'<section class="finding">{no}{h}{bk.get("intro_html","")}'
                f'<div class="claimbox"><span class="reject">{T(bk.get("label","Unverified"))}</span>'
                f'<div class="claim">{T(bk.get("claim",""))}</div><small>{bk.get("small","")}</small></div>'
                f'{bk.get("outro_html","")}</section>')
    if t == "notes":
        notes=""
        for n in bk.get("notes",[]):
            who=T(n.get("who",""))
            if n.get("url"): who=f'<a href="{A(n["url"])}" target="_blank" rel="noopener nofollow">{who} &#8599;</a>'
            tag=f'<span class="tag">&#9656; {T(n.get("tag","Field note"))}</span>'
            notes+=f'<div class="note">{tag}<p>&ldquo;{T(n.get("text",""))}&rdquo;</p><span class="who">{who}</span></div>'
        src=f'<p class="src" style="margin-top:14px">{T(bk["src_note"])}</p>' if bk.get("src_note") else ""
        return f'<section class="finding">{no}{h}{bk.get("intro_html","")}{notes}{src}</section>'
    if t == "estimate":
        rows=""
        for r in bk.get("rows",[]):
            rec=' class="rec"' if r.get("rec") else ""
            sub=f'<br><span class="src">{T(r["sub"])}</span>' if r.get("sub") else ""
            bc=r.get("buy_class","")
            rows+=(f'<tr{rec}><td><span class="item">{T(r.get("item",""))}</span>{sub}</td>'
                   f'<td class="cost">{T(r.get("cost",""))}</td>'
                   f'<td><span class="v {bc}">{T(r.get("buy",""))}</span></td>'
                   f'<td>{r.get("note","")}</td></tr>')
        cap=bk.get("caption","Itemized")
        return (f'<section class="finding">{no}{h}<div class="estimate">'
                f'<div class="cap"><span>{T(cap)}</span><span>Booked Job</span></div>'
                f'<div class="scroll"><table><thead><tr><th>Line item</th><th>Cost</th><th>Buy?</th><th>The ruthless note</th></tr></thead>'
                f'<tbody>{rows}</tbody></table></div></div></section>')
    if t == "ops":
        steps="".join(f'<li>{s}</li>' for s in bk.get("steps",[]))
        intro=bk.get("intro_html","")
        outro=bk.get("outro_html","")
        return f'<section class="finding">{no}{h}{intro}<div class="ops"><ol>{steps}</ol></div>{outro}</section>'
    return ""


def schema(spec):
    url=f"{B}/reviews/{spec['slug']}/"
    plain=re.sub("<[^>]+>","",spec["title"])
    graph=[{"@type":"Article","headline":plain,"description":spec.get("meta",""),
            "datePublished":spec.get("date","2026-11-10"),"dateModified":spec.get("date","2026-11-10"),
            "author":{"@type":"Organization","name":"Booked Job"},
            "publisher":{"@type":"Organization","name":"Booked Job","url":B+"/"},"mainEntityOfPage":url},
           {"@type":"BreadcrumbList","itemListElement":[
             {"@type":"ListItem","position":1,"name":"Booked Job","item":B+"/"},
             {"@type":"ListItem","position":2,"name":"Reviews","item":B+"/reviews/"},
             {"@type":"ListItem","position":3,"name":plain,"item":url}]}]
    if spec.get("faq"):
        graph.append({"@type":"FAQPage","mainEntity":[
          {"@type":"Question","name":f["q"],"acceptedAnswer":{"@type":"Answer","text":f["a"]}} for f in spec["faq"]]})
    return json.dumps({"@context":"https://schema.org","@graph":graph})


def render(spec):
    url=f"{B}/reviews/{spec['slug']}/"
    fil=spec.get("filing",{})
    filing="".join(f'<span>{T(k)} <b>{T(v)}</b></span>' for k,v in fil.items())
    blocks="".join(block_html(b) for b in spec.get("blocks",[]))
    wo=spec.get("workorder",{})
    aff="".join(f'<li><span class="k">{a.get("k","")}</span><a href="{A(a.get("href",B))}" target="_blank" rel="noopener nofollow">{T(a.get("cta","See &#8594;"))}</a></li>' for a in spec.get("affiliates",[]))
    faq=""
    if spec.get("faq"):
        items="".join(f'<dt>{T(f["q"])}</dt><dd>{T(f["a"])}</dd>' for f in spec["faq"])
        faq=f'<section class="faqs"><h3>Questions, answered straight</h3><dl>{items}</dl></section>'
    disc=spec.get("disclosure","BOOKED JOB — FIELD REPORTS FOR PEOPLE WHO'D RATHER BE ON THE TOOLS. FTC &amp; AFFILIATE DISCLOSURE: WE EARN COMMISSION ON SOME OUTBOUND LINKS. WE ONLY POINT YOU AT WHAT WE'D USE, AND WE'LL TELL YOU TO SPEND $0 WHEN THAT'S THE RIGHT CALL.")
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="claude:viewport-fit-sides" content="cover">
<title>{A(spec['title_tag'] or spec['title'])}</title>
<meta name="description" content="{A(spec.get('meta',''))}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article"><meta property="og:title" content="{A(spec.get('title_tag') or spec['title'])}">
<meta property="og:description" content="{A(spec.get('meta',''))}"><meta property="og:url" content="{url}">
<meta name="theme-color" content="#0e2235">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400;1,6..72,500&family=Courier+Prime:ital,wght@0,400;0,700;1,400&display=swap">
<script type="application/ld+json">{schema(spec)}</script>
<style>{CSS}</style><script async src="https://www.googletagmanager.com/gtag/js?id=G-FR77BS4NW5"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-FR77BS4NW5');</script></head><body>
<div class="report">
<header class="mast"><div class="top"><span>Booked Job &middot; Field Division</span>
<button id="themeToggle" type="button" aria-label="Toggle blueprint or paper">Blueprint</button></div>
<h1 class="brand">BOOKED&nbsp;JOB</h1><div class="filing">{filing}</div></header>
<div class="head"><div class="sec">&sect; {T(spec.get('sec','Inspection'))}</div>
<h2 class="title">{spec['title']}</h2><p class="dek">{T(spec.get('dek',''))}</p>
<div class="verdictrow"><span class="stamp big">{T(spec.get('verdict_stamp','Verdict'))}</span>
<p>{spec.get('verdict_text','')}</p></div></div>
{blocks}
<div class="workorder"><div class="cap"><span>Work Order &mdash; do it for me</span><span>Booked Job &middot; Hey Aaron</span></div>
<div class="body"><h3>{T(wo.get('h','We&rsquo;ll do it for you'))}</h3><p>{wo.get('p','')}</p>
<div class="wo-foot"><span class="price">Flat rate <b>{T(wo.get('price','$500'))}</b></span>
<a class="btn" href="https://aaron.chat" target="_blank" rel="noopener">File it &#8594; aaron.chat</a></div></div></div>
<div class="ledger"><h4>Tools we'd actually look at</h4><ul>{aff}</ul>
<p class="disc">{spec.get('ledger_note','Some of these are affiliate links &mdash; buy through them and we might make a few bucks, at no cost to you. It never changes the verdict.')}</p></div>
{faq}
<footer>{disc}</footer>
</div>{TOGGLE}</body></html>"""


def build(path):
    spec=json.load(open(path))
    d=os.path.join(OUT,spec["slug"]); os.makedirs(d,exist_ok=True)
    open(os.path.join(d,"index.html"),"w",encoding="utf-8").write(render(spec))
    return spec["slug"]


IDX_CSS=r"""
.intro{padding-block:26px 8px;border-bottom:1px solid var(--rule)}
.intro .sec{font-family:var(--mono);font-size:.7rem;color:var(--stamp);text-transform:uppercase;letter-spacing:.16em;font-weight:700}
.intro h2{font-family:var(--display);font-weight:800;font-size:clamp(2rem,6.4vw,3rem);margin:12px 0 0;letter-spacing:-.02em;line-height:1.02}
.intro p{font-size:1.12rem;margin:16px 0 0;max-width:62ch}
.idx{margin:0}
.case{display:block;text-decoration:none;color:inherit;padding:22px 0;border-bottom:1px solid var(--rule)}
.case:hover{background:var(--panel)}
.cmeta{display:flex;gap:16px;font-family:var(--mono);font-size:.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:.12em}
.ctitle{font-family:var(--display);font-weight:700;font-size:clamp(1.3rem,4.2vw,1.7rem);margin:8px 0 0;letter-spacing:-.01em;color:var(--ink)}
.cstamp{display:inline-block;font-family:var(--mono);font-weight:700;color:var(--stamp);border:2px solid var(--stamp);padding:3px 9px;margin-top:10px;text-transform:uppercase;letter-spacing:.07em;font-size:.72rem;transform:rotate(-2deg)}
.cone{margin:12px 0 0;color:var(--muted);font-size:1rem;max-width:66ch}
"""

def index():
    specs=[]
    for p in sorted(glob.glob(os.path.join(SPECS,"*.json"))):
        try: specs.append(json.load(open(p)))
        except Exception: pass
    def num(s):
        n=re.sub(r"\D","", str(s.get("filing",{}).get("Field Report","")))
        return int(n) if n else 0
    specs.sort(key=lambda s:(num(s), s.get("date","")), reverse=True)
    rows=""
    for s in specs:
        fil=s.get("filing",{}); plain=re.sub("<[^>]+>","",s["title"])
        no=T(fil.get("Field Report","")); subj=T(fil.get("Subject","")); who=T(fil.get("Filed for",""))
        stamp=T(re.sub("<[^>]+>"," ",s.get("verdict_stamp","Reviewed")))
        one=T(s.get("meta",""))
        rows+=(f'<a class="case" href="/reviews/{s["slug"]}/">'
               f'<div class="cmeta"><span>{no or "Field Report"}</span><span>{subj}{(" &middot; "+who) if who else ""}</span></div>'
               f'<div class="ctitle">{plain}</div><div class="cstamp">{stamp}</div><div class="cone">{one}</div></a>')
    url=f"{B}/reviews/"
    items=[{"@type":"ListItem","position":i+1,"url":f"{B}/reviews/{s['slug']}/","name":re.sub('<[^>]+>','',s['title'])} for i,s in enumerate(specs)]
    sch=json.dumps({"@context":"https://schema.org","@type":"CollectionPage","name":"Booked Job Reviews",
                    "url":url,"mainEntity":{"@type":"ItemList","itemListElement":items}})
    disc=("BOOKED JOB — FIELD REPORTS FOR PEOPLE WHO'D RATHER BE ON THE TOOLS. "
          "FTC &amp; AFFILIATE DISCLOSURE: WE EARN COMMISSION ON SOME OUTBOUND LINKS. "
          "WE ONLY POINT YOU AT WHAT WE'D USE, AND WE'LL TELL YOU TO SPEND $0 WHEN THAT'S THE RIGHT CALL.")
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Reviews — Booked Job | Honest field reports on the tools pitched to service pros</title>
<meta name="description" content="We spend the money, read the real complaints, and file the verdict on the AI tools, software, and lead services sold to contractors. When the answer is 'spend $0,' we say so.">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:title" content="Booked Job Reviews — honest field reports for service pros">
<meta property="og:url" content="{url}"><meta name="theme-color" content="#0e2235">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700;12..96,800&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Courier+Prime:ital,wght@0,400;0,700&display=swap">
<script type="application/ld+json">{sch}</script>
<style>{CSS}{IDX_CSS}</style><script async src="https://www.googletagmanager.com/gtag/js?id=G-FR77BS4NW5"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-FR77BS4NW5');</script></head><body>
<div class="report">
<header class="mast"><div class="top"><span><a href="/" style="color:inherit;text-decoration:none">&#8592; Booked Job</a> &middot; Field Division</span>
<button id="themeToggle" type="button" aria-label="Toggle blueprint or paper">Blueprint</button></div>
<h1 class="brand">THE REVIEWS DESK</h1>
<div class="filing"><span>Division <b>Field Reports</b></span><span>Subject <b>The tools they sell you</b></span><span>On file <b>{len(specs)}</b></span></div></header>
<section class="intro"><div class="sec">&sect; What this is</div>
<h2>The tools, apps &amp; lead services pitched to you &mdash; <em>inspected.</em></h2>
<p>Some guy in a branded vest wants $300 a month to answer your phone with a robot, or sell you the same lead as five other shops. We spend the money, read the real complaints, and file the verdict. When the right answer is <b>spend zero dollars</b>, that's what it'll say.</p></section>
<div class="idx">{rows}</div>
<footer>{disc}</footer>
</div>{TOGGLE}</body></html>"""


def main():
    args=sys.argv[1:]
    paths = sorted(glob.glob(os.path.join(SPECS,"*.json"))) if ("--all" in args or not args) else [a for a in args if a.endswith(".json")]
    for p in paths:
        print("  rendered /reviews/"+build(p)+"/")
    open(os.path.join(OUT,"index.html"),"w",encoding="utf-8").write(index())
    print(f"{len(paths)} page(s) + hub -> site/reviews/")


if __name__ == "__main__":
    main()
