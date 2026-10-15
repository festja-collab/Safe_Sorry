"""Tests the /api/reels router: Range support (iOS Safari fix), download, traversal, regression."""
import hashlib
import os

import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "https://protect-me-17.preview.emergentagent.com").rstrip("/")
VIDEO = f"{BASE_URL}/api/reels/file/safe-sorry-launch-reel.mp4"
COVER = f"{BASE_URL}/api/reels/file/safe-sorry-launch-reel-cover.jpg"


@pytest.fixture(scope="module")
def full_video():
    r = requests.get(VIDEO, timeout=30)
    assert r.status_code == 200, r.text
    assert r.headers.get("content-type") == "video/mp4"
    assert r.headers.get("accept-ranges") == "bytes"
    return r.content


# ---- Range behaviour ----
class TestRange:
    def test_200_no_range(self, full_video):
        assert len(full_video) == 1813264

    def test_206_small_range(self, full_video):
        r = requests.get(VIDEO, headers={"Range": "bytes=0-1"}, timeout=30)
        assert r.status_code == 206
        assert r.headers["Content-Range"] == "bytes 0-1/1813264"
        assert r.headers.get("Accept-Ranges") == "bytes"
        assert len(r.content) == 2
        assert r.content == full_video[:2]

    def test_206_open_ended(self, full_video):
        r = requests.get(VIDEO, headers={"Range": "bytes=1000000-"}, timeout=30)
        assert r.status_code == 206
        size = 1813264
        assert r.headers["Content-Range"] == f"bytes 1000000-{size - 1}/{size}"
        assert len(r.content) == size - 1000000
        assert r.content == full_video[1000000:]

    def test_206_suffix_range(self, full_video):
        r = requests.get(VIDEO, headers={"Range": "bytes=-500"}, timeout=30)
        assert r.status_code == 206
        size = 1813264
        assert r.headers["Content-Range"] == f"bytes {size - 500}-{size - 1}/{size}"
        assert len(r.content) == 500
        assert r.content == full_video[-500:]

    def test_416_out_of_range(self):
        r = requests.get(VIDEO, headers={"Range": "bytes=99999999-"}, timeout=30)
        assert r.status_code == 416
        assert r.headers.get("Content-Range") == "bytes */1813264"

    def test_concatenated_chunks_match_full(self, full_video):
        """iPhone pulls the file in ranged chunks; md5 of reassembled chunks must equal the full md5."""
        full_md5 = hashlib.md5(full_video).hexdigest()
        size = 1813264
        chunks = [(0, 499999), (500000, 999999), (1000000, 1499999), (1500000, size - 1)]
        buf = bytearray()
        for s, e in chunks:
            r = requests.get(VIDEO, headers={"Range": f"bytes={s}-{e}"}, timeout=30)
            assert r.status_code == 206
            assert r.headers["Content-Range"] == f"bytes {s}-{e}/{size}"
            buf += r.content
        assert len(buf) == size
        assert hashlib.md5(bytes(buf)).hexdigest() == full_md5


# ---- Download + cover + traversal ----
class TestDownloadAndSecurity:
    def test_download_param_sets_attachment(self):
        r = requests.get(f"{VIDEO}?download=1", timeout=30)
        assert r.status_code == 200
        cd = r.headers.get("Content-Disposition", "")
        assert "attachment" in cd
        assert "safe-sorry-launch-reel.mp4" in cd

    def test_cover_jpg_full(self):
        r = requests.get(COVER, timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type") == "image/jpeg"
        assert r.headers.get("accept-ranges") == "bytes"

    def test_cover_range(self):
        r = requests.get(COVER, headers={"Range": "bytes=0-9"}, timeout=30)
        assert r.status_code == 206
        assert len(r.content) == 10

    def test_cover_download(self):
        r = requests.get(f"{COVER}?download=1", timeout=30)
        assert r.status_code == 200
        assert "attachment" in r.headers.get("Content-Disposition", "")

    def test_traversal_blocked_dotdot(self):
        r = requests.get(f"{BASE_URL}/api/reels/file/..%2Fserver.py", timeout=30)
        assert r.status_code == 404

    def test_traversal_blocked_percent_encoded(self):
        # %2e%2e gets decoded to ".." by the ASGI layer; Starlette redirects (307) to /api/reels/
        # which is the public listing page. The attacker never reads server.py or any other file.
        r = requests.get(f"{BASE_URL}/api/reels/file/%2e%2e", timeout=30, allow_redirects=False)
        assert r.status_code in (307, 404)
        if r.status_code == 307:
            # Confirm it redirects to a safe public page, not an arbitrary file
            assert r.headers.get("location", "").rstrip("/").endswith("/api/reels")

    def test_unknown_extension_404(self):
        r = requests.get(f"{BASE_URL}/api/reels/file/random.txt", timeout=30)
        assert r.status_code == 404


# ---- Reels page ----
class TestReelsPage:
    def test_reels_page_returns_html(self):
        r = requests.get(f"{BASE_URL}/api/reels", timeout=30)
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        body = r.text
        assert "<video" in body
        assert "playsinline" in body
        assert "controls" in body
        assert "poster=" in body
        assert "safe-sorry-launch-reel.mp4" in body
        assert "download=1" in body
        assert "Download video" in body
        assert "Download cover image" in body


# ---- Regression: pre-existing endpoints ----
class TestRegression:
    def test_static_logo(self):
        r = requests.get(f"{BASE_URL}/api/static/logos/logo_dark_transparent.png", timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type") == "image/png"

    def test_try_page(self):
        r = requests.get(f"{BASE_URL}/api/try", timeout=30)
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")

    def test_presentation_page(self):
        r = requests.get(f"{BASE_URL}/api/presentation", timeout=30)
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
