"""4-week Instagram posting plan for Rosemount review. Browser page at /api/posting-plan (print/save as PDF)."""
from html import escape

AR = ("Secure for Life Wealth Management Ltd is an Appointed Representative of Rosemount Financial Solutions (IFA) "
      "Limited, which is authorised and regulated by the Financial Conduct Authority.")
FOOTER = f"Estimates only, not regulated advice. Figures are illustrative. {AR}"
TAGS_CORE = "#lifeinsurance #incomeprotection #criticalillnesscover #protectionadvice #familyfinances #personalfinanceuk"

# (week, day, format, asset title, asset file, caption, extra hashtags)
POSTS = [
    (1, "Mon", "Reel", "Coming soon reel (27s)", "safe-sorry-coming-soon.mp4",
     "Most of us know what our phone is insured for. Far fewer know what would happen to our family's money if we "
     "couldn't work, or weren't here.\n\nSafe > Sorry is a free family check that shows you, in plain English, in about "
     "5 minutes. Coming soon. Follow to be first to try it.", "#comingsoon #newapp #familyfirst"),
    (1, "Wed", "Reel", "What do we insure? (25s)", "safe-sorry-insure-reel.mp4",
     "Phone. Car. Holiday. Even the dog.\n\nWe insure the things we'd hate to lose. So what about the income your "
     "family relies on? Worth a thought this week.", "#insurance #moneytips #financialwellbeing"),
    (1, "Fri", "Carousel (6)", "Myth: “I’m young and healthy”", "safe-sorry-myth-young.zip",
     "Myth: \"I'm young and healthy, I don't need cover.\"\n\nSwipe for the facts. Not everyone needs cover, but it's "
     "worth knowing whether you do. Save this for later.", "#mythbusting #firsttimebuyer #youngfamilies"),
    (2, "Mon", "Reel", "Myth: death in service (27s)", "safe-sorry-myth-reel.mp4",
     "\"I've got death in service at work, so I'm covered.\"\n\nIt's a great start. But it usually stops when you leave "
     "your job, and it only pays out if you die. Do you know what yours would actually pay?", "#deathinservice #employeebenefits #mythbusting"),
    (2, "Wed", "Carousel (6)", "Launch carousel · what the app does", "safe-sorry-carousel.zip",
     "What does Safe > Sorry actually do? Swipe through.\n\nAnswer a few questions about your family, and see your "
     "family's safety net in pounds and months, not jargon. Free, and coming soon.", "#comingsoon #newapp #moneytips"),
    (2, "Fri", "Carousel (6)", "Myth: “The state will look after us”", "safe-sorry-myth-state.zip",
     "Myth: \"If something happened, the state would look after us.\"\n\nState support helps, but the amounts can be a "
     "surprise. Swipe for the 2026/27 figures. Eligibility rules apply.", "#statebenefits #sickpay #mythbusting"),
    (3, "Mon", "Reel", "Myth: “I’m young and healthy” (27s)", "safe-sorry-myth-young-reel.mp4",
     "The best time to check your cover is usually before you need it.\n\nYoung, healthy and someone relies on your "
     "income? It's worth 5 minutes to see where you stand.", "#mythbusting #newparents #youngfamilies"),
    (3, "Wed", "Reel", "Myth: “The state will look after us” (27s)", "safe-sorry-myth-state-reel.mp4",
     "Statutory Sick Pay is £123.25 a week in 2026/27. Could your household run on that?\n\nKnowing the numbers is the "
     "first step. Eligibility rules apply.", "#statebenefits #sickpay #financialwellbeing"),
    (3, "Fri", "Story (15s)", "Story · coming soon, link in bio", "safe-sorry-story-coming-soon.mp4",
     "(Story, no caption needed.) Add a countdown sticker to launch day and the link sticker to the landing page.", ""),
    (4, "Mon", "Reel", "Launch reel (27s) · LAUNCH DAY", "safe-sorry-launch-reel.mp4",
     "It's here. Safe > Sorry is live.\n\nA free family check that shows what would happen to your family's money if "
     "you couldn't work, or weren't here, and what you could do about it. Link in bio.", "#launchday #newapp #familyfirst"),
    (4, "Tue", "Story (15s)", "Story · launch day, link in bio", "safe-sorry-story-launch.mp4",
     "(Story, no caption needed.) Add the link sticker. Reshare the launch reel to Stories the same day.", ""),
    (4, "Fri", "Reel", "Award reel (21s)", "safe-sorry-award-reel.mp4",
     "Built by Mark Turner, Protection Adviser of the Year 2026 at the Next Intelligence awards.\n\nThe aim is simple: "
     "help families see their safety net clearly, then talk it through with a real person if they'd like to.",
     "#protectionadviseroftheyear #awardwinning #financialadvice"),
]

