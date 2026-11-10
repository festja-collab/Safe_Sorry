"""Pinned "About Safe > Sorry" Instagram post: 3 slides (1080x1350) + zip, with the full regulatory statement.
Run: python about_post.py"""
import zipfile

from PIL import ImageDraw

import scripts_make_reel as R
from reel_variants import CH
from scripts_make_reel import GOLD, MUTED, NAVY, SANS, SERIF, W, WHITE, text_block

T = 99


def footer(img, n, total=3):
    d = ImageDraw.Draw(img)
    d.rectangle((0, CH - 100, W, CH), fill=NAVY)
    f = SANS(26, "SemiBold")
    d.text((60, CH - 70), "safe > sorry · not regulated advice", font=f, fill=MUTED)
    if n < total:
        lbl = f"{n}/{total}  swipe >"
        d.text((W - 60 - d.textlength(lbl, font=f), CH - 70), lbl, font=f, fill=GOLD)


def slide_about():
    img = R.bg(CH).copy()
    logo = R.LOGO.resize((460, int(R.LOGO.height * 460 / R.LOGO.width)))
    img.alpha_composite(logo, ((W - logo.width) // 2, 120))
    y = 120 + logo.height + 50
    y = text_block(img, "About us", SERIF(96, "Bold"), y, WHITE, 0, T)
    y = text_block(img, "A free, gentle 5-minute check that shows what your family would face if the worst happened.",
                   SANS(48, "SemiBold"), y + 20, GOLD, 0, T, maxw=900)
    text_block(img, "Built by Mark Turner, Protection Adviser of the Year 2026.", SANS(42, "Medium"), y + 40, MUTED, 0, T, maxw=900)
    return img


def slide_how():
    img = R.bg(CH).copy()
    text_block(img, "How it works", SERIF(92, "Bold"), 170, WHITE, 0, T)
    d = ImageDraw.Draw(img)
    steps = ["Answer a few questions about your family", "See your safety net in pounds and months",
             "Read your personal family letter", "Talk it through with an adviser, only if you want to"]
    for n, s in enumerate(steps):
        yy = 400 + n * 190
        d.ellipse((100, yy, 176, yy + 76), fill=GOLD)
        num = str(n + 1)
        f = SERIF(52, "Bold")
        d.text((138 - d.textlength(num, font=f) / 2, yy + 8), num, font=f, fill=NAVY)
        lines, line = [], ""
        fs = SANS(46, "SemiBold")
        for w in s.split():
            if d.textlength((line + " " + w).strip(), font=fs) > 760:
                lines.append(line)
                line = w
            else:
                line = (line + " " + w).strip()
        lines.append(line)
        for k, ln in enumerate(lines):
            d.text((210, yy + 10 + k * 58), ln, font=fs, fill=WHITE)
    text_block(img, "Free · nothing to download · link in bio", SANS(44), 1170, GOLD, 0, T)
    return img


def slide_legal():
    img = R.bg(CH).copy()
    y = text_block(img, "Important information", SERIF(84, "Bold"), 180, WHITE, 0, T)
    y = text_block(img, R.AR_LINE, SANS(44, "SemiBold"), y + 50, WHITE, 0, T, maxw=920)
    y = text_block(img, "Safe > Sorry gives estimates only. It is not regulated advice. Figures are illustrative, "
                   "based on 2026/27 rates. Any advice is given only in a separate conversation with an adviser.",
                   SANS(38, "Medium"), y + 50, MUTED, 0, T, maxw=920)
    text_block(img, "Your data is handled by Secure for Life Wealth Management Ltd. See the privacy notice at the link in bio.",
               SANS(36, "Medium"), y + 40, MUTED, 0, T, maxw=920)
    return img


if __name__ == "__main__":
    slides = [slide_about(), slide_how(), slide_legal()]
    with zipfile.ZipFile(R.OUT / "safe-sorry-about.zip", "w") as z:
        for n, img in enumerate(slides, 1):
            footer(img, n)
            fn = f"safe-sorry-about-{n}.jpg"
            img.convert("RGB").save(R.OUT / fn, quality=94)
            z.write(R.OUT / fn, fn)
    print("about post done")
