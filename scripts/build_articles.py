#!/usr/bin/env python3
"""
Turn each Marketing 101 lesson's narration into a publish-ready pillar article
(site/blog/<slug>/index.html, matching the on-site schema + style) AND queue it
for syndication (content/syndication_queue.json). Body is derived from the
narration VO; SEO scaffolding (titles, short answer, stat, FAQ) authored below.

    python3 scripts/build_articles.py 1 2 3     # build specific lessons
    python3 scripts/build_articles.py all
"""
import json, os, re, sys, datetime

ROOT = os.path.join(os.path.dirname(__file__), "..")
BLOG = os.path.join(ROOT, "site", "blog")
NARR = os.path.join(ROOT, "content", "course")
QUEUE = os.path.join(ROOT, "content", "syndication_queue.json")
PLAYLIST = "https://www.youtube.com/playlist?list=PLQVb1V1iNPtg"
TODAY = "2026-06-29"

# authored SEO layer per lesson; body is pulled from the narration file
ART = {
 1: dict(slug="what-marketing-actually-is", n=1,
   h1="What Marketing <em>Actually</em> Is for Contractors",
   title="What Marketing Actually Is for Contractors (No-BS Guide)",
   meta="Marketing for contractors in plain English: get found, get picked, get booked. Why likes and followers don't pay payroll, and the two numbers that decide if your marketing makes money.",
   short="Marketing isn't ads or a logo. It's a machine that takes a stranger with a problem and turns them into a paid job: get found, get picked, get booked. Everything else is decoration.",
   stat=("3", "words that are the whole game: get found, get picked, get booked. Likes and followers don't pay payroll."),
   labels=["contractor marketing","home services","marketing basics","lead generation","trades"],
   faq=[("Do I need to be good at marketing to get more jobs?","No. You need to understand it well enough to make smart calls and not get fleeced — get found, get picked, get booked. That's it."),
        ("Is marketing the same as advertising?","No. Ads are one small piece. Marketing is being findable and trustable the moment someone needs your trade — most of which is free."),
        ("What's the one metric that actually matters?","Booked jobs. Not likes, not followers, not 'brand awareness.' If it doesn't fill your calendar, it doesn't count.")]),
 2: dict(slug="cost-per-lead-vs-cost-per-booked-job", n=2,
   h1="Cost Per Lead vs <em>Cost Per Booked Job</em>",
   title="CPL vs CPBJ: The 2 Numbers That Run Your Marketing",
   meta="Cost per lead vs cost per booked job for contractors. Why a low CPL lies, how a slipping close rate doubles your real cost, and how to calculate your true CPBJ in 5 minutes.",
   short="CPL (cost per lead) is the bait; CPBJ (cost per booked job) is the meal. A cheap lead that never books is the most expensive lead there is. Always judge a source by CPBJ.",
   stat=("5×", "A $50 cost-per-lead can hide a $250 cost-per-booked-job. The number that hits your bank account is usually 3–5× the lead price."),
   labels=["cost per lead","cost per booked job","contractor marketing","marketing roi","lead generation"],
   faq=[("What is a good cost per booked job for contractors?","It depends on your average ticket — but the only honest benchmark is: does the job profit after you subtract what it cost to get it? Track CPBJ monthly and compare sources."),
        ("Why is cost per lead misleading?","Because a low CPL means nothing if those leads don't book. Two sources at $50/lead can have wildly different costs per booked job once you factor in close rate."),
        ("How do I calculate my cost per booked job?","Take last month's total marketing spend and divide by the number of jobs that actually came from it. Most owners have never done this once.")]),
 3: dict(slug="where-customers-find-contractors", n=3,
   h1="The 5 Doors <em>Every Customer Comes Through</em>",
   title="Where Customers Actually Find Contractors (The 5 Doors)",
   meta="Customers find contractors through five doors: Google/map, website, paid ads, lead apps, and reviews. Which two are free, what a healthy lead mix looks like, and why 100% from one app is a time bomb.",
   short="Customers come through five doors: your Google profile, your website, paid ads, lead apps, and reviews. Two are free and come first. Living behind one door is a time bomb.",
   stat=("5", "doors — not fifty. Google/map, website, paid ads, lead apps, reviews. Most contractors use one or two and leave the rest wide open for competitors."),
   labels=["contractor marketing","lead generation","marketing channels","local seo","home services"],
   faq=[("What are the main ways customers find a contractor?","Five channels: Google Business Profile and the map pack, your website, paid ads, lead networks like Angi/Thumbtack, and reviews / word of mouth."),
        ("Which marketing channels are free for contractors?","Your Google Business Profile and your reviews cost nothing and are the foundation everything else sits on. Build those before paying for ads or leads."),
        ("Is it bad to get all my leads from one app?","Yes. One channel is a time bomb — the day that app raises prices or shuts your account off, your phone goes silent. Spread across doors.")]),
 4: dict(slug="google-business-profile-for-contractors", n=4,
   h1="Your Google Business Profile: <em>The Free Door at the Top</em>",
   title="Google Business Profile for Contractors: Win the Map Pack",
   meta="The contractor's guide to the Google Business Profile and the map pack — why only 3 spots matter, how to claim it free in 10 minutes, and the categories + photos that get you the call.",
   short="The map pack is free real estate at the top of local search with only 3 spots. Your Google Business Profile is what gets you in. Claim it, pick the right category, add real photos.",
   stat=("3", "spots in the Google map pack. If you're one of the three, the phone rings. If you're not, you don't exist — no matter how good you are."),
   labels=["google business profile","GBP","map pack","local seo","contractor marketing"],
   faq=[("Is a Google Business Profile free for contractors?","Yes — completely free, and it takes about 10 minutes to claim. It's the single highest-paying ten minutes in local marketing."),
        ("What's the most important part of a Google Business Profile?","Your primary category and your photos. Set the category to exactly what you are (e.g. emergency plumber, not just contractor) and add real job photos, not stock."),
        ("How do I show up in the Google map pack?","Claim and fully complete your profile, pick the right category, add real photos, and earn steady recent reviews. A complete profile beats a blank one every time.")]),
 5: dict(slug="contractor-website-one-job", n=5,
   h1="Your Website Has <em>One Job</em>",
   title="Why 98% of People Leave Your Contractor Website (and the Fix)",
   meta="Your contractor website has one job: turn a visitor into a phone call. Why the average site converts 2–3%, the five things that actually work, and the 3-second phone-number test.",
   short="A contractor website has one job: turn a visitor into a call. Most fail — the average converts 2–3%. Make it fast, mobile, with a giant tap-to-call number, proof, and one clear action.",
   stat=("98%", "of visitors leave the average contractor website without calling. You paid for the click and got a wave goodbye. The fix is speed and an obvious phone number."),
   labels=["contractor website","website conversion","home services","get more calls","mobile website"],
   faq=[("What should a contractor website include?","Five things: fast load, mobile-first design, your phone number everywhere as tap-to-call, real proof (photos + reviews), and one clear action — call now."),
        ("Why does my website get visitors but no calls?","Because it isn't built for the one job. If a panicked customer can't find and tap your number in about three seconds, they're already calling the next guy."),
        ("Does my contractor website need to look fancy?","No. A $10k pretty site that buries the phone number loses to an ugly one-page site with a giant tap-to-call button. Working beats pretty.")]),
 6: dict(slug="why-reviews-win-the-call", n=6,
   h1="Why Reviews <em>Decide Who Gets the Call</em>",
   title="Contractor Reviews: Why They Decide Who Gets the Call",
   meta="In the trades your reputation is currency. Why 9 of 10 people read reviews first, why count + recency + responses matter, and why 140 reviews beats 12 even at a higher price.",
   short="Before a customer hears your voice, they've judged you by your reviews. Count, recency, and your responses all matter — and a shop with 140 recent reviews beats one with 12, even at a higher price.",
   stat=("9 / 10", "people read reviews before calling a contractor, and most won't consider you under four stars. You're judged before the phone ever rings."),
   labels=["google reviews","online reputation","contractor marketing","reviews","local seo"],
   faq=[("How many reviews does a contractor need?","There's no magic number, but more recent reviews win. A shop with 140 recent reviews that replies to them beats one with 12 old ones — customers trust the crowd."),
        ("Should I respond to bad reviews?","Yes, especially the bad ones. A calm, professional reply sells harder than any five-star, because every future customer is watching how you handle it."),
        ("How do I get more reviews consistently?","Make asking a system, not luck: the moment a job goes well and the customer's happy, send a direct review link and ask. See our full review system guide.")]),
 7: dict(slug="should-you-pay-for-leads", n=7,
   h1="Should Contractors <em>Pay for Leads?</em>",
   title="Should Contractors Pay for Leads? The Honest Math (LSA, Angi, Thumbtack)",
   meta="Should you buy contractor leads? LSA vs shared-lead apps, why a $35 shared lead can cost $700 per booked job while a $120 exclusive costs $342, and how to tell a worthwhile source from a trap.",
   short="Sometimes paid leads are worth it, sometimes a trap. LSA pays per real lead at high intent; shared apps put you in a footrace. Judge every source by cost per booked job, never the sticker price.",
   stat=("$700", "the real cost per booked job of a 'cheap' $35 shared lead at a 5% close rate — vs $342 for an 'expensive' $120 exclusive lead. Cheap is expensive."),
   labels=["paid leads","angi","thumbtack","local service ads","LSA","contractor marketing"],
   faq=[("Are Google Local Service Ads worth it for contractors?","For most, yes — it's the first paid door worth opening. You pay per lead (not per click) and those people already searched for your trade, so intent is high."),
        ("Why are shared leads from apps risky?","Because 3–5 contractors buy the same lead. You're in a footrace, and if you don't answer first you paid for nothing. Only works if you're fast and track your numbers."),
        ("How do I know if buying leads is worth it?","Calculate your real cost per booked job from that source — usually 3–5× the lead price. If it profits after that, keep it. If not, kill it.")]),
 8: dict(slug="google-ads-without-burning-cash", n=8,
   h1="Google Ads <em>Without Lighting Money on Fire</em>",
   title="Google Ads for Contractors: Spend Your First Dollar Without Getting Burned",
   meta="Paid search ads for contractors done right: why search ads catch high intent, the missed-call trap that torches a $200 job, how to start tiny with tight keywords, and judging by cost per booked job.",
   short="Search ads put you in front of someone searching for your trade right now. The fix to not getting burned: answer every call, start tiny with tight keywords, track by cost per booked job, kill the losers.",
   stat=("$200", "the size of the job you set on fire every time a paid click rings your phone and nobody answers. Fix the phone before you spend a dime."),
   labels=["google ads","ppc","search ads","contractor marketing","paid ads"],
   faq=[("How much should a contractor spend on Google Ads to start?","Start tiny — a small daily budget you won't cry over, tight keywords (e.g. 'emergency plumber', not 'plumbing'), one city, and watch it daily."),
        ("Why are my Google Ads not working?","Usually three leaks: broad keywords paying for tire-kickers, no tracking, and slow or missed callbacks. A missed call on a paid ad is money set on fire."),
        ("How do I measure if my ads are profitable?","By cost per booked job, not clicks or calls. Find the few keywords that book real work, feed those, and kill the rest without mercy.")]),
 9: dict(slug="get-found-by-google-and-ai", n=9,
   h1="Get Found by <em>Google AND AI</em>",
   title="Get Found by Google AND AI: SEO + AEO for Contractors",
   meta="About a third of people now ask a chatbot who to hire. How contractors show up in both Google search and AI answers — SEO in plain English, how the AI decides who it names, and the one foundation that feeds both.",
   short="Getting found used to mean Google. Now a third of people ask an AI tool who to hire. The same foundation — a strong profile, real reviews, a clear website that answers questions — wins both.",
   stat=("1 / 3", "of people now start with an AI tool instead of a search bar. If the AI doesn't name you, you're invisible to a third of your market and don't know it."),
   labels=["seo","AI search","AEO","chatgpt","local seo","contractor marketing"],
   faq=[("How do I get my business recommended by ChatGPT or AI?","The AI repeats what the web says about you. Get named by having a strong Google profile, a clear website that says exactly what you do and where, and a pile of recent reviews."),
        ("What is AEO (answer engine optimization)?","It's showing up when people ask an AI tool a question instead of searching. Same foundations as SEO — clear pages, real content, reviews, citations."),
        ("Do I need a separate strategy for AI search?","No. The exact same foundation that ranks you on Google gets you named by the AI. Build it once; it feeds both doors.")]),
 10: dict(slug="marketing-scorecard-for-contractors", n=10,
   h1="Your Marketing Scorecard: <em>Run It Like an Owner</em>",
   title="The Contractor Marketing Scorecard: 5 Numbers to Track Monthly",
   meta="Put your whole marketing on one page. The five numbers contractors should track monthly — CPL, CPBJ, close rate, review count, response time — how to rate them green/yellow/red, and why it makes you impossible to fleece.",
   short="Track five numbers monthly: cost per lead, cost per booked job, close rate, review count, response time. Color each green/yellow/red. Knowing your numbers is what makes you impossible to fleece.",
   stat=("5", "numbers on one page run your entire marketing: CPL, CPBJ, close rate, reviews, and response time. Check them monthly and you direct the marketer instead of getting sold to."),
   labels=["marketing scorecard","kpis","contractor marketing","cost per booked job","small business"],
   faq=[("What marketing numbers should a contractor track?","Five, monthly: cost per lead, cost per booked job, close rate, review count, and response time (how fast you call people back)."),
        ("How often should I review my marketing numbers?","Once a month is plenty. Color each green (winning), yellow (watch), or red (leaking money) and fix the reddest one first."),
        ("How do I avoid getting ripped off by a marketing agency?","Know your five numbers. The difference between directing a marketer and getting fleeced by one is being able to ask the right questions and demand the right numbers.")]),
}

