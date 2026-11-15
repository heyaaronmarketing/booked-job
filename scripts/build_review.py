#!/usr/bin/env python3
"""
Content Review page — a single private catalog of everything we've produced:
blog articles, stat cards, queued FB/IG posts, reels/clips, pins, podcast, course.
Reads the live content files and writes a self-contained, browsable, filterable
page to site/dashboard/review.html (noindex). Re-run anytime to refresh.

    python3 scripts/build_review.py
"""
import json, os, glob, html

ROOT = os.path.join(os.path.dirname(__file__), "..")
B = "https://booked-job.com"


def load(p, d):
    try: return json.load(open(os.path.join(ROOT, p)))
    except Exception: return d


def esc(s): return html.escape(str(s or ""))


def main():
    synd = load("content/syndication_queue.json", {"items": []})["items"]
    posts = load("content/queue.json", {"posts": []})["posts"]
    reels = load("content/reels_queue.json", {"reels": []})["reels"]
    polls = load("content/telegram_polls.json", {"polls": []})
    polls = polls.get("polls", polls) if isinstance(polls, dict) else polls
    cards = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, "site/cards/*-sq.png")))
    pins = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, "site/pins/*.png")))
    clips = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, "site/reels/*.mp4")))

    # ---- blog articles grouped by series ----
    from collections import defaultdict
    by_series = defaultdict(list)
    for a in synd:
        by_series[a.get("short_title", "Other")].append(a)
    art_html = ""
    for series in sorted(by_series):
        items = by_series[series]
        art_html += f'<h3 class="ser">{esc(series)} <span class="c">{len(items)}</span></h3>'
        for a in items:
            art_html += (f'<div class="row" data-s="{esc(a["title"]).lower()} {esc(a.get("blurb","")).lower()}">'
                         f'<a class="t" href="{esc(a["url"])}" target="_blank">{esc(a["title"])} ↗</a>'
                         f'<div class="b">{esc(a.get("blurb",""))}</div></div>')

    # ---- queued FB/IG posts ----
    post_html = ""
    for p in posts:
        img = p.get("image") or ""
        thumb = ""
        if img and img.startswith("site/"):
            thumb = f'<img src="/{img[5:]}" loading="lazy"/>'
        elif img and "content/cards/" in img:
            thumb = f'<img src="/cards/{os.path.basename(img)}" loading="lazy"/>'
        link = f'<a href="{esc(p["link"])}" target="_blank">link ↗</a>' if p.get("link") else ""
        post_html += (f'<div class="card" data-s="{esc(p.get("caption","")).lower()}">{thumb}'
                      f'<div class="cap">{esc(p.get("caption",""))}</div>'
                      f'<div class="meta">{esc(p.get("archetype",""))} · {link}</div></div>')

    # ---- reels / clips ----
    reel_html = ""
    for r in reels:
        v = r.get("video", "")
        url = f"/reels/{os.path.basename(v)}" if v else ""
        reel_html += (f'<div class="card" data-s="{esc(r.get("hook","")).lower()}">'
                      f'<div class="hook">🎬 {esc(r.get("hook",""))}</div>'
                      f'<div class="cap">{esc(r.get("description",""))[:200]}</div>'
                      + (f'<a href="{url}" target="_blank">▶ watch</a>' if url else '<span class="gen">(generated on post)</span>')
                      + '</div>')

    # ---- cards / pins grids ----
    card_grid = "".join(f'<a href="/cards/{c}.png" target="_blank"><img src="/cards/{c}.png" loading="lazy"/></a>' for c in cards)
    pin_grid = "".join(f'<a href="/pins/{c}.png" target="_blank"><img src="/pins/{c}.png" loading="lazy"/></a>' for c in pins)

    # ---- polls ----
    poll_html = "".join(f'<div class="card"><b>❓ {esc(p.get("q"))}</b><div class="cap">{esc(" · ".join(p.get("options",[])))}</div></div>' for p in polls)

    # ---- podcast + course ----
    pod = ('<div class="card"><b>🎙️ Get Booked, Not F***ed</b><div class="cap">3 episodes · '
           f'<a href="{B}/podcast/" target="_blank">listen page ↗</a> · '
           f'<a href="https://iheart.com/podcast/337858388/" target="_blank">iHeart ↗</a></div></div>')
    course = ('<div class="card"><b>🎓 Marketing 101 course</b><div class="cap">10 public video lessons · '
              '<a href="https://www.youtube.com/playlist?list=PLQVb1V1iNPtg" target="_blank">playlist ↗</a></div></div>')

    counts = [("Blog articles", len(synd), "#articles"), ("FB/IG posts queued", len(posts), "#posts"),
              ("Reels / clips", len(reels), "#reels"), ("Stat cards", len(cards), "#cards"),
              ("Pinterest pins", len(pins), "#pins"), ("Telegram polls", len(polls), "#polls"),
              ("Hosted clips", len(clips), "#reels")]
    chips = "".join(f'<a class="chip" href="{anchor}"><b>{n}</b><span>{lbl}</span></a>' for lbl, n, anchor in counts)

    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/><meta name="robots" content="noindex,nofollow"/>
