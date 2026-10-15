"""Renders the Safe > Sorry launch reel (1080x1920, 30fps, silent – add music inside Instagram)."""
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
NAVY, NAVY2, GOLD, WHITE, MUTED = (34, 51, 66), (24, 37, 49), (191, 155, 48), (255, 255, 255), (195, 201, 210)
ROOT = Path(__file__).parent
SRC = ROOT / "static" / "reels" / "src"
OUT = ROOT / "static" / "reels"
FONTS = Path("/app/frontend/assets/fonts")


def font(name: str, size: int, weight: str = "Bold"):
    f = ImageFont.truetype(str(FONTS / name), size)
    f.set_variation_by_name(weight)
    return f


SERIF = lambda s, w="SemiBold": font("Fraunces.ttf", s, w)  # noqa: E731
SANS = lambda s, w="Bold": font("Quicksand.ttf", s, w)  # noqa: E731


def ease(t):  # easeOutCubic, clamped
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def text_block(img, text, f, y, color, t_in, t, maxw=900, spacing=1.18, align="center"):
    """Fade + slide-up text block. Returns bottom y."""
    a = ease((t - t_in) / 0.45)
    if a <= 0:
        return y
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = wrap(d, text, f, maxw)
    lh = int(f.size * spacing)
    off = int((1 - a) * 40)
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=f)
        x = (W - w) / 2 if align == "center" else (W - maxw) / 2
        d.text((x, y + i * lh + off), ln, font=f, fill=color + (int(255 * a),))
    img.alpha_composite(layer)
    return y + len(lines) * lh


def bg():
    img = Image.new("RGBA", (W, H), NAVY + (255,))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((-300, -200, 900, 900), fill=GOLD + (38,))
    return Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(160)))


BG = bg()


def battery(img, cx, cy, level, label, label_color=NAVY, scale=1.0):
    d = ImageDraw.Draw(img)
    w, h = int(520 * scale), int(250 * scale)
    x0, y0 = cx - w // 2, cy - h // 2
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=int(46 * scale), outline=WHITE, width=int(12 * scale))
    d.rounded_rectangle((x0 + w + 8, cy - 40 * scale, x0 + w + 36 * scale, cy + 40 * scale), radius=12, fill=WHITE)
    pad = int(26 * scale)
    fill_w = int((w - 2 * pad) * max(0.0, min(1.0, level)))
    col = GOLD if level > 0.25 else (196, 82, 66)
    if fill_w > 6:
        d.rounded_rectangle((x0 + pad, y0 + pad, x0 + pad + fill_w, y0 + h - pad), radius=int(24 * scale), fill=col)
    f = SANS(int(96 * scale))
    tw = d.textlength(label, font=f)
    d.text((cx - tw / 2, cy - f.size * 0.62), label, font=f, fill=label_color if fill_w > tw else WHITE)


