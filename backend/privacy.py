"""Privacy notice text (draft for compliance review). Version bumps require re-acceptance."""
from regulatory import regulatory_status

PRIVACY_VERSION = "2026-10-draft-2"

NOT_ADVICE = ("Please note this is not regulated advice. This Application will only provide you with an AI produced letter "
              "setting out any Life Cover requirements you may have. When you have the meeting with the adviser, we will then "
              "be able to advise you fully, based on your circumstances.")


def privacy_sections(*, app_name: str, firm: dict, contact_email: str) -> list[dict]:
    fn = firm.get("firm_name") or "your adviser's firm"
    status = regulatory_status(firm)
    return [
        {"heading": "Who we are", "body": f"{app_name} is provided by {fn}. {fn} is the data controller for the personal information you give us in this app. Questions? Email {contact_email}. Regulatory status: {status}"},
        {"heading": "What we collect", "body": "Your name, email address and password (stored only in scrambled form). The answers you give in a family check: your age, your partner's and children's first names and ages, income, spending, mortgage or rent, savings, debts and existing cover. If you ask for a call: your phone number, best time to call and any message. We also keep basic technical records (such as your internet connection address) for up to 24 hours to protect the app from misuse."},
        {"heading": "Why we use it", "body": "To create your family report and save it to your account (to provide the service you asked for). To write your personal family letter using an AI tool. To pass your details and report to your adviser when you ask for a call back, with your consent. To keep the app secure and prevent abuse (our legitimate interests). We do not use your information for automated decisions about you, and we do not sell it."},
        {"heading": "The AI tool", "body": "Your family letter is written by an AI tool (Anthropic's Claude). Before anything is sent, names are replaced with placeholders, so the AI only receives ages and financial figures: never your name, your family's names, your email address or your phone number. The AI provider does not use this information to train its models and deletes it within 30 days."},
        {"heading": "Who we share it with", "body": f"Your adviser at {fn}, only if you ask them to contact you. Our technology providers, who process data on our behalf: Emergent (app hosting and database), Anthropic (the AI tool, which receives no names or contact details) and our email delivery provider (to send your request to your adviser)."},
        {"heading": "How long we keep it", "body": "We keep your account and reports while your account is open. Call-back requests are kept for as long as needed to deal with your enquiry and meet our regulatory record-keeping duties. [Retention periods to be confirmed by compliance.]"},
        {"heading": "Deleting your data", "body": f"You can delete your account and everything in it at any time: Profile → Delete my account and data. This removes your account, all your family checks and letters, and any call-back requests. You'll get a reference number confirming it's done. You can also ask us by emailing {contact_email}."},
        {"heading": "Your rights", "body": f"You can ask to see, correct or delete your information, object to how we use it, or withdraw your consent at any time by emailing {contact_email}. You can also complain to the Information Commissioner's Office (ico.org.uk, 0303 123 1113)."},
        {"heading": "Important", "body": NOT_ADVICE},
    ]
