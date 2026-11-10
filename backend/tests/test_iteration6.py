"""Iteration 6: forgot-password, privacy notice, lead consent, firm dashboard, store-link gating.

Fixtures:
- Each test uses a unique X-Forwarded-For IP so register and reset rate limits don't collide.
- Mongo cleanup at module teardown: TEST_* users + their leads + db.rate_limits + db.password_resets.
"""
import hashlib
import os
import uuid
import pytest
import requests
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone, timedelta

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "https://protect-me-17.preview.emergentagent.com").rstrip("/")
MARK_EMAIL = "mark.turner@sflwealth.co.uk"
MARK_PASSWORD = "IupwtaavjJ2CfMKIFjRhfott"
TOM_EMAIL = "tom@example.com"
TOM_PASSWORD = "test1234"

MONGO = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
DB = MONGO[os.environ.get("DB_NAME", "test_database")]
JWT_SECRET = os.environ.get("JWT_SECRET", "9f3c2a7e5b1d48e6a0c4f7b2d9e8a1c3f5b7d9e2a4c6e8f0b1d3f5a7c9e1b3d5")


def _ip():
    return f"203.0.113.{uuid.uuid4().int % 250 + 1}"


def _h(ip=None, token=None):
    h = {"Content-Type": "application/json", "X-Forwarded-For": ip or _ip()}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


CREATED_EMAILS = []


def register_client(adviser_code="", privacy=True, name="TEST Client"):
    email = f"TEST_{uuid.uuid4().hex[:10]}@example.com"
    payload = {"name": name, "email": email, "password": "TestPass1234",
               "adviser_code": adviser_code, "heard_from": "", "privacy_accepted": privacy}
    r = requests.post(f"{BASE_URL}/api/auth/register", json=payload, headers=_h())
    if r.status_code == 200:
        CREATED_EMAILS.append(email)
    return email, "TestPass1234", r


def mark_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": MARK_EMAIL, "password": MARK_PASSWORD}, headers=_h())
    assert r.status_code == 200, r.text
    return r.json()["token"]


def code_hash(uid: str, code: str) -> str:
    return hashlib.sha256(f"{JWT_SECRET}:{uid}:{code}".encode()).hexdigest()


# ============ Privacy notice ============
class TestPrivacy:
    def test_privacy_returns_version_and_sections(self):
        r = requests.get(f"{BASE_URL}/api/privacy", headers=_h())
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["version"] and isinstance(d["version"], str)
        assert isinstance(d["sections"], list) and len(d["sections"]) >= 7
        for s in d["sections"]:
            assert "heading" in s and "body" in s
        text = " ".join(s["body"] for s in d["sections"])
        assert "Secure for Life Wealth Management" in text
        assert "Rosemount" in text

    def test_register_without_privacy_rejected(self):
        _, _, r = register_client(privacy=False)
        assert r.status_code == 400, r.text
        assert "privacy" in r.json().get("detail", "").lower()

    def test_register_with_privacy_persists_version(self):
        email, _, r = register_client(privacy=True)
        assert r.status_code == 200, r.text
        doc = DB.users.find_one({"email": email.lower()})
        assert doc is not None
        assert doc.get("privacy_version"), f"privacy_version missing: {doc}"
        assert doc.get("privacy_accepted_at"), f"privacy_accepted_at missing"


# ============ Lead consent ============
class TestConsent:
    def test_lead_without_consent_rejected(self):
        _, _, r = register_client()
        assert r.status_code == 200
        token = r.json()["token"]
        r2 = requests.post(f"{BASE_URL}/api/leads",
                           json={"name": "x", "phone": "07123456789", "message": "hi"},
                           headers=_h(token=token))
        assert r2.status_code == 400, r2.text
        assert "tick" in r2.json().get("detail", "").lower() or "consent" in r2.json().get("detail", "").lower()

    def test_lead_with_consent_stored(self):
        email, _, r = register_client()
        assert r.status_code == 200
        token = r.json()["token"]
        r2 = requests.post(f"{BASE_URL}/api/leads",
                           json={"name": "TEST Lead", "phone": "07123456789", "message": "hi", "consent": True},
                           headers=_h(token=token))
        assert r2.status_code == 200, r2.text
        lid = r2.json()["id"]
        d = DB.leads.find_one({"_id": ObjectId(lid)})
        assert d is not None
        assert d.get("consent_text", "").strip() != ""
        assert d.get("consent_at", "").strip() != ""
        assert "Mark" in d["consent_text"]