def phone(path, width=600):
    shot = Image.open(path).convert("RGBA")
    shot = shot.resize((width, int(shot.height * width / shot.width)), Image.LANCZOS)
    bez = 22
    frame = Image.new("RGBA", (width + 2 * bez, shot.height + 2 * bez), (0, 0, 0, 0))
    d = ImageDraw.Draw(frame)
    d.rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), radius=78, fill=(12, 18, 24, 255))
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, shot.width - 1, shot.height - 1), radius=58, fill=255)
    frame.paste(shot, (bez, bez), mask)
    shadow = Image.new("RGBA", (frame.width + 120, frame.height + 120), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((60, 80, frame.width + 60, frame.height + 60), radius=80, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    shadow.alpha_composite(frame, (60, 60))
    return shadow


PHONES = {k: phone(SRC / f"{k}.jpg") for k in ("home", "r1", "r2")}
LOGO = Image.open(ROOT / "static" / "logos" / "logo_dark_transparent.png").convert("RGBA")
LOGO = LOGO.resize((520, int(LOGO.height * 520 / LOGO.width)), Image.LANCZOS)


def place_phone(img, key, t, t_in, y=560):
    a = ease((t - t_in) / 0.6)
    if a <= 0:
        return
    p = PHONES[key].copy()
    if a < 1:
        p.putalpha(p.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(p, ((W - p.width) // 2, int(y + (1 - a) * 260)))


# ---------- scenes: (start, end, draw(img, local_t)) ----------
def s_hook(img, t):
    y = text_block(img, "You know your phone battery", SERIF(84), 300, WHITE, 0.0, t)
    text_block(img, "to the exact %.", SERIF(110, "Bold"), max(y, 420) + 10, GOLD, 0.5, t)
    level = 0.87 * ease((t - 0.3) / 1.2)
    battery(img, W // 2, 900, level, f"{int(level * 100)}%")
    text_block(img, "Quick question…", SANS(54, "SemiBold"), 1180, MUTED, 1.6, t)


def s_question(img, t):
    y = text_block(img, "If your income stopped tomorrow,", SERIF(80), 280, WHITE, 0.0, t)
    text_block(img, "how long would your family’s money last?", SERIF(92, "Bold"), y + 20, GOLD, 0.5, t)
    level = 0.87 - 0.72 * ease((t - 0.8) / 2.0)
    battery(img, W // 2, 1000, level, "" if t > 1.2 else f"{int(level * 100)}%", scale=0.95)
    text_block(img, "? months", SERIF(120, "Bold"), 1200, WHITE, 1.3, t)


def s_nobody(img, t):
    text_block(img, "Most families", SERIF(100), 620, WHITE, 0.0, t)
    text_block(img, "have no idea.", SERIF(120, "Bold"), 760, GOLD, 0.35, t)
    text_block(img, "Not because they don’t care.", SANS(56, "SemiBold"), 1010, MUTED, 1.0, t)
    text_block(img, "Because nobody ever showed them.", SANS(56, "SemiBold"), 1090, MUTED, 1.5, t)


def s_find(img, t):
    text_block(img, "Find out in 5 minutes", SERIF(84, "Bold"), 250, WHITE, 0.0, t)
    text_block(img, "12 simple questions. Free.", SANS(52, "SemiBold"), 370, GOLD, 0.3, t)
    place_phone(img, "home", t, 0.2, y=500)


def s_report(img, t):
    text_block(img, "See exactly how long", SERIF(80, "Bold"), 250, WHITE, 0.0, t)
    text_block(img, "the money would last", SERIF(80, "Bold"), 345, WHITE, 0.1, t)
    place_phone(img, "r2", t, 0.2, y=500)


def s_benefits(img, t):
    text_block(img, "Built for UK families", SERIF(86, "Bold"), 360, WHITE, 0.0, t)
    items = ["UK state benefits included", "A personal family letter", "Your existing cover counted", "No sales calls unless you ask"]
    for n, it in enumerate(items):
        a = ease((t - 0.4 - n * 0.35) / 0.4)
        if a <= 0:
            continue
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        y = 620 + n * 150 + int((1 - a) * 30)
        d.ellipse((120, y + 6, 176, y + 62), fill=GOLD + (int(255 * a),))
        d.line((134, y + 36, 146, y + 48, 164, y + 22), fill=NAVY + (int(255 * a),), width=7, joint="curve")
        d.text((205, y), it, font=SANS(52, "SemiBold"), fill=WHITE + (int(255 * a),))
        img.alpha_composite(layer)


def s_end(img, t):
    a = ease(t / 0.6)
    logo = LOGO.copy()
    logo.putalpha(logo.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(logo, ((W - logo.width) // 2, 260 + int((1 - a) * 40)))
    y = 260 + logo.height + 60
    y = text_block(img, "Know your number.", SERIF(88, "Bold"), y, WHITE, 0.5, t)
    text_block(img, "Download Safe > Sorry · free", SANS(56), y + 40, GOLD, 0.9, t)
    text_block(img, "Estimates only. This is not regulated advice. Figures are illustrative, based on 2026/27 rates.",
               SANS(30, "Medium"), 1420, MUTED, 1.3, t, maxw=860)
    text_block(img, "Secure for Life Wealth Management Ltd is an Appointed Representative of Rosemount Financial "
               "Solutions (IFA) Limited, which is authorised and regulated by the Financial Conduct Authority.",
               SANS(28, "Medium"), 1530, MUTED, 1.3, t, maxw=860)


SCENES = [(0, 3.4, s_hook), (3.4, 7.4, s_question), (7.4, 10.6, s_nobody), (10.6, 14.4, s_find),
          (14.4, 18.2, s_report), (18.2, 22.0, s_benefits), (22.0, 27.0, s_end)]
DUR = SCENES[-1][1]


def frame(t):
    img = BG.copy()
    for start, end, fn in SCENES:
        if start <= t < end or (fn is s_end and t >= start):
            local = t - start
            fn(img, local)
            fade_out = 0.0 if fn is s_end else ease((t - (end - 0.3)) / 0.3)
            if fade_out > 0:
                img = Image.blend(img, BG, fade_out)
            break
    return img.convert("RGB")


def main():
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "safe-sorry-launch-reel.mp4"
    p = subprocess.Popen([ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-shortest",
                          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-crf", "18", "-preset", "medium",
                          "-c:a", "aac", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = int(DUR * FPS)
    for i in range(n):
        f = frame(i / FPS)
        p.stdin.write(f.tobytes())
        if i == int(1.9 * FPS):
            f.save(OUT / "safe-sorry-launch-reel-cover.jpg", quality=92)
    p.stdin.close()
    p.wait()
    for name, ts in [("check_hook", 2.2), ("check_q", 6.5), ("check_find", 13.5), ("check_report", 17.5), ("check_ben", 21.5), ("check_end", 26.5)]:
        frame(ts).resize((360, 640)).save(f"/tmp/{name}.jpg")
    print("done", out, out.stat().st_size)


if __name__ == "__main__":
    main()