STORIES = [
    "Poll: \"Do you know what your family would get if you couldn't work for 6 months?\" Yes / Not really",
    "Quiz: \"How much is Statutory Sick Pay a week in 2026/27?\" £123.25 (correct) / £250 / £400",
    "Question box: \"What's your biggest money worry for your family?\" (answer generally, never give personal advice in DMs)",
    "Reshare each feed post to your Story on the day it goes out.",
]

BIO = ("Safe > Sorry · Better Safe Than Sorry\nFree 5-minute family protection check\nEstimates only, not advice\n"
       "From Protection Adviser of the Year 2026 ↓")


def posting_plan() -> str:
    e = escape
    rows, week = "", 0
    for w, day, fmt, title, asset, caption, tags in POSTS:
        if w != week:
            week = w
            label = {1: "Week 1 · build awareness", 2: "Week 2 · myths & what's coming", 3: "Week 3 · countdown",
                     4: "Week 4 · launch"}[w]
            rows += f'<tr class="wk"><td colspan="4">{label}</td></tr>'
        full = caption + (f"\n\n{FOOTER}\n\n{TAGS_CORE} {tags}" if tags else "")
        rows += (f'<tr><td><b>{e(day)}</b><br><span class="m">{e(fmt)}</span></td>'
                 f'<td><b>{e(title)}</b><br><a href="/api/reels/file/{e(asset)}?download=1">{e(asset)}</a></td>'
                 f'<td><pre>{e(full)}</pre></td><td class="sign">Approved ☐<br>By: ________<br>Date: ________<br>Ref: ________</td></tr>')
    stories = "".join(f"<li>{e(s)}</li>" for s in STORIES)
    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Safe &gt; Sorry · 4-week Instagram plan</title><style>
body{{margin:0;font-family:Arial,Helvetica,sans-serif;color:#2C2A28;background:#F5F3EE}} .wrap{{max-width:1100px;margin:0 auto;padding:24px 16px}}
h1{{color:#223342;font-family:Georgia,serif}} h2{{color:#223342;margin-top:32px}} .box{{background:#fff;border-radius:12px;padding:16px 20px;margin:12px 0}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden}} td{{vertical-align:top;padding:12px;border-bottom:1px solid #EEE9DF;font-size:14px}}
tr.wk td{{background:#223342;color:#BF9B30;font-weight:bold;font-size:15px}} pre{{white-space:pre-wrap;font-family:inherit;margin:0}}
.m{{color:#7D7973;font-size:12px}} .sign{{width:140px;color:#555;font-size:12px;line-height:1.9}} a{{color:#223342}}
.note{{background:#FFF4D6;border-left:4px solid #BF9B30;padding:10px 14px;border-radius:8px}} @media print{{body{{background:#fff}} a{{color:#000}}}}
</style></head><body><div class="wrap">
<h1>Safe &gt; Sorry · 4-week Instagram plan</h1>
<p class="note"><b>Draft for Rosemount compliance review.</b> Nothing is to be posted until each item below is approved. Each post carries
the not-advice wording and the appointed representative statement. All figures are 2026/27 and illustrative. Weeks 1–3 assume the app
is not yet in the app stores (reels in those weeks end with “Coming soon”). Week 4 is launch week; move it to match the real launch date.
Reels ending “Coming soon” should not be posted after launch.</p>
<div class="box"><b>Posting rhythm:</b> 3 feed posts a week (Mon / Wed / Fri, early evening 7–9pm works well for parents) plus 2–3 Stories.
Use Instagram’s commercial music library on Stories and carousels. Main reels already include licensed music.</div>
<h2>Profile bio (draft)</h2><div class="box"><pre>{e(BIO)}</pre><p class="m">Link in bio: the Safe &gt; Sorry landing page with tracking code MARK-SFL-IG.
The full statement below doesn't fit in the 150-character bio, so it goes in a pinned “About” post and Story highlight:</p><pre>{e(FOOTER)}</pre></div>
<h2>Feed posts</h2>
<table><tr><td><b>When</b></td><td><b>Asset</b></td><td><b>Caption + hashtags</b></td><td><b>Compliance</b></td></tr>{rows}</table>
<h2>Story ideas (any week)</h2><div class="box"><ul>{stories}</ul></div>
<h2>House rules</h2><div class="box"><ul>
<li>Never give personal recommendations in comments or DMs. Invite people to use the free check or book a call.</li>
<li>No guarantees, “cheapest” claims or fear-led wording. Keep every post fair, clear and not misleading on its own.</li>
<li>Keep a copy of each approved post and its approval reference.</li></ul></div>
<p class="m">Approval summary: Reviewed by ______________________ (Rosemount) &nbsp; Date ____________ &nbsp; Signature ______________________</p>
</div></body></html>"""
