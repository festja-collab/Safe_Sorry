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


def concept_sheet() -> str:
    cards = "".join(
        f'<div class="card"><div class="art">{svg}</div><h2>{k}. {t}</h2><p>{desc}</p></div>' for k, t, desc, svg in concepts())
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Safe &gt; Sorry: logo concepts</title><style>
body{{margin:0;background:#F5F6F8;font-family:{SANS};color:#1E2B38}} .wrap{{max-width:1000px;margin:0 auto;padding:32px 20px}}
h1{{font-family:{SERIF};color:{NAVY};margin:0 0 6px}} .sub{{color:#6C7683;margin:0 0 28px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}}
.card{{background:#fff;border-radius:20px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.06)}} .art svg{{width:100%;height:auto;display:block}}
.card:last-child .art svg{{width:140px}} h2{{font-family:{SERIF};font-size:20px;margin:16px 0 6px;color:{NAVY}}} p{{margin:0;line-height:1.5;color:#38434F}}
</style></head><body><div class="wrap"><h1>Safe <span style="color:{GOLD}">&gt;</span> Sorry: logo concepts</h1>
<p class="sub">Read as “better safe than sorry”. Navy and gold, matching the app. These are concepts only; nothing has been changed in the app.</p>
<div class="grid">{cards}</div></div></body></html>"""
