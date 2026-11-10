"""Two myth-buster reels made from the carousels ("young and healthy", "the state will look after us").
Run: python reel_myths2.py  (renders silent MP4s; music is mixed in afterwards with ffmpeg)."""
import scripts_make_reel as R
from reel_myth import fact, label
from scripts_make_reel import GOLD, MUTED, SANS, SERIF, WHITE, make_end, text_block

STATE_NOTE = "*2026/27 rates. Eligibility rules apply."


def myth(a, b):
    def scene(img, t):
        label(img, "COMMON MYTH", 380, t)
        y = text_block(img, a, SERIF(92, "Bold"), 560, WHITE, 0.3, t)
        text_block(img, b, SERIF(104, "Bold"), y + 30, GOLD, 1.1, t)
        text_block(img, "Let’s check that.", SANS(56, "SemiBold"), 1220, MUTED, 2.1, t)
    return scene


def noted(scene):
    def wrapped(img, t):
        scene(img, t)
        text_block(img, STATE_NOTE, SANS(30, "Medium"), 1480, MUTED, 1.0, t, maxw=860)
    return wrapped


def balance(a, b, c):
    def scene(img, t):
        y = text_block(img, a, SERIF(90), 640, WHITE, 0.0, t)
        y = text_block(img, b, SERIF(104, "Bold"), y, GOLD, 0.3, t)
        text_block(img, c, SANS(58, "SemiBold"), y + 60, WHITE, 1.2, t)
    return scene


REELS = {
    "safe-sorry-myth-young-reel": [
        (0, 4.0, myth("“I’m young and healthy…", "I don’t need cover.”")),
        (4.0, 8.6, fact(1, "Cover is usually cheapest when you’re young and healthy.",
                        "Prices are based on your age and health when you apply.", "pound")),
        (8.6, 13.0, fact(2, "Being young doesn’t protect your income.",
                         "Illness and injury can happen at any age, and the bills don’t pause.", "case")),
        (13.0, 17.6, fact(3, "If others rely on you, it matters now.",
                          "A partner, children, or a mortgage in your name all depend on your income.", "pound")),
        (17.6, 21.8, balance("Not everyone needs cover.", "But it’s worth knowing if you do.", "It takes 5 minutes to check.")),
        (21.8, 27.0, make_end("Know where you stand in 5 minutes.")),
    ],
    "safe-sorry-myth-state-reel": [
        (0, 4.0, myth("“If something happened,", "the state would look after us.”")),
        (4.0, 8.6, noted(fact(1, "Statutory Sick Pay is £123.25 a week.*",
                              "For up to 28 weeks. That’s about £534 a month. Self-employed people get none.", "case"))),
        (8.6, 13.0, noted(fact(2, "After that, ESA isn’t automatic.",
                               "New Style ESA is about £95.55 a week if you qualify, and for most people it stops after a year.*", "case"))),
        (13.0, 17.6, noted(fact(3, "Bereavement Support Payment is capped.",
                                "Up to £3,500 plus £350 a month for 18 months.* Then it stops.", "pound"))),
        (17.6, 21.8, balance("State support helps.", "But it’s rarely enough", "to keep a family’s plans on track.")),
        (21.8, 27.0, make_end("See what the state would really pay you.")),
    ],
}

if __name__ == "__main__":
    for name, scenes in REELS.items():
        R.render(scenes, name, cover_t=3.5)
        print("done", name)
