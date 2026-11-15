#!/usr/bin/env python3
"""
Standalone blog-article builder for NON-lesson posts (complementary cluster
content). Renders site/blog/<slug>/index.html in the same template + schema as
build_articles.py (Article+Person+Organization+BreadcrumbList+FAQPage), and
appends the post to content/syndication_queue.json.

    python3 scripts/build_blog.py            # build all specs below
Body is authored inline as [(h2, answer_or_None, "<p>…</p>…"), …].
"""
import json, os, re

ROOT = os.path.join(os.path.dirname(__file__), "..")
BLOG = os.path.join(ROOT, "site", "blog")
QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
TODAY = "2026-06-30"

POSTS = [
 dict(slug="speed-to-lead-for-contractors",
   h1="Speed to Lead: Why You're Losing Jobs You <em>Already Paid For</em>",
   title="Speed to Lead for Contractors: Why You're Losing Jobs You Already Paid For",
   meta="Contractors lose jobs on response time, not price. Why the first to call back usually wins, the 5-minute rule, and how to never miss a lead again — even with both hands under a sink.",
   short="Customers hire the first contractor who responds, not the best one. If you don't answer or text back within about five minutes, you've likely lost the job — and if you paid for that lead, you just paid your competitor to win it.",
   stat=("5 min", "the window that decides most jobs. Leads answered within five minutes convert dramatically better than ones called back even half an hour later — by then, most have already hired someone else."),
   labels=["speed to lead","lead response time","contractor marketing","missed calls","home services"],
   body=[
    ("The job doesn't go to the best contractor — it goes to the fastest", None,
     "<p>A homeowner with water coming through the ceiling is not shopping for craftsmanship. They're shopping for relief, right now. So they go down the list and hire whoever picks up or texts back first. The race starts the second they hit send — and most contractors don't even know they're in it.</p>"
     "<p>The uncomfortable part: this is true even when you're more qualified, cheaper, and better reviewed than the guy who answered. Reviews and price get you onto the list. Being first to respond is what wins the job off it.</p>"),
    ("A missed call is a missed invoice", "Every call you let ring is money walking next door — and if you paid for that lead, you paid for it twice.",
     "<p>When you buy leads from Angi, Thumbtack, or Google and then let them hit voicemail, you've done the worst possible thing with your marketing budget: you paid for the click, then handed the actual job to a competitor by not answering. You lit the money on fire twice.</p>"
     "<p>Run the math from the <a href=\"https://booked-job.com/blog/cost-per-lead-vs-cost-per-booked-job/\">cost per booked job</a> angle and it gets bleak fast. Every unanswered call quietly doubles what your booked jobs actually cost you.</p>"),
    ("The 5-minute rule", None,
     "<p>The window is brutally short. Leads contacted within about five minutes convert at a far higher rate than those contacted even thirty minutes later, and response rates fall off a cliff after the first half hour. You don't have to drop your wrench mid-job — but you do have to get <em>something</em> back to them inside five minutes.</p>"),
    ("You can't answer with both hands in a disposal — so automate the first touch", None,
     "<p>Three fixes, all cheap or free:</p>"
     "<p><b>1. Auto-text-back on missed calls.</b> Most phones, Google Voice, or a ~$20/month service will fire an instant text: \"Hey, it's Dom — I'm on a job, what's going on?\" That one line keeps you in the race while your hands are full.</p>"
     "<p><b>2. Book while you sleep.</b> A simple after-hours answering service or online scheduler that locks in the appointment beats a voicemail nobody checks. The contractor who books it tonight does the job tomorrow.</p>"
     "<p><b>3. Make your site easy to reach you from.</b> A giant tap-to-call button and a text option mean the lead reaches you the way they prefer — see <a href=\"https://booked-job.com/blog/contractor-website-one-job/\">why 98% leave your website</a>.</p>"),
    ("Speed beats slick", None,
     "<p>A fast \"yeah, I can be there Thursday\" beats the polished outfit that calls back in three days with a beautiful quote. Nobody waits anymore. The good news for a small shop: speed is free, and the big competitor with the call center is often slower than you think. This is the one lever where being small and hungry beats being big.</p>"
     "<p>We did a whole (very R-rated) episode on this — <a href=\"https://booked-job.com/podcast/\">\"Answer Your Phone\" on the Get Booked, Not F***ed podcast</a>.</p>"),
   ],
   faq=[("How fast do I really need to respond to a lead?","Inside five minutes if you can. Conversion drops sharply after the first few minutes and falls off after thirty — by then most homeowners have already called someone else."),
        ("What if I can't answer because I'm on a job?","Set up an automatic text-back on missed calls plus a way to book appointments after hours. A one-line text inside five minutes keeps you in the running; a voicemail nobody returns does not."),
        ("Is speed really more important than price or reviews?","For urgent work, usually yes. Reviews and price get you onto the homeowner's short list; being first to respond is what wins the job off it.")]),

 dict(slug="contractor-referrals-and-repeat-customers",
   h1="Referrals &amp; Repeat Customers: Your <em>Cheapest</em> Marketing",
   title="Contractor Referrals & Repeat Customers: Your Cheapest Marketing",
   meta="Referrals and repeat customers cost almost nothing and close fastest because they already trust you. Why most contractors leave them on the table, and a simple system to ask, follow up, and stay top of mind.",
   short="Your past customers are the cheapest, highest-closing leads you have — they already trust you. Most contractors never ask for the referral or follow up, so the work quietly goes to whoever does.",
   stat=("$0", "the cost of asking a happy customer \"know anyone else who needs this?\" — and it closes faster than any lead you'll ever buy."),
   labels=["referrals","repeat customers","word of mouth","contractor marketing","customer retention"],
   body=[
    ("The leads you already earned and never collected", None,
     "<p>Every happy customer is a referral and a repeat job you haven't asked for yet. They already trust you, they don't shop you on price, and they close fast. Then most contractors finish the job, get paid, disappear — and turn around to complain that leads are expensive.</p>"
     "<p>The cheapest marketing you have is the work you already did. You just have to go collect on it.</p>"),
    ("Why word of mouth still beats everything", "A referred customer shows up pre-sold — the \"getting picked\" step is already done for you.",
     "<p>A homeowner trusts a neighbor's recommendation over any ad you could ever run. When someone arrives through a referral, they've skipped the part where they doubt you — the trust transferred from whoever sent them. That's why referrals close faster and haggle less than any cold lead.</p>"
     "<p>It's the same engine behind <a href=\"https://booked-job.com/blog/why-reviews-win-the-call/\">why reviews win the call</a> — a review is just a referral you can read.</p>"),
    ("Ask — at the right moment, in plain words", None,
     "<p>The moment to ask is the second the job's done and they're thrilled, not three weeks later when the glow has worn off. Keep it plain and low-pressure: \"Glad you're happy with it. If a neighbor ever needs [trade], I'd appreciate you passing my number along.\" Hand them two cards — one for them, one to give away.</p>"
     "<p>You're not begging. You're making it easy for someone who already likes you to help you.</p>"),
    ("Stay top of mind without being annoying", None,
     "<p>Most referrals are lost to forgetting, not disloyalty. People mean to recommend you and then life happens. A light touch keeps you the name they reach for: a seasonal text (\"furnace tune-up season's here\"), a quick check-in after a big job, a simple email list you write to once a month. Not spam — just enough that you're the first name that pops up when a coworker asks.</p>"),
    ("Make the repeat job easy", None,
     "<p>The same customer will need you again — give them a reason and a reminder before they go searching. A maintenance plan, a fridge magnet with your number, a line on the invoice about your next service. The goal is simple: when the problem comes back, they don't open Google. They open their phone and find you. Track whether it's working with the <a href=\"https://booked-job.com/blog/marketing-scorecard-for-contractors/\">contractor marketing scorecard</a>.</p>"),
   ],
   faq=[("When should I ask for a referral?","The second the job is done and the customer is happy. Enthusiasm fades fast — ask while they're still thrilled, not weeks later."),
        ("How do I ask for referrals without feeling pushy?","Keep it plain: \"If anyone you know needs [trade], I'd appreciate the introduction.\" Hand them a card or two. You're not begging — you're making it easy for someone who likes you to help."),
        ("What is the cheapest marketing for a contractor?","The customers you already have. Referrals and repeat work cost almost nothing, close fastest, and don't shop you on price.")]),
]


