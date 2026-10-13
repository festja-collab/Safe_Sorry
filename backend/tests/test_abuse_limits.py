"""Abuse-protection / rate-limit tests for Safe > Sorry.

Each test uses a unique X-Forwarded-For and unique email so the module-scoped
`new_user` fixture in test_safe_sorry.py is unaffected. A session-scoped
fixture clears `rate_limits` before + after this file runs so tom@example.com
is not left locked out.
"""
import os
import time
import uuid

import jwt
import pymongo
import pytest
import requests

BASE = (os.environ.get("EXPO_PUBLIC_BACKEND_URL")
        or "https://protect-me-17.preview.emergentagent.com").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")
JWT_SECRET = os.environ.get(
    "JWT_SECRET",
    "9f3c2a7e5b1d48e6a0c4f7b2d9e8a1c3f5b7d9e2a4c6e8f0b1d3f5a7c9e1b3d5",
)

GOOD_PASS = "secret1234"  # 10 chars, passes new rule
LEGACY_PASS = "test1234"  # 8 chars - allowed for existing tom user


@pytest.fixture(scope="module", autouse=True)
def _clear_rate_limits():
    """Clear counters before + after module so neighbours aren't affected."""
    db = pymongo.MongoClient(MONGO_URL)[DB_NAME]
    db.rate_limits.delete_many({})
    yield
    db.rate_limits.delete_many({})


def _ip() -> str:
    """Unique IPv4 per call so tests don't share IP buckets."""
    return f"10.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}"


def _reg(email: str, password: str = GOOD_PASS, ip: str | None = None):
    headers = {"X-Forwarded-For": ip or _ip()}
    return requests.post(
        f"{BASE}/api/auth/register",
        json={"name": "TEST", "email": email, "password": password},
        headers=headers,
        timeout=15,
    )


def _login(email: str, password: str, ip: str | None = None):
    headers = {"X-Forwarded-For": ip or _ip()}
    return requests.post(
        f"{BASE}/api/auth/login",
        json={"email": email, "password": password},
        headers=headers,
        timeout=15,
    )


# ---------- Password length ----------
def test_register_short_password_rejected():
    r = _reg(f"test_short_{uuid.uuid4().hex[:8]}@example.com", password="short123")  # 8 chars
    assert r.status_code == 422, r.text


def test_register_9_char_password_rejected():
    r = _reg(f"test_nine_{uuid.uuid4().hex[:8]}@example.com", password="123456789")
    assert r.status_code == 422


def test_register_10_char_password_ok():
    email = f"test_ten_{uuid.uuid4().hex[:8]}@example.com"
    r = _reg(email, password="1234567890")
    assert r.status_code == 200, r.text


# ---------- Legacy login ----------
def test_legacy_login_8_char_password_works():
    r = _login("tom@example.com", LEGACY_PASS)
    assert r.status_code == 200, r.text
    assert r.json()["token"]


# ---------- JWT 7-day exp ----------
def test_jwt_token_has_7_day_expiry():
    r = _login("tom@example.com", LEGACY_PASS)
    token = r.json()["token"]
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    assert payload["exp"] - payload["iat"] == 7 * 24 * 3600


# ---------- Brute force: per-email (5/15min) ----------
def test_login_fail_per_email_locks_at_6th_attempt():
    email = f"test_bf_email_{uuid.uuid4().hex[:8]}@example.com"
    assert _reg(email).status_code == 200
    # Each wrong attempt uses a NEW IP so IP bucket never trips first.
    for i in range(5):
        r = _login(email, "wrong_password", ip=_ip())
        assert r.status_code == 401, f"attempt {i+1}: {r.status_code} {r.text}"
    r6 = _login(email, "wrong_password", ip=_ip())
    assert r6.status_code == 429, r6.text
    assert "Retry-After" in r6.headers
    assert int(r6.headers["Retry-After"]) > 0
    # Even the correct password is blocked while locked.
    r_right = _login(email, GOOD_PASS, ip=_ip())
    assert r_right.status_code == 429


def test_different_email_unaffected_by_other_email_lockout():
    # another user on fresh email + IP should still log in.
    email = f"test_other_{uuid.uuid4().hex[:8]}@example.com"
    assert _reg(email).status_code == 200
    r = _login(email, GOOD_PASS, ip=_ip())
    assert r.status_code == 200


