#!/usr/bin/env python3
"""Draws the profile README's cards (cards/*.svg) from data/contributions.json.

A README shows SVG only through <img>, where no script runs and nothing outside the file loads.
So each card carries its own CSS keyframes and its own fonts (subset WOFF, base64).
Every element is written as it ends; the keyframes only say where it comes from, so with
STATIC=1 (or prefers-reduced-motion) the card simply rests in its final state.

    python scripts/render_readme_cards.py            # animated
    STATIC=1 python scripts/render_readme_cards.py   # final frame, for screenshots
"""
import base64
import datetime as dt
import json
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"

# The onehub brand (onehublabs.com): ink, cobalt, ivory, and the hero's dark ground.
INK, COBALT, IVORY, GROUND = "#1f2020", "#2d49ad", "#f8f4e6", "#0a0b0a"
PAPER, LINE, MUTED, MUTED_DARK = "#f4f3ef", "#dcdad2", "#5f5e58", "#8f948b"
FONT = "'Space Grotesk',system-ui,-apple-system,'Segoe UI',sans-serif"

SITE = "https://onehublabs.com"
NAME = "Petros Pikionis"
ROLE = "AI Software Engineer"
MOTTO = ["Design.", "Build.", "Automate.", "Scale fast."]
LINE_ABOUT = "I turn ideas into working software."

TILES = [  # value, suffix, label (two lines), ground, text, accent
    ("projects", 9, "", ["Projects designed,", "built and shipped"], COBALT, IVORY, IVORY),
    ("scale", 800, "K+", ["Products processed", "daily with AI"], GROUND, IVORY, "#6f8cf0"),
    ("years", 9, "+", ["Years designing", "and shipping"], IVORY, INK, COBALT),
]

REPOS = [  # file, name, language, colour, description, tags
    ("feedgenix", "feedgenix.com", "PHP · TypeScript", "#2d49ad",
     "AI feed intelligence for e-commerce catalogues: AI field mapping, a translation engine, "
     "and an AI gateway with routing, retries and a circuit breaker. Mapping evals included.",
     ["Laravel 13", "React 19", "pgvector", "Evals", "32 ADRs"]),
    ("myweb", "myweb", "Astro · TypeScript", "#1f2020",
     "onehublabs.com, my own site. Astro and GSAP, three languages, a scroll-told career "
     "story, and a GitHub terrain built from my contributions.",
     ["Astro 5", "GSAP", "EN · EL · DE"]),
    ("arogikos", "arogikos", "PHP", "#2d49ad",
     "Website for a learning-support centre in Kos. Server-rendered Laravel and Blade, "
     "its own design system, self-hosted fonts, GDPR-friendly.",
     ["Laravel 13", "Blade", "Tailwind 4"]),
    ("ourbnb", "ourbnb", "HTML", "#1f2020",
     "ourbnb.gr: short-term rental management in Kos for Airbnb, Booking.com and Expedia. "
     "A static site with no build step and no database.",
     ["Static", "No build", "SEO"]),
]


# ── shared ──────────────────────────────────────────────────────────────────────────────

def font_css():
    css = ""
    for weight in (400, 500, 700):
        data = base64.b64encode((ROOT / "fonts" / f"space-grotesk-{weight}.woff").read_bytes()).decode()
        css += (f"@font-face{{font-family:'Space Grotesk';font-weight:{weight};"
                f"src:url(data:font/woff;base64,{data}) format('woff')}}")
    return css


