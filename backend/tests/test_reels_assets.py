"""Iteration 16 - Verifies new reel assets (coming soon, award, 15s stories, 6-slide carousel).

Validates against the public URL:
  * Each MP4 served via /api/reels/file/<name> returns 200 (no Range) and 206 (Range).
  * ffmpeg confirms 1080x1920, H.264 yuv420p, 30fps, AAC audio, correct duration.
  * Carousel JPGs are 1080x1350. ZIP contains all six.
  * /api/reels HTML lists five video cards + carousel card + "Download all 6 slides (zip)".
  * ?download=1 sets Content-Disposition: attachment.
"""
import io
import os
import subprocess
import zipfile
from pathlib import Path

import imageio_ffmpeg
import pytest
import requests
from PIL import Image

BASE_URL = os.environ["EXPO_PUBLIC_BACKEND_URL"].rstrip("/")
REELS = f"{BASE_URL}/api/reels"
FILE = f"{BASE_URL}/api/reels/file"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VIDEOS = {
    "safe-sorry-launch-reel.mp4": 27.0,
    "safe-sorry-coming-soon.mp4": 27.0,
    "safe-sorry-award-reel.mp4": 21.4,
    "safe-sorry-story-coming-soon.mp4": 15.0,
    "safe-sorry-story-launch.mp4": 15.0,
}

CAROUSEL_JPGS = [f"safe-sorry-carousel-{i}.jpg" for i in range(1, 7)]

TMP = Path("/tmp/reel_assets")
TMP.mkdir(exist_ok=True)


def _probe(path: Path) -> str:
    """Return concatenated ffmpeg -i stderr (format/stream info)."""
    return subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr


def _download(url: str, dest: Path):
    r = requests.get(url, timeout=60)
    assert r.status_code == 200, f"{url} → {r.status_code}"
    dest.write_bytes(r.content)
    return r


# ---------- Video reachability + metadata ----------
class TestVideos:
    @pytest.mark.parametrize("name,dur", list(VIDEOS.items()))
    def test_200_and_metadata(self, name, dur):
        local = TMP / name
        r = _download(f"{FILE}/{name}", local)
        assert r.headers["content-type"] == "video/mp4"
        assert r.headers.get("accept-ranges") == "bytes"
        info = _probe(local)
        assert "1080x1920" in info, info
        assert "h264" in info.lower()
        assert "yuv420p" in info
        assert "30 fps" in info
        assert "Audio: aac" in info
        # Duration string "HH:MM:SS.ss"
        want = f"Duration: 00:00:{int(dur):02d}.{int(round((dur - int(dur)) * 100)):02d}"
        assert want in info, f"expected {want} in\n{info}"

    @pytest.mark.parametrize("name", list(VIDEOS))
    def test_range_206(self, name):
        r = requests.get(f"{FILE}/{name}", headers={"Range": "bytes=0-1023"}, timeout=30)
        assert r.status_code == 206
        assert r.headers["Content-Range"].startswith("bytes 0-1023/")
        assert len(r.content) == 1024

    @pytest.mark.parametrize("name", list(VIDEOS))
    def test_download_attachment(self, name):
        r = requests.get(f"{FILE}/{name}?download=1", timeout=30)
        assert r.status_code == 200
        cd = r.headers.get("Content-Disposition", "")
        assert "attachment" in cd and name in cd


# ---------- Last-frame + mid-scene visual checks ----------
def _frame_at(video: Path, t: float, out: Path):
    subprocess.run(
        [FFMPEG, "-y", "-ss", f"{t}", "-i", str(video), "-frames:v", "1", "-q:v", "2", str(out)],
        check=True, capture_output=True,
    )
    return Image.open(out)


# Required text per iteration brief; we can't guarantee OCR works, so we rely on known pixel-level
# construction + separately verify text via a tiny OCR fallback (pytesseract if available).
try:
    import shutil

    import pytesseract  # type: ignore
    HAS_OCR = shutil.which("tesseract") is not None

    def _ocr(img: Image.Image) -> str:
        return pytesseract.image_to_string(img)
except Exception:
    HAS_OCR = False


END_EXPECTATIONS = {
    # last frame (just before end) → should contain these snippets
    "safe-sorry-coming-soon.mp4": ["Start your free check", "not regulated advice", "trading style"],
    "safe-sorry-award-reel.mp4": ["Start your free check", "not regulated advice", "trading style"],
    "safe-sorry-story-coming-soon.mp4": ["Link in bio", "not regulated advice", "Appointed Representative"],
    "safe-sorry-story-launch.mp4": ["Link in bio", "not regulated advice", "Appointed Representative"],
}


