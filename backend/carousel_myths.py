"""Two myth-buster carousels (1080x1350, 6 slides each). Run: python carousel_myths.py"""
import zipfile

from PIL import Image, ImageDraw

import scripts_make_reel as R
from reel_insure import icon
from reel_myth import label
from reel_variants import CH, footer
from scripts_make_reel import GOLD, MUTED, SANS, SERIF, W, WHITE, text_block

T = 99


def myth_slide(quote_a, quote_b):
    img = R.bg(CH).copy()
    label(img, "COMMON MYTH", 260, T)
    y = text_block(img, quote_a, SERIF(92, "Bold"), 440, WHITE, 0, T)
    text_block(img, quote_b, SERIF(104, "Bold"), y + 20, GOLD, 0, T)
    text_block(img, "Swipe to check the facts", SANS(50, "SemiBold"), 1080, MUTED, 0, T)
    return img


def fact_slide(n, kind, title, body):
    img = R.bg(CH).copy()
    label(img, f"FACT {n} OF 3", 200, T)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    icon(ImageDraw.Draw(layer), kind, W // 2 - 85, 340, 170, GOLD + (255,))
    img.alpha_composite(layer)
    y = text_block(img, title, SERIF(84, "Bold"), 580, WHITE, 0, T)
    text_block(img, body, SANS(50, "SemiBold"), y + 40, MUTED, 0, T)
    return img


def balance_slide(a, b, c):
    img = R.bg(CH).copy()
    y = text_block(img, a, SERIF(86), 400, WHITE, 0, T)
    y = text_block(img, b, SERIF(100, "Bold"), y, GOLD, 0, T)
    text_block(img, c, SANS(54, "SemiBold"), y + 50, WHITE, 0, T)
    return img


def end_slide(headline, extra=""):
    img = R.bg(CH).copy()
    logo = R.LOGO.resize((420, int(R.LOGO.height * 420 / R.LOGO.width)))
    img.alpha_composite(logo, ((W - logo.width) // 2, 100))
    y = 100 + logo.height + 40
    y = text_block(img, headline, SERIF(80, "Bold"), y, WHITE, 0, T)
    y = text_block(img, "Coming soon · follow to try it first", SANS(48), y + 20, GOLD, 0, T)
    y = text_block(img, (extra + " " if extra else "") + R.NOT_ADVICE_LINE, SANS(28, "Medium"), y + 50, MUTED, 0, T, maxw=880)
    text_block(img, R.AR_LINE, SANS(26, "Medium"), y + 14, MUTED, 0, T, maxw=880)
    return img


CAROUSELS = {
    "safe-sorry-myth-young": [
        myth_slide("“I’m young and healthy…", "I don’t need cover.”"),
        fact_slide(1, "pound", "Cover is usually cheapest when you’re young and healthy.",
                   "Prices are based on your age and health when you apply."),
        fact_slide(2, "case", "Being young doesn’t protect your income.",
                   "Illness and injury can happen at any age, and the bills don’t pause."),
        fact_slide(3, "pound", "If others rely on you, it matters now.",
                   "A partner, children, or a mortgage in your name all depend on your income."),
        balance_slide("Not everyone needs cover.", "But it’s worth knowing if you do.", "It takes 5 minutes to check."),
        end_slide("Know where you stand in 5 minutes."),
    ],
    "safe-sorry-myth-state": [
        myth_slide("“If something happened,", "the state would look after us.”"),
        fact_slide(1, "case", "Statutory Sick Pay is £123.25 a week.*",
                   "For up to 28 weeks. That’s about £534 a month. Self-employed people get none."),
        fact_slide(2, "case", "After that, ESA isn’t automatic.",
                   "New Style ESA is about £95.55 a week if you qualify, and for most people it stops after a year.*"),
        fact_slide(3, "pound", "Bereavement Support Payment is capped.",
                   "Up to £3,500 plus £350 a month for 18 months.* Then it stops."),
        balance_slide("State support helps.", "But it’s rarely enough", "to keep a family’s plans on track."),
        end_slide("See what the state would really pay you.", "*2026/27 rates. Eligibility rules apply."),
    ],
}

if __name__ == "__main__":
    for name, slides in CAROUSELS.items():
        with zipfile.ZipFile(R.OUT / f"{name}.zip", "w") as z:
            for n, img in enumerate(slides, 1):
                footer(img, n)
                fn = f"{name}-{n}.jpg"
                img.convert("RGB").save(R.OUT / fn, quality=94)
                z.write(R.OUT / fn, fn)
        print("done", name)
