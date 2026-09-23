# Generates assets/hero-light.svg and assets/hero-dark.svg. Run from the repo root: python scripts/gen_hero.py
THEMES = {
    "light": dict(bg="#FAFAF7", ink="#111111", mute="#6B6B66", rule="#D9D9D3", accent="#111111"),
    "dark":  dict(bg="#0B0B0C", ink="#F2F2EE", mute="#8A8A86", rule="#2A2A2C", accent="#F2F2EE"),
}
W, H = 1200, 400
SERIF = "Georgia, 'Iowan Old Style', 'Times New Roman', serif"
MONO  = "ui-monospace, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

TPL = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
  <title id="t">dickbown - Care for the system, and the surface.</title>
  <desc id="d">Typographic profile banner for dickbown (ROTl24): AI products, agent systems, creative tooling.</desc>
  <style>
    .serif {{ font-family: {SERIF}; }}
    .mono  {{ font-family: {MONO}; font-size: 15px; letter-spacing: 0.12em; text-transform: uppercase; }}
    .caret {{ animation: blink 1.1s steps(1, end) infinite; }}
    @keyframes blink {{ 0%, 55% {{ opacity: 1; }} 56%, 100% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .caret {{ animation: none; }} }}
  </style>
  <rect width="{W}" height="{H}" fill="{{bg}}"/>

  <!-- top meta row -->
  <text class="mono" x="64" y="72" fill="{{mute}}">dickbown&#160;&#160;/&#160;&#160;ROTl24</text>
  <text class="mono" x="{W-64}" y="72" fill="{{mute}}" text-anchor="end">AI products&#160;&#160;·&#160;&#160;agent systems&#160;&#160;·&#160;&#160;tooling</text>
  <line x1="64" y1="92" x2="{W-64}" y2="92" stroke="{{rule}}" stroke-width="1"/>

  <!-- headline -->
  <text class="serif" x="60" y="196" font-size="92" fill="{{ink}}" letter-spacing="-0.02em">Care for the system,</text>
  <text class="serif" x="60" y="290" font-size="92" fill="{{ink}}" letter-spacing="-0.02em" font-style="italic">and the surface.<tspan class="caret" font-style="normal" fill="{{accent}}">_</tspan></text>

  <!-- bottom index row -->
  <line x1="64" y1="330" x2="{W-64}" y2="330" stroke="{{rule}}" stroke-width="1"/>
  <text class="mono" x="64" y="360" fill="{{mute}}"><tspan fill="{{ink}}">01</tspan>&#160;&#160;Agent systems</text>
  <text class="mono" x="360" y="360" fill="{{mute}}"><tspan fill="{{ink}}">02</tspan>&#160;&#160;Creative tooling</text>
  <text class="mono" x="660" y="360" fill="{{mute}}"><tspan fill="{{ink}}">03</tspan>&#160;&#160;Full-stack products</text>
  <text class="mono" x="{W-64}" y="360" fill="{{ink}}" text-anchor="end">github.com/ROTl24&#160;&#8599;</text>
</svg>
"""

for name, c in THEMES.items():
    out = TPL
    for k, v in c.items():
        out = out.replace("{" + k + "}", v)
    with open(f"assets/hero-{name}.svg", "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote", f"assets/hero-{name}.svg", len(out), "bytes")
