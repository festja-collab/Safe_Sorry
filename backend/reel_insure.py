"""'What do we insure?' reel – no battery theme, the app only appears at the end. Run: python reel_insure.py"""
import math

from PIL import Image, ImageDraw

import scripts_make_reel as R
from scripts_make_reel import GOLD, MUTED, NAVY, SANS, SERIF, W, WHITE, ease, make_end, text_block

RED = (196, 82, 66)


def icon(d, kind, x, y, s, col):
    """Simple line icons drawn in a s×s box at (x, y)."""
    lw = max(4, s // 14)
    if kind == "phone":
        d.rounded_rectangle((x + s * .28, y + s * .05, x + s * .72, y + s * .95), radius=s * .1, outline=col, width=lw)
        d.line((x + s * .44, y + s * .84, x + s * .56, y + s * .84), fill=col, width=lw)
    elif kind == "car":
        d.rounded_rectangle((x + s * .05, y + s * .42, x + s * .95, y + s * .74), radius=s * .1, outline=col, width=lw)
        d.line((x + s * .2, y + s * .42, x + s * .32, y + s * .2, x + s * .68, y + s * .2, x + s * .8, y + s * .42), fill=col, width=lw)
        for cx in (.27, .73):
            d.ellipse((x + s * (cx - .1), y + s * .66, x + s * (cx + .1), y + s * .86), fill=NAVY, outline=col, width=lw)
    elif kind == "case":
        d.rounded_rectangle((x + s * .1, y + s * .3, x + s * .9, y + s * .88), radius=s * .1, outline=col, width=lw)
        d.rounded_rectangle((x + s * .36, y + s * .12, x + s * .64, y + s * .3), radius=s * .05, outline=col, width=lw)
        d.line((x + s * .1, y + s * .55, x + s * .9, y + s * .55), fill=col, width=lw)
    elif kind == "pound":
        d.ellipse((x + s * .05, y + s * .05, x + s * .95, y + s * .95), outline=col, width=lw)
        f = SERIF(int(s * .6), "Bold")
        tw = d.textlength("£", font=f)
        d.text((x + s / 2 - tw / 2, y + s * .13), "£", font=f, fill=col)


def tick(d, x, y, s, a):
    d.ellipse((x, y, x + s, y + s), fill=GOLD + (int(255 * a),))
    d.line((x + s * .25, y + s * .52, x + s * .43, y + s * .7, x + s * .76, y + s * .32), fill=NAVY + (int(255 * a),), width=max(5, s // 9), joint="curve")


ROWS = [("phone", "My phone"), ("car", "My car"), ("case", "My holiday")]


def checklist(img, t, show_income=False, income_t=0.0):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for n, (k, label) in enumerate(ROWS + ([("pound", "My income")] if show_income else [])):
        start = income_t if n == 3 else 0.5 + n * 0.55
        a = ease((t - start) / 0.4)
        if a <= 0:
            continue
        y = 640 + n * 190 + int((1 - a) * 30)
        col = (WHITE if n < 3 else GOLD) + (int(255 * a),)
        icon(d, k, 150, y, 110, col)
        d.text((300, y + 22), label, font=SANS(64, "Bold"), fill=col)
        if n < 3:
            tick(d, 830, y + 15, 84, ease((t - start - 0.25) / 0.3))
        else:
            pulse = 1 + 0.08 * math.sin((t - income_t) * 6)
            f = SERIF(int(120 * pulse), "Bold")
            d.text((842, y - 18), "?", font=f, fill=GOLD + (int(255 * a),))
    img.alpha_composite(layer)


def s_list(img, t):
    text_block(img, "Things we insure", SERIF(92, "Bold"), 300, WHITE, 0.0, t)
    text_block(img, "without thinking twice:", SERIF(80), 410, MUTED, 0.2, t)
    checklist(img, t)


def s_income(img, t):
    text_block(img, "And the thing that", SERIF(84), 280, WHITE, 0.0, t)
    text_block(img, "pays for all of it?", SERIF(96, "Bold"), 390, GOLD, 0.15, t)
    checklist(img, 99, show_income=True, income_t=99 - t + 0.4)  # earlier rows already shown


def s_value(img, t):
    text_block(img, "What you could earn", SERIF(84), 380, WHITE, 0.0, t)
    text_block(img, "over your working life:", SERIF(84), 480, WHITE, 0.1, t)
    v = int(1_050_000 * ease((t - 0.5) / 2.0))
    text_block(img, f"£{v:,}", SERIF(150, "Bold"), 700, GOLD, 0.4, t)
    text_block(img, "£35,000 a year × 30 years*", SANS(56, "SemiBold"), 920, WHITE, 1.4, t)
    text_block(img, "That's the biggest thing most families own.", SANS(50, "SemiBold"), 1060, MUTED, 2.2, t)
    text_block(img, "*Illustrative example only", SANS(32, "Medium"), 1400, MUTED, 1.4, t)


def s_ifit(img, t):
    y = text_block(img, "If illness, injury or the worst", SERIF(84), 560, WHITE, 0.0, t)
    y = text_block(img, "stopped that income…", SERIF(84), y, WHITE, 0.2, t)
    text_block(img, "would your family's plans still happen?", SERIF(92, "Bold"), y + 70, GOLD, 1.2, t)


def s_check(img, t):
    text_block(img, "Most people", SERIF(104), 640, WHITE, 0.0, t)
    text_block(img, "never check.", SERIF(124, "Bold"), 780, GOLD, 0.3, t)
    text_block(img, "It takes 5 minutes to find out.", SANS(58, "SemiBold"), 1040, WHITE, 1.2, t)


END = make_end("Check your protection in 5 minutes.")
SCENES = [(0, 4.2, s_list), (4.2, 7.6, s_income), (7.6, 12.2, s_value), (12.2, 16.2, s_ifit), (16.2, 19.6, s_check), (19.6, 25.0, END)]

if __name__ == "__main__":
    R.render(SCENES, "safe-sorry-insure-reel", cover_t=6.0)
    for n, ts in enumerate([3.8, 6.5, 11.5, 15.8, 19.0, 24.8]):
        R.frame(ts, SCENES).resize((300, 533)).save(f"/tmp/ins{n}.jpg")