ACR = [("H-V-A-C","HVAC"),("C P B J","CPBJ"),("C P L","CPL"),("A E O","AEO"),("S E O","SEO"),
       ("G B P","GBP"),("L S A","LSA"),(" A I "," AI "),("one-oh-one","101"),("dot com",".com"),
       ("two, maybe three percent","2–3%")]
SOFT = [("bullshit","nonsense"),("Bullshit","Nonsense"),("blowing smoke up your ass","blowing smoke"),
        ("up your ass","at you"),("your ass","you"),(" ass "," "),("pissed off","fed up"),
        ("screw it up","get it wrong"),("some poor bastard","a homeowner"),("bastard","homeowner"),("damn ","")]


def clean(t):
    for a, b in ACR + SOFT:
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def parse_narration(n):
    """Return [(beat_title, vo_text, on_screen), ...] from the lesson narration md."""
    cands = [os.path.join(NARR, f"booked-course{n}-narration.md"),
             os.path.join(NARR, f"booked-course{n}-intro-narration.md"),
             os.path.expanduser(f"~/Downloads/booked-course{n}-intro-narration.md"),
             os.path.expanduser(f"~/Downloads/booked-course{n}-narration.md")]
    path = next((p for p in cands if os.path.exists(p)), None)
    if not path:
        raise FileNotFoundError(f"no narration found for course {n} (tried {cands})")
    txt = open(path).read().split("## WHAT THEY")[0].split("## PRODUCTION")[0]
    beats = []
    for m in re.finditer(r"\*\*BEAT[^\n]*?—\s*([^\*\n]+)\*\*(.*?)(?=\n\*\*BEAT|\Z)", txt, re.S):
        title = m.group(1).strip().title()
        body = m.group(2)
        vo = " ".join(re.findall(r"VO:\s*(.+)", body))
        onscreen = ""
        osm = re.search(r"ON SCREEN:\s*([^`\n]+)", body)
        if osm: onscreen = osm.group(1).strip().strip('"')
        if vo:
            beats.append((title, clean(vo), onscreen))
    return beats


