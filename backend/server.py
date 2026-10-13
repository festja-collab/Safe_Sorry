from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, BeforeValidator, ConfigDict
from typing import List, Optional, Annotated
from datetime import datetime, timezone, timedelta
from pathlib import Path
from html import escape
from bson import ObjectId
import os
import re
import json
import uuid
import asyncio
import secrets
import logging
from pymongo.errors import DuplicateKeyError
import bcrypt
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from calc import compute  # noqa: E402
from articles import ARTICLES  # noqa: E402
from emailer import send_email  # noqa: E402
from compliance_pack import build_pack  # noqa: E402
from invite import invite_page  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
import limiter  # noqa: E402
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone  # noqa: E402

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
JWT_SECRET = os.environ["JWT_SECRET"]
EMERGENT_LLM_KEY = os.environ["EMERGENT_LLM_KEY"]
ADVISER_EMAIL = os.environ["ADVISER_EMAIL"]
CALENDLY_URL = os.environ["CALENDLY_URL"]
APP_NAME = os.environ["APP_NAME"]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()
api = APIRouter(prefix="/api")
bearer = HTTPBearer(auto_error=False)

PyObjectId = Annotated[str, BeforeValidator(str)]


class BaseDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    @classmethod
    def from_mongo(cls, doc: dict):
        return cls.model_validate(doc)

    def to_mongo(self) -> dict:
        d = self.model_dump(by_alias=True)
        d.pop("_id", None)
        return d


class User(BaseDocument):
    email: str
    name: str
    password_hash: str
    created_at: str
    role: str = "client"                 # "client" | "adviser"
    adviser_id: Optional[str] = None     # clients: linked adviser
    firm_id: Optional[str] = None
    is_firm_admin: bool = False
    # Adviser profile (advisers only)
    title: str = ""
    bio: str = ""
    photo_url: str = ""
    phone: str = ""
    calendly_url: str = ""
    lead_email: str = ""
    adviser_code: Optional[str] = None
    password_version: int = 0
    must_change_password: bool = False
    # Attribution (clients)
    signup_code: str = ""      # full code entered, e.g. MARK-SFL-FB
    signup_source: str = ""    # suffix, e.g. FB / INV
    heard_from: str = ""


class Firm(BaseDocument):
    code: str
    name: str
    fca_number: str = ""
    principal_name: str = ""
    principal_fca_number: str = ""
    created_at: str


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    adviser_code: str = Field(default="", max_length=40)
    heard_from: str = Field(default="", max_length=40)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class Child(BaseModel):
    name: str = ""
    age: int = Field(ge=0, le=30, default=0)


class AssessmentIn(BaseModel):
    first_name: str = ""
    age: int = Field(ge=16, le=90, default=35)
    relationship: str = "single"
    partner_name: str = ""
    partner_income: float = Field(ge=0, default=0)
    children: List[Child] = []
    employment: str = "employed"
    annual_income: float = Field(ge=0, default=0)
    monthly_outgoings: float = Field(ge=0, default=0)
    housing: str = "mortgage"
    mortgage_balance: float = Field(ge=0, default=0)
    monthly_housing: float = Field(ge=0, default=0)
    mortgage_years: int = Field(ge=0, le=50, default=0)
    other_debts: float = Field(ge=0, default=0)
    savings: float = Field(ge=0, default=0)
    life_cover: float = Field(ge=0, default=0)
    death_in_service: float = Field(ge=0, le=10, default=0)
    sick_pay_months: float = Field(ge=0, le=24, default=0)
    income_protection: float = Field(ge=0, default=0)
    critical_illness: float = Field(ge=0, default=0)
    worry: str = ""


class Assessment(BaseDocument):
    user_id: str
    inputs: dict
    results: dict
    story: Optional[dict] = None
    created_at: str


class LeadIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=6, max_length=30)
    preferred_time: str = Field(default="", max_length=40)
    message: str = Field(default="", max_length=1000)
    assessment_id: Optional[str] = None


class Lead(BaseDocument):
    user_id: str
    email: str
    name: str
    phone: str
    preferred_time: str
    message: str
    assessment_id: Optional[str] = None
    adviser_id: Optional[str] = None
    firm_id: Optional[str] = None
    status: str = "new"                  # new | contacted | closed
    source_code: str = ""
    source: str = ""
    heard_from: str = ""
    email_sent: bool = False
    created_at: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- Abuse limits ----
