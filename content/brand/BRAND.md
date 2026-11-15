# Booked Job — Brand (field report)

**This is the branding. It matches [booked-job.com](https://booked-job.com/). Do not
reintroduce the old black + hi-vis-orange "STAY BOOKED" look (retired 2026-11-15).**

## Look & feel
A "field report" / filed-document aesthetic: **paper** panel inside a thin ink border,
blunt black display wordmark, stamp-red used *only* as an accent (section markers,
primary buttons, the FIELD REPORT seal). Calm, editorial, blue-collar-credible.

## Palette
**Light / default (the site + all static branding — avatars, banners, cards, email):**
| token | hex | use |
|---|---|---|
| desk | `#d7ccb0` | outer background |
| paper | `#f2ebd9` | panel / card background |
| panel | `#e9e0c9` | insets |
| ink | `#211c12` | text + wordmark (the wordmark is BLACK, never red) |
| muted | `#655c45` | mono kickers / labels |
| rule | `#c3b894` | hairlines |
| **stamp** | `#a62d1a` | the accent — § markers, primary buttons, seal, "REVIEWS" |
| link | `#8a3a1f` | links |
| check | `#2f6b3a` | positive |

**Dark / "blueprint" (the reel/video engine — reels play on dark screens; `lib.ts`):**
paper→`#0e2235` navy · stamp→`#ff6a45` · check→`#4fd083` · link→`#ff9270` · ink→`#e4ecf5`.

## Type
- **Display / wordmark:** Bricolage Grotesque 700–800 (black ink).
- **Body / tagline:** Newsreader (serif; the italic is the signature accent, e.g. *"sold to you."*).
- **Kickers / labels / seal:** Courier Prime (mono, uppercase, wide tracking).

## Wordmark rules
`BOOKED JOB` in black Bricolage. Red is an accent, never the wordmark. Signature marks:
the stamp-red **§** and the rotated **FIELD REPORT · FILED · HONEST** seal.

## Social assets — regenerate, never hand-edit the PNGs
Sources: `content/brand/_assets/*.html`. Render all with:
```
python3 scripts/make_brand_assets.py
```
Outputs (exact size) + where they upload:
| file | size | platform |
|---|---|---|
| `avatar.png` | 1000×1000 | profile pic — FB, IG, YouTube, TikTok, Bluesky, Mastodon |
| `banner.png` | 1500×500 | Bluesky banner + Mastodon header |
| `banner-fb.png` | 1640×624 | Facebook Page cover |
| `banner-yt.png` | 2560×1440 | YouTube channel art |

Uploading to each platform is manual. IG + TikTok use the avatar only.