class TestFrames:
    @pytest.mark.skipif(not HAS_OCR, reason="pytesseract not installed")
    @pytest.mark.parametrize("name,snippets", list(END_EXPECTATIONS.items()))
    def test_last_frame_text(self, name, snippets):
        local = TMP / name
        if not local.exists():
            _download(f"{FILE}/{name}", local)
        dur = VIDEOS[name]
        img = _frame_at(local, dur - 0.3, TMP / f"{name}.end.jpg")
        text = _ocr(img).lower()
        for s in snippets:
            assert s.lower() in text, f"'{s}' missing from last frame of {name}; got:\n{text!r}"

    @pytest.mark.skipif(not HAS_OCR, reason="pytesseract not installed")
    def test_award_reel_award_scene(self):
        name = "safe-sorry-award-reel.mp4"
        local = TMP / name
        if not local.exists():
            _download(f"{FILE}/{name}", local)
        text = _ocr(_frame_at(local, 3.0, TMP / "award_3s.jpg")).lower()
        assert "protection adviser" in text
        assert "2026" in text
        assert "next intelligence" in text

    @pytest.mark.skipif(not HAS_OCR, reason="pytesseract not installed")
    def test_award_reel_mark_scene(self):
        name = "safe-sorry-award-reel.mp4"
        local = TMP / name
        if not local.exists():
            _download(f"{FILE}/{name}", local)
        text = _ocr(_frame_at(local, 7.0, TMP / "award_7s.jpg")).lower()
        assert "mark turner" in text

    @pytest.mark.parametrize("name", list(VIDEOS))
    def test_no_edge_text_clipping(self, name):
        """Check mid-scene frame: left/right 40px columns contain no bright white pixels
        (text uses WHITE/GOLD). If they do, text is likely cut off at the edge."""
        local = TMP / name
        if not local.exists():
            _download(f"{FILE}/{name}", local)
        dur = VIDEOS[name]
        for t in (dur * 0.25, dur * 0.5, dur * 0.75):
            img = _frame_at(local, t, TMP / f"{name}.{t:.1f}.jpg").convert("L")
            left = img.crop((0, 100, 40, img.height - 100))
            right = img.crop((img.width - 40, 100, img.width, img.height - 100))
            # Threshold: >220 means near-white (text). Allow very few stray pixels (<50).
            left_bright = sum(1 for p in left.getdata() if p > 220)
            right_bright = sum(1 for p in right.getdata() if p > 220)
            assert left_bright < 50, f"{name} @ {t:.1f}s: {left_bright} bright px in LEFT edge (text clipped?)"
            assert right_bright < 50, f"{name} @ {t:.1f}s: {right_bright} bright px in RIGHT edge (text clipped?)"


# ---------- Carousel ----------
class TestCarousel:
    @pytest.mark.parametrize("name", CAROUSEL_JPGS)
    def test_slide_1080x1350(self, name):
        r = requests.get(f"{FILE}/{name}", timeout=30)
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/jpeg"
        img = Image.open(io.BytesIO(r.content))
        assert img.size == (1080, 1350), f"{name} is {img.size}"

    def test_zip_contains_all_six(self):
        r = requests.get(f"{FILE}/safe-sorry-carousel.zip", timeout=30)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/zip"
        z = zipfile.ZipFile(io.BytesIO(r.content))
        assert sorted(z.namelist()) == sorted(CAROUSEL_JPGS)
        for n in CAROUSEL_JPGS:
            assert z.getinfo(n).file_size > 10_000

    @pytest.mark.skipif(not HAS_OCR, reason="pytesseract not installed")
    def test_slide6_coming_soon_and_compliance(self):
        r = requests.get(f"{FILE}/safe-sorry-carousel-6.jpg", timeout=30)
        text = pytesseract.image_to_string(Image.open(io.BytesIO(r.content))).lower()
        for s in ("start your free check", "not regulated advice", "trading style"):
            assert s in text, f"'{s}' missing from carousel-6; got:\n{text!r}"

    def test_zip_download_attachment(self):
        r = requests.get(f"{FILE}/safe-sorry-carousel.zip?download=1", timeout=30)
        assert "attachment" in r.headers.get("Content-Disposition", "")
        assert "safe-sorry-carousel.zip" in r.headers.get("Content-Disposition", "")


# ---------- /api/reels listing page ----------
class TestReelsPage:
    def test_lists_all_videos_and_carousel(self):
        r = requests.get(REELS, timeout=30)
        assert r.status_code == 200
        body = r.text
        for v in VIDEOS:
            assert v in body, f"{v} missing from /api/reels"
        # all 6 carousel thumbs
        for c in CAROUSEL_JPGS:
            assert c in body, f"{c} missing from carousel grid"
        assert "Download all 6 slides (zip)" in body
        assert "safe-sorry-carousel.zip?download=1" in body
        # titles for each video card
        for title in (
            "Main reel", "Intro reel", "Award reel",
            "Story (15s) · free check", "Story (15s) · start your free check",
        ):
            assert title in body, f"title '{title}' missing"
