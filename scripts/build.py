"""Build the profile README.

- Fetches merged pull requests authored by LOGIN in repositories LOGIN does not own.
- Renders assets/terminal.svg: a self-contained animated terminal (SMIL, no scripts, no external fonts).
- Rewrites the block between <!-- prs:start --> and <!-- prs:end --> in README.md.

Run from the repo root:  python scripts/build.py
Auth: GH_TOKEN or GITHUB_TOKEN in the environment (falls back to `gh auth token`).
"""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from datetime import date

LOGIN = "ROTl24"
NAME = "dickbown"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG_PATH = os.path.join(ROOT, "assets", "terminal.svg")
README_PATH = os.path.join(ROOT, "README.md")

# ---------------------------------------------------------------- data ------


def token() -> str:
    t = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if t:
        return t
    return subprocess.check_output(["gh", "auth", "token"], text=True).strip()


def fetch_prs() -> list[dict]:
    q = f"author:{LOGIN} type:pr -user:{LOGIN}"
    url = ("https://api.github.com/search/issues?q=" + urllib.parse.quote(q)
           + "&sort=created&order=desc&per_page=50")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token()}",
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{LOGIN}-profile-builder",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        items = json.load(r)["items"]
    prs = []
    for it in items:
        repo = it["repository_url"].split("/repos/")[1]
        merged = bool((it.get("pull_request") or {}).get("merged_at"))
        state = "merged" if merged else it["state"]  # merged | open | closed
        prs.append({
            "repo": repo,
            "number": it["number"],
            "title": it["title"],
            "url": it["html_url"],
            "state": state,
            "date": it["created_at"][:10],
        })
    return [p for p in prs if p["state"] == "merged"]


# ------------------------------------------------------------- terminal -----

W = 1100
PAD_X, LINE_H, TOP = 40, 30, 94           # left padding, line height, first baseline
FS, CW = 18, 10.8                         # font size, forced character advance
MAX_COLS = int((W - 2 * PAD_X) / CW)      # characters per line
CMD_CPS = 0.055                           # seconds per typed character
PROMPT = "~ $ "
FONT = ("ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, "
        "'Liberation Mono', 'DejaVu Sans Mono', monospace")

C = dict(bg="#0B0F17", border="#1C2433", bar="#111826", title="#6B7A90",
         prompt="#3FB950", cmd="#E6EDF3", out="#8B98A9", key="#C9D1D9", art="#E6EDF3",
         orange="#FF9F43", merged="#D2A8FF", open="#3FB950", closed="#F85149")

ART = [  # figlet "slant"
    "       ___      __   __                      ",
    "  ____/ (_)____/ /__/ /_  ____ _      ______ ",
    " / __  / / ___/ //_/ __ \\/ __ \\ | /| / / __ \\",
    "/ /_/ / / /__/ ,< / /_/ / /_/ / |/ |/ / / / /",
    "\\__,_/_/\\___/_/|_/_.___/\\____/|__/|__/_/ /_/ ",
]
ART_W = max(len(r) for r in ART)
INFO_COL = ART_W + 4


