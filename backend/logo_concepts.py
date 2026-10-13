"""Logo concept sheet for Safe > Sorry (navy #223342 + gold #BF9B30). Concepts only, nothing is applied to the app."""

NAVY, GOLD, CREAM = "#223342", "#BF9B30", "#F4EEDC"
SERIF = "Georgia, 'Times New Roman', serif"
SANS = "Arial, Helvetica, sans-serif"


def _wordmark(fg: str, x: int = 0, y: int = 0, size: int = 56) -> str:
    """'Safe > Sorry' with a bold gold chevron as the '>'."""
    w = size * 2.0
    cx = x + w + size * 0.55
    h = size * 0.62
    chevron = (f'<path d="M{cx - h * 0.42:.0f} {y - h:.0f} L{cx + h * 0.42:.0f} {y - h / 2:.0f} L{cx - h * 0.42:.0f} {y:.0f}" '
               f'fill="none" stroke="{GOLD}" stroke-width="{size * 0.16:.0f}" stroke-linecap="round" stroke-linejoin="round"/>')
    return (f'<text x="{x}" y="{y}" font-family="{SERIF}" font-size="{size}" font-weight="bold" fill="{fg}">Safe</text>{chevron}'
            f'<text x="{cx + size * 0.62:.0f}" y="{y}" font-family="{SERIF}" font-size="{size}" font-weight="bold" fill="{fg}">Sorry</text>')


def _tag(fg: str, x: int, y: int, anchor: str = "start") -> str:
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{SANS}" font-size="13" letter-spacing="4" fill="{fg}">'
            'BETTER SAFE THAN SORRY</text>')


def concepts() -> list[tuple[str, str, str]]:
    a = (f'<svg viewBox="0 0 460 160" xmlns="http://www.w3.org/2000/svg"><rect width="460" height="160" rx="24" fill="#fff"/>'
         f'{_wordmark(NAVY, 40, 92)}{_tag("#6C7683", 42, 124)}</svg>')
    shield = (f'<path d="M60 26 L104 40 V78 C104 106 84 124 60 134 C36 124 16 106 16 78 V40 Z" fill="{NAVY}"/>'
              f'<path d="M48 58 L74 78 L48 98" fill="none" stroke="{GOLD}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>')
    b = (f'<svg viewBox="0 0 460 160" xmlns="http://www.w3.org/2000/svg"><rect width="460" height="160" rx="24" fill="#fff"/>'
         f'<g transform="translate(16,0)">{shield}</g>'
         f'<text x="150" y="82" font-family="{SERIF}" font-size="44" font-weight="bold" fill="{NAVY}">Safe <tspan fill="{GOLD}">&gt;</tspan> Sorry</text>'
         f'{_tag("#6C7683", 152, 112)}</svg>')
    roof = (f'<path d="M30 88 L80 42 L130 88" fill="none" stroke="{GOLD}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="64" cy="98" r="9" fill="#fff"/><circle cx="96" cy="98" r="9" fill="#fff"/><circle cx="80" cy="108" r="6" fill="#fff"/>'
            f'<path d="M50 132 C50 116 78 114 78 132 Z M82 132 C82 116 110 116 110 132 Z M70 132 C70 122 90 122 90 132 Z" fill="#fff"/>')
    c = (f'<svg viewBox="0 0 460 160" xmlns="http://www.w3.org/2000/svg"><rect width="460" height="160" rx="24" fill="{NAVY}"/>'
         f'<g transform="translate(10,0)">{roof}</g>'
         f'<text x="170" y="86" font-family="{SERIF}" font-size="44" font-weight="bold" fill="#fff">Safe <tspan fill="{GOLD}">&gt;</tspan> Sorry</text>'
         f'{_tag("#C3C9D2", 172, 116)}</svg>')
    d = (f'<svg viewBox="0 0 460 160" xmlns="http://www.w3.org/2000/svg"><rect width="460" height="160" rx="24" fill="{CREAM}"/>'
         f'<circle cx="86" cy="80" r="56" fill="{NAVY}"/><circle cx="86" cy="80" r="48" fill="none" stroke="{GOLD}" stroke-width="2"/>'
         f'<text x="62" y="96" text-anchor="middle" font-family="{SERIF}" font-size="44" font-weight="bold" fill="#fff">S</text>'
         f'<path d="M80 66 L96 80 L80 94" fill="none" stroke="{GOLD}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
         f'<text x="112" y="96" text-anchor="middle" font-family="{SERIF}" font-size="44" font-weight="bold" fill="#fff">S</text>'
         f'<text x="170" y="84" font-family="{SERIF}" font-size="40" font-weight="bold" fill="{NAVY}">Safe <tspan fill="{GOLD}">&gt;</tspan> Sorry</text>'
         f'{_tag("#6E5714", 172, 112)}</svg>')
    icon = (f'<svg viewBox="0 0 160 160" xmlns="http://www.w3.org/2000/svg"><rect width="160" height="160" rx="36" fill="{NAVY}"/>'
            f'<path d="M58 44 L104 80 L58 116" fill="none" stroke="{GOLD}" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    return [
        ("A", "Classic wordmark", "The phrase itself, with a bold gold chevron as the “&gt;”. Clean, confident and easy to read at any size.", a),
        ("B", "Shield", "A navy shield (protection) holding the gold chevron, beside the wordmark. Feels secure and trustworthy.", b),
        ("C", "Family roof", "The “&gt;” turned upwards becomes a roof sheltering a family. It tells the app’s story at a glance.", c),
        ("D", "Monogram seal", "An “S &gt; S” seal for a premium, established feel, like a crest. Works well on letters and the presentation.", d),
        ("E", "App icon", "The gold chevron on navy. Simple enough to stand out on a phone home screen, and it pairs with any of A to D.", icon),
    ]


