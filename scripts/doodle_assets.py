#!/usr/bin/env python3
"""Doodle Explainer — reusable SVG asset library (the one-time investment).
Emits clean marker-style SVG components into doodle/assets/. Character is RIGGED:
each part is its own full-canvas (500x820) transparent SVG so the engine can rotate
it about its joint pivot. Props are standalone SVGs. Tokens are the single source of
truth. Run: python3 scripts/doodle_assets.py  (re-run to regenerate after edits)."""
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "doodle", "assets")

# ---- A1 design tokens ----
INK = "#141414"; STROKE = 9
PAL = {"skin": "#f3d3bf", "brand": "#a62d1a", "yellow": "#c8321b", "blue": "#3FA7D6",
       "green": "#46c06b", "paper": "#FFFFFF", "ink": INK}
CW, CH = 500, 820          # character canvas
# joint pivots in character space (engine reads these)
PIVOTS = {"head": (250, 300), "armFront": (305, 350), "armBack": (195, 350),
          "torso": (250, 560)}


def _svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}"><g fill="none" stroke="{INK}" stroke-width="{STROKE}" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>')


def write(name, w, h, body):
    open(os.path.join(ASSETS, name + ".svg"), "w").write(_svg(w, h, body))


# ---------- CHARACTER PARTS (shared 500x820 canvas) ----------
def char_parts(shirt=PAL["brand"], tag=""):
    # legs (static, back)
    write(f"legs{tag}", CW, CH,
          f'<path d="M222,548 L208,742" /><path d="M278,548 L292,742" />'
          f'<path d="M208,742 q-26,8 -34,2" /><path d="M292,742 q26,8 34,2" />')
    # armBack (far arm, pivot at shoulder 195,350) — behind torso
    write(f"armBack{tag}", CW, CH,
          f'<path d="M198,352 q-46,58 -40,118" /><circle cx="156" cy="474" r="13" fill="{PAL["skin"]}"/>')
    # torso (tee, filled shirt)
    write(f"torso{tag}", CW, CH,
          f'<path d="M196,344 q54,-20 108,0 l18,150 q6,70 -72,72 q-78,-2 -72,-72 z" '
          f'fill="{shirt}" />')
    # neck
    write(f"neck{tag}", CW, CH, f'<path d="M232,300 l0,46" /><path d="M268,300 l0,46" />')
    # head (riggable) — 4 swappable expressions (mouth + brows), shared eyes. NO hat here:
    # the hat is a separate SLOT overlay (trade-swap system, art-direction §2).
    eyes = (f'<circle cx="222" cy="216" r="10" fill="{INK}" stroke="none"/>'
            f'<circle cx="278" cy="216" r="10" fill="{INK}" stroke="none"/>')
    MOODS = {
        "neutral":   ('<path d="M222,250 q28,12 56,0" />', ''),
        "frustrated":('<path d="M222,256 q28,-14 56,0" />', '<path d="M206,198 l28,10" /><path d="M294,198 l-28,10" />'),
        "thinking":  ('<path d="M236,252 q18,6 30,-2" />', '<path d="M206,196 q14,-4 28,0" /><path d="M264,184 q14,-5 28,0" />'),
        "delighted": ('<path d="M210,242 q40,40 80,0 q-40,6 -80,0 z" fill="' + INK + '" />',
                      '<path d="M206,194 q14,-9 28,-2" /><path d="M266,192 q14,-7 28,2" />'),
    }
    for mood, (mouth, brows) in MOODS.items():
        write(f"head_{mood}{tag}", CW, CH,
              f'<circle cx="250" cy="222" r="84" fill="{PAL["paper"]}" />' + eyes + brows + mouth)
    # armFront (near arm, pivot shoulder 305,350) — in front of torso
    write(f"armFront{tag}", CW, CH,
          f'<path d="M302,352 q48,56 42,118" /><circle cx="346" cy="474" r="13" fill="{PAL["skin"]}"/>')


