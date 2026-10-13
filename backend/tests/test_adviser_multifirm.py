"""End-to-end tests for the adviser / multi-firm feature set.

Covers:
- Seeded adviser login & shape of /auth/me
- Register with valid / invalid / blank adviser code
- Lead routing to a client's adviser
- Adviser-only endpoints (/adviser/leads, /adviser/leads/{id}, PATCH status, stats, profile, firm)
- Cross-adviser isolation (second adviser inserted directly into Mongo)
- /api/assessments/{id} accessible by owning adviser via their lead only
- /api/my-adviser and /api/me/adviser (link client by code)
- /api/compliance-pack still 200
Rate limits are respected via unique X-Forwarded-For per sign-up.
"""
import os
import uuid
import pytest
import requests
import bcrypt
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))

BASE = (os.environ.get("EXPO_PUBLIC_BACKEND_URL")
        or "https://protect-me-17.preview.emergentagent.com").rstrip("/")

MARK_EMAIL = "mark.turner@sflwealth.co.uk"
MARK_PASSWORD = "IupwtaavjJ2CfMKIFjRhfott"
MARK_CODE = "MARK-SFL"

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


# ---------------- helpers ----------------
def _ip():
    return f"203.0.113.{uuid.uuid4().int % 250 + 1}"


def _h(ip=None, tok=None):
    h = {"Content-Type": "application/json", "X-Forwarded-For": ip or _ip()}
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def _register_client(adviser_code: str = "", ip: str | None = None):
    email = f"test_mf_{uuid.uuid4().hex[:10]}@example.com"
    r = requests.post(f"{BASE}/api/auth/register",
                      json={"name": "TEST MF", "email": email, "password": "secretpass1234",
                            "adviser_code": adviser_code}, headers=_h(ip))
    return email, r


def _make_assessment(token):
    body = {"first_name": "Tom", "age": 36, "relationship": "married",
            "partner_name": "S", "partner_income": 20000,
            "children": [{"name": "L", "age": 4}],
            "employment": "employed", "annual_income": 55000,
            "monthly_outgoings": 2000, "housing": "mortgage",
            "mortgage_balance": 220000, "monthly_housing": 1200,
            "mortgage_years": 20, "other_debts": 0, "savings": 5000,
            "life_cover": 100000, "death_in_service": 2, "sick_pay_months": 3,
            "income_protection": 0, "critical_illness": 0, "worry": "house"}
    r = requests.post(f"{BASE}/api/assessments", json=body, headers=_h(tok=token))
    assert r.status_code == 200, r.text
    return r.json()["id"]


# -------- Mongo & cleanup fixtures --------
@pytest.fixture(scope="module")
def mongo():
    cli = MongoClient(MONGO_URL)
    yield cli[DB_NAME]
    cli.close()


@pytest.fixture(scope="module", autouse=True)
def _rate_limit_cleanup(mongo):
    mongo.rate_limits.delete_many({})
    yield
    mongo.rate_limits.delete_many({})


@pytest.fixture(scope="module")
def mark_original(mongo):
    """Snapshot Mark's profile + firm so we can restore after mutations."""
    u = mongo.users.find_one({"email": MARK_EMAIL})
    f = mongo.firms.find_one({"_id": u["firm_id"]}) if u and u.get("firm_id") else None
    yield u, f
    # restore from .env canonical values (safer than snapshot in case tests half-ran)
    mongo.users.update_one({"email": MARK_EMAIL}, {"$set": {
        "name": os.environ["ADVISER_NAME"],
        "title": "Senior Protection Specialist",
        "bio": os.environ["ADVISER_BIO"],
        "photo_url": os.environ["ADVISER_PHOTO_URL"],
        "phone": os.environ["ADVISER_PHONE"],
        "calendly_url": os.environ["CALENDLY_URL"],
        "lead_email": os.environ["ADVISER_EMAIL"],
        "adviser_code": os.environ["ADVISER_CODE"],
    }})
    if f:
        mongo.firms.update_one({"_id": f["_id"]}, {"$set": {
            "name": os.environ["FIRM_NAME"], "fca_number": os.environ["FCA_NUMBER"],
            "principal_name": os.environ["PRINCIPAL_NAME"],
            "principal_fca_number": os.environ["PRINCIPAL_FCA_NUMBER"],
        }})