def fit(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def neofetch_block(prs: list[dict]) -> list[dict]:
    """Side-by-side figlet name (left) and key/value info (right), then a colour swatch row."""
    merged = len(prs)
    info = [
        [(f"{NAME}@github", "key")],
        [("─" * len(f"{NAME}@github"), "out")],
        [("Role      ", "key"), ("AI product builder", "cmd")],
        [("Roots     ", "key"), ("Japanese · Chinese", "cmd")],
        [("Location  ", "key"), ("Germany · 12 countries so far", "cmd")],
        [("Languages ", "key"), ("日本語 · 中文 · English", "cmd")],
        [("Focus     ", "key"), ("agents · creative tooling · full-stack", "cmd")],
        [("Projects  ", "key"), ("wenyao", "orange"), (" · ", "out"), ("tiktok-ai-skills", "orange")],
        [("Upstream  ", "key"), (f"{merged} merged pull requests", "cmd")],
        [("Contact   ", "key"), ("xdickbown@gmail.com", "cmd")],
    ]
    rows: list[dict] = []
    for i in range(max(len(ART), len(info))):
        segs: list = []
        left = ART[i] if i < len(ART) else ""
        segs.append((left.ljust(INFO_COL), "art" if i < len(ART) else "out"))
        if i < len(info):
            segs += info[i]
        rows.append({"typed": False, "segs": segs})
    return rows


def terminal_lines(prs: list[dict]) -> list[dict]:
    """Each line: {'segs': [(text, color)], 'typed': bool}. Typed lines start with the prompt."""
    P = [(PROMPT, "prompt")]
    lines: list[dict] = [{"typed": True, "segs": P + [("neofetch", "cmd")]}]
    lines += neofetch_block(prs)
    lines += [
        {"typed": False, "segs": [("", "out")]},
        {"typed": True, "segs": P + [("gh pr list --author @me --state merged --search '-user:@me' --limit 4", "cmd")]},
    ]
    repo_w, num_w = 30, 6
    for pr in prs[:4]:
        repo = fit(pr["repo"], repo_w).ljust(repo_w)
        num = f"#{pr['number']}".ljust(num_w)
        state = pr["state"].ljust(7)
        title = fit(pr["title"], MAX_COLS - 2 - 7 - 1 - repo_w - 1 - num_w - 1)
        lines.append({"typed": False, "segs": [
            ("● ", pr["state"]), (state, pr["state"]), (" ", "out"), (repo, "cmd"), (" ", "out"),
            (num, "orange"), (" ", "out"), (title, "out"),
        ]})
    lines.append({"typed": True, "segs": list(P)})  # idle prompt with a blinking caret
    return lines


def clip(i: int, y: int, start_w: float, anims: str) -> str:
    return (f'<clipPath id="c{i}"><rect x="{PAD_X}" y="{y - 22}" width="{start_w:.1f}" '
            f'height="{LINE_H}">{anims}</rect></clipPath>')


def render_svg(prs: list[dict]) -> str:
    lines = terminal_lines(prs)
    height = TOP + LINE_H * len(lines) + 24
    t = 0.6  # timeline cursor in seconds
    defs, body, caret = [], [], []
    p = len(PROMPT)

    for i, ln in enumerate(lines):
        y = TOP + i * LINE_H
        text = "".join(s for s, _ in ln["segs"])
        n = len(text)
        width = n * CW
        tspans = "".join(f'<tspan fill="{C[c]}">{html.escape(s)}</tspan>' for s, c in ln["segs"])
        body.append(f'<text x="{PAD_X}" y="{y}" clip-path="url(#c{i})" textLength="{width:.1f}" '
                    f'lengthAdjust="spacing">{tspans}</text>')

        if not ln["typed"]:
            defs.append(clip(i, y, 0, f'<set attributeName="width" to="{width:.1f}" begin="{t:.2f}s" fill="freeze"/>'))
            t += 0.12
            if i + 1 < len(lines) and lines[i + 1]["typed"]:
                t += 0.45
            continue

        typed = n - p
        caret.append(f'<set attributeName="y" to="{y - 17}" begin="{t:.2f}s" fill="freeze"/>')
        if typed:
            dur = typed * CMD_CPS
            values = ";".join(f"{(p + k) * CW:.1f}" for k in range(typed + 1))
            xs = ";".join(f"{PAD_X + (p + k) * CW:.1f}" for k in range(typed + 1))
            defs.append(clip(i, y, 0,
                             f'<set attributeName="width" to="{p * CW:.1f}" begin="{t:.2f}s" fill="freeze"/>'
                             f'<animate attributeName="width" begin="{t:.2f}s" dur="{dur:.2f}s" values="{values}" '
                             f'calcMode="discrete" fill="freeze"/>'))
            caret.append(f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>')
            caret.append(f'<animate attributeName="x" begin="{t:.2f}s" dur="{dur:.2f}s" values="{xs}" '
                         f'calcMode="discrete" fill="freeze"/>')
            t += dur + 0.35
            caret.append(f'<set attributeName="opacity" to="0" begin="{t:.2f}s" fill="freeze"/>')
        else:
            defs.append(clip(i, y, 0, f'<set attributeName="width" to="{width:.1f}" begin="{t:.2f}s" fill="freeze"/>'))
            caret.append(f'<set attributeName="x" to="{PAD_X + p * CW:.1f}" begin="{t:.2f}s" fill="freeze"/>')
            caret.append(f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.55;0.55;1" '
                         f'dur="1.1s" begin="{t:.2f}s" repeatCount="indefinite"/>')

    caret_el = (f'<rect x="{PAD_X}" y="{TOP - 17}" width="{CW:.1f}" height="22" rx="1" '
                f'fill="{C["cmd"]}" opacity="0">' + "".join(caret) + "</rect>")
    nl = "\n"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-labelledby="t d">
<title id="t">{NAME} ({LOGIN}) terminal</title>
<desc id="d">Animated terminal: whoami, projects wenyao and tiktok-ai-skills, and recent pull requests to other open-source repositories.</desc>
<style>text{{font-family:{FONT};font-size:{FS}px;white-space:pre}}</style>
<defs>{"".join(defs)}</defs>
<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="14" fill="{C['bg']}" stroke="{C['border']}"/>
<path d="M14.5 0.5h{W - 29}a14 14 0 0 1 14 14v31.5H0.5V14.5a14 14 0 0 1 14-14z" fill="{C['bar']}"/>
<line x1="0.5" y1="46" x2="{W - 0.5}" y2="46" stroke="{C['border']}"/>
<circle cx="26" cy="23" r="6" fill="#FF5F57"/><circle cx="46" cy="23" r="6" fill="#FEBC2E"/><circle cx="66" cy="23" r="6" fill="#28C840"/>
<text x="{W / 2}" y="29" text-anchor="middle" fill="{C['title']}" font-size="14">{NAME}@github — ~</text>
{nl.join(body)}
{caret_el}
</svg>
"""


# --------------------------------------------------------------- ticker -----

TICKER_PATH = os.path.join(ROOT, "assets", "ticker.svg")
TICKER_ITEMS = ["agent systems", "creative tooling", "full-stack products", "wenyao",
                "tiktok-ai-skills", "open source", "jp × cn", "based in germany", "12 countries", "odd little products"]


def render_ticker() -> str:
    """Orange strip with an endlessly scrolling line of text (SMIL translate, seamless loop)."""
    h, fs, cw = 46, 14, 8.4
    projects = {"wenyao", "tiktok-ai-skills"}
    segs = []
    for it in TICKER_ITEMS:
        segs.append((it.upper(), "orange" if it in projects else "out"))
        segs.append(("   ✦   ", "title"))
    phrase = "".join(t for t, _ in segs)
    seg_w = len(phrase) * cw
    reps = int(W / seg_w) + 2
    text = "".join(f'<tspan fill="{C[c]}">{html.escape(t)}</tspan>' for t, c in segs * reps)
    total_w = seg_w * reps
    dur = seg_w / 60  # 60 px per second
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{html.escape(' · '.join(TICKER_ITEMS))}">
<defs><clipPath id="strip"><rect x="0" y="0" width="{W}" height="{h}" rx="10"/></clipPath></defs>
<rect x="0.5" y="0.5" width="{W - 1}" height="{h - 1}" rx="10" fill="{C['bar']}" stroke="{C['border']}"/>
<g clip-path="url(#strip)"><text x="0" y="{h / 2 + fs * 0.36:.1f}" font-family="{FONT}" font-size="{fs}px" font-weight="600" letter-spacing="0.08em" textLength="{total_w:.1f}" lengthAdjust="spacing" xml:space="preserve">{text}<animateTransform attributeName="transform" type="translate" from="0 0" to="{-seg_w:.1f} 0" dur="{dur:.2f}s" repeatCount="indefinite"/></text></g>
</svg>
"""


# --------------------------------------------------------------- readme -----


def prs_markdown(prs: list[dict]) -> str:
    rows = []
    for pr in prs[:8]:
        icon = f'<img src="./assets/icons/{pr["state"]}.svg" width="16" height="16" alt="{pr["state"]}" align="top">'
        rows.append(f"{icon}&nbsp; **[{pr['repo']}](https://github.com/{pr['repo']})** "
                    f"[#{pr['number']}]({pr['url']}) · {pr['title']}  ")
        rows.append(f"<sub>{pr['date']}</sub>\n")
    rows.append(f"<sub>Updated {date.today().isoformat()} · regenerated daily by GitHub Actions</sub>")
    return "\n".join(rows)


def update_readme(prs: list[dict]) -> None:
    md = open(README_PATH, encoding="utf-8").read()
    if "<!-- prs:start -->" not in md or "<!-- prs:end -->" not in md:
        raise SystemExit("README.md has no <!-- prs:start --> / <!-- prs:end --> markers")
    block = "<!-- prs:start -->\n" + prs_markdown(prs) + "\n<!-- prs:end -->"
    new = re.sub(r"<!-- prs:start -->.*?<!-- prs:end -->", lambda m: block, md, flags=re.S)
    open(README_PATH, "w", encoding="utf-8", newline="\n").write(new)


if __name__ == "__main__":
    prs = fetch_prs()
    os.makedirs(os.path.dirname(SVG_PATH), exist_ok=True)
    open(SVG_PATH, "w", encoding="utf-8", newline="\n").write(render_svg(prs))
    open(TICKER_PATH, "w", encoding="utf-8", newline="\n").write(render_ticker())
    update_readme(prs)
    print(f"{len(prs)} pull requests · wrote assets/terminal.svg, assets/ticker.svg and README.md")
