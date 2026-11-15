#!/usr/bin/env python3
"""
One-time "leave us a Google review" email to the Booked Job audience (Resend).
Drives them to booked-job.com/review/ (which one-taps to the GBP review box).

Run manually once the GBP is verified and the review link is wired:
    python3 scripts/review_blast.py            # send
    python3 scripts/review_blast.py --dry-run

Honest-ask only (no incentives, no gating) — Google removes incentivized/fake reviews.
"""
import argparse, datetime as dt, json, os, sys, urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
API = "https://api.resend.com"
REVIEW_PAGE = "https://booked-job.com/review/"


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "resend.env")):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def post(path, key, body):
    req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "curl/8.4.0")
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Resend error {ex.code} on {path}: {ex.read().decode()[:300]}")


HTML = """<!DOCTYPE html><html><body style="margin:0;background:#F4F2EE;font-family:Helvetica,Arial,sans-serif">
 <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F2EE;padding:24px 0"><tr><td align="center">
  <table role="presentation" width="540" cellpadding="0" cellspacing="0" style="max-width:540px;width:100%;background:#fff;border-radius:14px;overflow:hidden">
   <tr><td style="background:#0e2235;padding:22px 26px"><span style="font-family:Impact,Helvetica,sans-serif;color:#fff;font-size:22px;letter-spacing:1px">BOOKED<span style="color:#a62d1a">JOB</span></span></td></tr>
   <tr><td style="padding:28px;text-align:center">
     <div style="font-size:26px;letter-spacing:3px">⭐️⭐️⭐️⭐️⭐️</div>
     <h1 style="font-size:22px;color:#0e2235;margin:14px 0 10px">Quick favor — 30 seconds?</h1>
     <p style="font-size:16px;color:#54585E;line-height:1.6;margin:0 0 18px">If Booked Job has saved you a headache — a post, a Reel, the Angi calculator — an honest review on Google would mean a lot, and it helps the next shop owner find us. No account hoops.</p>
     <a href="%s" style="display:inline-block;background:#a62d1a;color:#fff;font-weight:800;text-decoration:none;padding:14px 28px;border-radius:10px;font-size:16px">Leave a Google review →</a>
     <p style="color:#94a3b8;font-size:12px;margin-top:26px">Honest takes only — even a line helps. <a href="{{{{RESEND_UNSUBSCRIBE_URL}}}}" style="color:#94a3b8">Unsubscribe</a>.</p>
   </td></tr>
  </table>
 </td></tr></table></body></html>""" % REVIEW_PAGE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rl = os.path.join(ROOT, "content", "review_url.txt")
    if not os.path.exists(rl):
        sys.exit("content/review_url.txt missing — add the GBP writereview link first (the /review page reads it too).")
    if a.dry_run:
        print("SUBJECT: Quick favor — 30 seconds? · drives to " + REVIEW_PAGE); return
    e = env()
    bc = post("broadcasts", e["RESEND_API_KEY"], {
        "audience_id": e["RESEND_AUDIENCE_ID"], "from": e["RESEND_FROM"],
        "subject": "Quick favor — 30 seconds?", "html": HTML, "name": f"Review ask {dt.date.today().isoformat()}"})
    post(f"broadcasts/{bc['id']}/send", e["RESEND_API_KEY"], {})
    print(f"sent review-ask broadcast {bc['id']}")


if __name__ == "__main__":
    main()
