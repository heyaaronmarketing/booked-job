#!/usr/bin/env python3
"""Render Booked Job social branding (profile avatar + platform banners) in the
field-report look — matches booked-job.com exactly (paper/desk, black Bricolage
wordmark, stamp-red accents, FIELD REPORT seal).

Source of truth = the HTML in content/brand/_assets/. This just renders each to an
exact-size PNG via chrome-headless-shell, so regenerating never drifts off-brand.
(Replaces the retired orange "STAY BOOKED" PIL generator — do NOT bring that back.)

  python3 scripts/make_brand_assets.py
"""
import glob, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
BRAND = os.path.join(ROOT, "content", "brand"); SRC = os.path.join(BRAND, "_assets")

# name -> (width, height). avatar is universal; banners are per-platform.
ASSETS = [("avatar", 1000, 1000),      # all platforms' profile picture
          ("banner", 1500, 500),       # Bluesky banner + Mastodon header
          ("banner-fb", 1640, 624),    # Facebook Page cover
          ("banner-yt", 2560, 1440)]   # YouTube channel art (safe-zone centered)


def chrome():
    for p in glob.glob(os.path.expanduser(
            "~/Library/Caches/ms-playwright/chromium_headless_shell-*/"
            "chrome-headless-shell-mac-arm64/chrome-headless-shell")):
        return p
    for p in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"]:
        if os.path.exists(p):
            return p
    sys.exit("no chrome-headless-shell / Chrome found — install Playwright chromium or Chrome")


def main():
    binary = chrome()
    for name, w, h in ASSETS:
        src = os.path.join(SRC, name + ".html"); out = os.path.join(BRAND, name + ".png")
        if not os.path.exists(src):
            print(f"  !! missing {name}.html"); continue
        subprocess.run([binary, "--headless", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", "--virtual-time-budget=3500",
                        f"--window-size={w},{h}", f"--screenshot={out}", "file://" + src],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  {name}.png ({w}x{h})")
    print("brand assets rendered -> content/brand/  (upload to each platform manually)")


if __name__ == "__main__":
    main()
