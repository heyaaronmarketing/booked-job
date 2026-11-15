#!/usr/bin/env python3
"""
One-time Google Business Profile OAuth — reuses the Google Cloud OAuth client from
secrets/youtube.env (same project as YouTube/Blogger), adds the business.manage
scope, captures a refresh token, and records the account + location. Writes
secrets/gbp.env.

Requires (enable in the SAME Google Cloud project, one time):
  - Google My Business API            (v4 — the one that posts local posts; needs approval)
  - My Business Account Management API
  - My Business Business Information API

    python3 scripts/gbp_oauth.py            # reuses client from youtube.env
    python3 scripts/gbp_oauth.py --client-id <ID> --client-secret <SECRET>
"""
import argparse, http.server, json, os, sys, threading, time, urllib.parse, urllib.request, webbrowser

SCOPE = "https://www.googleapis.com/auth/business.manage"
REDIRECT = "http://127.0.0.1:8080"
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
_code = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _code["code"] = p.get("code", [None])[0]; _code["error"] = p.get("error", [None])[0]
        self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
        m = "Authorized — close this tab. 🛠️" if _code.get("code") else f"Error: {_code.get('error')}"
        self.wfile.write(f"<body style='font-family:sans-serif;background:#0e2235;color:#fff;padding:60px;text-align:center'><h2>Booked Job · Google Business</h2><p>{m}</p></body>".encode())

    def log_message(self, *a):
        pass


def creds_from_youtube():
    p = os.path.join(os.path.dirname(__file__), "..", "secrets", "youtube.env")
    e = {}
    if os.path.exists(p):
        for line in open(p):
            if "=" in line:
                k, v = line.strip().split("=", 1); e[k] = v
    return e.get("YT_CLIENT_ID"), e.get("YT_CLIENT_SECRET")


def gget(url, tok):
    r = urllib.request.Request(url); r.add_header("Authorization", f"Bearer {tok}")
    return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-id"); ap.add_argument("--client-secret")
    a = ap.parse_args()
    cid, csec = a.client_id, a.client_secret
    if not (cid and csec):
        cid, csec = creds_from_youtube()
    if not (cid and csec):
        sys.exit("No client creds — pass --client-id/--client-secret or connect YouTube first.")

    url = AUTH + "?" + urllib.parse.urlencode({"client_id": cid, "redirect_uri": REDIRECT,
        "response_type": "code", "scope": SCOPE, "access_type": "offline", "prompt": "consent"})
    srv = http.server.HTTPServer(("127.0.0.1", 8080), Handler)
    threading.Thread(target=lambda: [srv.handle_request() for _ in iter(lambda: not (_code.get("code") or _code.get("error")), False)], daemon=True).start()
    print(">>> Open this URL in the Booked Job Google account:\n\n" + url + "\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    for _ in range(290):
        if _code.get("code") or _code.get("error"):
            break
        time.sleep(1)
    if not _code.get("code"):
        sys.exit(f"No code ({_code.get('error') or 'timeout'}).")

    body = urllib.parse.urlencode({"code": _code["code"], "client_id": cid, "client_secret": csec,
        "redirect_uri": REDIRECT, "grant_type": "authorization_code"}).encode()
    try:
        tok = json.loads(urllib.request.urlopen(urllib.request.Request(TOKEN, data=body), timeout=30).read().decode())
    except urllib.error.HTTPError as ex:
        sys.exit(f"token exchange failed {ex.code}: {ex.read().decode()[:300]}")
    if "refresh_token" not in tok:
        sys.exit("No refresh_token. Revoke at myaccount.google.com/permissions and retry.")

    # find the account + location (needs the Account Mgmt + Business Info APIs enabled)
    acct = loc = locname = ""
    try:
        accts = gget("https://mybusinessaccountmanagement.googleapis.com/v1/accounts", tok["access_token"]).get("accounts", [])
        if accts:
            acct = accts[0]["name"]   # e.g. accounts/123
            locs = gget(f"https://mybusinessbusinessinformation.googleapis.com/v1/{acct}/locations?readMask=name,title", tok["access_token"]).get("locations", [])
            if locs:
                loc = locs[0]["name"]; locname = locs[0].get("title", "")
    except Exception as ex:
        print(f">>> (couldn't list accounts/locations: {ex}\n    Enable 'My Business Account Management API' + 'My Business Business Information API' in the project, then re-run — the token below is still valid.)")

    out = os.path.join(os.path.dirname(__file__), "..", "secrets", "gbp.env")
    with open(out, "w") as f:
        f.write(f"GBP_CLIENT_ID={cid}\nGBP_CLIENT_SECRET={csec}\n")
        f.write(f"GBP_REFRESH_TOKEN={tok['refresh_token']}\n")
        f.write(f"GBP_ACCOUNT={acct}\nGBP_LOCATION={loc}\nGBP_LOCATION_NAME={locname}\n")
    os.chmod(out, 0o600)
    print(f"\n✅ wrote secrets/gbp.env")
    print(f">>> ACCOUNT: {acct or '(not listed)'}  LOCATION: {locname or loc or '(not listed)'}")


if __name__ == "__main__":
    main()