ROUND = "'Trebuchet MS', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"


def _emblem(fg: str, ring_a: str, ring_b: str, uid: str) -> str:
    """User's draft emblem redrawn: open ring, gold sun, roof, family of three, gold wave."""
    return f"""<defs><linearGradient id="r{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{ring_a}"/><stop offset="1" stop-color="{ring_b}"/></linearGradient></defs>
<path d="M180 70 A118 118 0 1 0 367 120" fill="none" stroke="url(#r{uid})" stroke-width="11" stroke-linecap="round"/>
<circle cx="334" cy="68" r="25" fill="{GOLD}"/>
<path d="M158 152 L256 80 L354 152" fill="none" stroke="{fg}" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="220" cy="130" r="14" fill="{fg}"/>
<path d="M203 152 Q220 144 237 152 L240 196 L232 196 L232 236 L222 236 L222 202 L218 202 L218 236 L208 236 L208 196 L200 196 Z" fill="{fg}"/>
<circle cx="294" cy="130" r="13" fill="{fg}"/>
<path d="M279 152 Q294 144 309 152 L318 206 L306 206 L306 236 L297 236 L297 210 L291 210 L291 236 L282 236 L282 206 L270 206 Z" fill="{fg}"/>
<circle cx="257" cy="180" r="9" fill="{fg}"/>
<path d="M248 194 Q257 189 266 194 L268 214 L263 214 L263 236 L259 236 L259 218 L255 218 L255 236 L251 236 L251 214 L246 214 Z" fill="{fg}"/>
<path d="M238 176 Q244 196 249 200 M276 178 Q270 196 265 200" fill="none" stroke="{fg}" stroke-width="5" stroke-linecap="round"/>
<path d="M146 246 C196 222 270 256 366 226 C320 268 214 274 146 246 Z" fill="{GOLD}"/>"""


def _draft_logo(bg: str, fg: str, sub: str, ring_a: str, ring_b: str, uid: str) -> str:
    return f"""<svg viewBox="0 0 512 480" xmlns="http://www.w3.org/2000/svg"><rect width="512" height="480" rx="28" fill="{bg}"/>
{_emblem(fg, ring_a, ring_b, uid)}
<text x="226" y="340" text-anchor="end" font-family="{ROUND}" font-size="74" font-weight="bold" fill="{fg}">safe</text>
<path d="M244 302 L270 320 L244 338" fill="none" stroke="{GOLD}" stroke-width="15" stroke-linecap="round" stroke-linejoin="round"/>
<text x="288" y="340" font-family="{ROUND}" font-size="74" font-weight="bold" fill="{fg}">sorry</text>
<text x="256" y="384" text-anchor="middle" font-family="{ROUND}" font-size="22" fill="{fg}">Make sense of your protection needs</text>
<line x1="216" y1="410" x2="296" y2="410" stroke="{GOLD}" stroke-width="3" stroke-linecap="round"/>
<text x="256" y="446" text-anchor="middle" font-family="{ROUND}" font-size="18" letter-spacing="1.5" fill="{sub}">it’s better to be safe than sorry</text></svg>"""