def render(a):
    url = f"https://booked-job.com/blog/{a['slug']}/"
    faq_ld = ",".join('{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
                      % (json.dumps(q), json.dumps(ans)) for q, ans in a["faq"])
    lead = re.sub(r"<[^>]+>", "", a["body"][0][2]).strip()
    lead = lead[:280].rsplit(".", 1)[0] + "." if len(lead) > 280 else lead
    secs = ""
    for h2, ans, p in a["body"]:
        abox = f'<div class="answer">{ans}</div>' if ans else ""
        secs += f"\n  <h2>{h2}</h2>{abox}\n  {p}"
    faq_html = "".join(f'\n  <h3>{q}</h3>\n  <p>{ans}</p>' for q, ans in a["faq"])
    big, lab = a["stat"]
    plain_h1 = re.sub("<[^>]+>", "", a["h1"]).replace("&amp;", "&")
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{a['title']}</title>
<meta name="description" content="{a['meta']}" />
<link rel="canonical" href="{url}" />
<meta property="og:type" content="article" /><meta property="og:title" content="{a['title']}" />
<meta property="og:description" content="{a['meta']}" /><meta property="og:url" content="{url}" />
<meta name="theme-color" content="#0e2235" />
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
  <h1>{a['h1']}</h1>
  <div class="meta"><span class="av">AP</span> By Aaron Phillips · Booked Job · Updated June 2026</div>
  <div class="answer"><b>Short answer:</b> {a['short']}</div>
  <p class="lead">{lead}</p>
  <div class="stat"><div class="big">{big}</div><div class="lab">{lab}</div></div>{secs}
  <h2>Frequently asked questions</h2>{faq_html}
  <div class="answer"><b>Next step:</b> Get the full free Marketing 101 course and tools at <a href="https://booked-job.com/">booked-job.com</a>. Get found. Get picked. Get booked.</div>
</article>
<footer style="text-align:center;padding:40px;color:#888;font-size:14px">© Booked Job · Honest marketing for the trades · <a href="https://booked-job.com/">booked-job.com</a></footer>
</body></html>"""
    return html, url


def main():
    q = json.load(open(QUEUE)); ids = {it["id"] for it in q["items"]}
    built = []
    for a in POSTS:
        html, url = render(a)
        d = os.path.join(BLOG, a["slug"]); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w").write(html)
        built.append(a["slug"])
        if a["slug"] not in ids:
            q["items"].append({"id": a["slug"], "title": a["title"], "labels": a["labels"],
                               "short_title": a["title"].split(":")[0], "blurb": a["short"],
                               "url": url, "posted": {}})
    json.dump(q, open(QUEUE, "w"), indent=2)
    print("built:", ", ".join(built))


if __name__ == "__main__":
    main()
