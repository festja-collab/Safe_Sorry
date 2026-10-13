"""Public invite landing page: the link an adviser sends to a client."""
from html import escape


def invite_page(*, app_name: str, adviser: dict, name: str, code_display: str, ad: bool, ios_url: str, android_url: str) -> str:
    e = escape
    first = e(adviser["name"].split(" ")[0])
    hello = f"Hi {e(name)}," if name else "Hi,"
    photo = f'<img src="{e(adviser["photo_url"])}" alt="{e(adviser["name"])}" class="ph">' if adviser.get("photo_url", "").startswith("https://") else ""
    logo = f'<img src="{e(adviser["logo_url"])}" alt="{e(adviser.get("firm_name", ""))}" class="logo">' if adviser.get("logo_url", "").startswith("/api/") else ""
    hero_bg = adviser.get("brand_color") or "#223342"
    stores = ""
    if ios_url.startswith("https://"):
        stores += f'<a class="btn" href="{e(ios_url)}">Download on the App Store</a>'
    if android_url.startswith("https://"):
        stores += f'<a class="btn" href="{e(android_url)}">Get it on Google Play</a>'
    if not stores:
        stores = '<p class="soon">Coming soon to the App Store and Google Play.</p>'
    if ad:
        body = (
            "<p><b>Most families never ask the question. This app answers it — gently, in five minutes.</b></p>"
            "<ul style='line-height:1.8;font-size:16px'><li>See the month your family's money would run out</li>"
            "<li>Find out what the state would (and wouldn't) pay</li><li>Learn which gaps matter for your children's future</li>"
            "<li>Free, private, no sales calls unless you ask</li></ul>"
            "<p>When you sign up, enter this code to get your report:</p>"
        )
    else:
        body = (
            f"<p>{hello}</p><p>Thanks for chatting with me. If you'd like to see, in real terms, what your family would face "
            "if you couldn't be there — and whether there's a gap worth closing — this app walks you through it in about five minutes.</p>"
            "<p>When you sign up, enter my code so I can help if you want me to:</p>"
        )
    reg = ""
    if adviser.get("firm_name"):
        reg = f'{e(adviser["firm_name"])} (FRN {e(adviser["fca_number"])})'
        if adviser.get("principal_name"):
            reg += f' is an Appointed Representative of {e(adviser["principal_name"])}, which is authorised and regulated by the Financial Conduct Authority (FRN {e(adviser["principal_fca_number"])}).'
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(app_name)} — an invitation from {first}</title>
<meta property="og:title" content="{e(app_name)} — would your family be okay?">
<meta property="og:description" content="A gentle 5-minute check that shows what your family would face if the worst happened.">
<style>
body{{margin:0;font-family:Georgia,serif;background:#FFFFFF;color:#1E2B38}}
.hero{{background:{e(hero_bg)};color:#fff;padding:40px 24px 32px}}
.logo{{display:block;max-height:56px;max-width:200px;object-fit:contain;background:#fff;border-radius:10px;padding:8px;margin-bottom:16px}} .wrap{{max-width:520px;margin:0 auto}}
.applogo{{display:block;width:120px;background:#fff;border-radius:16px;padding:8px}}
.brand{{color:#BF9B30;letter-spacing:2px;font-size:13px;font-family:Arial,sans-serif}} h1{{font-size:30px;line-height:1.2;margin:12px 0}}
.card{{max-width:520px;margin:-16px auto 0;background:#F5F6F8;border-radius:16px;padding:24px;box-sizing:border-box}}
.who{{display:flex;gap:16px;align-items:center;margin-bottom:12px}} .ph{{width:72px;height:72px;border-radius:14px;object-fit:cover}}
p{{line-height:1.6;font-size:17px}} .code{{font-family:Arial,sans-serif;font-size:28px;letter-spacing:3px;color:#8F7019;background:#F4EEDC;border-radius:12px;padding:12px;text-align:center;margin:12px 0}}
.btn{{display:block;text-align:center;background:#BF9B30;color:#1A2633;text-decoration:none;font-family:Arial,sans-serif;font-size:17px;padding:16px;border-radius:999px;margin:10px 0}}
.soon{{font-family:Arial,sans-serif;color:#6C7683;text-align:center}} .small{{font-family:Arial,sans-serif;font-size:13px;color:#6C7683;line-height:1.5}}
.main{{padding:24px}}
</style></head><body>
<div class="hero"><div class="wrap">{logo}<img src="/api/static/logos/logo_full_cropped.png" alt="{e(app_name)}" class="applogo"><h1>Would your family be okay if the worst happened?</h1>
<div>A gentle five-minute check. No sales, no obligation.</div></div></div>
<div class="main"><div class="card">
<div class="who">{photo}<div><b>{e(adviser["name"])}</b><br><span class="small">{e(adviser.get("title", ""))}</span></div></div>
{body}
<div class="code">{e(code_display)}</div>
{stores}
<p class="small">Estimates only, based on current UK tax and benefit rates. Not financial advice. {reg}</p>
</div></div></body></html>"""
