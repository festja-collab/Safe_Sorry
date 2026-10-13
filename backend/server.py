from fastapi import FastAPI, APIRouter, Depends, HTTPException
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
import logging
import bcrypt
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from calc import compute  # noqa: E402
from articles import ARTICLES  # noqa: E402
from emailer import send_email  # noqa: E402
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


class RegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


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
    email_sent: bool = False
    created_at: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=30)
    return jwt.encode({"sub": user_id, "exp": exp}, JWT_SECRET, algorithm="HS256")


def public_user(u: User) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name}


async def current_user(c: HTTPAuthorizationCredentials = Depends(bearer)) -> User:
    if not c:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(c.credentials, JWT_SECRET, algorithms=["HS256"])
        doc = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    except Exception:
        doc = None
    if not doc:
        raise HTTPException(401, "Invalid or expired session")
    return User.from_mongo(doc)


@api.get("/")
async def root():
    return {"message": f"{APP_NAME} API"}


@api.get("/config")
async def config():
    return {"calendly_url": CALENDLY_URL, "app_name": APP_NAME}


@api.post("/auth/register")
async def register(body: RegisterIn):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(409, "An account with this email already exists")
    pw = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    user = User(email=email, name=body.name.strip(), password_hash=pw, created_at=now_iso())
    res = await db.users.insert_one(user.to_mongo())
    user.id = str(res.inserted_id)
    return {"token": make_token(user.id), "user": public_user(user)}


@api.post("/auth/login")
async def login(body: LoginIn):
    doc = await db.users.find_one({"email": body.email.lower()})
    if not doc or not bcrypt.checkpw(body.password.encode(), doc["password_hash"].encode()):
        raise HTTPException(401, "Incorrect email or password")
    user = User.from_mongo(doc)
    return {"token": make_token(user.id), "user": public_user(user)}


@api.get("/auth/me")
async def me(user: User = Depends(current_user)):
    return public_user(user)


def assessment_out(a: Assessment) -> dict:
    return {"id": a.id, "inputs": a.inputs, "results": a.results, "story": a.story, "created_at": a.created_at}


@api.post("/assessments")
async def create_assessment(body: AssessmentIn, user: User = Depends(current_user)):
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


@api.get("/articles/{slug}")
async def article(slug: str):
    for a in ARTICLES:
        if a["slug"] == slug:
            return a
    raise HTTPException(404, "Article not found")


def lead_email_html(lead: Lead, summary: Optional[dict]) -> str:
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
        f'<p style="font-size:12px;color:#888;margin-top:24px">Sent by {escape(APP_NAME)}.</p>'
        '</td></tr></table>'
    )


@api.post("/leads")
async def create_lead(body: LeadIn, user: User = Depends(current_user)):
    summary = (await get_owned(body.assessment_id, user)).results if body.assessment_id else None
    lead = Lead(user_id=user.id, email=user.email, name=body.name.strip(), phone=body.phone.strip(),
                preferred_time=body.preferred_time, message=body.message, assessment_id=body.assessment_id,
                created_at=now_iso())
    res = await db.leads.insert_one(lead.to_mongo())
    lead.id = str(res.inserted_id)
    try:
        await send_email(to=ADVISER_EMAIL, subject=f"New {APP_NAME} adviser request: {lead.name}",
                         html=lead_email_html(lead, summary), reply_to=user.email)
        await db.leads.update_one({"_id": ObjectId(lead.id)}, {"$set": {"email_sent": True}})
        lead.email_sent = True
    except Exception as e:
        logger.error(f"Lead email failed: {e}")
    return {"id": lead.id, "email_sent": lead.email_sent}


app.include_router(api)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.assessments.create_index("user_id")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