KEYFRAMES = """
@keyframes rise{from{opacity:0;transform:translateY(14px)}}
@keyframes fade{from{opacity:0}}
@keyframes draw{from{stroke-dashoffset:1}}
@keyframes grow{from{transform:scaleY(0)}}
@keyframes pop{from{opacity:0;transform:scale(.2)}}
@keyframes swing{0%{opacity:0;transform:translateY(40px) rotate(4deg)}70%{opacity:1;transform:translateY(-4px) rotate(-.6deg)}100%{transform:none}}
@keyframes frame{from{opacity:1}to{opacity:1}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes ring{from{opacity:.5;transform:scale(.4)}to{opacity:0;transform:scale(2.4)}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
@keyframes sweep{0%,55%{transform:translateX(-140%)}100%{transform:translateX(240%)}}
.rise{animation:rise .7s cubic-bezier(.2,.7,.2,1) both}
.fade{animation:fade .6s ease both}
.draw{stroke-dasharray:1;animation:draw 1.3s cubic-bezier(.6,0,.2,1) both}
.grow{transform-box:fill-box;transform-origin:bottom;animation:grow .7s cubic-bezier(.2,.8,.2,1) both}
.pop{transform-box:fill-box;transform-origin:center;animation:pop .35s cubic-bezier(.2,1.4,.4,1) both}
.swing{transform-box:fill-box;transform-origin:center bottom;animation:swing .9s cubic-bezier(.2,.8,.2,1) both}
.pulse{animation:pulse 2s ease-in-out infinite}
.ring{transform-box:fill-box;transform-origin:center;opacity:0;animation:ring 2.4s ease-out infinite}
.nudge{transform-box:fill-box;animation:nudge 2.2s ease-in-out infinite}
.sweep{opacity:.5;animation:sweep 5s ease-in-out infinite backwards}
.f{opacity:0;animation:frame linear}
@media (prefers-reduced-motion:reduce){*{animation:none!important}.sweep,.ring{display:none}}
"""
STILL = "*{animation:none!important}.sweep,.ring{display:none}"


def svg(w, h, body, label):
    style = font_css() + KEYFRAMES + (STILL if STATIC else "") + f"text{{font-family:{FONT}}}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f"<style>{style}</style>{body}</svg>\n")


def d(seconds):
    return f'style="animation-delay:{seconds:.2f}s"'


