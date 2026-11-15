#!/usr/bin/env python3
"""Email welcome drip (launchd, daily) — the owned nurture-to-Consent-Resolve engine.
For each subscriber, sends the drip email(s) they're due for based on days-since-signup,
tracking what's been sent. Excludes internal/seed addresses. Resend API.
Source: content/email_drip.json · State: content/email_drip_state.json"""
import argparse, datetime as dt, json, os, sys, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DRIP = os.path.join(ROOT, "content", "email_drip.json")
STATE = os.path.join(ROOT, "content", "email_drip_state.json")
LOG = os.path.join(ROOT, "content", "email_drip.log")
EXCLUDE_DOMAINS = ("consentresolve.com", "techassets.com")  # seed/internal — don't drip
UA = "curl/8.4.0"  # Resend's CF edge blocks python-urllib


def log(m):
    line = f"{dt.datetime.now().isoformat(timespec='seconds')}  {m}"
    print(line); open(LOG, "a").write(line + "\n")


def env():
    e = {}
    for line in open(os.path.join(ROOT, "secrets", "resend.env")):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def _req(method, path, key, body=None):
    req = urllib.request.Request(f"https://api.resend.com{path}",
                                 data=json.dumps(body).encode() if body else None, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json"); req.add_header("User-Agent", UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def wrap(heading, body, cta_text, cta_url):
    return (f'<div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#0e2235">'
            f'<div style="background:#0e2235;padding:16px 24px"><span style="font-family:Arial Black,Impact,sans-serif;color:#fff;font-size:19px;font-weight:900">BOOKED <span style="color:#a62d1a">JOB</span></span></div>'
            f'<div style="height:5px;background:#a62d1a"></div>'
            f'<div style="padding:26px 24px"><h1 style="font-size:22px;margin:0 0 14px">{heading}</h1>{body}'
            f'<p style="margin:24px 0"><a href="{cta_url}" style="background:#a62d1a;color:#fff;text-decoration:none;font-weight:700;padding:13px 22px;border-radius:8px;display:inline-block">{cta_text} &rarr;</a></p></div>'
            f'<div style="padding:16px 24px;border-top:1px solid #eee;color:#999;font-size:12px">Booked Job &middot; For service pros who\'d rather be working.<br>'
            f'You subscribed at booked-job.com. Reply STOP or email unsubscribe@booked-job.com to opt out.</div></div>')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(os.path.join(ROOT, "secrets", "resend.env")):
        log("Resend not connected — skipping."); return
    e = env(); key = e["RESEND_API_KEY"]; aid = e["RESEND_AUDIENCE_ID"]; frm = e.get("RESEND_FROM", "Booked Job <newsletter@booked-job.com>")
    emails = json.load(open(DRIP))["emails"]
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    try:
        contacts = _req("GET", f"/audiences/{aid}/contacts", key).get("data", [])
    except Exception as ex:
        log(f"contacts fetch failed: {ex}"); return
    if a.status:
        print(json.dumps({"contacts": len(contacts), "sent_state": len(state)}, indent=2)); return

    sent_now = 0
    now = dt.datetime.now(dt.timezone.utc)
    for c in contacts:
        if c.get("unsubscribed") or any(c.get("email", "").lower().endswith(d) for d in EXCLUDE_DOMAINS):
            continue
        try:
            created = dt.datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
        except Exception:
            continue
        days = (now - created).days
        done = set(state.get(c["id"], []))
        for i, em in enumerate(emails):
            if em["day"] <= days and i not in done:
                if a.dry_run:
                    log(f"[dry] would send #{i} ('{em['subject']}') to {c['email']} (day {days})")
                else:
                    try:
                        _req("POST", "/emails", key, {"from": frm, "to": [c["email"]],
                             "subject": em["subject"], "html": wrap(em["heading"], em["body"], em["cta_text"], em["cta_url"])})
                        done.add(i); sent_now += 1
                        log(f"sent #{i} ('{em['subject']}') to {c['email']}")
                    except Exception as ex:
                        log(f"send failed to {c['email']}: {ex}")
        if not a.dry_run:
            state[c["id"]] = list(done)
    if not a.dry_run:
        json.dump(state, open(STATE, "w"), indent=2)
    log(f"drip run: {sent_now} emails sent across {len(contacts)} contacts")


if __name__ == "__main__":
    main()
