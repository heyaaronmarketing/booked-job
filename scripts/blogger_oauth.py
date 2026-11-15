#!/usr/bin/env python3
"""
One-time Blogger OAuth — reuses the Google Cloud OAuth client from
secrets/youtube.env (same project), adds the Blogger scope, captures a refresh
token, and records the target blog id. Writes secrets/blogger.env.

    python3 scripts/blogger_oauth.py            # reuses client from youtube.env
    python3 scripts/blogger_oauth.py --client-id <ID> --client-secret <SECRET>
"""
import argparse, http.server, json, os, sys, threading, time, urllib.parse, urllib.request, webbrowser

SCOPE = "https://www.googleapis.com/auth/blogger"
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
        self.wfile.write(f"<body style='font-family:sans-serif;background:#0e2235;color:#fff;padding:60px;text-align:center'><h2>Booked Job · Blogger</h2><p>{m}</p></body>".encode())

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

    # find the blog id
    bid = bname = ""
    try:
        r = urllib.request.Request("https://www.googleapis.com/blogger/v3/users/self/blogs")
        r.add_header("Authorization", f"Bearer {tok['access_token']}")
        blogs = json.loads(urllib.request.urlopen(r, timeout=30).read().decode()).get("items", [])
        if blogs:
            bid, bname = blogs[0]["id"], blogs[0]["name"]
    except Exception as ex:
        print(f">>> (couldn't list blogs: {ex} — enable Blogger API v3 in the project)")

    out = os.path.join(os.path.dirname(__file__), "..", "secrets", "blogger.env")
    with open(out, "w") as f:
        f.write(f"BLOGGER_CLIENT_ID={cid}\nBLOGGER_CLIENT_SECRET={csec}\n")
        f.write(f"BLOGGER_REFRESH_TOKEN={tok['refresh_token']}\n")
        f.write(f"BLOGGER_BLOG_ID={bid}\nBLOGGER_BLOG_NAME={bname}\n")
    os.chmod(out, 0o600)
    print(f"\n✅ wrote secrets/blogger.env")
    print(f">>> TARGET BLOG: '{bname}' (id {bid})  ← confirm this is the Booked Job blog.")


if __name__ == "__main__":
    main()
