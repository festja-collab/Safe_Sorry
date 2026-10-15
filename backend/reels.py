"""Serves Instagram reels with HTTP Range support (required by iPhone Safari) + a simple download page."""
import re
from html import escape
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

REELS = Path(__file__).parent / "static" / "reels"
router = APIRouter()
TYPES = {".mp4": "video/mp4", ".jpg": "image/jpeg", ".png": "image/png", ".zip": "application/zip"}


def _file(name: str) -> Path:
    p = (REELS / name).resolve()
    if p.parent != REELS.resolve() or p.suffix not in TYPES or not p.is_file():
        raise HTTPException(404, "Not found")
    return p


@router.get("/reels/file/{name}")
async def reel_file(name: str, request: Request, download: int = 0):
    p = _file(name)
    size = p.stat().st_size
    headers = {"Accept-Ranges": "bytes", "Cache-Control": "public, max-age=3600"}
    if download:
        headers["Content-Disposition"] = f'attachment; filename="{p.name}"'
    m = re.match(r"bytes=(\d*)-(\d*)", request.headers.get("range", ""))
    if not m or (not m.group(1) and not m.group(2)):
        return Response(p.read_bytes(), media_type=TYPES[p.suffix], headers=headers)
    if m.group(1):
        start = int(m.group(1))
        end = min(int(m.group(2)) if m.group(2) else size - 1, size - 1)
    else:  # suffix range: last N bytes
        start, end = max(0, size - int(m.group(2))), size - 1
    if start >= size or start > end:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{size}"})
    with p.open("rb") as f:
        f.seek(start)
        data = f.read(end - start + 1)
    headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    return Response(data, status_code=206, media_type=TYPES[p.suffix], headers=headers)


@router.get("/reels", response_class=HTMLResponse)
async def reels_page():
    order = ["safe-sorry-launch-reel", "safe-sorry-coming-soon", "safe-sorry-award-reel", "safe-sorry-story-coming-soon", "safe-sorry-story-launch"]
    titles = {"safe-sorry-launch-reel": "Launch reel (27s) · for launch day", "safe-sorry-coming-soon": "Coming soon reel (27s) · post before launch",
              "safe-sorry-award-reel": "Award reel (21s) · builds trust", "safe-sorry-story-coming-soon": "Story (15s) · coming soon, link in bio",
              "safe-sorry-story-launch": "Story (15s) · launch day, link in bio"}
    vids = sorted((p.name for p in REELS.glob("*.mp4")), key=lambda n: order.index(n[:-4]) if n[:-4] in order else 99)
    cards = ""
    for v in vids:
        cover = v.replace(".mp4", "-cover.jpg")
        poster = f' poster="/api/reels/file/{escape(cover)}"' if (REELS / cover).is_file() else ""
        cards += f"""<div class="card"><h2>{escape(titles.get(v[:-4], v))}</h2><video src="/api/reels/file/{escape(v)}" controls playsinline preload="metadata"{poster}></video>
<a class="btn" href="/api/reels/file/{escape(v)}?download=1" download>⬇ Download video</a>
{f'<a class="btn ghost" href="/api/reels/file/{escape(cover)}?download=1" download>⬇ Download cover image</a>' if poster else ''}</div>"""
    slides = sorted(REELS.glob("safe-sorry-carousel-*.jpg"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))
    if slides:
        imgs = "".join(f'<a href="/api/reels/file/{p.name}?download=1" download><img src="/api/reels/file/{p.name}" alt="Slide {i}"></a>'
                       for i, p in enumerate(slides, 1))
        cards += f"""<div class="card"><h2>Launch carousel (6 slides) · post before launch</h2><div class="grid">{imgs}</div>
<a class="btn" href="/api/reels/file/safe-sorry-carousel.zip?download=1" download>⬇ Download all 6 slides (zip)</a>
<p class="tip">On iPhone it's easiest to tap each slide, then press and hold → Save to Photos (zip files open in the Files app).</p></div>"""
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Safe &gt; Sorry reels</title><style>
body{{margin:0;background:#223342;color:#fff;font-family:Arial,Helvetica,sans-serif}} .wrap{{max-width:480px;margin:0 auto;padding:24px 16px}}
h1{{font-family:Georgia,serif;font-size:24px}} p{{color:#C3C9D2;line-height:1.5}}
.card{{background:#1A2836;border-radius:18px;padding:12px;margin:16px 0}} video{{width:100%;border-radius:12px;background:#000;display:block}}
.btn{{display:block;text-align:center;background:#BF9B30;color:#1A2633;text-decoration:none;font-weight:bold;padding:14px;border-radius:999px;margin-top:12px}}
h2{{font-size:16px;margin:4px 4px 10px;color:#BF9B30}} .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}} .grid img{{width:100%;border-radius:8px;display:block}} .tip{{font-size:13px}}
.ghost{{background:transparent;color:#BF9B30;border:2px solid #BF9B30}}
</style></head><body><div class="wrap"><h1>Your reels</h1>
<p>Tap play to watch. To save: tap <b>Download video</b>. On iPhone, tap the blue arrow in the address bar → Downloads → open the video → Share → <b>Save Video</b>. On Android it goes straight to your Downloads / Gallery.</p>
{cards}</div></body></html>"""