<title>Booked Job — Content Review</title>
<style>
:root{{--o:#a62d1a;--bg:#0e2235;--c2:#1E2227;--ln:#2A2F36;--mut:#9aa0a8;}}
*{{box-sizing:border-box;margin:0}}body{{font-family:-apple-system,Inter,sans-serif;background:var(--bg);color:#eef;line-height:1.5;padding:0 0 60px}}
.tape{{height:8px;background:repeating-linear-gradient(45deg,#c8321b 0 20px,#0e2235 20px 40px)}}
header{{padding:24px 22px 8px;max-width:1100px;margin:0 auto}}
h1{{font-size:26px}}.sub{{color:var(--mut);font-size:14px;margin-top:4px}}
.chips{{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}}
.chip{{background:var(--c2);border:1px solid var(--ln);border-radius:10px;padding:10px 14px;text-decoration:none;color:#eef;display:flex;flex-direction:column}}
.chip b{{font-size:22px;color:var(--o)}}.chip span{{font-size:12px;color:var(--mut)}}
.wrap{{max-width:1100px;margin:0 auto;padding:0 22px}}
#q{{width:100%;padding:12px 14px;border-radius:10px;border:1px solid var(--ln);background:var(--c2);color:#fff;font-size:15px;margin:10px 0 24px}}
h2{{font-size:20px;margin:34px 0 12px;border-bottom:2px solid var(--o);padding-bottom:6px}}
h3.ser{{font-size:15px;color:var(--o);margin:18px 0 8px}}h3 .c{{color:var(--mut);font-size:13px}}
.row{{padding:10px 0;border-bottom:1px solid var(--ln)}}.row .t{{color:#fff;text-decoration:none;font-weight:600}}.row .t:hover{{color:var(--o)}}
.row .b{{color:var(--mut);font-size:13px;margin-top:3px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}}
.card{{background:var(--c2);border:1px solid var(--ln);border-radius:12px;padding:14px}}
.card img{{width:100%;border-radius:8px;margin-bottom:8px}}.cap{{font-size:13px;color:#cfd}}.meta,.hook{{font-size:12px;color:var(--mut);margin-top:6px}}.hook{{color:var(--o);font-weight:600;margin:0 0 6px}}
.card a{{color:var(--o)}}.gen{{color:var(--mut);font-size:12px}}
.imgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}}.imgrid img{{width:100%;border-radius:8px}}
</style></head><body><div class="tape"></div>
<header><h1>📋 Content Review</h1><div class="sub">Everything Booked Job has produced — click any item to open it. Type to filter.</div>
<div class="chips">{chips}</div></header>
<div class="wrap"><input id="q" placeholder="🔍 Filter articles & posts by keyword…" oninput="filt()"/>
<h2 id="articles">📝 Blog articles ({len(synd)})</h2>{art_html}
<h2 id="cards">📊 Stat cards ({len(cards)})</h2><div class="imgrid">{card_grid}</div>
<h2 id="posts">📣 Facebook / Instagram posts queued ({len(posts)})</h2><div class="grid">{post_html}</div>
<h2 id="reels">🎬 Reels / video clips ({len(reels)})</h2><div class="grid">{reel_html}</div>
<h2 id="pins">📌 Pinterest pins ({len(pins)})</h2><div class="imgrid">{pin_grid}</div>
<h2 id="polls">❓ Telegram polls ({len(polls)})</h2><div class="grid">{poll_html}</div>
<h2>🎙️ Podcast & 🎓 Course</h2><div class="grid">{pod}{course}</div>
</div>
<script>function filt(){{var q=document.getElementById('q').value.toLowerCase();
document.querySelectorAll('[data-s]').forEach(function(e){{e.style.display=e.getAttribute('data-s').includes(q)?'':'none'}})}}</script>
</body></html>"""
    out = os.path.join(ROOT, "site", "dashboard", "review.html")
    open(out, "w").write(page)
    print(f"built review page -> site/dashboard/review.html")
    print(f"  {len(synd)} articles · {len(posts)} FB/IG posts · {len(reels)} reels · {len(cards)} cards · {len(pins)} pins · {len(polls)} polls")


if __name__ == "__main__":
    main()
