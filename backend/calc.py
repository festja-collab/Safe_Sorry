"""UK protection gap engine. Turns numbers into real-world family impacts."""
from datetime import datetime, timezone
from typing import List, Optional

# All state figures are for the 2026/27 tax year (gov.uk benefit and pension rates 2026 to 2027).
TAX_YEAR = "2026/27"
FUNERAL = 5000
SSP_WEEKLY = 123.25          # or 80% of average weekly earnings if lower; payable from day one, up to 28 weeks
SSP_WEEKS = 28
ESA_WEEKLY = 95.55           # New Style ESA, age 25+; must be claimed, depends on NI record + Work Capability Assessment
ESA_MONTHS = 12              # contribution-based ESA (work-related activity group) is limited to 365 days
SSP_MONTHLY = SSP_WEEKLY * 52 / 12
ESA_MONTHLY = ESA_WEEKLY * 52 / 12
UNI_FEES_YEAR = 9535
WEEKLY_SHOP_MONTH = 120 * 52 / 12  # avg family food shop


def net_annual(gross: float, self_employed: bool = False) -> float:
    """Income tax (England/Wales/NI bands) + NI: Class 1 employee 8%/2%, or Class 4 self-employed 6%/2%."""
    if gross <= 0:
        return 0.0
    pa = 12570.0
    if gross > 100000:
        pa = max(0.0, pa - (gross - 100000) / 2)
    taxable = max(0.0, gross - pa)
    basic_band = 37700.0
    tax = min(taxable, basic_band) * 0.2
    if taxable > basic_band:
        higher = min(taxable, 125140 - pa) - basic_band
        tax += max(0.0, higher) * 0.4
    if gross > 125140:
        tax += (gross - 125140) * 0.45
    ni = 0.0
    if gross > 12570:
        ni += (min(gross, 50270) - 12570) * (0.06 if self_employed else 0.08)
    if gross > 50270:
        ni += (gross - 50270) * 0.02
    return gross - tax - ni


def _add_months(months: int) -> str:
    now = datetime.now(timezone.utc)
    y = now.year + (now.month - 1 + months) // 12
    m = (now.month - 1 + months) % 12 + 1
    return datetime(y, m, 1).strftime("%B %Y")


def _fmt(n: float) -> str:
    return f"£{round(n):,}"


def _duration(months: Optional[int]) -> str:
    if months is None:
        return "indefinitely"
    if months < 1:
        return "less than a month"
    if months < 24:
        return f"{months} month{'s' if months != 1 else ''}"
    y, mo = divmod(months, 12)
    return f"{y} years" + (f" and {mo} months" if mo else "")


