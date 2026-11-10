"""Browser slide deck introducing the app to SFL management. Print → Save as PDF gives one slide per page."""
from html import escape


def _list(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def build_presentation(*, app_name: str, adviser: dict) -> str:
    e = escape
    name, firm = e(adviser["name"]), e(adviser["firm_name"])
    photo = f'<img class="ph" src="{e(adviser["photo_url"])}" alt="{name}">' if adviser.get("photo_url", "").startswith("https://") else ""
    app = e(app_name)
    slides = [
        f"""<div class="cover"><img src="/api/static/logos/logo_dark_transparent.png" alt="{app}" style="width:170px">
<h1>Helping families see what's really at stake, and opening better protection conversations</h1>
<div class="who">{photo}<div><b>{name}</b><br>{e(adviser.get("title", ""))}<br>{firm}</div></div></div>""",

        """<h2>The problem</h2><div class="cols"><div>
<h3>Families know they "should" sort cover…</h3>""" + _list([
            "Most people put it off. Protection feels abstract, morbid or expensive.",
            "Calculators show numbers, but numbers rarely move people to act.",
            "Few people know what the state would actually pay, or how long their savings would last.",
        ]) + """</div><div><h3>…and advisers spend time chasing cold leads</h3>""" + _list([
            "Bought-in leads are costly and often unengaged.",
            "First meetings start from zero: no facts, no emotional buy-in.",
            "Existing clients rarely raise protection themselves.",
        ]) + "</div></div>",

        f"""<h2>What {app} does</h2><p class="lead">A free, five-minute family check that shows, in real terms, what an unprotected gap would mean for a family if the worst happened.</p>
<div class="grid">
<div class="card"><b>12 simple questions</b><br>Family, income, home, savings and existing cover. One question per screen.</div>
<div class="card"><b>UK-specific calculations</b><br>Tax, National Insurance, Bereavement Support Payment, Statutory Sick Pay and other state benefits.</div>
<div class="card"><b>"How long would the money last?"</b><br>A savings runway and timeline: the month money runs out, children's milestones, the mortgage.</div>
<div class="card"><b>A personal family letter</b><br>A warm, AI-written story that turns the numbers into what life would actually feel like.</div>
<div class="card"><b>Clear gaps</b><br>Life cover, income protection and critical illness: what's needed, what's in place, the gap.</div>
<div class="card"><b>One tap to {name.split(" ")[0]}</b><br>Book a call, phone, or request a call-back with the report attached.</div>
</div>""",

        """<h2>The client journey</h2><div class="steps">
<div><span>1</span>Sees an ad, a flyer or a personal invite</div>
<div><span>2</span>Taps the link and creates a free account, nothing to download</div>
<div><span>3</span>Answers 12 questions (about 5 minutes)</div>
<div><span>4</span>Gets their report and family letter</div>
<div><span>5</span>Ticks consent and asks for a call-back</div>
<div><span>6</span>The adviser calls a warm, informed lead</div></div>
<p class="note">No pressure at any step: it's estimates only, not financial advice, and there are no sales calls unless the client asks.</p>""",

        f"""<h2>What the adviser gets</h2><div class="cols"><div>""" + _list([
            "<b>Lead inbox</b>: every call-back request, with status tracking (new, contacted, closed).",
            "<b>The full report attached</b>: family, income, debts, existing cover and gaps before the first call.",
            "<b>Lead source tracking</b>: which ad, flyer or invite each lead came from.",
        ]) + "</div><div>" + _list([
            "<b>Invite a client</b>: send a personal link to anyone who's undecided.",
            "<b>Ad links</b>: one link per campaign (Facebook, Instagram, Google, flyers) to measure results.",
            f"<b>Dashboard</b>: leads, clients and results at a glance, with a firm-wide view for {firm}.",
        ]) + "</div></div>",

        """<h2>Why the leads should be better</h2><div class="grid">
<div class="card"><b>Self-qualified</b><br>They've already looked at their own numbers and decided they want to talk.</div>
<div class="card"><b>Emotionally engaged</b><br>They've read what a gap would mean for their own children and home.</div>
<div class="card"><b>Fact-find started</b><br>Key details are captured before the first call, so meetings are shorter and more focused.</div>
<div class="card"><b>Trust built first</b><br>The adviser's photo, bio and FCA details are in the app from the start.</div>
<div class="card"><b>Measurable</b><br>Every lead has a source, so we only keep spending on what works.</div>
<div class="card"><b>Repeatable</b><br>The same check can be sent after every review, mortgage or life event.</div></div>""",

        """<h2>Built with compliance in mind</h2><div class="cols"><div>""" + _list([
            "Clearly labelled as estimates only, not financial advice.",
            "Privacy notice plus a sign-up agreement; explicit consent before any details go to an adviser.",
            "Each person's data is locked to their own account; passwords are securely encrypted.",
            "Firm and principal FCA disclosures shown in the app and on every landing page.",
        ]) + "</div><div>" + _list([
            "Usage limits to prevent abuse.",
            "A full compliance review pack covering every customer-facing word, the calculation method and the AI prompt.",
            "No ads or public launch until compliance and the principal firm have approved them.",
            "Consumer Duty: the emotional framing is designed to be accurate, respectful and in the customer's interest.",
        ]) + '</div></div><p class="note">Compliance pack: <a href="/api/compliance-pack">open the review pack</a></p>',

        f"""<h2>The plan: start small, measure, report back</h2><div class="cols"><div><h3>Phase 1: {name.split(" ")[0]} only</h3>""" + _list([
            "Use the app to generate my own protection leads.",
            "Channels: invites to existing contacts, referrals, flyers with QR codes, then small, approved social ads.",
            "Low cost: a modest test budget, with every lead tracked to its source.",
        ]) + "</div><div><h3>What I'll report back</h3>" + _list([
            "Families who completed a check",
            "Call-back requests (leads)",
            "Leads that became clients and cases written",
            "Cost per lead and cost per client by channel",
            "Client feedback and any compliance points",
        ]) + "</div></div>",

        """<h2>How it could make money</h2><div class="grid">
<div class="card"><b>More protection cases</b><br>A steady stream of warm leads that the adviser generates directly, rather than buying them in.</div>
<div class="card"><b>Lower cost per lead</b><br>Our own tracked ads and referrals instead of paying per lead to third parties.</div>
<div class="card"><b>Existing clients</b><br>Send the check to mortgage, pension and investment clients to surface protection gaps we'd otherwise miss.</div>
<div class="card"><b>Fuller protection</b><br>The report shows life, income and illness gaps together, so conversations naturally cover more than one need.</div>
<div class="card"><b>Referrals</b><br>Clients can share a five-minute check with friends and family far more easily than "speak to my adviser".</div>
<div class="card"><b>Recurring opportunities</b><br>New baby, new home, new job: each life event is a reason to re-check and review.</div></div>
<div class="example"><b>Illustrative example only:</b> if a channel produces 20 call-back requests and 1 in 4 goes ahead, that's 5 new protection clients, each also a relationship for future mortgage, pension and investment advice. The pilot will replace these assumptions with real figures.</div>""",

        """<h2>Future possibilities</h2><div class="grid">
<div class="card"><b>Roll out to the SFL team</b><br>Each adviser gets their own code, lead inbox and results. Already supported.</div>
<div class="card"><b>Review reminders</b><br>Prompt clients to re-check after life events or once a year.</div>
<div class="card"><b>Mortgage tie-in</b><br>Send the check with every mortgage and remortgage, while the gap is front of mind.</div>
<div class="card"><b>Workplace & events</b><br>QR codes at employer seminars, community events and partner offices.</div>
<div class="card"><b>Next generation</b><br>Wealth clients share it with grown-up children starting families.</div>
<div class="card"><b>Fully SFL branded</b><br>Logo, colours and approved wording throughout.</div></div>""",

        f"""<div class="cover"><div class="brand">NEXT STEPS</div><h1>Start small, prove it, then decide together</h1>""" + _list([
            "Compliance and principal-firm review of the app and the review pack",
            f"{name.split(' ')[0]} runs a personal lead-generation pilot",
            "Report back with real numbers: leads, clients, cost per lead",
            "Decide on next steps for SFL based on the results",
        ]) + f"""<p class="small">{e(adviser["regulatory_status"])} Internal presentation, not for client use.</p></div>""",
    ]
    body = "".join(f'<section class="slide{" dark" if i in (0, len(slides) - 1) else ""}">{s}<div class="num">{i + 1} / {len(slides)}</div></section>'
                   for i, s in enumerate(slides))
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{app}: introduction for {firm}</title><style>
*{{box-sizing:border-box}} html,body{{margin:0;height:100%;background:#E9ECF0;font-family:Arial,Helvetica,sans-serif;color:#1E2B38}}
.slide{{display:none;width:100vw;height:100vh;padding:6vh 7vw;background:#fff;position:relative;overflow:auto}}
.slide.on{{display:flex;flex-direction:column;justify-content:center}}
.dark{{background:#223342;color:#fff}} .dark a{{color:#BF9B30}}
h1{{font-family:Georgia,serif;font-size:clamp(28px,4.4vw,56px);line-height:1.15;margin:16px 0 28px;max-width:1000px}}
h2{{font-family:Georgia,serif;font-size:clamp(24px,3.4vw,44px);margin:0 0 24px;color:#223342}} h2:after{{content:"";display:block;width:64px;height:4px;background:#BF9B30;margin-top:14px}}
h3{{font-size:clamp(16px,1.6vw,20px);color:#8F7019;margin:0 0 8px}}
.brand{{color:#BF9B30;letter-spacing:3px;font-size:14px;font-weight:bold}}
p,li{{font-size:clamp(15px,1.5vw,20px);line-height:1.55}} li{{margin-bottom:8px}}
.lead{{font-size:clamp(17px,1.8vw,24px);max-width:1000px;margin:0 0 20px}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:4vw}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}
.card{{background:#F5F6F8;border-radius:16px;padding:18px 20px;font-size:clamp(14px,1.3vw,17px);line-height:1.5;border-top:4px solid #BF9B30}}
.card b{{color:#223342;font-size:1.1em}}
.steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}
.steps div{{background:#F5F6F8;border-radius:16px;padding:20px;font-size:clamp(15px,1.5vw,19px)}}
.steps span{{display:inline-flex;width:36px;height:36px;border-radius:50%;background:#223342;color:#fff;align-items:center;justify-content:center;margin-right:10px;font-weight:bold}}
.note,.small{{color:#6C7683;font-size:14px}} .dark .small{{color:#C3C9D2;margin-top:28px}}
.example{{margin-top:18px;background:#F4EEDC;border-radius:12px;padding:14px 18px;font-size:15px;color:#6E5714}}
.who{{display:flex;gap:20px;align-items:center;font-size:18px;line-height:1.5}} .ph{{width:96px;height:96px;border-radius:16px;object-fit:cover}}
.num{{position:absolute;right:28px;bottom:20px;font-size:13px;color:#8C96A3}}
.nav{{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);display:flex;gap:10px;z-index:5}}
.nav button{{border:0;background:#BF9B30;color:#1A2633;font-size:16px;padding:12px 22px;border-radius:999px;cursor:pointer}}
@media (max-width:760px){{.cols,.grid,.steps{{grid-template-columns:1fr}} .slide{{padding:28px 22px 90px}} .slide.on{{justify-content:flex-start}}}}
@media print{{@page{{size:A4 landscape;margin:0}} .nav{{display:none}} .slide{{display:flex!important;flex-direction:column;justify-content:center;width:297mm;height:210mm;page-break-after:always;overflow:hidden}}
.dark{{-webkit-print-color-adjust:exact;print-color-adjust:exact}} .card,.steps div,.example,h2:after,.steps span{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}}}
</style></head><body>{body}
<div class="nav"><button id="prev" aria-label="Previous slide">‹ Back</button><button id="next" aria-label="Next slide">Next ›</button><button id="full" aria-label="Full screen">⛶</button></div>
<script>
const s=[...document.querySelectorAll('.slide')];let i=0;
function show(n){{i=Math.max(0,Math.min(s.length-1,n));s.forEach((x,k)=>x.classList.toggle('on',k===i));}}
document.getElementById('prev').onclick=()=>show(i-1);document.getElementById('next').onclick=()=>show(i+1);
document.getElementById('full').onclick=()=>document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();
document.addEventListener('keydown',ev=>{{if(['ArrowRight','PageDown',' '].includes(ev.key)){{ev.preventDefault();show(i+1)}}if(['ArrowLeft','PageUp'].includes(ev.key))show(i-1)}});
let x0=null;document.addEventListener('touchstart',ev=>x0=ev.touches[0].clientX);document.addEventListener('touchend',ev=>{{if(x0===null)return;const d=ev.changedTouches[0].clientX-x0;if(Math.abs(d)>50)show(i+(d<0?1:-1));x0=null}});
show(0);
</script></body></html>"""