def render(a):
    beats = parse_narration(a["n"])
    lead = beats[0][1] if beats else ""
    sections = beats[1:]
    url = f"https://booked-job.com/blog/{a['slug']}/"
    faq_ld = ",".join('{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
                      % (json.dumps(q), json.dumps(ans)) for q, ans in a["faq"])
    secs_html = ""
    for h2, body, onscreen in sections:
        ans = f'<div class="answer">{onscreen}</div>' if onscreen else ""
        secs_html += f"\n  <h2>{h2}</h2>{ans}\n  <p>{body}</p>"
    faq_html = "".join(f'\n  <h3>{q}</h3>\n  <p>{ans}</p>' for q, ans in a["faq"])
    big, lab = a["stat"]
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
{{"@type":"Article","headline":{json.dumps(re.sub('<[^>]+>','',a['h1']))},"description":{json.dumps(a['meta'])},
"datePublished":"{TODAY}","dateModified":"{TODAY}",
"author":{{"@type":"Person","name":"Aaron Phillips","jobTitle":"Founder, Booked Job","url":"https://booked-job.com/about/"}},
"publisher":{{"@type":"Organization","name":"Booked Job","url":"https://booked-job.com/"}},
"mainEntityOfPage":"{url}"}},
{{"@type":"BreadcrumbList","itemListElement":[
{{"@type":"ListItem","position":1,"name":"Booked Job","item":"https://booked-job.com/"}},
{{"@type":"ListItem","position":2,"name":"Blog","item":"https://booked-job.com/blog/"}},
{{"@type":"ListItem","position":3,"name":{json.dumps(re.sub('<[^>]+>','',a['h1']))},"item":"{url}"}}]}},
{{"@type":"FAQPage","mainEntity":[{faq_ld}]}}]}}
</script></head><body>
<header><div class="nav">
  <a class="logo" href="/"><span class="mark">B</span><b>BOOKED<span>JOB</span></b></a>
  <a class="cta" href="https://www.facebook.com/bookedjob" target="_blank" rel="noopener">Follow</a>
