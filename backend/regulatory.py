"""Single source of the regulatory status sentence shown everywhere (app, web pages, emails, marketing)."""


def regulatory_status(p: dict) -> str:
    """p has firm_name, fca_number, principal_name, principal_fca_number and optional trading_name."""
    firm = p.get("firm_name") or ""
    if not firm:
        return ""
    firm += f" (FRN {p['fca_number']})" if p.get("fca_number") else ""
    tn = p.get("trading_name") or ""
    if p.get("principal_name"):
        principal = p["principal_name"] + (f" (FRN {p['principal_fca_number']})" if p.get("principal_fca_number") else "")
        tail = f"an Appointed Representative of {principal}, which is authorised and regulated by the Financial Conduct Authority."
        return f"{tn} is a trading style of {firm}, which is {tail}" if tn else f"{firm} is {tail}"
    tail = "authorised and regulated by the Financial Conduct Authority."
    return f"{tn} is a trading style of {firm}, which is {tail}" if tn else f"{firm} is {tail}"


# Default firm wording for marketing assets (reels, carousels, posting plan).
SFL_STATUS = regulatory_status({
    "trading_name": "Safe > Sorry", "firm_name": "Secure for Life Wealth Management Ltd", "fca_number": "912517",
    "principal_name": "Rosemount Financial Solutions (IFA) Limited", "principal_fca_number": "535515"})