def text(x, y, s, size, fill, weight=400, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def wrap(s, width):
    lines, line = [], ""
    for word in s.split():
        if len(line) + len(word) + 1 > width and line:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


def width(s, size):
    """A close enough width for Space Grotesk, to set words side by side."""
    return sum(0.28 if ch in "il.,I·' " else 0.42 if ch in "ftjr" else 0.86 if ch in "mwMW" else 0.6 for ch in s) * size


def arrow(x, y, colour, cls="nudge"):
    return (f'<g class="{cls}" fill="none" stroke="{colour}" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round"><path d="M{x} {y + 12}L{x + 12} {y}M{x + 3} {y}H{x + 12}V{y + 9}"/></g>')


def write(name, content):
    OUT.mkdir(exist_ok=True)
    (OUT / f"{name}.svg").write_text(content, encoding="utf-8")
    print(f"cards/{name}.svg  {len(content) / 1024:.0f} KB")


# ── data ────────────────────────────────────────────────────────────────────────────────

def load():
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    end = dt.date.fromisoformat(data["endDate"])
    counts = data["counts"]
    days = [(end - dt.timedelta(days=len(counts) - 1 - i), n) for i, n in enumerate(counts)]

    longest = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current = 0
    for _, n in reversed(days):
        if not n:
            break
        current += 1
    best_day = max(days, key=lambda x: x[1])

    months = {}
    for day, n in days:
        months[(day.year, day.month)] = months.get((day.year, day.month), 0) + n
    months = sorted(months.items())[-12:]

    return {"days": days, "total": sum(counts), "active": sum(1 for n in counts if n),
            "longest": longest, "current": current, "best_day": best_day, "months": months}


# ── cards ───────────────────────────────────────────────────────────────────────────────

def hero():
    logo = json.loads((ROOT / "data" / "logo.json").read_text())
    w, h = 840, 300
    scale = 0.215
    paths = ""
    for i, path in enumerate(logo["arc"]):
        paths += f'<path class="draw" pathLength="1" {d(0.9 + i * 0.1)} stroke="{COBALT}" d="{path}"/>'
    for i, path in enumerate(logo["loops"]):
        paths += f'<path class="draw" pathLength="1" {d(0.1 + i * 0.25)} stroke="{IVORY}" d="{path}"/>'
    symbol = (f'<g transform="translate(58 64) scale({scale})" fill="none" stroke-width="30" '
              f'stroke-linecap="round" stroke-linejoin="round">{paths}</g>')

    x = 300
    motto, mx = "", x
    for i, word in enumerate(MOTTO):
        motto += f'<g class="rise" {d(1.5 + i * 0.22)}>{text(mx, 236, word, 17, IVORY, 500)}</g>'
        mx += width(word, 17) + 12
    body = f"""
<defs><clipPath id="c"><rect width="{w}" height="{h}" rx="20"/></clipPath>
<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{COBALT}" stop-opacity="0"/>
<stop offset=".5" stop-color="#6f8cf0"/><stop offset="1" stop-color="{COBALT}" stop-opacity="0"/></linearGradient></defs>
<rect width="{w}" height="{h}" rx="20" fill="{GROUND}"/>
<g clip-path="url(#c)"><rect class="sweep" x="0" y="{h - 3}" width="320" height="3" fill="url(#g)"/></g>
{symbol}
<g class="fade" {d(0.2)}>{text(x, 78, "ONEHUB LABS", 12, MUTED_DARK, 500, extra='letter-spacing="3"')}</g>
<g class="rise" {d(0.5)}>{text(x, 134, NAME, 56, IVORY, 700, extra='letter-spacing="-1.5"')}</g>
<g class="grow" {d(1.0)}><rect x="{x}" y="150" width="56" height="4" rx="2" fill="{COBALT}"/></g>
<g class="rise" {d(1.1)}>{text(x, 188, ROLE, 21, IVORY, 500)}
<circle class="pulse" cx="{x + 232}" cy="181" r="4.5" fill="#6f8cf0"/>
{text(x + 245, 188, LINE_ABOUT, 15, MUTED_DARK)}</g>
{motto}
<g class="fade" {d(2.5)}>{text(w - 62, 262, "onehublabs.com", 13, MUTED_DARK, 500, "end")}{arrow(w - 54, 250, "#6f8cf0")}</g>
"""
    write("hero", svg(w, h, body, f"{NAME}, {ROLE}. {LINE_ABOUT} {' '.join(MOTTO)}"))


def tile(key, value, suffix, label, ground, ink, accent, order):
    w, h = 272, 170
    start = 0.25 + order * 0.18
    steps, span = 18, 1.1
    frames = ""
    for i in range(steps):
        shown = round(value * (i + 1) / (steps + 1))
        frames += (f'<text class="f" style="animation-duration:{span / steps:.3f}s;'
                   f'animation-delay:{start + 0.3 + i * span / steps:.3f}s" x="24" y="86" font-size="56" '
                   f'font-weight="700" fill="{ink}" letter-spacing="-2">{shown}{escape(suffix)}</text>')
    final = (f'<text class="fade" style="animation-duration:.01s;animation-delay:{start + 0.3 + span:.3f}s" '
             f'x="24" y="86" font-size="56" font-weight="700" fill="{ink}" letter-spacing="-2">'
             f"{value}{escape(suffix)}</text>")
    border = f'stroke="{LINE}"' if ground == IVORY else ""
    lines = "".join(text(24, 122 + i * 20, s, 15, ink, 500, extra='opacity=".82"') for i, s in enumerate(label))
    body = f"""
<defs><clipPath id="c"><rect width="{w}" height="{h}" rx="18"/></clipPath></defs>
<g class="swing" {d(start)}>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="{ground}" {border}/>
<g clip-path="url(#c)"><g transform="skewX(-18)"><rect class="sweep" style="animation-delay:{start + 2:.2f}s;opacity:.12" x="0" y="0" width="70" height="{h}" fill="{accent}"/></g></g>
<circle class="ring" style="animation-delay:{start + 1:.2f}s" cx="{w - 34}" cy="34" r="9" fill="none" stroke="{accent}" stroke-width="2"/>
{frames}{final}{lines}
{arrow(w - 40, 28, accent)}
</g>"""
    write(f"tile-{key}", svg(w, h, body, f"{value}{suffix} {' '.join(label)}"))


def activity(c):
    w, h = 840, 250
    months = c["months"]
    top = max(n for _, n in months) or 1
    best = max(range(len(months)), key=lambda i: months[i][1])
    x0, base, bar_w, gap, bar_h = 36, 196, 30, 12, 118
    bars = ""
    for i, ((_, month), n) in enumerate(months):
        x = x0 + i * (bar_w + gap)
        height = max(4, round(bar_h * n / top))
        fill = COBALT if i == best else INK
        bars += (f'<rect class="grow" {d(0.3 + i * 0.06)} x="{x}" y="{base - height}" width="{bar_w}" '
                 f'height="{height}" rx="5" fill="{fill}" opacity="{1 if i == best else .86}"/>')
        bars += text(x + bar_w / 2, base + 20, dt.date(2000, month, 1).strftime("%b"), 11, MUTED, 500, "middle")
        if i == best:
            bars += (f'<g class="pop" {d(1.3)}>'
                     f'{text(x + bar_w / 2, base - height - 9, str(n), 14, COBALT, 700, "middle")}</g>')
    best_date, best_n = c["best_day"]
    stats = [(str(c["total"]), "contributions in the last year"), (str(c["active"]), "active days"),
             (f'{c["longest"]} days', "longest streak"), (f'{best_n} on {best_date.strftime("%-d %b")}', "busiest day")]
    side = ""
    for i, (value, label) in enumerate(stats):
        y = 70 + i * 42
        side += (f'<g class="rise" {d(0.9 + i * 0.12)}>{text(584, y, value, 22, INK, 700)}'
                 f'{text(584, y + 17, label, 12, MUTED, 500)}</g>')
    body = f"""
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="20" fill="{IVORY}" stroke="{LINE}"/>
<g class="fade">{text(36, 40, "BY MONTH", 12, MUTED, 500, extra='letter-spacing="3"')}</g>
<line x1="36" x2="{x0 + 12 * (bar_w + gap) - gap}" y1="{base + .5}" y2="{base + .5}" stroke="{LINE}"/>
{bars}
<line x1="552" x2="552" y1="36" y2="{h - 36}" stroke="{LINE}"/>
{side}"""
    write("activity", svg(w, h, body, f'{c["total"]} contributions in the last year, {c["active"]} active days'))


def graph(c):
    w, h = 840, 176
    days = c["days"]
    values = sorted(n for _, n in days if n)
    cuts = [values[int(len(values) * q)] for q in (0.25, 0.5, 0.75)] if values else [1, 2, 3]

    def level(n):
        return 0 if not n else 1 + sum(n > cut for cut in cuts)

    shades = ["#e9e4d3", "#b9c3e6", "#8094d8", "#4f69c4", COBALT]
    cell, step = 11, 14.6
    first = days[0][0]
    offset = (first.weekday() + 1) % 7  # weeks start on Sunday, as on GitHub
    cols = {}
    for day, n in days:
        index = (day - first).days + offset
        cols.setdefault(index // 7, []).append((index % 7, n))
    grid = ""
    for col, cells in sorted(cols.items()):
        squares = "".join(f'<rect y="{row * step:.1f}" width="{cell}" height="{cell}" rx="2.6" fill="{shades[level(n)]}"/>'
                          for row, n in cells)
        grid += f'<g class="pop" {d(0.2 + col * 0.022)} transform="translate({col * step:.1f} 0)">{squares}</g>'
    legend = "".join(f'<rect x="{w - 124 + i * 15}" y="26" width="11" height="11" rx="2.6" fill="{s}"/>'
                     for i, s in enumerate(shades))
    body = f"""
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="20" fill="{IVORY}" stroke="{LINE}"/>
<g class="fade">{text(36, 36, "A YEAR OF COMMITS", 12, MUTED, 500, extra='letter-spacing="3"')}
{text(w - 134, 36, "less", 11, MUTED, 400, "end")}{legend}{text(w - 42, 36, "more", 11, MUTED)}</g>
<g transform="translate(34 54)">{grid}</g>"""
    write("graph", svg(w, h, body, f'Contribution graph: {c["total"]} contributions in the last year'))


def repo(key, name, language, colour, description, tags, order):
    w, h = 414, 196
    start = 0.2 + order * 0.14
    lines = "".join(text(24, 76 + i * 19, s, 13.5, MUTED) for i, s in enumerate(wrap(description, 56)[:4]))
    chips, x = "", 24
    for tag in tags:
        width = len(tag) * 6.7 + 20
        chips += (f'<rect x="{x}" y="156" width="{width:.0f}" height="22" rx="11" fill="none" stroke="{LINE}"/>'
                  f'{text(x + width / 2, 171, tag, 11, INK, 500, "middle")}')
        x += width + 7
    body = f"""
<g class="rise" {d(start)}>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="{IVORY}" stroke="{LINE}"/>
<rect x="24" y="24" width="4" height="22" rx="2" fill="{colour}"/>
{text(38, 42, name, 20, INK, 700)}
{text(w - 46, 41, language, 11.5, MUTED, 500, "end")}
{arrow(w - 36, 28, COBALT)}
{lines}{chips}
</g>"""
    write(f"repo-{key}", svg(w, h, body, f"{name}: {description}"))


def main():
    c = load()
    hero()
    for order, t in enumerate(TILES):
        tile(*t, order)
    graph(c)
    activity(c)
    for order, r in enumerate(REPOS):
        repo(*r, order)


if __name__ == "__main__":
    main()