DAY = 86400
LOGIN_WINDOW = 15 * 60
LOGIN_IP_LIMIT, LOGIN_EMAIL_LIMIT = 10, 5      # failed logins per 15 min
REGISTER_IP_LIMIT = 5                          # new accounts per IP per hour
ASSESSMENTS_PER_DAY = 5                        # per account
STORIES_PER_DAY = 5                            # AI stories per account
LEADS_PER_DAY = 3                              # call-back requests per account
DUMMY_HASH = bcrypt.hashpw(b"timing-equaliser", bcrypt.gensalt()).decode()


def make_token(user_id: str, pwdv: int = 0) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": user_id, "iat": now, "exp": now + timedelta(days=7), "pwdv": pwdv}, JWT_SECRET, algorithm="HS256")


def public_user(u: User) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name, "role": u.role, "is_firm_admin": u.is_firm_admin,
            "adviser_code": u.adviser_code if u.role == "adviser" else None,
            "must_change_password": u.must_change_password}


def source_label(source: str, code: str) -> str:
    if source == "INV":
        return "Invite link"
    if source:
        return f"Campaign: {source}"
    if code:
        return "Adviser code"
    return "No code"


async def session_user(c: HTTPAuthorizationCredentials = Depends(bearer)) -> User:
    """Valid session, even if a password change is still required."""
    if not c:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(c.credentials, JWT_SECRET, algorithms=["HS256"], options={"require": ["sub", "iat", "exp"]})
        doc = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    except Exception:
        doc = None
    # Tokens are revoked when the password changes (password_version bump)
    if not doc or payload.get("pwdv", 0) != doc.get("password_version", 0):
        raise HTTPException(401, "Invalid or expired session")
    return User.from_mongo(doc)


async def current_user(user: User = Depends(session_user)) -> User:
    if user.must_change_password:
        raise HTTPException(403, "Please set a new password to continue")
    return user


@api.get("/")
async def root():
    return {"message": f"{APP_NAME} API"}


@api.get("/config")
async def config():
    return {"app_name": APP_NAME}


# ---------------- Firms & advisers ----------------
async def find_adviser_by_code(code: str) -> Optional[User]:
    doc = await db.users.find_one({"adviser_code": code.strip().upper(), "role": "adviser"})
    return User.from_mongo(doc) if doc else None


async def resolve_code(code: str) -> tuple[Optional[User], str]:
    """MARK-SFL -> (Mark, ""); MARK-SFL-FB -> (Mark, "FB") for campaign/invite tracking."""
    c = code.strip().upper()
    a = await find_adviser_by_code(c)
    if a:
        return a, ""
    if "-" in c:
        base, src = c.rsplit("-", 1)
        if re.fullmatch(r"[A-Z0-9]{1,12}", src):
            a = await find_adviser_by_code(base)
            if a:
                return a, src
    return None, ""


async def default_adviser() -> User:
    doc = await db.users.find_one({"email": os.environ["DEFAULT_ADVISER_EMAIL"].lower(), "role": "adviser"})
    return User.from_mongo(doc)


async def adviser_for(user: User) -> User:
    if user.role == "adviser":
        return user
    if user.adviser_id:
        doc = await db.users.find_one({"_id": ObjectId(user.adviser_id), "role": "adviser"})
        if doc:
            return User.from_mongo(doc)
    return await default_adviser()


async def get_firm(firm_id: Optional[str]) -> Optional[Firm]:
    doc = await db.firms.find_one({"_id": ObjectId(firm_id)}) if firm_id else None
    return Firm.from_mongo(doc) if doc else None


async def adviser_profile(a: User) -> dict:
    f = await get_firm(a.firm_id)
    return {
        "id": a.id, "name": a.name, "title": a.title, "bio": a.bio, "photo_url": a.photo_url, "phone": a.phone,
        "calendly_url": a.calendly_url, "email": a.lead_email or a.email, "adviser_code": a.adviser_code,
        "firm_name": f.name if f else "", "fca_number": f.fca_number if f else "",
        "principal_name": f.principal_name if f else "", "principal_fca_number": f.principal_fca_number if f else "",
    }