# -------- Adviser login --------
@pytest.fixture(scope="module")
def mark_token():
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email": MARK_EMAIL, "password": MARK_PASSWORD}, headers=_h())
    assert r.status_code == 200, r.text
    return r.json()


def test_seeded_adviser_login_shape(mark_token):
    u = mark_token["user"]
    assert u["role"] == "adviser"
    assert u["is_firm_admin"] is True
    assert u["adviser_code"] == MARK_CODE
    assert mark_token["token"]


def test_adviser_me(mark_token):
    r = requests.get(f"{BASE}/api/auth/me", headers=_h(tok=mark_token["token"]))
    assert r.status_code == 200
    assert r.json()["role"] == "adviser"


# -------- Register with codes --------
def test_register_with_valid_code_links():
    email, r = _register_client(adviser_code=MARK_CODE)
    assert r.status_code == 200, r.text
    tok = r.json()["token"]
    adv = requests.get(f"{BASE}/api/my-adviser", headers=_h(tok=tok))
    assert adv.status_code == 200
    assert adv.json()["adviser_code"] == MARK_CODE
    assert adv.json()["name"]  # Mark Turner


def test_register_with_invalid_code_400():
    email = f"test_bad_{uuid.uuid4().hex[:8]}@example.com"
    r = requests.post(f"{BASE}/api/auth/register",
                      json={"name": "X", "email": email, "password": "secretpass1234",
                            "adviser_code": "DOES-NOT-EXIST"}, headers=_h())
    assert r.status_code == 400, r.text
    assert "adviser" in r.json().get("detail", "").lower()


def test_register_blank_code_links_default_adviser():
    email, r = _register_client(adviser_code="")
    assert r.status_code == 200
    tok = r.json()["token"]
    adv = requests.get(f"{BASE}/api/my-adviser", headers=_h(tok=tok))
    assert adv.status_code == 200
    j = adv.json()
    assert j["adviser_code"] == MARK_CODE  # default is Mark
    assert j["firm_name"]


# -------- Lead routing + adviser-only endpoints --------
@pytest.fixture(scope="module")
def client_with_lead(mark_token):
    """A client under Mark + an assessment + a lead."""
    _, r = _register_client(adviser_code=MARK_CODE)
    assert r.status_code == 200
    tok = r.json()["token"]
    uid = r.json()["user"]["id"]
    aid = _make_assessment(tok)
    body = {"name": "TEST Lead MF", "phone": "+447123000111",
            "preferred_time": "Evenings", "message": "please help",
            "assessment_id": aid}
    lr = requests.post(f"{BASE}/api/leads", json=body, headers=_h(tok=tok))
    assert lr.status_code == 200, lr.text
    return {"token": tok, "user_id": uid, "aid": aid, "lead_id": lr.json()["id"]}


def test_adviser_leads_list_contains_new_lead(mark_token, client_with_lead):
    r = requests.get(f"{BASE}/api/adviser/leads", headers=_h(tok=mark_token["token"]))
    assert r.status_code == 200
    items = r.json()
    found = [x for x in items if x["id"] == client_with_lead["lead_id"]]
    assert found, "new lead not visible to adviser"
    lead = found[0]
    assert lead["status"] == "new"
    assert lead["summary"] is not None
    assert "headline" in lead["summary"]


def test_adviser_leads_forbidden_for_client(client_with_lead):
    r = requests.get(f"{BASE}/api/adviser/leads", headers=_h(tok=client_with_lead["token"]))
    assert r.status_code == 403


