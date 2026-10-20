"""Myth-buster reel: "My employer's death-in-service is enough". Run: python reel_myth.py"""
from PIL import Image, ImageDraw

import scripts_make_reel as R
from reel_insure import icon
from scripts_make_reel import GOLD, MUTED, SANS, SERIF, W, WHITE, ease, make_end, text_block


def label(img, text, y, t, t_in=0.0):
    a = ease((t - t_in) / 0.4)
    if a <= 0:
        return
    d = ImageDraw.Draw(img)
    f = SANS(44, "Bold")
    tw = d.textlength(text, font=f)
    x0 = (W - tw) / 2 - 36
    d.rounded_rectangle((x0, y, x0 + tw + 72, y + 84), radius=42, outline=GOLD + (int(255 * a),), width=4)
    d.text((x0 + 36, y + 14), text, font=f, fill=GOLD + (int(255 * a),))


def s_myth(img, t):
    label(img, "COMMON MYTH", 380, t)
    y = text_block(img, "“I’ve got death in service", SERIF(92, "Bold"), 560, WHITE, 0.3, t)
    y = text_block(img, "at work…", SERIF(92, "Bold"), y, WHITE, 0.5, t)
    text_block(img, "so I’m covered.”", SERIF(108, "Bold"), y + 30, GOLD, 1.2, t)
    text_block(img, "Let’s check that.", SANS(56, "SemiBold"), 1220, MUTED, 2.2, t)


def fact(n, title, body, kind):
    def scene(img, t):
        label(img, f"FACT {n} OF 3", 330, t)
        a = ease((t - 0.2) / 0.4)
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        icon(ImageDraw.Draw(layer), kind, W // 2 - 90, 480, 180, GOLD + (int(255 * a),))
        img.alpha_composite(layer)
        y = text_block(img, title, SERIF(96, "Bold"), 740, WHITE, 0.3, t)
        text_block(img, body, SANS(54, "SemiBold"), y + 50, MUTED, 1.1, t)
    return scene


def s_enough(img, t):
    label(img, "FACT 3 OF 3", 300, t)
    text_block(img, "Would it be enough?", SERIF(96, "Bold"), 440, WHITE, 0.2, t)
    d = ImageDraw.Draw(img)
    bars = [("Death in service (4 × £35,000)", 140_000, GOLD, 0.6), ("Mortgage left to pay", 180_000, WHITE, 1.2)]
    for i, (name, val, col, start) in enumerate(bars):
        a = ease((t - start) / 0.9)
        if a <= 0:
            continue
        y = 730 + i * 230
        d.text((120, y), name, font=SANS(46, "SemiBold"), fill=MUTED)
        full = 840 * val / 180_000
        d.rounded_rectangle((120, y + 70, 120 + max(20, full * a), y + 150), radius=40, fill=col)
        f = SERIF(56, "Bold")
        d.text((140, y + 78), f"£{int(val * a):,}", font=f, fill=R.NAVY)
    text_block(img, "…before a single bill is paid.", SERIF(72, "Bold"), 1230, GOLD, 2.3, t)
    text_block(img, "*Illustrative example only. Cover levels vary by employer.", SANS(30, "Medium"), 1420, MUTED, 1.0, t, maxw=860)


def s_start(img, t):
    y = text_block(img, "Death in service is", SERIF(90), 640, WHITE, 0.0, t)
    y = text_block(img, "a great start.", SERIF(110, "Bold"), y, GOLD, 0.3, t)
    text_block(img, "But it’s rarely the whole picture.", SANS(58, "SemiBold"), y + 60, WHITE, 1.2, t)


END = make_end("Know what you’re really covered for.", "Coming soon", "Follow to be first to try it")
SCENES = [
    (0, 4.0, s_myth),
    (4.0, 8.6, fact(1, "It usually stops when you leave your job.", "New job, redundancy or going self-employed? The cover often goes with it.", "case")),
    (8.6, 13.0, fact(2, "It only pays out if you die.", "Nothing if illness or injury stops you working.", "pound")),
    (13.0, 18.4, s_enough),
    (18.4, 21.8, s_start),
    (21.8, 27.0, END),
]

if __name__ == "__main__":
    R.render(SCENES, "safe-sorry-myth-reel", cover_t=3.5)