@api.post("/auth/register")
async def register(body: RegisterIn, request: Request):
    await limiter.take(db.rate_limits, namespace="register-ip", key=limiter.client_ip(request), limit=REGISTER_IP_LIMIT,
                       window=3600, message="Too many accounts created from this connection. Please try again later.")
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(409, "An account with this email already exists")
    source = ""
    if body.adviser_code.strip():
        adviser, source = await resolve_code(body.adviser_code)
        if not adviser:
            raise HTTPException(400, "We couldn't find that adviser code. Please check it or leave it blank.")
    else:
        adviser = await default_adviser()
    pw = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    user = User(email=email, name=body.name.strip(), password_hash=pw, created_at=now_iso(),
                adviser_id=adviser.id, firm_id=adviser.firm_id, signup_code=body.adviser_code.strip().upper(),
                signup_source=source, heard_from=body.heard_from.strip())
    res = await db.users.insert_one(user.to_mongo())
    user.id = str(res.inserted_id)
    return {"token": make_token(user.id, 0), "user": public_user(user)}


@api.post("/auth/login")
async def login(body: LoginIn, request: Request):
    email = body.email.lower()
    ip = limiter.client_ip(request)
    msg = "Too many sign-in attempts. Please wait 15 minutes and try again."
    await limiter.check(db.rate_limits, namespace="login-fail-ip", key=ip, limit=LOGIN_IP_LIMIT, window=LOGIN_WINDOW, message=msg)
    await limiter.check(db.rate_limits, namespace="login-fail-email", key=email, limit=LOGIN_EMAIL_LIMIT, window=LOGIN_WINDOW, message=msg)
    doc = await db.users.find_one({"email": email})
    ok = bcrypt.checkpw(body.password.encode(), (doc["password_hash"] if doc else DUMMY_HASH).encode())
    if not doc or not ok:
        await limiter.record(db.rate_limits, namespace="login-fail-ip", key=ip, window=LOGIN_WINDOW)
        await limiter.record(db.rate_limits, namespace="login-fail-email", key=email, window=LOGIN_WINDOW)
        raise HTTPException(401, "Incorrect email or password")
    user = User.from_mongo(doc)
    return {"token": make_token(user.id, user.password_version), "user": public_user(user)}


@api.get("/auth/me")
async def me(user: User = Depends(session_user)):
    return public_user(user)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


@api.post("/auth/change-password")
async def change_password(body: ChangePasswordIn, user: User = Depends(session_user)):
    msg = "Too many attempts. Please wait 15 minutes and try again."
    await limiter.check(db.rate_limits, namespace="pwchange-fail", key=user.id, limit=5, window=LOGIN_WINDOW, message=msg)
    if not bcrypt.checkpw(body.current_password.encode(), user.password_hash.encode()):
        await limiter.record(db.rate_limits, namespace="pwchange-fail", key=user.id, window=LOGIN_WINDOW)
        raise HTTPException(400, "Your current password isn't right")
    if body.current_password == body.new_password:
        raise HTTPException(400, "Please choose a different password from your current one")
    res = await db.users.update_one(
        {"_id": ObjectId(user.id), "password_version": user.password_version},
        {"$set": {"password_hash": bcrypt.hashpw(body.new_password.encode(), bcrypt.gensalt()).decode(),
                  "must_change_password": False}, "$inc": {"password_version": 1}},
    )
    if res.modified_count != 1:
        raise HTTPException(409, "Your password was just changed. Please sign in again.")
    fresh = User.from_mongo(await db.users.find_one({"_id": ObjectId(user.id)}))
    # Old tokens (all devices) are now revoked; this device gets a fresh one
    return {"token": make_token(fresh.id, fresh.password_version), "user": public_user(fresh)}


def assessment_out(a: Assessment) -> dict:
    return {"id": a.id, "inputs": a.inputs, "results": a.results, "story": a.story, "created_at": a.created_at}


@api.post("/assessments")
async def create_assessment(body: AssessmentIn, user: User = Depends(current_user)):
    await limiter.take(db.rate_limits, namespace="assess-user", key=user.id, limit=ASSESSMENTS_PER_DAY, window=DAY,
                       message=f"You've reached today's limit of {ASSESSMENTS_PER_DAY} family checks. Please come back tomorrow.")
    inputs = body.model_dump()
    a = Assessment(user_id=user.id, inputs=inputs, results=compute(inputs), created_at=now_iso())
    res = await db.assessments.insert_one(a.to_mongo())
    a.id = str(res.inserted_id)
    return assessment_out(a)