def compute(a: dict) -> dict:
    income = float(a.get("annual_income") or 0)
    partner_income = float(a.get("partner_income") or 0)
    relationship = a.get("relationship", "single")
    has_partner = relationship in ("partner", "married")
    married = relationship == "married"
    partner = (a.get("partner_name") or "your partner").strip() or "your partner"
    kids: List[dict] = [k for k in (a.get("children") or []) if k.get("name") or k.get("age") is not None]
    outgoings = float(a.get("monthly_outgoings") or 0)
    housing = a.get("housing", "mortgage")
    housing_pay = float(a.get("monthly_housing") or 0)
    mortgage_bal = float(a.get("mortgage_balance") or 0) if housing == "mortgage" else 0.0
    mortgage_years = int(a.get("mortgage_years") or 0)
    debts = float(a.get("other_debts") or 0)
    savings = float(a.get("savings") or 0)
    life_cover = float(a.get("life_cover") or 0)
    dis = float(a.get("death_in_service") or 0) * income
    sick_months = float(a.get("sick_pay_months") or 0)
    ip_existing = float(a.get("income_protection") or 0)
    ci_existing = float(a.get("critical_illness") or 0)
    self_employed = a.get("employment") == "self_employed"

    user_net_m = net_annual(income, self_employed) / 12
    ssp_monthly = min(SSP_WEEKLY, 0.8 * income / 52) * 52 / 12
    partner_net_m = net_annual(partner_income) / 12 if has_partner else 0.0
    youngest = min([int(k.get("age") or 0) for k in kids], default=None)
    has_dependants = has_partner or bool(kids)

    # ---------- If you died ----------
    # Bereavement Support Payment: spouses/civil partners, and (since Feb 2023) cohabiting partners with dependent children
    if has_partner and kids:
        bsp_lump, bsp_month = 3500, 350
    elif married:
        bsp_lump, bsp_month = 2500, 100
    else:
        bsp_lump, bsp_month = 0, 0
    total_debt = mortgage_bal + debts
    pot = life_cover + dis + savings + bsp_lump - FUNERAL
    debts_cleared = pot >= total_debt
    if debts_cleared:
        pot -= total_debt
        monthly_cost = outgoings + (housing_pay if housing == "rent" else 0)
    else:
        monthly_cost = outgoings + (housing_pay if housing != "own" else 0)
    monthly_income = partner_net_m
    runway: Optional[int] = None
    if has_dependants:
        p = pot
        for m in range(1, 601):
            short = monthly_cost - monthly_income - (bsp_month if m <= 18 else 0)
            p -= short
            if p < 0:
                runway = m - 1
                break
    monthly_gap_death = max(0.0, monthly_cost - monthly_income)

    years_needed = 0
    if kids:
        years_needed = max(21 - (youngest or 0), 5)
    elif has_partner:
        years_needed = 5
    life_need = (
        total_debt + FUNERAL
        + max(0.0, (outgoings + (housing_pay if housing == "rent" else 0) - partner_net_m) * 12 * years_needed)
        - (bsp_lump + bsp_month * 18)
    )
    life_need = max(life_need, total_debt + FUNERAL)
    life_have = life_cover + dis + savings
    life_gap = max(0.0, life_need - life_have)

    # ---------- If you couldn't work ----------
    ill_need = outgoings + (housing_pay if housing != "own" else 0)
    ill_savings = savings
    ill_runway: Optional[int] = None
    for m in range(1, 601):
        ssp_end = 0 if self_employed else sick_months + SSP_WEEKS * 12 / 52
        if not self_employed and m <= sick_months:
            inc = user_net_m
        elif m <= ssp_end:
            inc = ssp_monthly
        elif m <= ssp_end + ESA_MONTHS:
            inc = ESA_MONTHLY  # only if eligible and claimed
        else:
            inc = 0.0
        inc += partner_net_m + ip_existing
        ill_savings -= ill_need - inc
        if ill_savings < 0:
            ill_runway = m - 1
            break
    ill_long_gap = max(0.0, ill_need - (partner_net_m + ip_existing))  # once sick pay and ESA have ended
    ip_need = round(income * 0.6 / 12)
    ip_gap = max(0.0, ip_need - ip_existing)

    # ---------- Critical illness ----------
    ci_need = max(2 * income, mortgage_bal)
    ci_gap = max(0.0, ci_need - ci_existing)

    # ---------- Real-terms impacts ----------
    impacts = []
    child_names = [k.get("name") or "your child" for k in kids]
    if has_dependants and runway is not None:
        ages = ", ".join(
            f"{k.get('name') or 'your child'} would be {int(k.get('age') or 0) + runway // 12}" for k in kids
        )
        impacts.append({
            "icon": "clock",
            "title": f"The money runs out by {_add_months(runway)}",
            "body": f"After {_duration(runway)}, everything you've left behind is gone." + (f" {ages}." if ages else ""),
            "tone": "error",
        })
    elif has_dependants:
        impacts.append({
            "icon": "sun",
            "title": "Your family could keep going",
            "body": f"With {partner}'s income and the cover you have, the money wouldn't run out. That's a gift.",
            "tone": "success",
        })
    if housing == "mortgage" and mortgage_bal > 0 and not debts_cleared:
        ratio = (housing_pay / partner_net_m * 100) if partner_net_m else None
        body = f"The {_fmt(mortgage_bal)} mortgage doesn't disappear. "
        if has_partner and ratio:
            body += f"{partner.capitalize() if partner == 'your partner' else partner} would need to find {_fmt(housing_pay)} every month — {round(ratio)}% of their take-home pay."
        else:
            body += f"Someone would need to find {_fmt(housing_pay)} every month to keep the house."
        impacts.append({"icon": "home", "title": "Your home is at risk", "body": body, "tone": "warning"})
    elif housing == "mortgage" and mortgage_bal > 0:
        impacts.append({"icon": "home", "title": "Your home would be safe", "body": "Your cover would clear the mortgage. They could stay in the home they know.", "tone": "success"})
    if has_dependants and monthly_gap_death > 0:
        shops = monthly_gap_death / WEEKLY_SHOP_MONTH * 4.33
        impacts.append({
            "icon": "shopping-bag",
            "title": f"{_fmt(monthly_gap_death)} missing every month",
            "body": f"That's roughly {round(shops)} weekly food shops a month your family would have to find — or go without.",
            "tone": "warning",
        })
    if has_partner and not married and not kids:
        impacts.append({
            "icon": "alert-circle",
            "title": "No Bereavement Support Payment",
            "body": f"Because you're not married or in a civil partnership and have no children together, {partner} wouldn't qualify for Bereavement Support Payment.",
            "tone": "error",
        })
    for k in kids:
        age = int(k.get("age") or 0)
        if age < 21:
            impacts.append({
                "icon": "heart",
                "title": f"{k.get('name') or 'Your child'} still needs you for {21 - age} years",
                "body": f"University alone could cost {_fmt(UNI_FEES_YEAR * 3)} in fees. Would that dream still be possible?",
                "tone": "info",
            })
    esa_note = (f"you may be able to claim New Style ESA, about {_fmt(ESA_MONTHLY)} a month for up to a year. "
                "It isn't automatic: it depends on your National Insurance record and a medical assessment.")
    ill_body = (
        "As self-employed, there's no sick pay. " + esa_note[0].upper() + esa_note[1:]
        if self_employed
        else f"Your employer pays you for {int(sick_months)} month{'s' if sick_months != 1 else ''}. Then Statutory Sick Pay of about "
             f"{_fmt(ssp_monthly)} a month for up to 28 weeks. After that, {esa_note}"
    )
    ill_body += f" Your savings would bridge the gap for {_duration(ill_runway)}."
    impacts.append({"icon": "activity", "title": "If you couldn't work", "body": ill_body, "tone": "warning" if ill_runway is not None else "success"})

    # ---------- Milestones timeline (months from now) ----------
    milestones = []
    for k in kids:
        age = int(k.get("age") or 0)
        nm = k.get("name") or "Your child"
        for target, label in ((11, "starts secondary school"), (16, "sits their GCSEs"), (18, "heads to university or work")):
            if age < target:
                milestones.append({"month": (target - age) * 12, "label": f"{nm} {label}", "kind": "child"})
    if housing == "mortgage" and mortgage_years > 0:
        milestones.append({"month": mortgage_years * 12, "label": "The mortgage is finally paid off", "kind": "home"})
    if runway is not None and has_dependants:
        milestones.append({"month": runway, "label": "The money runs out", "kind": "runout"})
    milestones.sort(key=lambda x: x["month"])
    for ms in milestones:
        ms["date"] = _add_months(ms["month"])
        ms["funded"] = runway is None or ms["month"] <= runway

    life_pct = min(100, round(life_have / life_need * 100)) if life_need else 100

    if not has_dependants:
        headline = "No one depends on your income — but your future self does."
    elif runway is None:
        headline = "Your family could stay on their feet. Let's keep it that way."
    elif runway < 12:
        headline = f"If you weren't here tomorrow, your family would have {_duration(runway)} before the money runs out."
    else:
        headline = f"Your family would be okay for {_duration(runway)}. Then what?"

    return {
        "tax_year": TAX_YEAR,
        "headline": headline,
        "has_dependants": has_dependants,
        "runway_months": runway,
        "runway_label": _duration(runway),
        "runout_date": _add_months(runway) if runway is not None else None,
        "illness_runway_months": ill_runway,
        "illness_runway_label": _duration(ill_runway),
        "monthly_gap_death": round(monthly_gap_death),
        "monthly_gap_illness": round(ill_long_gap),
        "user_net_monthly": round(user_net_m),
        "partner_net_monthly": round(partner_net_m),
        "debts_cleared": debts_cleared,
        "protected_pct": life_pct,
        "gaps": {
            "life": {"need": round(life_need), "have": round(life_have), "gap": round(life_gap)},
            "income": {"need": ip_need, "have": round(ip_existing), "gap": round(ip_gap), "monthly": True},
            "critical": {"need": round(ci_need), "have": round(ci_existing), "gap": round(ci_gap)},
        },
        "impacts": impacts,
        "milestones": milestones,
        "child_names": child_names,
    }