def test_adviser_leads_status_filter(mark_token, client_with_lead):
    r = requests.get(f"{BASE}/api/adviser/leads?status=new", headers=_h(tok=mark_token["token"]))
    assert r.status_code == 200
    assert all(x["status"] == "new" for x in r.json())
    assert any(x["id"] == client_with_lead["lead_id"] for x in r.json())
    r2 = requests.get(f"{BASE}/api/adviser/leads?status=closed", headers=_h(tok=mark_token["token"]))
    assert r2.status_code == 200
    assert all(x["status"] == "closed" for x in r2.json())


def test_adviser_lead_detail_includes_assessment(mark_token, client_with_lead):
    r = requests.get(f"{BASE}/api/adviser/leads/{client_with_lead['lead_id']}",
                     headers=_h(tok=mark_token["token"]))
    assert r.status_code == 200
    d = r.json()
    assert d["id"] == client_with_lead["lead_id"]
    assert d["assessment"] is not None
    assert d["assessment"]["id"] == client_with_lead["aid"]
    assert "gaps" in d["assessment"]["results"]


def test_patch_lead_status(mark_token, client_with_lead):
    for st in ("contacted", "closed", "new"):
        r = requests.patch(f"{BASE}/api/adviser/leads/{client_with_lead['lead_id']}",
                           json={"status": st}, headers=_h(tok=mark_token["token"]))
        assert r.status_code == 200, r.text
        assert r.json()["status"] == st


def test_patch_lead_bad_status(mark_token, client_with_lead):
    r = requests.patch(f"{BASE}/api/adviser/leads/{client_with_lead['lead_id']}",
                       json={"status": "garbage"}, headers=_h(tok=mark_token["token"]))
    assert r.status_code == 422


# -------- Second adviser isolation --------
@pytest.fixture(scope="module")
def second_adviser(mongo):
    code = f"TEST-OTH-{uuid.uuid4().hex[:4].upper()}"
    pw = bcrypt.hashpw(b"otherpass1234", bcrypt.gensalt()).decode()
    doc = {"email": f"test_oth_{uuid.uuid4().hex[:6]}@example.com",
           "name": "TEST Other Adviser", "password_hash": pw,
           "created_at": "2026-01-01T00:00:00+00:00", "role": "adviser",
           "is_firm_admin": False, "adviser_code": code,
           "title": "", "bio": "", "photo_url": "", "phone": "",
           "calendly_url": "", "lead_email": "", "adviser_id": None, "firm_id": None}
    res = mongo.users.insert_one(doc)
    # login to get a token
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email": doc["email"], "password": "otherpass1234"}, headers=_h())
    assert r.status_code == 200, r.text
    tok = r.json()["token"]
    yield {"id": str(res.inserted_id), "token": tok, "code": code, "email": doc["email"]}
    mongo.users.delete_one({"_id": res.inserted_id})


def test_other_adviser_cannot_see_marks_lead(second_adviser, client_with_lead):
    r = requests.get(f"{BASE}/api/adviser/leads/{client_with_lead['lead_id']}",
                     headers=_h(tok=second_adviser["token"]))
    assert r.status_code == 404


def test_other_adviser_cannot_patch_marks_lead(second_adviser, client_with_lead):
    r = requests.patch(f"{BASE}/api/adviser/leads/{client_with_lead['lead_id']}",
                       json={"status": "closed"}, headers=_h(tok=second_adviser["token"]))
    assert r.status_code == 404


# -------- Adviser access to assessments only via their leads --------
def test_mark_can_get_assessment_via_lead(mark_token, client_with_lead):
    r = requests.get(f"{BASE}/api/assessments/{client_with_lead['aid']}",
                     headers=_h(tok=mark_token["token"]))
    assert r.status_code == 200
    assert r.json()["id"] == client_with_lead["aid"]


def test_other_adviser_cannot_get_assessment(second_adviser, client_with_lead):
    r = requests.get(f"{BASE}/api/assessments/{client_with_lead['aid']}",
                     headers=_h(tok=second_adviser["token"]))
    assert r.status_code == 404