@api.get("/assessments")
async def list_assessments(user: User = Depends(current_user)):
    docs = await db.assessments.find({"user_id": user.id}).sort("created_at", -1).to_list(100)
    out = []
    for d in docs:
        a = Assessment.from_mongo(d)
        out.append({
            "id": a.id,
            "created_at": a.created_at,
            "headline": a.results.get("headline"),
            "runway_label": a.results.get("runway_label"),
            "runway_months": a.results.get("runway_months"),
            "protected_pct": a.results.get("protected_pct"),
            "life_gap": a.results.get("gaps", {}).get("life", {}).get("gap"),
            "has_dependants": a.results.get("has_dependants"),
        })
    return out


async def get_owned(aid: str, user: User) -> Assessment:
    try:
        doc = await db.assessments.find_one({"_id": ObjectId(aid), "user_id": user.id})
    except Exception:
        doc = None
    if not doc:
        raise HTTPException(404, "Assessment not found")
    return Assessment.from_mongo(doc)


@api.get("/assessments/{aid}")
async def get_assessment(aid: str, user: User = Depends(current_user)):
    if user.role == "adviser":
        lead = await db.leads.find_one({"assessment_id": aid, "adviser_id": user.id})
        doc = await db.assessments.find_one({"_id": ObjectId(aid), "user_id": lead["user_id"]}) if lead else None
        if not doc:
            raise HTTPException(404, "Assessment not found")
        return assessment_out(Assessment.from_mongo(doc))
    return assessment_out(await get_owned(aid, user))


@api.delete("/assessments/{aid}")
async def delete_assessment(aid: str, user: User = Depends(current_user)):
    a = await get_owned(aid, user)
    await db.assessments.delete_one({"_id": ObjectId(a.id)})
    return {"ok": True}


STORY_SYSTEM = """You are a compassionate UK protection adviser and gifted writer for the app "Safe > Sorry".
You write short, deeply human stories that help a parent or partner FEEL what an unprotected gap would mean for the people they love - not just see numbers.
Rules:
- Second person ("you"), warm, honest, gentle but unflinching. British English. No cliches, no hype, no sales pressure, no jargon.
- Use the family's real names and ages. Paint concrete everyday scenes (school runs, the kitchen table, birthdays, the front door of their home).
- Weave in at most 3 key numbers naturally (e.g. the month the money runs out, the monthly shortfall, the mortgage).
- If the family is well protected, celebrate it honestly and mention any remaining weak spot.
- If they have no dependants, focus on their own future self and illness risk.
- End with hope: this is fixable, often for less than a weekly takeaway.
Return ONLY valid JSON: {"title": str (max 8 words), "paragraphs": [3 strings, each 45-75 words], "closing": str (max 25 words)}"""


@api.post("/assessments/{aid}/story")
async def story(aid: str, user: User = Depends(current_user)):
    a = await get_owned(aid, user)
    if a.story:
        return a.story
    await limiter.take(db.rate_limits, namespace="story-user", key=user.id, limit=STORIES_PER_DAY, window=DAY,
                       message="You've reached today's limit for new stories. Please try again tomorrow.")
    i, r = a.inputs, a.results
    facts = {
        "name": i.get("first_name") or user.name,
        "age": i.get("age"),
        "relationship": i.get("relationship"),
        "partner_name": i.get("partner_name"),
        "children": i.get("children"),
        "biggest_worry": i.get("worry"),
        "housing": i.get("housing"),
        "monthly_mortgage_or_rent": i.get("monthly_housing"),
        "mortgage_balance": i.get("mortgage_balance"),
        "savings": i.get("savings"),
        "if_they_died": {
            "money_runs_out_after": r.get("runway_label"),
            "runout_date": r.get("runout_date"),
            "monthly_shortfall": r.get("monthly_gap_death"),
            "mortgage_cleared_by_existing_cover": r.get("debts_cleared"),
            "life_cover_gap": r["gaps"]["life"]["gap"],
        },
        "if_they_could_not_work": {
            "savings_last": r.get("illness_runway_label"),
            "long_term_monthly_shortfall": r.get("monthly_gap_illness"),
        },
        "critical_illness_gap": r["gaps"]["critical"]["gap"],
        "upcoming_milestones": [m["label"] + " (" + m["date"] + ")" for m in r.get("milestones", [])][:6],
    }
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"story-{aid}-{uuid.uuid4()}",
                   system_message=STORY_SYSTEM).with_model("anthropic", "claude-sonnet-5-5")

    async def run() -> str:
        text = ""
        async for ev in chat.stream_message(UserMessage(text="Write the story for this family:\n" + json.dumps(facts, default=str))):
            if isinstance(ev, TextDelta):
                text += ev.content
            elif isinstance(ev, StreamDone):
                break
        return text

    try:
        raw = await asyncio.wait_for(run(), timeout=90)
        m = re.search(r"\{.*\}", raw, re.S)
        data = json.loads(m.group(0) if m else raw)
        result = {
            "title": str(data.get("title", "Your family's story")),
            "paragraphs": [str(p) for p in data.get("paragraphs", [])][:4],
            "closing": str(data.get("closing", "")),
        }
        if not result["paragraphs"]:
            raise ValueError("empty story")
    except Exception as e:
        logger.error(f"Story generation failed: {e}")
        raise HTTPException(502, "We couldn't write your story just now. Please try again.")
    await db.assessments.update_one({"_id": ObjectId(a.id)}, {"$set": {"story": result}})
    return result


