"""Public 'try the app' page: a QR code any phone camera can open (web version of the app)."""
from html import escape

import segno


def try_page(*, app_name: str, url: str) -> str:
    e = escape
    qr = segno.make(url, error="m").svg_inline(dark="#223342", light="#FFFFFF", border=4, omitsize=True)  # viewBox only → scales to fit
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Try {e(app_name)}</title><style>
body{{margin:0;font-family:Arial,Helvetica,sans-serif;background:#223342;color:#fff;text-align:center}}
.wrap{{max-width:460px;margin:0 auto;padding:32px 20px}} .logo{{width:170px}}
.qr{{background:#fff;border-radius:20px;padding:12px;display:inline-block;margin:20px 0}} .qr svg{{width:min(260px,70vw);height:auto;display:block;shape-rendering:crispEdges}}
h1{{font-family:Georgia,serif;font-size:26px;margin:16px 0 8px}} p{{line-height:1.6;color:#E9ECF0}}
.btn{{display:inline-block;background:#BF9B30;color:#1A2633;text-decoration:none;padding:14px 26px;border-radius:999px;font-size:17px;margin-top:8px}}
.small{{font-size:13px;color:#C3C9D2;margin-top:24px}}
</style></head><body><div class="wrap">
<img class="logo" src="/api/static/logos/logo_dark_transparent.png" alt="{e(app_name)}">
<h1>Try the app on your phone</h1>
<p>Point your phone’s normal camera at this code and tap the link that appears. It opens in your web browser, so there’s nothing to install.</p>
<div class="qr" id="qr">{qr}</div>
<div><a class="btn" href="{e(url)}">Or open it here</a></div>
<p class="small">Preview version for testing. Estimates only, not financial advice.</p>
</div></body></html>"""