# -------- Stats / profile / firm --------
def test_adviser_stats(mark_token):
    r = requests.get(f"{BASE}/api/adviser/stats", headers=_h(tok=mark_token["token"]))
    assert r.status_code == 200
    d = r.json()
    for k in ("new", "contacted", "closed", "total", "clients"):
        assert k in d and isinstance(d[k], int)
    assert d["total"] == d["new"] + d["contacted"] + d["closed"]


def test_get_adviser_profile(mark_token, mark_original):
    r = requests.get(f"{BASE}/api/adviser/profile", headers=_h(tok=mark_token["token"]))
    assert r.status_code == 200
    d = r.json()
    assert d["adviser_code"] == MARK_CODE
    assert d["firm_name"]


def test_put_adviser_profile_https_validation(mark_token):
    bad = {"name": "Mark Turner", "title": "x", "bio": "x",
           "photo_url": "http://insecure.com/img.jpg",  # must be https
           "phone": "123", "calendly_url": "", "lead_email": MARK_EMAIL}
    r = requests.put(f"{BASE}/api/adviser/profile", json=bad, headers=_h(tok=mark_token["token"]))
    assert r.status_code == 422


def test_put_adviser_profile_ok(mark_token, mark_original):
    body = {"name": "Mark Turner", "title": "Protection Specialist (test)",
            "bio": "temp bio", "photo_url": "https://example.com/x.jpg",
            "phone": "07000000000", "calendly_url": "https://calendly.com/test",
            "lead_email": MARK_EMAIL}
    r = requests.put(f"{BASE}/api/adviser/profile", json=body, headers=_h(tok=mark_token["token"]))
    assert r.status_code == 200
    assert r.json()["title"] == "Protection Specialist (test)"


def test_put_firm_admin_ok(mark_token):
    body = {"name": "SFL Wealth Management Ltd", "fca_number": "912517",
            "principal_name": "Rosemount Financial Solutions (IFA) Limited",
            "principal_fca_number": "535515"}
    r = requests.put(f"{BASE}/api/firm", json=body, headers=_h(tok=mark_token["token"]))
    assert r.status_code == 200
    assert r.json()["firm_name"] == body["name"]


def test_put_firm_forbidden_for_non_admin(second_adviser):
    body = {"name": "hacker firm"}
    r = requests.put(f"{BASE}/api/firm", json=body, headers=_h(tok=second_adviser["token"]))
    assert r.status_code == 403


def test_put_firm_forbidden_for_client():
    _, reg = _register_client("")
    tok = reg.json()["token"]
    r = requests.put(f"{BASE}/api/firm", json={"name": "x"}, headers=_h(tok=tok))
    assert r.status_code == 403


# -------- Link adviser (client) --------
def test_link_adviser_success(second_adviser):
    _, reg = _register_client("")  # initially under default (Mark)
    tok = reg.json()["token"]
    r = requests.post(f"{BASE}/api/me/adviser", json={"code": second_adviser["code"]},
                      headers=_h(tok=tok))
    assert r.status_code == 200, r.text
    assert r.json()["adviser_code"] == second_adviser["code"]
    # verify via my-adviser
    r2 = requests.get(f"{BASE}/api/my-adviser", headers=_h(tok=tok))
    assert r2.status_code == 200
    assert r2.json()["adviser_code"] == second_adviser["code"]


def test_link_adviser_bad_code():
    _, reg = _register_client("")
    tok = reg.json()["token"]
    r = requests.post(f"{BASE}/api/me/adviser", json={"code": "NO-SUCH-CODE"},
                      headers=_h(tok=tok))
    assert r.status_code == 404


def test_link_adviser_forbidden_for_adviser(mark_token):
    r = requests.post(f"{BASE}/api/me/adviser", json={"code": "ANY"},
                      headers=_h(tok=mark_token["token"]))
    assert r.status_code == 400


# -------- Compliance pack --------
def test_compliance_pack_still_200():
    r = requests.get(f"{BASE}/api/compliance-pack")
    assert r.status_code == 200
    assert "<" in r.text  # HTML