@api.get("/articles")
async def articles():
    return [{k: v for k, v in a.items() if k != "body"} for a in ARTICLES]


@api.get("/compliance-pack", response_class=HTMLResponse)
async def compliance_pack():
    adviser = await adviser_profile(await default_adviser())
    return await build_pack(app_name=APP_NAME, adviser=adviser, story_prompt=STORY_SYSTEM,
                            limits={"assess": ASSESSMENTS_PER_DAY, "story": STORIES_PER_DAY, "leads": LEADS_PER_DAY})


@api.get("/invite/{code}", response_class=HTMLResponse)
async def invite_landing(code: str, name: str = ""):
    adviser = await find_adviser_by_code(code)
    if not adviser:
        raise HTTPException(404, "Invite not found")
    return invite_page(app_name=APP_NAME, adviser=await adviser_profile(adviser), name=name.strip()[:40],
                       code_display=f"{adviser.adviser_code}-INV", ad=False,
                       ios_url=os.environ.get("IOS_APP_URL", ""), android_url=os.environ.get("ANDROID_APP_URL", ""))


@api.get("/start", response_class=HTMLResponse)
@api.get("/start/{code}", response_class=HTMLResponse)
async def ad_landing(code: str = "", src: str = ""):
    adviser = await find_adviser_by_code(code) if code else await default_adviser()
    if not adviser:
        raise HTTPException(404, "Page not found")
    tag = re.sub(r"[^A-Z0-9]", "", src.upper())[:12]
    return invite_page(app_name=APP_NAME, adviser=await adviser_profile(adviser), name="",
                       code_display=f"{adviser.adviser_code}-{tag}" if tag else adviser.adviser_code, ad=True,
                       ios_url=os.environ.get("IOS_APP_URL", ""), android_url=os.environ.get("ANDROID_APP_URL", ""))


@api.get("/articles/{slug}")
async def article(slug: str):
    for a in ARTICLES:
        if a["slug"] == slug:
            return a
    raise HTTPException(404, "Article not found")


def lead_email_html(lead: Lead, summary: Optional[dict], firm_name: str) -> str:
    rows = [("Name", lead.name), ("Email", lead.email), ("Phone", lead.phone),
            ("Best time", lead.preferred_time or "Any"), ("Message", lead.message or "-")]
    if summary:
        g = summary.get("gaps", {})
        rows += [
            ("Family runway", summary.get("runway_label", "-")),
            ("Life cover gap", f"£{g.get('life', {}).get('gap', 0):,}"),
            ("Income protection gap", f"£{g.get('income', {}).get('gap', 0):,}/month"),
            ("Critical illness gap", f"£{g.get('critical', {}).get('gap', 0):,}"),
        ]
    trs = "".join(
        f'<tr><td style="padding:6px 12px;color:#7D7973">{escape(k)}</td>'
        f'<td style="padding:6px 12px;color:#2C2A28">{escape(str(v))}</td></tr>'
        for k, v in rows
    )
    return (
        '<table role="presentation" width="100%" style="background:#FDFBF7"><tr><td style="padding:24px;font-family:Arial,sans-serif">'
        '<h2 style="color:#2C2A28;margin:0 0 12px">New adviser request</h2>'
        f'<p style="color:#3A3835">A {escape(APP_NAME)} user would like to talk about protecting their family.</p>'
        f'<table role="presentation" style="border-collapse:collapse">{trs}</table>'
        f'<p style="font-size:12px;color:#888;margin-top:24px">Sent by {escape(APP_NAME)} for {escape(firm_name)}.</p>'
        '</td></tr></table>'
    )