# ============ Forgot password ============
class TestForgotPassword:
    def test_forgot_generic_response_unknown_email(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": f"nobody_{uuid.uuid4().hex[:6]}@example.com"}, headers=_h())
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True
        assert "6-digit" in d.get("message", "")

    def test_forgot_generic_response_known_email_and_creates_reset(self):
        email, _, r = register_client()
        assert r.status_code == 200
        uid = r.json()["user"]["id"]
        r2 = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                           json={"email": email}, headers=_h())
        assert r2.status_code == 200
        assert r2.json().get("ok") is True
        # Reset doc created
        reset = DB.password_resets.find_one({"user_id": uid})
        assert reset is not None, "password_resets doc not created"
        assert reset.get("code_hash") and len(reset["code_hash"]) == 64
        assert reset.get("attempts") == 0
        # No plaintext code field
        assert "code" not in reset

    def test_forgot_email_rate_limit(self):
        email, _, r = register_client()
        assert r.status_code == 200
        # Share same IP to also hit per-IP; but email limit 3/hour first
        ip = _ip()
        for i in range(3):
            r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                              json={"email": email}, headers=_h(ip=ip))
            assert r.status_code == 200, f"attempt {i}: {r.text}"
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password",
                          json={"email": email}, headers=_h(ip=ip))
        assert r.status_code == 429, r.text

    def test_reset_with_correct_code(self):
        email, _, r = register_client()
        assert r.status_code == 200
        uid = r.json()["user"]["id"]
        # Insert our own reset doc (bypass email delivery)
        code = "654321"
        DB.password_resets.delete_many({"user_id": uid})
        DB.password_resets.insert_one({
            "user_id": uid, "code_hash": code_hash(uid, code), "attempts": 0,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
        })
        # Wrong code -> 400 and attempts++
        r2 = requests.post(f"{BASE_URL}/api/auth/reset-password",
                           json={"email": email, "code": "000000", "new_password": "NewPassword99A"},
                           headers=_h())
        assert r2.status_code == 400
        reset = DB.password_resets.find_one({"user_id": uid})
        assert reset["attempts"] == 1

        # Correct code -> 200 + token + user, bumps password_version
        old_doc = DB.users.find_one({"_id": ObjectId(uid)})
        old_pwdv = old_doc.get("password_version", 0)
        r3 = requests.post(f"{BASE_URL}/api/auth/reset-password",
                           json={"email": email, "code": code, "new_password": "NewPassword99A"},
                           headers=_h())
        assert r3.status_code == 200, r3.text
        d = r3.json()
        assert "token" in d and "user" in d

        new_doc = DB.users.find_one({"_id": ObjectId(uid)})
        assert new_doc["password_version"] == old_pwdv + 1

        # Old token revoked
        old_token = r.json()["token"]
        r4 = requests.get(f"{BASE_URL}/api/auth/me", headers=_h(token=old_token))
        assert r4.status_code == 401

        # Reset doc single-use
        assert DB.password_resets.find_one({"user_id": uid}) is None

        # Login with new password works
        r5 = requests.post(f"{BASE_URL}/api/auth/login",
                           json={"email": email, "password": "NewPassword99A"}, headers=_h())
        assert r5.status_code == 200

    def test_reset_lockout_after_5_wrong(self):
        email, _, r = register_client()
        assert r.status_code == 200
        uid = r.json()["user"]["id"]
        code = "111222"
        DB.password_resets.delete_many({"user_id": uid})
        DB.password_resets.insert_one({
            "user_id": uid, "code_hash": code_hash(uid, code), "attempts": 0,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
        })
        for i in range(5):
            r2 = requests.post(f"{BASE_URL}/api/auth/reset-password",
                               json={"email": email, "code": "999999", "new_password": "Password1234"},
                               headers=_h())
            assert r2.status_code == 400
        # Correct code now also 400 (locked)
        r3 = requests.post(f"{BASE_URL}/api/auth/reset-password",
                           json={"email": email, "code": code, "new_password": "Password1234"},
                           headers=_h())
        assert r3.status_code == 400

    def test_reset_expired_fails(self):
        email, _, r = register_client()
        assert r.status_code == 200
        uid = r.json()["user"]["id"]
        code = "333444"
        DB.password_resets.delete_many({"user_id": uid})
        DB.password_resets.insert_one({
            "user_id": uid, "code_hash": code_hash(uid, code), "attempts": 0,
            "created_at": datetime.now(timezone.utc) - timedelta(minutes=30),
            "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
        })
        r2 = requests.post(f"{BASE_URL}/api/auth/reset-password",
                           json={"email": email, "code": code, "new_password": "Password1234"},
                           headers=_h())
        assert r2.status_code == 400