# ---------- Brute force: per-IP (10/15min) ----------
def test_login_fail_per_ip_locks_at_11th_attempt():
    ip = _ip()
    # 10 different emails -> email bucket never trips, only IP bucket.
    for i in range(10):
        email = f"test_bfip_{uuid.uuid4().hex[:6]}_{i}@example.com"
        r = _login(email, "wrong_password", ip=ip)
        assert r.status_code == 401, f"attempt {i+1}: {r.status_code}"
    # 11th from the same IP should 429.
    r11 = _login(f"test_bfip_{uuid.uuid4().hex[:6]}@example.com", "wrong_password", ip=ip)
    assert r11.status_code == 429
    assert "Retry-After" in r11.headers


# ---------- Register per IP (5/hour) ----------
def test_register_per_ip_locks_at_6th():
    ip = _ip()
    for i in range(5):
        email = f"test_regip_{uuid.uuid4().hex[:6]}_{i}@example.com"
        r = _reg(email, ip=ip)
        assert r.status_code == 200, f"reg {i+1}: {r.status_code} {r.text}"
    r6 = _reg(f"test_regip_{uuid.uuid4().hex[:6]}@example.com", ip=ip)
    assert r6.status_code == 429, r6.text
    assert "Retry-After" in r6.headers


# ---------- Assessments per user per day (5) ----------
SAMPLE = {
    "first_name": "Tom", "age": 36, "relationship": "married",
    "partner_name": "Sarah", "partner_income": 30000,
    "children": [{"name": "Lily", "age": 4}],
    "employment": "employed", "annual_income": 55000,
    "monthly_outgoings": 2200, "housing": "mortgage",
    "mortgage_balance": 220000, "monthly_housing": 1300,
    "mortgage_years": 22, "other_debts": 4000, "savings": 8000,
    "life_cover": 100000, "death_in_service": 3, "sick_pay_months": 3,
    "income_protection": 0, "critical_illness": 0, "worry": "house",
}


@pytest.fixture
def fresh_user_token():
    email = f"test_quota_{uuid.uuid4().hex[:8]}@example.com"
    r = _reg(email)
    assert r.status_code == 200
    return r.json()["token"]


def test_assessments_per_user_locked_at_6th(fresh_user_token):
    h = {"Authorization": f"Bearer {fresh_user_token}"}
    for i in range(5):
        r = requests.post(f"{BASE}/api/assessments", json=SAMPLE, headers=h, timeout=20)
        assert r.status_code == 200, f"assessment {i+1}: {r.status_code} {r.text}"
    r6 = requests.post(f"{BASE}/api/assessments", json=SAMPLE, headers=h, timeout=20)
    assert r6.status_code == 429, r6.text
    assert "limit" in r6.json().get("detail", "").lower()
    assert "Retry-After" in r6.headers


# ---------- Leads per user per day (3) ----------
def test_leads_per_user_locked_at_4th(fresh_user_token):
    h = {"Authorization": f"Bearer {fresh_user_token}"}
    body = {"name": "TEST Lead", "phone": "+447123456789",
            "preferred_time": "Evenings", "message": "please help"}
    for i in range(3):
        r = requests.post(f"{BASE}/api/leads", json=body, headers=h, timeout=20)
        assert r.status_code == 200, f"lead {i+1}: {r.status_code} {r.text}"
    r4 = requests.post(f"{BASE}/api/leads", json=body, headers=h, timeout=20)
    assert r4.status_code == 429, r4.text
    assert "Retry-After" in r4.headers


# ---------- Story quota (cached story bypasses, counter still enforced) ----------
def test_story_cached_bypasses_quota_counter():
    """tom already has a cached story on his existing assessment.
    Hitting it 6+ times must stay 200 (cached), never 429."""
    r = _login("tom@example.com", LEGACY_PASS)
    assert r.status_code == 200
    tok = r.json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    r_list = requests.get(f"{BASE}/api/assessments", headers=h, timeout=15)
    assert r_list.status_code == 200
    items = r_list.json()
    if not items:
        pytest.skip("tom has no assessments to probe cached story")
    aid = items[0]["id"]
    # Confirm it is cached (should be <2s).
    t0 = time.time()
    r = requests.post(f"{BASE}/api/assessments/{aid}/story", headers=h, timeout=15)
    assert r.status_code == 200, r.text
    assert time.time() - t0 < 5, "story was not cached - skipping quota probe"
    # Hit it 6 times - cached hits should NOT consume quota.
    for _ in range(6):
        r = requests.post(f"{BASE}/api/assessments/{aid}/story", headers=h, timeout=15)
        assert r.status_code == 200
