"""Extra reels (coming soon, award, 15s stories) and the 6-slide launch carousel. Run: python scripts_make_reel.py <name>"""
from PIL import Image, ImageDraw

import scripts_make_reel as R
from scripts_make_reel import GOLD, MUTED, NAVY, SANS, SERIF, SRC, W, WHITE, ease, make_end, place_phone, text_block

MARK = Image.open(SRC / "mark.jpg").convert("RGBA")


def circle_photo(img, size, cx, cy, a=1.0):
    ph = MARK.copy()
    s = min(ph.size)
    ph = ph.crop(((ph.width - s) // 2, 0, (ph.width + s) // 2, s)).resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=int(255 * a))
    ring = Image.new("RGBA", (size + 24, size + 24), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, size + 23, size + 23), fill=GOLD + (int(255 * a),))
    img.alpha_composite(ring, (cx - (size + 24) // 2, cy - (size + 24) // 2))
    img.paste(ph, (cx - size // 2, cy - size // 2), mask)


def medal(img, cx, cy, r, a=1.0):
    d = ImageDraw.Draw(img)
    al = int(255 * a)
    d.polygon([(cx - r * 0.55, cy + r * 0.6), (cx - r * 0.95, cy + r * 1.9), (cx - r * 0.35, cy + r * 1.55), (cx - r * 0.1, cy + r * 2.1),
               (cx + r * 0.1, cy + r * 0.8)], fill=(150, 118, 30, al))
    d.polygon([(cx + r * 0.55, cy + r * 0.6), (cx + r * 0.95, cy + r * 1.9), (cx + r * 0.35, cy + r * 1.55), (cx + r * 0.1, cy + r * 2.1),
               (cx - r * 0.1, cy + r * 0.8)], fill=(170, 135, 38, al))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD + (al,))
    d.ellipse((cx - r * 0.78, cy - r * 0.78, cx + r * 0.78, cy + r * 0.78), outline=WHITE + (al,), width=6)
    import math
    pts = [(cx + math.cos(math.pi / 2 + k * math.pi / 5) * (r * 0.5 if k % 2 == 0 else r * 0.22) * -1,
            cy - math.sin(math.pi / 2 + k * math.pi / 5) * (r * 0.5 if k % 2 == 0 else r * 0.22)) for k in range(10)]
    d.polygon(pts, fill=WHITE + (al,))


# ---------------- award reel ----------------
def a_award(img, t):
    medal(img, W // 2, 560, 150, ease(t / 0.5))
    y = text_block(img, "Protection Adviser", SERIF(96, "Bold"), 940, WHITE, 0.4, t)
    y = text_block(img, "of the Year 2026", SERIF(96, "Bold"), y, GOLD, 0.6, t)
    text_block(img, "Next Intelligence Awards", SANS(52, "SemiBold"), y + 40, MUTED, 1.0, t)


def a_mark(img, t):
    circle_photo(img, 420, W // 2, 640, ease(t / 0.5))
    y = text_block(img, "Mark Turner", SERIF(100, "Bold"), 920, WHITE, 0.3, t)
    y = text_block(img, "Secure for Life Wealth Management", SANS(48, "SemiBold"), y + 10, GOLD, 0.6, t)
    text_block(img, "Award-winning protection adviser", SANS(48, "SemiBold"), y + 30, MUTED, 1.0, t)


def a_why(img, t):
    y = text_block(img, "Years of helping families", SERIF(88), 600, WHITE, 0.0, t)
    y = text_block(img, "protect what matters most…", SERIF(88), y, WHITE, 0.3, t)
    text_block(img, "so I built a way to help even more of them.", SERIF(88, "Bold"), y + 60, GOLD, 1.1, t)


def a_app(img, t):
    y = text_block(img, "Safe > Sorry shows how long", SERIF(76, "Bold"), 230, WHITE, 0.0, t)
    text_block(img, "your family's money would last.", SERIF(76, "Bold"), y, GOLD, 0.2, t)
    place_phone(img, "r2", t, 0.3, y=520)


award_end = make_end("Better safe than sorry.", "Coming soon", "Follow to be first to try it")

# ---------------- 15s stories ----------------
story_soon = make_end("Know your number.", "Link in bio", "Coming soon · free")
story_live = make_end("Know your number.", "Link in bio", "Free on iPhone & Android")

VARIANTS = {
    "safe-sorry-coming-soon": (R.SCENES[:-1] + [(22.0, 27.0, make_end("Coming soon.", "Follow us to be first to try it", "Better safe than sorry."))],
                               "safe-sorry-coming-soon"),
    "safe-sorry-award-reel": ([(0, 3.8, a_award), (3.8, 7.8, a_mark), (7.8, 12.0, a_why), (12.0, 16.4, a_app), (16.4, 21.4, award_end)],
                              "safe-sorry-award-reel", 2.6),
    "safe-sorry-story-coming-soon": ([(0, 3.4, R.s_hook), (3.4, 7.2, R.s_question), (7.2, 11.0, R.s_find), (11.0, 15.0, story_soon)],
                                     "safe-sorry-story-coming-soon"),
    "safe-sorry-story-launch": ([(0, 3.4, R.s_hook), (3.4, 7.2, R.s_question), (7.2, 11.0, R.s_find), (11.0, 15.0, story_live)],
                                "safe-sorry-story-launch"),
}


# ---------------- carousel (1080x1350) ----------------
CH = 1350
T = 99  # fully revealed


def footer(img, n):
    d = ImageDraw.Draw(img)
    d.rectangle((0, CH - 100, W, CH), fill=NAVY)
    f = SANS(26, "SemiBold")
    d.text((60, CH - 70), "safe > sorry · not regulated advice", font=f, fill=MUTED)
    if n < 6:
        lbl = f"{n}/6  swipe >"
        d.text((W - 60 - d.textlength(lbl, font=f), CH - 70), lbl, font=f, fill=GOLD)


def carousel():
    slides = []
    # 1 hook
    img = R.bg(CH).copy()
    y = text_block(img, "You know your phone battery", SERIF(80), 200, WHITE, 0, T)
    text_block(img, "to the exact %.", SERIF(110, "Bold"), y + 10, GOLD, 0, T)
    R.battery(img, W // 2, 820, 0.87, "87%")
    text_block(img, "But there's a number most families never check…", SANS(48, "SemiBold"), 1050, MUTED, 0, T)
    slides.append(img)
    # 2 question
    img = R.bg(CH).copy()
    y = text_block(img, "If your income stopped tomorrow,", SERIF(78), 220, WHITE, 0, T)
    text_block(img, "how many months would your family be okay?", SERIF(92, "Bold"), y + 20, GOLD, 0, T)
    R.battery(img, W // 2, 900, 0.18, "")
    text_block(img, "? months", SERIF(110, "Bold"), 1040, WHITE, 0, T)
    slides.append(img)
    # 3 app intro
    img = R.bg(CH).copy()
    y = text_block(img, "Safe > Sorry finds out", SERIF(80, "Bold"), 130, WHITE, 0, T)
    y = text_block(img, "in 5 minutes", SERIF(80, "Bold"), y, GOLD, 0, T)
    text_block(img, "12 simple questions. Free.", SANS(46, "SemiBold"), y + 10, MUTED, 0, T)
    p = R.phone(SRC / "home.jpg", width=460)
    img.alpha_composite(p, ((W - p.width) // 2, 520))
    slides.append(img)
    # 4 timeline
    img = R.bg(CH).copy()
    y = text_block(img, "See exactly how long", SERIF(80, "Bold"), 130, WHITE, 0, T)
    text_block(img, "the money would last", SERIF(80, "Bold"), y, GOLD, 0, T)
    p = R.phone(SRC / "r2.jpg", width=460)
    img.alpha_composite(p, ((W - p.width) // 2, 400))
    slides.append(img)
    # 5 benefits
    img = R.bg(CH).copy()
    text_block(img, "Built for UK families", SERIF(86, "Bold"), 200, WHITE, 0, T)
    d = ImageDraw.Draw(img)
    for n, it in enumerate(["UK state benefits included", "A personal family letter", "Your existing cover counted",
                            "No sales calls unless you ask"]):
        yy = 440 + n * 160
        d.ellipse((120, yy + 6, 176, yy + 62), fill=GOLD)
        d.line((134, yy + 36, 146, yy + 48, 164, yy + 22), fill=NAVY, width=7, joint="curve")
        d.text((205, yy), it, font=SANS(52, "SemiBold"), fill=WHITE)
    slides.append(img)
    # 6 end
    img = R.bg(CH).copy()
    logo = R.LOGO.resize((440, int(R.LOGO.height * 440 / R.LOGO.width)))
    img.alpha_composite(logo, ((W - logo.width) // 2, 110))
    y = 110 + logo.height + 50
    y = text_block(img, "Coming soon.", SERIF(90, "Bold"), y, WHITE, 0, T)
    y = text_block(img, "Follow to be first to try it", SANS(54), y + 20, GOLD, 0, T)
    y = text_block(img, R.NOT_ADVICE_LINE, SANS(28, "Medium"), y + 60, MUTED, 0, T, maxw=880)
    text_block(img, R.AR_LINE, SANS(26, "Medium"), y + 16, MUTED, 0, T, maxw=880)
    slides.append(img)
    for n, img in enumerate(slides, 1):
        footer(img, n)
        img.convert("RGB").save(R.OUT / f"safe-sorry-carousel-{n}.jpg", quality=94)
    import zipfile
    with zipfile.ZipFile(R.OUT / "safe-sorry-carousel.zip", "w") as z:
        for n in range(1, 7):
            z.write(R.OUT / f"safe-sorry-carousel-{n}.jpg", f"safe-sorry-carousel-{n}.jpg")
    print("carousel done")


if __name__ == "__main__":
    carousel()