# ============ Firm dashboard ============
class TestFirmDashboard:
    def test_firm_stats_as_admin(self):
        token = mark_token()
        r = requests.get(f"{BASE_URL}/api/firm/stats", headers=_h(token=token))
        assert r.status_code == 200, r.text
        d = r.json()
        assert "totals" in d
        totals = d["totals"]
        for k in ("clients", "checks", "leads", "new", "contacted", "closed"):
            assert k in totals, f"missing total: {k}"
            assert isinstance(totals[k], int)
        assert "advisers" in d and isinstance(d["advisers"], list)
        assert "by_source" in d and isinstance(d["by_source"], list)
        # Mark himself is in the list
        codes = [a.get("adviser_code") for a in d["advisers"]]
        assert "MARK-SFL" in codes

    def test_firm_stats_non_admin_adviser_forbidden(self):
        # Create a new adviser via Mark then login as them
        token = mark_token()
        email = f"TEST_fs_{uuid.uuid4().hex[:6]}@sflwealth.co.uk"
        r = requests.post(f"{BASE_URL}/api/firm/advisers",
                          json={"name": "Nonadmin", "email": email, "title": "x"},
                          headers=_h(token=token))
        assert r.status_code == 200
        temp = r.json()["temporary_password"]
        try:
            # login
            r2 = requests.post(f"{BASE_URL}/api/auth/login",
                               json={"email": email, "password": temp}, headers=_h())
            tk = r2.json()["token"]
            # Must change pw first before stats, but firm/stats depends on firm_admin
            # Change password to lift must_change_password
            r3 = requests.post(f"{BASE_URL}/api/auth/change-password",
                               json={"current_password": temp, "new_password": "FreshPass123A"},
                               headers=_h(token=tk))
            assert r3.status_code == 200
            tk = r3.json()["token"]
            r4 = requests.get(f"{BASE_URL}/api/firm/stats", headers=_h(token=tk))
            assert r4.status_code == 403, r4.text
        finally:
            DB.users.delete_one({"email": email.lower()})

    def test_firm_stats_client_forbidden(self):
        _, _, r = register_client()
        assert r.status_code == 200
        tk = r.json()["token"]
        r2 = requests.get(f"{BASE_URL}/api/firm/stats", headers=_h(token=tk))
        assert r2.status_code == 403


# ============ Store link gating ============
class TestStoreLinkGating:
    def test_start_shows_coming_soon_when_env_empty(self):
        r = requests.get(f"{BASE_URL}/api/start", headers=_h())
        assert r.status_code == 200
        assert "Start your free check" in r.text

    def test_invite_shows_coming_soon(self):
        r = requests.get(f"{BASE_URL}/api/invite/MARK-SFL", headers=_h())
        assert r.status_code == 200
        assert "Start your free check" in r.text


# ============ Regression ============
class TestRegression:
    def test_tom_login_and_report(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": TOM_EMAIL, "password": TOM_PASSWORD}, headers=_h())
        assert r.status_code == 200, r.text
        tk = r.json()["token"]
        r2 = requests.get(f"{BASE_URL}/api/assessments", headers=_h(token=tk))
        assert r2.status_code == 200

    def test_mark_leads_and_stats(self):
        tk = mark_token()
        r = requests.get(f"{BASE_URL}/api/adviser/leads", headers=_h(token=tk))
        assert r.status_code == 200
        r = requests.get(f"{BASE_URL}/api/adviser/stats", headers=_h(token=tk))
        assert r.status_code == 200

    def test_mark_change_password_endpoint_accessible(self):
        tk = mark_token()
        # Just send wrong current to ensure endpoint still 400 (no change made)
        r = requests.post(f"{BASE_URL}/api/auth/change-password",
                          json={"current_password": "wrong-current-pw", "new_password": "ShouldNotApply1"},
                          headers=_h(token=tk))
        assert r.status_code == 400


# ============ Final cleanup ============
def teardown_module(module):
    for e in CREATED_EMAILS:
        u = DB.users.find_one({"email": e.lower()})
        if u:
            DB.leads.delete_many({"user_id": str(u["_id"])})
            DB.password_resets.delete_many({"user_id": str(u["_id"])})
            DB.users.delete_one({"_id": u["_id"]})
    DB.rate_limits.delete_many({})
    DB.password_resets.delete_many({})