@api.post("/leads")
async def create_lead(body: LeadIn, user: User = Depends(current_user)):
    await limiter.take(db.rate_limits, namespace="lead-user", key=user.id, limit=LEADS_PER_DAY, window=DAY,
                       message="We've already got your request. Your adviser will be in touch soon.")
    summary = (await get_owned(body.assessment_id, user)).results if body.assessment_id else None
    adviser = await adviser_for(user)
    firm = await get_firm(adviser.firm_id)
    lead = Lead(user_id=user.id, email=user.email, name=body.name.strip(), phone=body.phone.strip(),
                preferred_time=body.preferred_time, message=body.message, assessment_id=body.assessment_id,
                adviser_id=adviser.id, firm_id=adviser.firm_id, created_at=now_iso(),
                source_code=user.signup_code, source=user.signup_source, heard_from=user.heard_from)
    res = await db.leads.insert_one(lead.to_mongo())
    lead.id = str(res.inserted_id)
    try:
        await send_email(to=adviser.lead_email or adviser.email, subject=f"New {APP_NAME} adviser request: {lead.name}",
                         html=lead_email_html(lead, summary, firm.name if firm else APP_NAME), reply_to=user.email)
        await db.leads.update_one({"_id": ObjectId(lead.id)}, {"$set": {"email_sent": True}})
        lead.email_sent = True
    except Exception as e:
        logger.error(f"Lead email failed: {e}")
    return {"id": lead.id, "email_sent": lead.email_sent}


@api.get("/my-adviser")
async def my_adviser(user: User = Depends(current_user)):
    return await adviser_profile(await adviser_for(user))


class LinkAdviserIn(BaseModel):
    code: str = Field(min_length=2, max_length=40)


@api.post("/me/adviser")
async def link_adviser(body: LinkAdviserIn, user: User = Depends(current_user)):
    if user.role != "client":
        raise HTTPException(400, "Adviser accounts can't link to another adviser")
    adviser, _ = await resolve_code(body.code)
    if not adviser:
        raise HTTPException(404, "We couldn't find that adviser code")
    await db.users.update_one({"_id": ObjectId(user.id)}, {"$set": {"adviser_id": adviser.id, "firm_id": adviser.firm_id}})
    return await adviser_profile(adviser)


async def adviser_user(user: User = Depends(current_user)) -> User:
    if user.role != "adviser":
        raise HTTPException(403, "Adviser access only")
    return user


def lead_out(d: dict) -> dict:
    lead = Lead.from_mongo(d)
    return {"id": lead.id, "name": lead.name, "email": lead.email, "phone": lead.phone, "preferred_time": lead.preferred_time,
            "message": lead.message, "status": lead.status, "created_at": lead.created_at, "assessment_id": lead.assessment_id,
            "source_code": lead.source_code, "source_label": source_label(lead.source, lead.source_code), "heard_from": lead.heard_from}


@api.get("/adviser/leads")
async def adviser_leads(status: Optional[str] = None, me: User = Depends(adviser_user)):
    q = {"adviser_id": me.id}
    if status in ("new", "contacted", "closed"):
        q["status"] = status
    docs = await db.leads.find(q).sort("created_at", -1).to_list(500)
    ids = [ObjectId(d["assessment_id"]) for d in docs if d.get("assessment_id")]
    summaries = {}
    if ids:
        for a in await db.assessments.find({"_id": {"$in": ids}}).to_list(500):
            r = a.get("results", {})
            summaries[str(a["_id"])] = {"headline": r.get("headline"), "protected_pct": r.get("protected_pct"),
                                        "life_gap": r.get("gaps", {}).get("life", {}).get("gap")}
    return [{**lead_out(d), "summary": summaries.get(d.get("assessment_id") or "")} for d in docs]