def draft_versions() -> list[tuple[str, str, str]]:
    icon = (f'<svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg"><rect width="512" height="512" rx="110" fill="{NAVY}"/>'
            f'<g transform="translate(-154,0) scale(1.6)">{_emblem("#FFFFFF", GOLD, "#E3CF8F", "i")}</g></svg>')
    return [
        ("Main logo (light)", "Your design in the app’s navy and gold: a navy ring, family and wordmark, with a gold sun, wave and chevron.",
         _draft_logo("#FFFFFF", NAVY, "#6C7683", NAVY, "#5B7186", "a")),
        ("Main logo (dark)", "The same logo reversed for navy backgrounds: the welcome screen, splash screen and presentation cover.",
         _draft_logo(NAVY, "#FFFFFF", "#C3C9D2", GOLD, "#E3CF8F", "b")),
        ("App icon", "Just the emblem (family, roof, sun and wave) on navy, sized for a phone home screen.", icon),
    ]


def concept_sheet() -> str:
    mine = "".join(f'<div class="card"><div class="art">{svg}</div><h2>{t}</h2><p>{d}</p></div>' for t, d, svg in draft_versions())
    polished = "".join(
        f'<div class="card"><div class="art"><img src="/api/static/logos/logo_{k}.png" alt="Logo {n}" style="width:100%;border-radius:12px"></div>'
        f'<h2>{n}</h2><p>{d}</p></div>' for k, n, d in [
            ("v1", "Polished 1: closest to your draft", "Your layout refined, with a navy ring, family and wave, a gold sun and a gold chevron."),
            ("v2", "Polished 2: gold ring", "A gold ring and gold ribbon wave around a navy family. The warmest and most premium of the three."),
            ("v3", "Polished 3: soft modern", "Softer shading on the family and a gold, ribbon-style chevron. Calm and modern."),
        ])
    cards = "".join(
        f'<div class="card"><div class="art">{svg}</div><h2>{k}. {t}</h2><p>{desc}</p></div>' for k, t, desc, svg in concepts())
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Safe &gt; Sorry: logo concepts</title><style>
body{{margin:0;background:#F5F6F8;font-family:{SANS};color:#1E2B38}} .wrap{{max-width:1000px;margin:0 auto;padding:32px 20px}}
h1{{font-family:{SERIF};color:{NAVY};margin:0 0 6px}} .sub{{color:#6C7683;margin:0 0 28px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}}
.card{{background:#fff;border-radius:20px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.06)}} .art svg{{width:100%;height:auto;display:block}}
.card:last-child .art svg{{width:140px}} .mine .card:last-child .art svg{{width:200px}} h2{{font-family:{SERIF};font-size:20px;margin:16px 0 6px;color:{NAVY}}} p{{margin:0;line-height:1.5;color:#38434F}}
</style></head><body><div class="wrap"><h1>Safe <span style="color:{GOLD}">&gt;</span> Sorry: logo concepts</h1>
<p class="sub">Read as “better safe than sorry”. Navy and gold, matching the app. These are concepts only; nothing has been changed in the app.</p>
<h1 style="font-size:24px">Polished versions of your draft</h1><p class="sub">Created from your design with an AI image tool, recoloured in navy and gold.</p>
<div class="grid">{polished}</div>
<h1 style="font-size:24px;margin-top:40px">Your draft, reimagined</h1><p class="sub">Same idea (family under a roof, sun, wave and the “&gt;”) redrawn cleanly in navy and gold.</p>
<div class="grid mine">{mine}</div>
<h1 style="font-size:24px;margin-top:40px">Earlier concepts</h1><p class="sub">For comparison.</p>
<div class="grid">{cards}</div></div></body></html>"""
