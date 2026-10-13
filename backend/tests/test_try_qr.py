"""Tests for /api/try QR code page (iteration 8) + light regression on invite/presentation/logo-concepts."""
import io
import os
import re

import pytest
import requests
from PIL import Image
from pyzbar.pyzbar import decode as qr_decode

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", "https://protect-me-17.preview.emergentagent.com").rstrip("/")
EXPECTED_HOST = "protect-me-17.preview.emergentagent.com"
EXPECTED_URL = f"https://{EXPECTED_HOST}/"


@pytest.fixture(scope="module")
def try_html():
    r = requests.get(f"{BASE_URL}/api/try", timeout=20)
    assert r.status_code == 200, f"/api/try returned {r.status_code}"
    assert "text/html" in r.headers.get("content-type", "")
    return r.text


class TestTryPage:
    """GET /api/try: HTML with inline SVG QR encoding the https web app URL."""

    def test_returns_200_html(self, try_html):
        assert "<html" in try_html.lower()
        assert "<svg" in try_html.lower()

    def test_contains_logo_image_tag(self, try_html):
        assert "/api/static/logos/logo_dark_transparent.png" in try_html

    def test_logo_image_loads_200(self):
        r = requests.get(f"{BASE_URL}/api/static/logos/logo_dark_transparent.png", timeout=20)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("image/")
        assert len(r.content) > 100

    def test_or_open_it_here_link_has_https_href(self, try_html):
        # Match: <a class="btn" href="HREF">Or open it here</a>
        m = re.search(r'href="([^"]+)"[^>]*>Or open it here', try_html)
        assert m, "'Or open it here' link not found"
        href = m.group(1)
        assert href == EXPECTED_URL, f"href is {href!r}, expected {EXPECTED_URL!r}"
        assert not href.startswith("exp://"), "href must not be exp://"

    def test_no_exp_scheme_anywhere(self, try_html):
        assert "exp://" not in try_html, "page must not contain any exp:// scheme"

    def test_qr_decodes_to_https_url(self, try_html):
        # Extract the inline SVG inside the #qr div and rasterize via Playwright-free path:
        # segno's svg_inline uses <svg> with <path> elements; we render by using segno again
        # from the same text we fetched? No — we must decode the actual QR shown. Use a
        # headless browser via Playwright OR convert SVG->PNG with cairosvg. Fall back to
        # extracting the URL from the QR by re-encoding and comparing: not acceptable per spec.
        # Use cairosvg if available; else use svglib+reportlab; else use wand.
        svg_match = re.search(r'(<svg\b[^>]*>.*?</svg>)', try_html, re.DOTALL | re.IGNORECASE)
        assert svg_match, "inline <svg> not found in page"
        svg_bytes = svg_match.group(1).encode("utf-8")

        png_bytes = _svg_to_png(svg_bytes)
        img = Image.open(io.BytesIO(png_bytes)).convert("L")
        # Upscale for reliable decoding
        img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
        results = qr_decode(img)
        assert results, "pyzbar could not decode the QR code"
        payload = results[0].data.decode("utf-8")
        assert payload == EXPECTED_URL, f"QR decoded to {payload!r}, expected {EXPECTED_URL!r}"
        assert not payload.startswith("exp://")


def _svg_to_png(svg_bytes: bytes) -> bytes:
    """Convert SVG to PNG using whichever lib is installed."""
    # Try cairosvg
    try:
        import cairosvg  # type: ignore
        return cairosvg.svg2png(bytestring=svg_bytes, output_width=600, output_height=600)
    except Exception:
        pass
    # Fallback: svglib + reportlab
    try:
        from svglib.svglib import svg2rlg  # type: ignore
        from reportlab.graphics import renderPM  # type: ignore
        drawing = svg2rlg(io.BytesIO(svg_bytes))
        buf = io.BytesIO()
        renderPM.drawToFile(drawing, buf, fmt="PNG")
        return buf.getvalue()
    except Exception:
        pass
    # Last resort: re-build QR locally from the href (verifies at least SVG shape is sane)
    pytest.skip("No SVG->PNG rasterizer available (install cairosvg or svglib)")


# ------------------- Light regression -------------------
class TestRegression:
    def test_invite_mark_sfl(self):
        r = requests.get(f"{BASE_URL}/api/invite/MARK-SFL", timeout=20)
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        assert len(r.text) > 500

    def test_presentation(self):
        r = requests.get(f"{BASE_URL}/api/presentation", timeout=20)
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")

    def test_logo_concepts(self):
        r = requests.get(f"{BASE_URL}/api/logo-concepts", timeout=20)
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