async def owned_lead(lid: str, me: User) -> dict:
    try:
        d = await db.leads.find_one({"_id": ObjectId(lid), "adviser_id": me.id})
    except Exception:
        d = None
    if not d:
        raise HTTPException(404, "Lead not found")
    return d


@api.get("/adviser/leads/{lid}")
async def adviser_lead(lid: str, me: User = Depends(adviser_user)):
    d = await owned_lead(lid, me)
    out = lead_out(d)
    out["assessment"] = None
    if d.get("assessment_id"):
        a = await db.assessments.find_one({"_id": ObjectId(d["assessment_id"]), "user_id": d["user_id"]})
        if a:
            out["assessment"] = assessment_out(Assessment.from_mongo(a))
    return out


class LeadStatusIn(BaseModel):
    status: str = Field(pattern="^(new|contacted|closed)$")


@api.patch("/adviser/leads/{lid}")
async def update_lead(lid: str, body: LeadStatusIn, me: User = Depends(adviser_user)):
    d = await owned_lead(lid, me)
    await db.leads.update_one({"_id": d["_id"], "adviser_id": me.id}, {"$set": {"status": body.status}})
    return {"ok": True, "status": body.status}


@api.get("/adviser/stats")
async def adviser_stats(me: User = Depends(adviser_user)):
    counts = {s: await db.leads.count_documents({"adviser_id": me.id, "status": s}) for s in ("new", "contacted", "closed")}
    clients = await db.users.count_documents({"adviser_id": me.id, "role": "client"})
    by_source: dict = {}
    async for d in db.leads.find({"adviser_id": me.id}, {"source": 1, "source_code": 1, "heard_from": 1}):
        k = source_label(d.get("source", ""), d.get("source_code", ""))
        by_source[k] = by_source.get(k, 0) + 1
    by_heard: dict = {}
    async for d in db.leads.find({"adviser_id": me.id, "heard_from": {"$nin": ["", None]}}, {"heard_from": 1}):
        by_heard[d["heard_from"]] = by_heard.get(d["heard_from"], 0) + 1
    return {**counts, "total": sum(counts.values()), "clients": clients,
            "by_source": [{"label": k, "count": v} for k, v in sorted(by_source.items(), key=lambda x: -x[1])],
            "by_heard": [{"label": k, "count": v} for k, v in sorted(by_heard.items(), key=lambda x: -x[1])]}


class NewAdviserIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    title: str = Field(default="Protection Adviser", max_length=80)


async def firm_admin(me: User = Depends(adviser_user)) -> User:
    if not me.is_firm_admin or not me.firm_id:
        raise HTTPException(403, "Only your firm's administrator can manage advisers")
    return me


@api.get("/firm/advisers")
async def list_firm_advisers(me: User = Depends(firm_admin)):
    out = []
    async for d in db.users.find({"firm_id": me.firm_id, "role": "adviser"}).sort("created_at", 1):
        a = User.from_mongo(d)
        out.append({"id": a.id, "name": a.name, "email": a.email, "title": a.title, "adviser_code": a.adviser_code,
                    "is_firm_admin": a.is_firm_admin, "pending_setup": a.must_change_password,
                    "leads": await db.leads.count_documents({"adviser_id": a.id})})
    return out


@api.post("/firm/advisers")
async def add_firm_adviser(body: NewAdviserIn, me: User = Depends(firm_admin)):
    email = str(body.email).lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(409, "Someone already has an account with this email")
    firm = await get_firm(me.firm_id)
    first = re.sub(r"[^A-Z0-9]", "", body.name.strip().split(" ")[0].upper())[:10] or "ADVISER"
    base = f"{first}-{firm.code.upper()}"
    code, n = base, 2
    while await db.users.find_one({"adviser_code": code}):
        code, n = f"{first}{n}-{firm.code.upper()}", n + 1
    temp = secrets.token_urlsafe(12)
    a = User(email=email, name=body.name.strip(), created_at=now_iso(),
             password_hash=bcrypt.hashpw(temp.encode(), bcrypt.gensalt()).decode(),
             role="adviser", firm_id=me.firm_id, title=body.title, lead_email=email, adviser_code=code,
             must_change_password=True)
    try:
        res = await db.users.insert_one(a.to_mongo())
    except DuplicateKeyError:
        raise HTTPException(409, "Someone already has an account with this email")
    # Temporary password is returned once and never stored in plain text
    return {"id": str(res.inserted_id), "name": a.name, "email": email, "adviser_code": code, "temporary_password": temp}


class AdviserProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    title: str = Field(default="", max_length=80)
    bio: str = Field(default="", max_length=300)
    photo_url: str = Field(default="", max_length=500, pattern=r"^(https://\S+)?$")
    phone: str = Field(default="", max_length=30)
    calendly_url: str = Field(default="", max_length=300, pattern=r"^(https://\S+)?$")
    lead_email: EmailStr


@api.get("/adviser/profile")
async def get_adviser_profile(me: User = Depends(adviser_user)):
    return await adviser_profile(me)


@api.put("/adviser/profile")
async def put_adviser_profile(body: AdviserProfileIn, me: User = Depends(adviser_user)):
    data = body.model_dump()
    data["lead_email"] = str(body.lead_email).lower()
    await db.users.update_one({"_id": ObjectId(me.id)}, {"$set": data})
    return await adviser_profile(User.from_mongo(await db.users.find_one({"_id": ObjectId(me.id)})))


class FirmIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    fca_number: str = Field(default="", max_length=20)
    principal_name: str = Field(default="", max_length=120)
    principal_fca_number: str = Field(default="", max_length=20)


@api.put("/firm")
async def put_firm(body: FirmIn, me: User = Depends(adviser_user)):
    if not me.is_firm_admin or not me.firm_id:
        raise HTTPException(403, "Only your firm's administrator can change firm details")
    await db.firms.update_one({"_id": ObjectId(me.firm_id)}, {"$set": body.model_dump()})
    return await adviser_profile(me)


async def seed_default_adviser():
    """Idempotent: creates SFL + Mark once; never overwrites later edits or a changed password."""
    await db.firms.update_one({"code": os.environ["FIRM_CODE"]}, {"$setOnInsert": Firm(
        code=os.environ["FIRM_CODE"], name=os.environ["FIRM_NAME"], fca_number=os.environ["FCA_NUMBER"],
        principal_name=os.environ["PRINCIPAL_NAME"], principal_fca_number=os.environ["PRINCIPAL_FCA_NUMBER"],
        created_at=now_iso()).to_mongo()}, upsert=True)
    firm = await db.firms.find_one({"code": os.environ["FIRM_CODE"]})
    email = os.environ["DEFAULT_ADVISER_EMAIL"].lower()
    seed = User(email=email, name=os.environ["ADVISER_NAME"], created_at=now_iso(),
                password_hash=bcrypt.hashpw(os.environ["ADVISER_SEED_PASSWORD"].encode(), bcrypt.gensalt()).decode(),
                role="adviser", firm_id=str(firm["_id"]), is_firm_admin=True, title="Senior Protection Specialist",
                bio=os.environ["ADVISER_BIO"], photo_url=os.environ["ADVISER_PHOTO_URL"], phone=os.environ["ADVISER_PHONE"],
                calendly_url=CALENDLY_URL, lead_email=ADVISER_EMAIL, adviser_code=os.environ["ADVISER_CODE"])
    try:
        await db.users.update_one({"email": email}, {"$setOnInsert": seed.to_mongo()}, upsert=True)
    except Exception as e:  # concurrent worker won the race
        logger.info(f"Adviser seed skipped: {e}")
    # One-off migration: link pre-existing clients and leads to the default adviser
    mark = await db.users.find_one({"email": email})
    await db.users.update_many({"role": {"$exists": False}}, {"$set": {"role": "client"}})
    await db.users.update_many({"role": "client", "adviser_id": None}, {"$set": {"adviser_id": str(mark["_id"]), "firm_id": mark.get("firm_id")}})
    await db.leads.update_many({"adviser_id": None}, {"$set": {"adviser_id": str(mark["_id"]), "firm_id": mark.get("firm_id"), "status": "new"}})


app.include_router(api)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("adviser_code", unique=True, partialFilterExpression={"adviser_code": {"$type": "string"}})
    await db.firms.create_index("code", unique=True)
    await db.assessments.create_index("user_id")
    await db.leads.create_index("adviser_id")
    await db.rate_limits.create_index("expires_at", expireAfterSeconds=0)
    await seed_default_adviser()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
