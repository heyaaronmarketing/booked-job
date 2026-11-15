#!/usr/bin/env python3
"""
Booked Job weekly newsletter. Builds a brand-voiced HTML digest from the latest
content and sends it to the Resend audience (creates + sends a broadcast).

Reads secrets/resend.env:
  RESEND_API_KEY=...
  RESEND_AUDIENCE_ID=...
  RESEND_FROM=Booked Job <newsletter@booked-job.com>

Flags: --dry-run (build + print, don't send), --force.
State: content/newsletter_state.json.
"""
import argparse, datetime as dt, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
API = "https://api.resend.com"


def env():
    p = os.path.join(ROOT, "secrets", "resend.env")
    if not os.path.exists(p):
        sys.exit("secrets/resend.env missing — add Resend creds first.")
    e = {}
    for line in open(p):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1); e[k] = v
    return e


def post(path, key, body):
    req = urllib.request.Request(f"{API}/{path}", data=json.dumps(body).encode(), method="POST")
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "curl/8.4.0")  # Resend's CF edge blocks default python-urllib UA
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"Resend error {ex.code} on {path}: {ex.read().decode()[:300]}")


def build_html(items):
    feat = items[0] if items else None
    rows = ""
    for it in items[:3]:
        rows += f"""
        <tr><td style="padding:14px 0;border-bottom:1px solid #E4E0D9">
          <a href="{it['url']}" style="color:#0e2235;font-weight:700;font-size:17px;text-decoration:none">{it['title']}</a>
          <div style="color:#54585E;font-size:14px;margin-top:4px">{it.get('blurb','')[:160]}</div>
          <a href="{it['url']}" style="color:#a62d1a;font-weight:700;font-size:13px;text-decoration:none">Read it &rarr;</a>
        </td></tr>"""
    return f"""<!DOCTYPE html><html><body style="margin:0;background:#F4F2EE;font-family:Helvetica,Arial,sans-serif">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F4F2EE;padding:24px 0">
   <tr><td align="center">
    <table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;background:#fff;border-radius:14px;overflow:hidden">
      <tr><td style="background:#0e2235;padding:22px 26px">
        <span style="font-family:Impact,Helvetica,sans-serif;color:#fff;font-size:22px;letter-spacing:1px">BOOKED<span style="color:#a62d1a">JOB</span></span>
      </td></tr>
      <tr><td style="padding:26px">
        <p style="font-size:17px;color:#0e2235;margin:0 0 14px">Here's what's worth your time this week — no fluff, just what keeps a shop booked.</p>
        <table role="presentation" width="100%">{rows}</table>
        <div style="background:#0e2235;border-radius:12px;padding:20px;margin-top:24px;text-align:center">
          <div style="color:#fff;font-weight:700;font-size:16px;margin-bottom:6px">Stop renting your leads.</div>
          <a href="https://booked-job.com/blog/is-angi-worth-it/" style="display:inline-block;background:#a62d1a;color:#fff;font-weight:700;text-decoration:none;padding:11px 20px;border-radius:8px;font-size:14px">See the real cost of an Angi lead &rarr;</a>
        </div>
        <p style="color:#94a3b8;font-size:12px;margin-top:24px">You're getting this because you signed up at booked-job.com. <a href="{{{{RESEND_UNSUBSCRIBE_URL}}}}" style="color:#94a3b8">Unsubscribe</a>.</p>
      </td></tr>
    </table>
   </td></tr>
  </table></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    items = json.load(open(os.path.join(ROOT, "content", "syndication_queue.json")))["items"]
    if not items:
        print("no content to feature"); return
    subject = f"Booked Job — {items[0].get('short_title', items[0]['title'])}"
    html = build_html(items)

    if a.dry_run:
        print(f"SUBJECT: {subject}\n({len(html)} bytes html, {len(items)} items)"); return

    # Send window — run_all calls this hourly, so without a gate every subscriber
    # gets an email every run (this is the bug that sent one sub 5 emails a night).
    # Locked to Tuesday ~6am Central (the cloud runs in TZ America/Chicago): top of
    # the inbox before the trade's workday, on the best-performing B2B day.
    # Mon=0..Tue=1 ; send hour (24h, Central) ; dedup window only guards against a
    # second send the SAME Tuesday (runs are hours apart), so 2 days is plenty and
    # never blocks next Tuesday (7 days out).
    SEND_DOW, SEND_HOUR, MIN_DAYS = 1, 6, 2
    state_path = os.path.join(ROOT, "content", "newsletter_state.json")
    state = {}
    try:
        state = json.load(open(state_path))
    except Exception:
        pass
    last = state.get("last_sent")
    if not a.force:
        now = dt.datetime.now()
        if now.weekday() != SEND_DOW or now.hour < SEND_HOUR:
            print(f"not the send window (Tue {SEND_HOUR:02d}:00 CT) — now {now:%a %H:%M}, skipping.")
            return
        if last:
            try:
                since = (now - dt.datetime.fromisoformat(last)).total_seconds() / 86400
            except Exception:
                since = MIN_DAYS  # unparseable state -> don't block a legit send
            if since < MIN_DAYS:
                print(f"already sent {since:.1f}d ago (<{MIN_DAYS}d) — skipping to avoid a double send.")
                return

    if not os.path.exists(os.path.join(ROOT, "secrets", "resend.env")):
        print("Resend not connected yet (no secrets/resend.env) — skipping."); return

    e = env()
    bc = post("broadcasts", e["RESEND_API_KEY"], {
        "audience_id": e["RESEND_AUDIENCE_ID"], "from": e["RESEND_FROM"],
        "subject": subject, "html": html, "name": f"Weekly {dt.date.today().isoformat()}"})
    post(f"broadcasts/{bc['id']}/send", e["RESEND_API_KEY"], {})
    json.dump({"last_sent": dt.datetime.now().isoformat(timespec="minutes"), "broadcast": bc["id"]},
              open(os.path.join(ROOT, "content", "newsletter_state.json"), "w"), indent=2)
    print(f"sent broadcast {bc['id']}")
    try:
        sys.path.insert(0, HERE); import log_change
        log_change.add("site", f"Sent weekly newsletter: {subject}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
