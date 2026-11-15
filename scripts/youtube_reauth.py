#!/usr/bin/env python3
"""
Re-authorize the YouTube token with the BROADER scopes needed to post comments
(youtube.force-ssl) in addition to upload + read. Reuses the existing OAuth client
in secrets/youtube.env, captures a new refresh token via loopback, and rewrites
YT_REFRESH_TOKEN in place (all other keys preserved). Run once:

    python3 scripts/youtube_reauth.py
"""
import http.server, json, os, sys, threading, time, urllib.parse, urllib.request, webbrowser

SCOPES = " ".join([
    "https://www.googleapis.com/auth/youtube.upload",     # keep: uploading Shorts
    "https://www.googleapis.com/auth/youtube.force-ssl",  # NEW: post/reply to comments
    "https://www.googleapis.com/auth/youtube.readonly",   # keep: stats
])
REDIRECT = "http://127.0.0.1:8080"
AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
ENVP = os.path.join(os.path.dirname(__file__), "..", "secrets", "youtube.env")
_code = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _code["code"] = p.get("code", [None])[0]; _code["error"] = p.get("error", [None])[0]
        self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
        m = "Authorized — close this tab. 🛠️" if _code.get("code") else f"Error: {_code.get('error')}"
        self.wfile.write(f"<body style='font-family:sans-serif;background:#0e2235;color:#fff;padding:60px;text-align:center'><h2>Booked Job · YouTube</h2><p>{m}</p></body>".encode())

    def log_message(self, *a):
        pass


def main():
    e = {}
    for line in open(ENVP):
        if "=" in line:
            k, v = line.strip().split("=", 1); e[k] = v
    cid, csec = e.get("YT_CLIENT_ID"), e.get("YT_CLIENT_SECRET")
    if not (cid and csec):
        sys.exit("No YT_CLIENT_ID/SECRET in youtube.env.")

    url = AUTH + "?" + urllib.parse.urlencode({"client_id": cid, "redirect_uri": REDIRECT,
        "response_type": "code", "scope": SCOPES, "access_type": "offline", "prompt": "consent"})
    srv = http.server.HTTPServer(("127.0.0.1", 8080), Handler)
    threading.Thread(target=lambda: [srv.handle_request() for _ in iter(lambda: not (_code.get("code") or _code.get("error")), False)], daemon=True).start()
    print(">>> Opening browser — authorize as the BOOKED JOB Google account.\n>>> If it doesn't open, paste this URL:\n\n" + url + "\n")
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
        sys.exit("No refresh_token returned. Revoke at myaccount.google.com/permissions and retry.")

    e["YT_REFRESH_TOKEN"] = tok["refresh_token"]
    with open(ENVP, "w") as f:
        for k in ["YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN", "YT_CHANNEL_ID", "YT_CHANNEL_TITLE"]:
            if e.get(k) is not None:
                f.write(f"{k}={e[k]}\n")
    os.chmod(ENVP, 0o600)
    print("\n✅ youtube.env updated with the new refresh token (force-ssl scope). YouTube CTA is now live.")


if __name__ == "__main__":
    main()