def hats_and_tools():
    """Trade-swap SLOT assets (full-canvas 500x820, aligned to the rig). One rig -> many
    verticals by swapping hat_<trade> + tool_<trade>. art-direction §2."""
    # HATS (sit on the head, top ~y92-184)
    write("hat_hardhat", CW, CH,
          f'<path d="M150,182 q100,22 200,0" fill="{PAL["yellow"]}" />'
          f'<path d="M168,184 a82,82 0 0 1 164,0 z" fill="{PAL["yellow"]}" />'
          f'<path d="M250,104 l0,80" stroke-width="6"/><path d="M212,114 l-14,68" stroke-width="5"/>'
          f'<path d="M288,114 l14,68" stroke-width="5"/>')
    write("hat_cap", CW, CH,                                   # ball cap — sits high, clear of the eyes
          f'<path d="M178,156 a74,62 0 0 1 148,0 z" fill="{PAL["brand"]}" />'
          f'<path d="M154,158 q-6,12 16,16 q88,6 116,-6" fill="{PAL["brand"]}" />'
          f'<circle cx="252" cy="92" r="9" fill="{PAL["brand"]}"/>')
    write("hat_beanie", CW, CH,                                # knit cap (winter trades)
          f'<path d="M172,184 a80,68 0 0 1 160,0 z" fill="{PAL["blue"]}" />'
          f'<path d="M172,182 l160,0" stroke-width="12"/><circle cx="252" cy="108" r="12" fill="{PAL["blue"]}"/>')
    # TOOLS (held near the front hand ~ (346,474))
    write("tool_wrench", CW, CH,                               # plumber
          f'<path d="M352,470 l40,80" stroke-width="16"/>'
          f'<path d="M384,536 q26,16 44,-6 q-10,-22 -32,-16 z" fill="{PAL["device"] if "device" in PAL else "#3b3b3b"}"/>')
    write("tool_roller", CW, CH,                               # painter
          f'<path d="M348,478 l30,64" stroke-width="14"/><rect x="356" y="436" width="74" height="26" rx="8" fill="{PAL["brand"]}"/>')
    write("tool_brush", CW, CH,                                # general
          f'<path d="M346,476 l34,70" stroke-width="14"/><path d="M362,430 l40,18 l-10,30 l-40,-18 z" fill="{PAL["yellow"]}"/>')


# ---------- PROPS (standalone SVGs) ----------
def props():
    # brand hero-prop: hard hat (Booked Job)
    write("brandhat", 360, 260,
          f'<path d="M40,196 q140,-46 280,0" fill="{PAL["brand"]}" />'
          f'<path d="M120,150 q60,-70 120,0" fill="{PAL["yellow"]}" />'
          f'<path d="M30,196 l300,0" /><rect x="168" y="120" width="24" height="60" fill="{PAL["yellow"]}"/>')
    # phone with search bar (draw-on capable bezel as single stroked path elsewhere)
    write("phone", 240, 420,
          f'<rect x="20" y="20" width="200" height="380" rx="28" fill="{PAL["paper"]}" />'
          f'<rect x="48" y="70" width="144" height="50" rx="14" fill="{PAL["blue"]}" opacity="0.18" stroke="{INK}"/>'
          f'<circle cx="74" cy="95" r="13" /><path d="M84,105 l16,16" />'
          f'<path d="M48,170 l144,0" stroke-width="6"/><path d="M48,220 l120,0" stroke-width="6"/>'
          f'<path d="M48,270 l140,0" stroke-width="6"/>')
    # house
    write("house", 360, 320,
          f'<path d="M40,150 L180,40 L320,150" /><rect x="74" y="150" width="212" height="150" fill="{PAL["paper"]}"/>'
          f'<rect x="160" y="210" width="60" height="90" fill="{PAL["brand"]}" opacity="0.25" stroke="{INK}"/>'
          f'<rect x="96" y="180" width="44" height="40" stroke="{INK}" fill="{PAL["yellow"]}" opacity="0.4"/>')
    # funnel (single stroked outline = draw-on capable) + 4 stage labels handled by engine text
    write("funnel", 420, 420,
          f'<path d="M40,50 L380,50 L250,250 L250,360 L170,360 L170,250 Z" fill="{PAL["paper"]}" />')
    # magnifier
    write("magnifier", 300, 300,
          f'<circle cx="130" cy="130" r="86" fill="{PAL["paper"]}"/><path d="M192,192 L268,268" stroke-width="14"/>')
    # coin (plain disc, no markings)
    write("coin", 200, 200,
          f'<circle cx="100" cy="100" r="84" fill="{PAL["yellow"]}"/>'
          f'<circle cx="100" cy="100" r="64" fill="none" stroke="{INK}" stroke-width="6"/>')
    # speech bubble
    write("bubble", 300, 240,
          f'<path d="M30,30 h240 a20,20 0 0 1 20,20 v110 a20,20 0 0 1 -20,20 h-150 l-50,46 l6,-46 h-46 a20,20 0 0 1 -20,-20 v-110 a20,20 0 0 1 20,-20 z" fill="{PAL["paper"]}"/>')
    # clock (7am)
    write("clock", 240, 240,
          f'<circle cx="120" cy="120" r="96" fill="{PAL["paper"]}"/><path d="M120,120 L120,60 M120,120 L162,150" stroke-width="8"/>'
          f'<path d="M60,40 q-26,-26 -44,6 M180,40 q26,-26 44,6" />')


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    char_parts(shirt=PAL["blue"], tag="")          # default narrator (blue tee)
    char_parts(shirt=PAL["brand"], tag="_brand")    # variant speaker (orange)
    hats_and_tools()
    props()
    import glob
    print("wrote", len(glob.glob(os.path.join(ASSETS, "*.svg"))), "SVG assets ->", ASSETS)
