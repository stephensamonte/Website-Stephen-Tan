#!/usr/bin/env python3
import json, re, sys
from pathlib import Path
HEX = r'#[0-9a-fA-F]{6}'
def chan(h):
    h = h.lstrip('#').lower()
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
def lum(c):
    v = [x/255.0 for x in c]
    v = [x/12.92 if x <= 0.03928 else ((x+0.055)/1.055)**2.4 for x in v]
    return 0.2126*v[0] + 0.7152*v[1] + 0.0722*v[2]
def ratio(a,b):
    la, lb = lum(a), lum(b)
    return (max(la,lb)+0.05)/(min(la,lb)+0.05)
def main():
    site = Path(sys.argv[1])
    html = (site/'index.html').read_text(encoding='utf-8', errors='ignore')
    css = ''
    for href in re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', html, re.I):
        if href.lower().endswith('.css') and not href.startswith(('http','//')):
            p = site/href
            if p.exists():
                css = p.read_text(encoding='utf-8', errors='ignore')
                break
    hexes = []
    for h in re.findall(HEX, css):
        if h.lower() not in [u.lower() for u in hexes]:
            hexes.append(h)
    body = re.search(r'body\s*\{([^}]*)\}', css, re.I)
    bg = fg = None
    if body:
        m = re.search(r'background(?:-color)?\s*:\s*(#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}))', body.group(1))
        if m: bg = m.group(1)
        m = re.search(r'(?<![-\w])color\s*:\s*(#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}))', body.group(1))
        if m: fg = m.group(1)
    if not bg and hexes: bg = hexes[0]
    if not fg and len(hexes) > 2: fg = hexes[2]
    warm = [h for h in hexes if chan(h)[0] > chan(h)[1] > chan(h)[2]]
    palette = min(10, (3 if len(hexes) >= 4 else 0) + (3 if warm else 0) + (2 if any(chan(h)[0] < 40 and chan(h)[1] < 40 for h in hexes) else 0) + (2 if not any(chan(h)[2] > chan(h)[0] + 40 for h in hexes) else 0))
    contrast = 0
    if bg and fg:
        contrast += 5 if ratio(chan(bg), chan(fg)) >= 4.5 else 0
        muted = next((h for h in hexes if 100 <= chan(h)[0] <= 200), None)
        if muted:
            r = ratio(chan(muted), chan(bg))
            contrast += 3 if r >= 4.5 else (2 if r >= 3 else 0)
        if warm: contrast += 2 if ratio(chan(warm[0]), chan(bg)) >= 3 else 0
    sizes = re.findall(r'font-size\s*:\s*([\d.]+)([a-z]+)', css, re.I)
    rem = [v for v,u in sizes if u.lower() == 'rem']
    fonts = set()
    for line in css.splitlines():
        if 'font-family' in line or re.match(r'\s*--(?:display|body)\b', line):
            fonts.update(re.findall(r'"([^"]+)"', line))
    typography = min(10, (3 if len(fonts) >= 2 else 0) + (2 if len(set(rem)) >= 4 else 0) + (2 if sizes and rem and len(rem) == len(sizes) else 0) + (1 if 'font-weight' in css else 0) + (1 if 'letter-spacing' in css else 0) + (1 if 'line-height' in css else 0))
    tags = ['<main','<section','<article','<header','<footer']
    found = sum(1 for t in tags if re.search(t, html, re.I))
    layout = min(10, (2 if re.search(r'display\s*:\s*grid', css) else 0) + (2 if found == 5 else (1 if found == 4 else 0)) + (2 if re.search(r'(?:max-width|--container)\s*:\s*1[12]\d\dpx', css) else 0) + (2 if re.search(r'@media[^{]*max-width\s*:\s*768px', css) else 0) + (2 if re.search(r'grid-template-columns\s*:[^;}]*\S+\s+\S+', css) or re.search(r'column-count\s*:\s*2', css) else 0))
    durs = [float(d) for d in re.findall(r'(\d+(?:\.\d+)?)ms', css)]
    motion = min(10, (3 if re.search(r'@media[^{]*prefers-reduced-motion', css) else 0) + (3 if re.search(r'transition|animation', css) else 0) + (2 if durs and all(100 <= d <= 300 for d in durs) else 0) + (2 if not re.search(r'<script', html, re.I) else 0))
    imgs = re.findall(r'<img\b[^>]*>', html, re.I)
    content = min(10, (2 if re.search(r'<meta\s+name=["\']description["\']', html, re.I) else 0) + (2 if len(re.findall(r'<h1[\s>]', html, re.I)) == 1 else 0) + (2 if imgs and all('alt=' in i for i in imgs) else 0) + (2 if re.search(r'>[^<]*resume[^<]*</a>', html, re.I) else 0) + (2 if 'linkedin.com' in html else 0))
    cards = set(re.findall(r'card-[a-z0-9-]+', html))
    anti_slop = min(10, (2 if 'href="#"' not in html else 0) + (2 if not re.search(r'lorem|ipsum', html, re.I) else 0) + (2 if len(cards) >= 3 else 0) + (2 if not re.search(r'\.hero\s*\{[^}]*text-align\s*:\s*center', css) else 0) + (2 if '-webkit-background-clip' not in css else 0))
    dims = {'palette': palette, 'contrast': contrast, 'typography': typography, 'layout': layout, 'motion': motion, 'content': content, 'anti_slop': anti_slop}
    total = round(sum(dims.values()) * 100 / 70)
    print(json.dumps({**dims, 'total': total}))
    sys.exit(0 if total >= 70 and all(v >= 5 for v in dims.values()) else 1)
if __name__ == '__main__':
    main()
