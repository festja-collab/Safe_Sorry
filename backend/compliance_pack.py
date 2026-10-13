"""Generates the compliance review pack as a printable HTML page."""
from datetime import datetime, timezone
from html import escape

from articles import ARTICLES
from calc import compute, FUNERAL, SSP_MONTHLY, ESA_MONTHLY, UNI_FEES_YEAR

QUESTIONS = [
    ("First, a little about you.", "This is your family's story — so let's start with its author.", "First name, age"),
    ("Who shares your life?", "It matters more than you'd think — the state treats couples very differently.", "Single / living with partner / married or civil partnership; partner's first name"),
    ("Are there little (or not so little) ones?", "Their names help us show what your plan means for them.", "Number of children (0–5), each child's first name and age"),
    ("How do you earn your living?", "", "Employed / self-employed; yearly income before tax"),
    ("And what does [partner] earn?", "Their income is what your family would be living on.", "Partner's yearly income before tax (only if partner)"),
    ("What does it cost to run your home each month?", "Food, bills, childcare, cars, clubs, the little treats. Leave out the mortgage or rent — we'll ask next.", "Monthly household spending"),
    ("Tell us about home.", "", "Mortgage / rent / own outright"),
    ("The mortgage, in a nutshell. / What's the rent?", "", "Mortgage balance, monthly payment, years remaining — or monthly rent"),
    ("What's in the safety net?", "Savings you could actually reach, and any loans or cards still owed.", "Savings; other debts"),
    ("Any cover already in place?", "Don't worry if you're unsure — a best guess is fine. Zero is a perfectly honest answer.", "Personal life cover; death-in-service multiple (employed only)"),
    ("If illness kept you from work…", "This is the risk most of us forget — and the most likely one to happen.", "Employer sick pay months; income protection monthly benefit; critical illness lump sum"),
    ("Last one. What keeps you up at night?", "We'll keep this front of mind as we write your story.", "Losing our home / The children's future / Partner coping alone (or Being a burden on family) / Our everyday way of life"),
]

EXAMPLE = {
    "first_name": "Tom", "age": 38, "relationship": "partner", "partner_name": "Sarah", "partner_income": 24000,
    "children": [{"name": "Emma", "age": 7}, {"name": "Leo", "age": 3}], "employment": "employed",
    "annual_income": 52000, "monthly_outgoings": 2200, "housing": "mortgage", "mortgage_balance": 240000,
    "monthly_housing": 1250, "mortgage_years": 22, "other_debts": 8000, "savings": 12000, "life_cover": 100000,
    "death_in_service": 2, "sick_pay_months": 3, "income_protection": 0, "critical_illness": 0, "worry": "Losing our home",
}


# Fixed sample letter produced by the AI for the worked example (never a real customer's data)
SAMPLE_STORY = {
    "title": "The Home That Holds Everything",
    "paragraphs": [
        "It's a Tuesday morning, and you're hunting for Leo's other shoe while Emma reads her book aloud at the kitchen table. Sarah is finding keys. It's ordinary, noisy, and yours. The house holds all of it: the height marks on the doorframe, the wobbly stair gate. Behind those walls sits a mortgage of £240,000, and your existing cover wouldn't clear it if you weren't there.",
        "If you died, Sarah would be at that same table, sorting the post alone. Your cover and savings would help, but each month she'd be £1,717 short. She'd stretch it, cut things, and quietly stop saying what she needed. By December 2036, the money would be gone. Emma would be nearly ready to leave school, Leo not yet in his GCSE years, and Sarah still carrying the house on her own.",
        "And it isn't only death. If illness stopped you working, your savings would carry you a little over a year. After that, you'd be lying awake doing sums instead of getting better, while Sarah juggled work, nursery pick-ups and hospital car parks. Nobody plans for this. That's exactly why the gap is so easy to leave open."
    ],
    "closing": "This is fixable, Tom, often for less than a weekly takeaway. Keep that home safe, so Emma and Leo never have to leave it."
}


def gbp(n) -> str:
    return f"£{round(n or 0):,}"