</div></header><div class="tape"></div>
<article class="wrap">
  <p class="crumb"><a href="/">Home</a> › <a href="/blog/">Blog</a> › {re.sub('<[^>]+>','',a['h1'])}</p>
  <h1>{a['h1']}</h1>
  <div class="meta"><span class="av">AP</span> By Aaron Phillips · Marketing 101 · Lesson {a['n']} of 10 · Updated June 2026</div>
  <div class="answer"><b>Short answer:</b> {a['short']}</div>
  <p class="lead">{lead}</p>
  <div class="stat"><div class="big">{big}</div><div class="lab">{lab}</div></div>{secs_html}
  <h2>Watch this lesson (free)</h2>
  <p>This article is the companion to <b>Lesson {a['n']}</b> of the free <b>Marketing 101</b> course for contractors — 10 short, plain-English videos. <a href="{PLAYLIST}" target="_blank" rel="noopener">Watch the whole series free on YouTube →</a></p>
  <h2>Frequently asked questions</h2>{faq_html}
  <div class="answer"><b>Next step:</b> Get the full free course and tools at <a href="https://booked-job.com/">booked-job.com</a>. Get found. Get picked. Get booked.</div>
</article>
<footer style="text-align:center;padding:40px;color:#888;font-size:14px">© Booked Job · Honest marketing for the trades · <a href="https://booked-job.com/">booked-job.com</a></footer>
</body></html>"""
    return html, url


def main():
    nums = sorted(ART) if sys.argv[1:] == ["all"] or not sys.argv[1:] else [int(x) for x in sys.argv[1:]]
    q = json.load(open(QUEUE)); ids = {it["id"] for it in q["items"]}
    built = []
    for n in nums:
        a = ART[n]
        html, url = render(a)
        d = os.path.join(BLOG, a["slug"]); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w").write(html)
        built.append(a["slug"])
        if a["slug"] not in ids:
            q["items"].append({"id": a["slug"], "title": a["title"], "labels": a["labels"],
                               "short_title": f"Marketing 101 · Lesson {n}", "blurb": a["short"],
                               "url": url, "posted": {}})
    json.dump(q, open(QUEUE, "w"), indent=2)
    print(f"built {len(built)} articles -> site/blog/: " + ", ".join(built))
    print(f"syndication queue now has {len(q['items'])} items")


if __name__ == "__main__":
    main()
