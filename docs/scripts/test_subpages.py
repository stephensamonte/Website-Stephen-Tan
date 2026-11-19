#!/usr/bin/env python3
"""Regression tests for the restyled sub-pages (about.html, computer-science.html).

Follows the project convention of scripts/score_website.py: stdlib only,
deterministic, prints one JSON result object, exits 0 only when every case
passes. The cases pin the sub-page design contract: each sub-page is themed by
the shared stylesheet assets/css/site.css (no inline style overrides, no
scripts, no other stylesheets), that stylesheet carries the front-page design
tokens from assets/css/index.css :root (bg #141210 / text #ece7df / muted
#a89f93 / accent #e8825a / container 1120px, Sora + Source Sans 3 stacks),
body is pinned to those tokens (rgb(20,18,16) bg, rgb(236,231,223) text,
~15.3:1 AAA contrast), and the content hygiene the accept gate asserts
(one h1, ordered headings, meta description, no a[href="#"], alt on every img).

Usage: python scripts/test_subpages.py <site-dir>   (site dir contains about.html)
"""
import json, re, sys
from pathlib import Path

SUB_PAGES = ["about.html", "computer-science.html"]
SPEC_TOKENS = {
    "--bg": "#141210",
    "--text": "#ece7df",
    "--muted": "#a89f93",
    "--accent": "#e8825a",
    "--container": "1120px",
}


def root_tokens(css):
    m = re.search(r":root\s*\{([^}]*)\}", css)
    toks = {}
    if m:
        for name, val in re.findall(r"(--[a-z-]+)\s*:\s*([^;]+);", m.group(1)):
            toks[name] = val.strip()
    return toks


def heading_order_ok(html):
    levels = [int(t) for t in re.findall(r"<h([1-6])[\s>]", html, re.I)]
    return all(b <= a + 1 for a, b in zip(levels, levels[1:]))


def check_page(site, name):
    html = (site / name).read_text(encoding="utf-8", errors="ignore")
    cases = []

    def case(label, ok):
        cases.append({"case": name + ": " + label, "pass": bool(ok)})

    sheets = re.findall(r"<link[^>]*>", html, re.I)
    sheets = [s for s in sheets if re.search(r"rel=[\"']stylesheet[\"']", s, re.I)]
    hrefs = re.findall(r"href=[\"']([^\"']+)[\"']", " ".join(sheets))
    case("exactly one stylesheet link, assets/css/site.css",
         len(hrefs) == 1 and hrefs[0] == "assets/css/site.css")
    case("no <script> elements", not re.search(r"<script\b", html, re.I))
    case("exactly one <h1>", len(re.findall(r"<h1[\s>]", html, re.I)) == 1)
    desc = re.search(r"<meta\s+name=[\"']description[\"']\s+content=[\"']([^\"']*)[\"']", html, re.I)
    case("meta description present, >= 20 chars",
         bool(desc) and len(desc.group(1)) >= 20)
    case("heading levels never skip down", heading_order_ok(html))
    case('no a[href="#"]', 'href="#"' not in html)
    imgs = re.findall(r"<img\b[^>]*>", html, re.I)
    case("every <img> has an alt attribute", all("alt=" in i for i in imgs))
    inline = re.findall(r"<[a-z][a-z0-9]*[^>]*\bstyle=[\"'][^\"']*[\"']", html, re.I)
    case("no inline style attributes (theme comes from site.css)", not inline)
    return cases


def check_theme(site):
    index_css = (site / "assets/css/index.css").read_text(encoding="utf-8", errors="ignore")
    site_css = (site / "assets/css/site.css").read_text(encoding="utf-8", errors="ignore")
    front, sub = root_tokens(index_css), root_tokens(site_css)
    cases = []

    def case(label, ok):
        cases.append({"case": "site.css: " + label, "pass": bool(ok)})

    for name, spec in SPEC_TOKENS.items():
        case("token " + name + " equals front page and spec (" + spec + ")",
             sub.get(name) == spec and front.get(name) == spec)
    case('display stack uses "Sora"', '"Sora"' in sub.get("--display", ""))
    case('body stack uses "Source Sans 3"', '"Source Sans 3"' in sub.get("--body", ""))
    body = re.search(r"body\s*\{([^}]*)\}", site_css)
    b = body.group(1) if body else ""
    case("body background pinned to --bg token",
         re.search(r"background(?:-color)?\s*:\s*var\(--bg\)", b) is not None)
    case("body color pinned to --text token",
         re.search(r"(?<![-\w])color\s*:\s*var\(--text\)", b) is not None)
    return cases


def main():
    site = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    cases = []
    for name in SUB_PAGES:
        cases += check_page(site, name)
    cases += check_theme(site)
    failed = [c for c in cases if not c["pass"]]
    print(json.dumps({"total": len(cases), "failed": len(failed), "cases": cases}, indent=1))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