def table(headers, rows) -> str:
    th = "".join(f"<th>{escape(h)}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


async def build_pack(*, app_name: str, adviser: dict, story_prompt: str, limits: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%d %B %Y")
    ex = compute(EXAMPLE)
    story = SAMPLE_STORY

    e = escape
    firm = f"{e(adviser['firm_name'])} (FRN {e(adviser['fca_number'])})"
    principal = f"{e(adviser['principal_name'])} (FRN {e(adviser['principal_fca_number'])})"

    q_rows = [(str(i + 1), f"<b>{e(t)}</b><br><span class='muted'>{e(s)}</span>", e(a)) for i, (t, s, a) in enumerate(QUESTIONS)]

    impacts_rows = [
        ("Money runs out", "“The money runs out by [Month Year]” — “After [X months/years], everything you've left behind is gone. [Child] would be [age].”", "Family has dependants and resources run out within 50 years"),
        ("Family would be okay", "“Your family could keep going” — “With [partner]'s income and the cover you have, the money wouldn't run out. That's a gift.”", "Resources never run out"),
        ("Home at risk", "“Your home is at risk” — “The £[balance] mortgage doesn't disappear. [Partner] would need to find £[payment] every month — [X]% of their take-home pay.”", "Existing cover + savings would not clear mortgage and debts"),
        ("Home safe", "“Your home would be safe” — “Your cover would clear the mortgage. They could stay in the home they know.”", "Cover clears the mortgage"),
        ("Monthly shortfall", "“£[X] missing every month” — “That's roughly [N] weekly food shops a month your family would have to find — or go without.”", "Monthly costs exceed partner's net income"),
        ("No Bereavement Support Payment", "“Because you're not married or in a civil partnership, [partner] would receive nothing from the state.”", "Cohabiting, not married"),
        ("Each child", "“[Child] still needs you for [N] years” — “University alone could cost £28,605 in fees. Would that dream still be possible?”", "Each child under 21"),
        ("Illness", "“If you couldn't work” — sick pay → SSP → ESA explanation and how long savings would last.", "Always shown"),
    ]
    headlines = [
        ("No dependants", "“No one depends on your income — but your future self does.”"),
        ("Never runs out", "“Your family could stay on their feet. Let's keep it that way.”"),
        ("Runs out within 12 months", "“If you weren't here tomorrow, your family would have [X] before the money runs out.”"),
        ("Runs out after 12+ months", "“Your family would be okay for [X]. Then what?”"),
    ]

    assumptions = [
        ("Income tax", "Personal allowance £12,570 (tapered above £100,000); 20% to £50,270; 40% to £125,140; 45% above", "rUK 2025/26 rates. <b>Scottish rates not modelled.</b>"),
        ("National Insurance", "8% on £12,570–£50,270; 2% above", "Employee Class 1, 2025/26. Same applied to self-employed (approximation)."),
        ("Bereavement Support Payment", "Married with children: £3,500 + £350/month × 18. Married, no children: £2,500 + £100/month × 18. Cohabiting: £0", "Current DWP rates"),
        ("Statutory Sick Pay", f"£118.75/week (≈{gbp(SSP_MONTHLY)}/month) for 28 weeks after employer sick pay", "2025/26 rate; self-employed receive none"),
        ("ESA after SSP", f"≈£92.05/week (≈{gbp(ESA_MONTHLY)}/month)", "Approximation; eligibility and assessments not modelled"),
        ("Funeral costs", gbp(FUNERAL), "Deducted from resources on death"),
        ("University fees", f"{gbp(UNI_FEES_YEAR)}/year × 3", "Used in wording only, not in the calculation"),
        ("Weekly food shop", "£120", "Used to translate the monthly shortfall into everyday terms"),
    ]
    method = [
        ("Life cover need", "Debts (mortgage + other) + funeral + (monthly spending + rent − partner's net income) × 12 × years needed − Bereavement Support Payment. Years needed: until the youngest child is 21 (minimum 5); 5 years if a partner but no children; 0 if no dependants."),
        ("Existing life provision", "Personal life cover + death-in-service (multiple × salary) + savings."),
        ("Savings runway (death)", "Starting pot = cover + death-in-service + savings + BSP lump sum − funeral. If the pot clears all debts, debts are cleared and monthly costs exclude the mortgage; otherwise the mortgage payment continues. Each month the shortfall (costs − partner's net income − BSP monthly) is subtracted until the pot is exhausted."),
        ("Savings runway (illness)", "Monthly need = spending + housing. Income = full net pay during employer sick pay, then SSP for 28 weeks, then ESA, plus partner's net income and any income protection. Savings fund the shortfall."),
        ("Income protection need", "60% of gross monthly income, less existing income protection."),
        ("Critical illness need", "The higher of 2 × annual income or the mortgage balance, less existing cover."),
        ("Not modelled", "Child Benefit, Universal Credit, inflation, investment growth, interest, inheritance tax, trust arrangements, partner's own cover, pension death benefits, Scottish tax, policy definitions or exclusions."),
    ]

    ex_rows = [
        ("Headline", e(ex["headline"])),
        ("Savings runway", e(ex["runway_label"]) + (f" (money runs out {e(ex['runout_date'])})" if ex["runout_date"] else "")),
        ("Monthly shortfall if Tom died", gbp(ex["monthly_gap_death"])),
        ("Life cover: needs / has / gap", f"{gbp(ex['gaps']['life']['need'])} / {gbp(ex['gaps']['life']['have'])} / <b>{gbp(ex['gaps']['life']['gap'])}</b>"),
        ("Income protection: needs / has / gap", f"{gbp(ex['gaps']['income']['need'])}/mo / {gbp(ex['gaps']['income']['have'])}/mo / <b>{gbp(ex['gaps']['income']['gap'])}/mo</b>"),
        ("Critical illness: needs / has / gap", f"{gbp(ex['gaps']['critical']['need'])} / {gbp(ex['gaps']['critical']['have'])} / <b>{gbp(ex['gaps']['critical']['gap'])}</b>"),
        ("Savings would last if unable to work", e(ex["illness_runway_label"])),
    ]
    ex_impacts = "".join(f"<li><b>{e(i['title'])}</b> — {e(i['body'])}</li>" for i in ex["impacts"])

    story_html = ""
    if story:
        paras = "".join(f"<p>{e(p)}</p>" for p in story.get("paragraphs", []))
        story_html = f"<div class='letter'><h4>{e(story.get('title', ''))}</h4>{paras}<p class='hl'>{e(story.get('closing', ''))}</p></div>"
    else:
        story_html = "<p class='muted'>No sample story has been generated yet.</p>"

    data_rows = [
        ("Account", "First name, email, password (stored only as a secure bcrypt hash)", "Sign-in and saving results"),
        ("Family check answers", "Name and age; partner's first name and income; children's first names and ages; income; spending; mortgage/rent; savings; debts; existing cover; biggest worry", "Calculating the report"),
        ("Report and AI story", "Calculated results and the generated letter", "Showing the report again later"),
        ("Call-back request", "Name, phone number, best time to call, optional message, link to the latest report", "Passed to the adviser by email"),
        ("Usage counters", "Internet connection address and account ID, kept for up to 24 hours", "Preventing abuse (rate limits)"),
    ]
    processors = [
        ("Emergent (hosting platform)", "Hosts the app and database; provides AI and email gateways", "Confirm data location, DPA and sub-processors with Emergent"),
        ("Anthropic (Claude AI, via Emergent)", "Receives family check answers (first names, ages, finances — <b>no email or phone</b>) to write the story", "Confirm data retention and training terms"),
        ("Email delivery provider (via Emergent)", "Delivers call-back requests to the adviser's inbox", f"Lead emails go to {e(adviser.get('email', ''))}"),
    ]
    controls = [
        "Passwords hashed with bcrypt; minimum 10 characters for new accounts",
        "Sign-in sessions expire after 7 days",
        "Each user can only access their own reports (ownership checks on every request)",
        f"Abuse limits: {limits['assess']} family checks, {limits['story']} AI stories and {limits['leads']} call-back requests per account per day; 5 failed sign-ins per email per 15 minutes; 5 new accounts per connection per hour",
        "Security review carried out October 2026: conditional pass, no critical or high-risk issues; medium issues fixed",
        "Lead emails use fixed server-side templates with all customer text escaped (no links or forms)",
    ]
    open_items = [
        "Approve the app as a financial promotion (or confirm it falls outside), including tone, headlines and emotional framing",
        "Approve all wording in Sections 4 and 6, including the AI instructions",
        "Decide whether the AI-written letter is acceptable without human review of each output, or needs changes (e.g. a fixed template)",
        "Privacy notice: content, and where it is shown (sign-up and call-back form)",
        "Consent: explicit tick box before a call-back request is passed to the adviser; marketing consent (none collected today)",
        "Data controller: confirm whether SFL Wealth Management Ltd, Rosemount, or both are the controller(s); DPIA if required",
        "Retention period for accounts, reports and leads (none set — data is kept until deleted); in-app account and data deletion (not yet built)",
        "Risk warnings and disclaimers wording (currently: “Estimates only, based on 2025/26 UK tax and benefit rates. Not financial advice.”)",
        "Vulnerable customers: content discusses death and serious illness; consider signposting (e.g. bereavement support) and gentler entry wording",
        "Complaints information and the regulatory status wording on the Adviser screen",
        "Annual review of tax and benefit figures; Scottish taxpayers (rates not modelled)",
        "Record keeping of approved versions and any changes after approval",
    ]

    articles_html = "".join(
        f"<div class='article'><h4>{e(a['title'])}</h4><p class='muted'>{e(a['category'])} · {a['read_minutes']} min · “{e(a['excerpt'])}”</p>"
        + "".join(f"<p>{e(p)}</p>" for p in a["body"]) + "</div>"
        for a in ARTICLES
    )

    return f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(app_name)} — Compliance Review Pack</title>
<style>
body{{font-family:Georgia,'Times New Roman',serif;color:#1E2B38;max-width:880px;margin:0 auto;padding:32px 24px;line-height:1.55;font-size:15px}}
h1{{font-size:34px;margin:0 0 8px;color:#223342}} h2{{color:#223342;border-bottom:2px solid #BF9B30;padding-bottom:6px;margin-top:40px;font-size:22px;page-break-after:avoid}}
h3{{color:#223342;font-size:17px;margin-top:24px}} h4{{margin:16px 0 6px}}
.cover{{background:#223342;color:#fff;padding:32px;border-radius:12px;margin-bottom:24px}} .cover h1{{color:#fff}} .gold{{color:#BF9B30}}
table{{width:100%;border-collapse:collapse;margin:12px 0;font-size:14px;font-family:Arial,sans-serif}} th{{background:#F4EEDC;text-align:left}}
th,td{{border:1px solid #E3E2E7;padding:8px;vertical-align:top}} .muted{{color:#6C7683}} code,pre{{font-family:Menlo,Consolas,monospace;font-size:12.5px}}
pre{{background:#F5F6F8;padding:14px;border-radius:8px;white-space:pre-wrap}} .letter{{border:1px solid #E3E2E7;border-radius:12px;padding:16px 20px}}
.hl{{background:#F6EED6;padding:10px;border-radius:8px}} .box{{background:#F5F6F8;border-left:4px solid #BF9B30;padding:12px 16px;border-radius:6px;font-family:Arial,sans-serif;font-size:14px}}
.article{{border-top:1px solid #E3E2E7;padding-top:8px}} li{{margin:4px 0}} .print{{font-family:Arial,sans-serif;background:#BF9B30;color:#1A2633;border:0;padding:10px 18px;border-radius:999px;font-size:14px;cursor:pointer}}
@media print{{.print{{display:none}} body{{padding:0}} h2{{page-break-before:auto}}}}
</style></head><body>
<button class="print" onclick="window.print()">Save as PDF / Print</button>
<div class="cover"><div class="gold">COMPLIANCE REVIEW PACK</div><h1>{e(app_name)}</h1>
<div>A mobile app that helps families understand their protection gap</div><br>
<div>Prepared for: {firm}, an Appointed Representative of {principal}</div>
<div>Adviser: {e(adviser['name'])}, {e(adviser.get('title', 'Senior Protection Specialist'))}</div>
<div>Generated: {now} · Status: <b>pre-launch, not publicly released</b></div></div>

<div class="box">This pack is generated directly from the app's live settings and content, so the wording, figures and instructions shown here are exactly what the app uses today.</div>

<h2>1. Summary</h2>
<p><b>Purpose.</b> {e(app_name)} helps UK adults with family responsibilities understand what would happen to their household financially if they died or could not work because of illness. It turns the numbers into real terms (dates, monthly shortfalls, children's milestones) and invites the user to speak to a regulated adviser.</p>
<p><b>Target users.</b> UK adults, typically parents or people with a partner, mortgage or rent.</p>
<p><b>What the app does NOT do:</b> it does not give personal recommendations, name products or providers, show prices or quotes, take applications or payments, or arrange cover. All advice happens in a separate conversation with the adviser.</p>
<p><b>Tone.</b> Deliberately emotional but balanced: it shows the impact on the family, celebrates good protection when it's in place, and always ends on a hopeful, no-pressure note (“This is fixable”).</p>

<h2>2. How to review the app</h2>
<ol>
<li><b>Recommended — private test builds:</b> once deployed, the app can be sent to reviewers through Apple <b>TestFlight</b> (iPhone) or as an Android test file, without appearing in any app store.</li>
<li><b>Alternative — Expo Go:</b> install the free “Expo Go” app, then scan the QR code the adviser shares from the deployed app.</li>
<li>Create an account with your own email address (password of at least 10 characters), complete a family check with sample figures, then read the full report, the Learn guides and the Adviser screen.</li>
<li>Please do not submit real personal details during review. Call-back requests are emailed to the adviser.</li>
</ol>

<h2>3. Customer journey</h2>
<ol>
<li><b>Welcome screen:</b> family photo; “The people you love deserve more than ‘it'll be fine’.” / “In five gentle minutes, see what life would really look like for your family if you weren't there — and how to make sure they're okay.”</li>
<li><b>Sign-up / sign-in:</b> first name, email, password.</li>
<li><b>Family check:</b> 12 short questions, one per screen (Section 4.1).</li>
<li><b>Report — “Your family's story”:</b> headline, savings runway bar, timeline of family milestones marked funded or unfunded, real-terms statements, AI-written letter, three gap cards (life, income protection, critical illness), invitation to speak to the adviser, disclaimer.</li>
<li><b>Learn:</b> five plain-English guides (Section 4.5).</li>
<li><b>Adviser:</b> adviser profile, “Book a call” (Calendly), tap-to-call, optional call-back form, regulatory status wording.</li>
<li><b>Profile:</b> saved reports, new check, log out.</li>
</ol>

<h2>4. Customer-facing wording</h2>
<h3>4.1 Family check questions</h3>{table(["#", "Question shown", "Information collected"], q_rows)}
<h3>4.2 Report headlines</h3>{table(["When", "Headline"], [(e(a), e(b)) for a, b in headlines])}
<h3>4.3 “What it would mean, in real terms” statements</h3>{table(["Statement", "Wording", "Shown when"], [(e(a), e(b), e(c)) for a, b, c in impacts_rows])}
<h3>4.4 Calls to action and disclaimers</h3>
<ul><li>Report: “This is fixable. Often for less than a weekly takeaway.” / “A friendly adviser can turn this story into a plan in one short call.” / button “Talk to someone who can help”.</li>
<li>Report footer: “Estimates only, based on 2025/26 UK tax and benefit rates. Not financial advice.”</li>
<li>Timeline marker: “The money runs out” — “Everything below this line, your family faces without you — and without money.” Later milestones are labelled “Unfunded”.</li>
<li>Adviser screen: “Hi, I'm {e(adviser['name'].split(' ')[0])}.” / “{e(adviser['bio'])}” / “Let's close the gap together.” / “Fifteen minutes on the phone is often all it takes…”</li>
<li>Regulatory status shown: “{firm} is an Appointed Representative of {principal}, which is authorised and regulated by the Financial Conduct Authority.”</li>
<li>Call-back confirmation: “Taking this step is the hardest part, and you've done it.”</li></ul>
<h3>4.5 Learn guides (full text)</h3>{articles_html}

<h2>5. Calculation method and assumptions</h2>
<h3>5.1 Figures used</h3>{table(["Item", "Figure", "Notes"], assumptions)}
<h3>5.2 Method</h3>{table(["Result", "How it is worked out"], [(e(a), e(b)) for a, b in method])}
<h3>5.3 Worked example</h3>
<p class="muted">Tom, 38, lives with Sarah (not married; she earns £24,000). Children Emma (7) and Leo (3). Tom earns £52,000; household spending £2,200/month; mortgage £240,000 at £1,250/month with 22 years left; other debts £8,000; savings £12,000; life cover £100,000; death-in-service 2× salary; 3 months' full sick pay; no income protection or critical illness cover.</p>
{table(["Result", "Value"], ex_rows)}<p><b>Statements shown:</b></p><ul>{ex_impacts}</ul>

<h2>6. AI-written letter</h2>
<p><b>What it is.</b> Each report includes a short letter written by an AI model (Anthropic Claude Sonnet 5.5, accessed through Emergent). It describes, in everyday scenes, what the gap would mean for the family. It is generated once per report and saved; it is not checked by a person before the user sees it.</p>
<p><b>Information sent to the AI:</b> first names and ages of the user, partner and children; relationship status; biggest worry; housing, mortgage, savings; and the calculated results. <b>Email address and phone number are never sent.</b></p>
<h3>6.1 Full instructions given to the AI</h3><pre>{e(story_prompt)}</pre>
<h3>6.2 Example output</h3>{story_html}
<h3>6.3 Limitations and current controls</h3>
<ul><li>The AI may occasionally phrase things imperfectly or misstate a detail; figures in the letter come from the calculation, but the wording is not pre-approved.</li>
<li>The instructions forbid hype, sales pressure and jargon, require British English, and require a hopeful ending.</li>
<li>Limited to {limits['story']} new letters per account per day.</li>
<li>Options for compliance: approve as is; add an on-screen label (e.g. “Written by AI from your answers”); require tighter instructions; or replace with fixed, pre-approved wording.</li></ul>

<h2>7. Data protection and security</h2>
<h3>7.1 Data collected</h3>{table(["Category", "Details", "Purpose"], [(e(a), e(b), e(c)) for a, b, c in data_rows])}
<h3>7.2 Third parties</h3>{table(["Party", "Role", "Notes"], processors)}
<h3>7.3 Security controls</h3><ul>{''.join(f'<li>{e(c)}</li>' for c in controls)}</ul>

<h2>8. Consumer Duty considerations</h2>
<ul><li><b>Consumer understanding:</b> plain English, one question per screen, results expressed in real terms (dates, monthly amounts, milestones) as well as totals.</li>
<li><b>Fair and balanced:</b> positive statements are shown where cover is adequate (“Your home would be safe”, “Your family could keep going”); the state safety net is explained in the guides.</li>
<li><b>No pressure:</b> no countdowns, discounts or urgency prompts; contacting the adviser is optional and can be done at any time.</li>
<li><b>Emotional content:</b> intentionally confronts death and illness to make the risk real. Reviewers should consider the effect on vulnerable or recently bereaved users (see open items).</li></ul>

<h2>9. Open items for compliance decision</h2>
<table><thead><tr><th>#</th><th>Item</th><th>Decision / notes</th></tr></thead><tbody>
{''.join(f'<tr><td>{i + 1}</td><td>{e(t)}</td><td style="width:35%"></td></tr>' for i, t in enumerate(open_items))}
</tbody></table>
<h3>Sign-off</h3>
<table><tbody><tr><td style="width:30%">Reviewed by</td><td></td></tr><tr><td>Role</td><td></td></tr><tr><td>Decision</td><td>Approved / Approved with changes / Not approved</td></tr><tr><td>Date</td><td></td></tr></tbody></table>
<p class="muted">Generated by {e(app_name)} on {now}.</p>
</body></html>"""
