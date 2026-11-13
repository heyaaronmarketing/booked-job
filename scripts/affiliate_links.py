#!/usr/bin/env python3
"""Centralized affiliate-link config (verified 2026-11-13, all under hello@aaron.chat).

Reference an affiliate link from any review/article JSON with the token "aff:<key>"
in place of a URL — the renderer resolves it through resolve() and applies the
sponsored rel. Swap a URL here ONCE and every page picks it up on the next render.

ONLY these four vendors have a live affiliate link. Everyone else stays a plain,
untracked URL (Smith.ai has no self-serve program and stays plain permanently;
Jobber/Housecall/Workiz/AnswerForce/PatLive etc. are pending — add them here when
their links go live, don't invent tracking params).
"""

AFFILIATE_LINKS = {
    "ruby": "https://affiliate.ruby.com/server/affiliate_application/r/AARONBP",
    "rosie": "https://heyrosie.com/?ref=aaronky",
    "goodcall": "https://goodcall.com/?ref=aaron61",
    "whatconverts": "https://partners.whatconverts.com/qfzipgqssdai",
}

# FTC: affiliate links get rel="sponsored"; everything keeps nofollow + noopener.
REL_AFFILIATE = "sponsored nofollow noopener"
REL_PLAIN = "noopener nofollow"


def resolve(href):
    """(url, is_affiliate). 'aff:<key>' → the tracked URL + True; anything else → as-is + False."""
    if isinstance(href, str) and href.startswith("aff:"):
        key = href[4:]
        if key in AFFILIATE_LINKS:
            return AFFILIATE_LINKS[key], True
    return href, False
