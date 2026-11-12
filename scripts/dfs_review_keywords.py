#!/usr/bin/env python3
"""Pull real US search volume + CPC + competition for the Reviews Desk keyword
universe via DataForSEO. Creds at ~/.dataforseo (login\\npassword). Prints a
ranked table by cluster. NEVER sum a cluster to size a market (close variants
report identical volume) — read it floor-to-ceiling, by intent."""
import base64, json, os, urllib.request

CRED = open(os.path.expanduser("~/.dataforseo")).read().split()
AUTH = base64.b64encode(f"{CRED[0]}:{CRED[1]}".encode()).decode()

CLUSTERS = {
    "AI receptionist / answering": [
        "ai receptionist", "ai receptionist for contractors", "ai receptionist for small business",
        "ai answering service", "ai answering service for contractors", "ai phone answering service",
        "smith.ai review", "rosie ai", "goodcall", "best ai receptionist", "ai receptionist cost",
        "virtual receptionist for contractors", "answering service for contractors"],
    "Lead mills (review-to-warn)": [
        "is angi worth it", "angi leads", "angi leads review", "angi for contractors", "homeadvisor",
        "homeadvisor review", "is thumbtack worth it", "thumbtack for contractors", "thumbtack pro",
        "bark leads", "is bark worth it", "networx leads", "buying leads for contractors",
        "best lead generation for contractors", "shared leads"],
    "Field-service software (affiliate)": [
        "jobber", "jobber review", "jobber vs housecall pro", "housecall pro", "housecall pro review",
        "servicetitan", "servicetitan review", "workiz", "best field service software",
        "best software for contractors", "field service management software", "crm for contractors"],
    "Marketing truth for service pros": [
        "marketing for contractors", "how to get leads for contractors", "how to get more plumbing customers",
        "how to get more roofing leads", "how to get more hvac customers", "google ads for contractors",
        "local seo for contractors", "how to get google reviews", "how many google reviews do i need",
        "contractor marketing", "how to get customers as a contractor", "should i buy leads", "speed to lead"],
    "AI marketing skepticism": [
        "ai marketing for small business", "ai social media posts", "is ai worth it for small business",
        "ai tools for small business", "best ai tools for contractors"],
}

ALL = [k for ks in CLUSTERS.values() for k in ks]
body = json.dumps([{"keywords": ALL, "location_code": 2840, "language_code": "en"}]).encode()
req = urllib.request.Request("https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live",
                             data=body, headers={"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"})
res = json.loads(urllib.request.urlopen(req, timeout=90).read())
rows = {r["keyword"]: r for r in res["tasks"][0]["result"] if r}

def fmt(k):
    r = rows.get(k, {})
    v = r.get("search_volume") or 0
    cpc = r.get("cpc") or 0
    comp = (r.get("competition") or "")
    return v, cpc, comp

print(f"cost: ${res['tasks'][0].get('cost',0)}\n")
for cluster, ks in CLUSTERS.items():
    ranked = sorted(ks, key=lambda k: fmt(k)[0], reverse=True)
    print(f"━━ {cluster} ━━")
    for k in ranked:
        v, cpc, comp = fmt(k)
        print(f"  {v:>6}/mo  ${cpc:>6.2f} cpc  {str(comp):<7}  {k}")
    print()
