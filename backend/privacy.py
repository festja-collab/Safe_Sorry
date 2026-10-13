"""Privacy notice text (draft for compliance review). Version bumps require re-acceptance."""

PRIVACY_VERSION = "2026-10-draft-1"


def privacy_sections(*, app_name: str, firm: dict, contact_email: str) -> list[dict]:
    fn = firm.get("firm_name") or "your adviser's firm"
    reg = f"{fn} (FRN {firm.get('fca_number', '')})"
    if firm.get("principal_name"):
        reg += f", an Appointed Representative of {firm['principal_name']} (FRN {firm.get('principal_fca_number', '')})"
    return [
        {"heading": "Who we are", "body": f"{app_name} is provided by {reg}. We are the data controller for the personal information you give us in this app. Questions? Email {contact_email}."},
        {"heading": "What we collect", "body": "Your name, email address and password (stored only in scrambled form). The answers you give in a family check: your age, your partner's and children's first names and ages, income, spending, mortgage or rent, savings, debts and existing cover. If you ask for a call: your phone number, best time to call and any message. We also keep basic technical records (such as your internet connection address) for up to 24 hours to protect the app from misuse."},
        {"heading": "Why we use it", "body": "To create your family report and save it to your account (to provide the service you asked for). To write your personal family letter using an AI service. To pass your details and report to your adviser when you ask for a call back, with your consent. To keep the app secure and prevent abuse (our legitimate interests). We do not use your information for automated decisions about you, and we do not sell it."},
        {"heading": "Who we share it with", "body": "Your adviser at " + fn + ", only if you ask them to contact you. Our technology providers, who process data on our behalf under contract: Emergent (app hosting and database), Anthropic (the AI that writes your family letter — it receives first names, ages and financial figures, never your email address or phone number) and our email delivery provider (to send your request to your adviser)."},
        {"heading": "How long we keep it", "body": "We keep your account and reports while your account is open. Call-back requests are kept for as long as needed to deal with your enquiry and meet our regulatory record-keeping duties. [Retention periods to be confirmed by compliance.]"},
        {"heading": "Your rights", "body": f"You can ask to see, correct or delete your information, object to how we use it, or withdraw your consent at any time by emailing {contact_email}. You can also complain to the Information Commissioner's Office (ico.org.uk, 0303 123 1113)."},
        {"heading": "Important", "body": f"{app_name} gives estimates for information only. It is not financial advice and does not recommend any product. Advice is only given by a qualified adviser after a full conversation."},
    ]
