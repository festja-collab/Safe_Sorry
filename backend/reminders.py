"""One gentle reminder email a month after someone completes a family check, with a one-click opt-out."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from html import escape

logger = logging.getLogger(__name__)

REMIND_AFTER = timedelta(days=30)
POLL_SECONDS = 3600
MAX_ATTEMPTS = 3


def reminder_html(*, app_name: str, first_name: str, base: str, report_id: str, unsub_url: str, reg: str) -> str:
    e = escape
    btn = ('display:inline-block;background:#BF9B30;color:#1A2633;padding:14px 24px;border-radius:999px;'
           'font-weight:bold;text-decoration:none;font-family:Arial,sans-serif')
    return (
        '<table role="presentation" width="100%" style="background:#FDFBF7">'
        '<tr><td align="center" bgcolor="#223342" style="background:#223342;padding:24px 16px">'
        f'<img src="{e(base)}/api/static/logos/logo_dark_transparent.png" width="120" alt="{e(app_name)}" '
        'style="display:block;width:120px;height:auto;border:0"></td></tr>'
        '<tr><td style="padding:28px 24px;font-family:Georgia,serif;color:#1E2B38;font-size:17px;line-height:1.6">'
        f'<p>Hi {e(first_name)},</p>'
        "<p>It's been about a month since you checked your family's safety net. We hope it gave you a clearer picture.</p>"
        "<p>Life moves quickly. If anything has changed, like a new baby, a house move, a new job or a change in pay, "
        "it's worth five minutes to look again.</p>"
        f'<p style="margin:28px 0"><a href="{e(base)}/report/{e(report_id)}" style="{btn}">View your report</a></p>'
        '<p style="font-family:Arial,sans-serif;font-size:13px;color:#6C7683;line-height:1.5">'
        'Estimates only. This is not regulated advice. Figures are illustrative, based on 2026/27 rates. '
        f'{e(reg)}</p>'
        '<p style="font-family:Arial,sans-serif;font-size:13px;color:#6C7683">This is the only reminder we send. '
        f'<a href="{e(unsub_url)}" style="color:#6C7683">Don\'t send me reminders</a></p>'
        '</td></tr></table>'
    )


async def send_due_reminders(db, *, send, build) -> int:
    """send(to, subject, html) sends; build(user_doc, assessment_doc) -> (subject, html). Returns emails sent."""
    from bson import ObjectId
    cutoff = (datetime.now(timezone.utc) - REMIND_AFTER).isoformat()
    sent = 0
    q = {"created_at": {"$lte": cutoff}, "origin": {"$nin": [None, ""]},
         "$or": [{"reminder_status": {"$exists": False}}, {"reminder_status": "failed", "reminder_attempts": {"$lt": MAX_ATTEMPTS}}]}
    async for a in db.assessments.find(q).limit(200):
        # Claim atomically so two workers never double-send
        claimed = await db.assessments.find_one_and_update(
            {"_id": a["_id"], "reminder_status": a.get("reminder_status", {"$exists": False})},
            {"$set": {"reminder_status": "sending"}})
        if not claimed:
            continue
        user = await db.users.find_one({"_id": ObjectId(a["user_id"])}) if ObjectId.is_valid(a["user_id"]) else None
        newer = await db.assessments.find_one({"user_id": a["user_id"], "created_at": {"$gt": a["created_at"]}})
        if not user or user.get("reminders_opt_out") or newer:
            await db.assessments.update_one({"_id": a["_id"]}, {"$set": {"reminder_status": "skipped"}})
            continue
        try:
            subject, html = await build(user, a)
            await send(user["email"], subject, html)
            await db.assessments.update_one({"_id": a["_id"]}, {"$set": {
                "reminder_status": "sent", "reminder_sent_at": datetime.now(timezone.utc).isoformat()}})
            sent += 1
        except Exception as ex:  # noqa: BLE001 - retry later, up to MAX_ATTEMPTS
            logger.warning(f"Reminder email failed: {ex}")
            await db.assessments.update_one({"_id": a["_id"]}, {"$set": {"reminder_status": "failed"},
                                                                 "$inc": {"reminder_attempts": 1}})
    return sent


async def reminder_loop(db, *, send, build):
    while True:
        try:
            n = await send_due_reminders(db, send=send, build=build)
            if n:
                logger.info(f"Sent {n} report reminder(s)")
        except Exception as ex:  # noqa: BLE001 - keep the loop alive
            logger.error(f"Reminder loop error: {ex}")
        await asyncio.sleep(POLL_SECONDS)
