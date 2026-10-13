"""Iteration 7 tests: firm self sign-up, logo upload, brand color, marketing tips page UI."""
import io
import os
import time
import uuid
import pytest
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "https://protect-me-17.preview.emergentagent.com").rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

mongo = MongoClient(MONGO_URL)
db = mongo[DB_NAME]

MARK_EMAIL = "mark.turner@sflwealth.co.uk"
MARK_PASS = "IupwtaavjJ2CfMKIFjRhfott"


def _clear_rate_limits():
    db.rate_limits.delete_many({})


# Per-worker tracking of created resources (cleanup only what this worker made,
# avoids xdist cross-worker races where one worker's module teardown wipes
# another worker's live test data).
_CREATED_USER_IDS: list = []
_CREATED_FIRM_IDS: list = []


def _unique_email(tag="firm"):
    return f"TEST_{tag}_{uuid.uuid4().hex[:10]}@example.com"


def _unique_firm_name():
    return f"TEST Firm {uuid.uuid4().hex[:6]}"


@pytest.fixture(autouse=True)
def _reset_limits():
    _clear_rate_limits()
    yield
    _clear_rate_limits()


@pytest.fixture(scope="module", autouse=True)
def _cleanup_after():
    yield
    from bson import ObjectId
    # Only delete resources this worker created (prevents cross-worker race)
    uids = [ObjectId(x) for x in _CREATED_USER_IDS if x]
    if uids:
        db.leads.delete_many({"user_id": {"$in": [str(x) for x in uids]}})
        db.assessments.delete_many({"user_id": {"$in": [str(x) for x in uids]}})
        db.users.delete_many({"_id": {"$in": uids}})
    fids = [ObjectId(x) for x in _CREATED_FIRM_IDS if x]
    if fids:
        db.firms.delete_many({"_id": {"$in": fids}})
    db.rate_limits.delete_many({})


# ---------------- Firm Register ----------------
class TestFirmRegister:
    def _payload(self, **over):
        p = {
            "firm_name": _unique_firm_name(),
            "fca_number": "123456",
            "principal_name": "Rosemount Financial Solutions Ltd",
            "principal_fca_number": "7654321",
            "brand_color": "#223342",
            "name": "Jane TestUser",
            "title": "Protection Adviser",
            "phone": "+447700900000",
            "email": _unique_email(),
            "password": "verySecret1234",
            "privacy_accepted": True,
        }
        p.update(over)
        return p

    def test_register_success_and_profile(self):
        payload = self._payload(name="Jane TestUser")
        r = requests.post(f"{BASE}/api/firms/register", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        _CREATED_USER_IDS.append(body["user"]["id"])
        assert "token" in body and "user" in body
        u = body["user"]
        assert u["role"] == "adviser"
        assert u["is_firm_admin"] is True
        assert u["adviser_code"] and u["adviser_code"].startswith("JANE-")
        # GET /adviser/profile
        headers = {"Authorization": f"Bearer {body['token']}"}
        p = requests.get(f"{BASE}/api/adviser/profile", headers=headers)
        assert p.status_code == 200, p.text
        prof = p.json()
        _CREATED_FIRM_IDS.append(prof["firm_id"])
        assert prof["plan"] == "trial"
        assert prof["trial_days_left"] in (13, 14)
        assert prof["brand_color"] == "#223342"
        assert prof["firm_name"] == payload["firm_name"]
        assert prof["fca_number"] == "123456"

    def test_fca_number_validation(self):
        r = requests.post(f"{BASE}/api/firms/register", json=self._payload(fca_number="12"))
        assert r.status_code == 422
        r = requests.post(f"{BASE}/api/firms/register", json=self._payload(fca_number="12345678"))
        assert r.status_code == 422

    def test_password_min_length(self):
        r = requests.post(f"{BASE}/api/firms/register", json=self._payload(password="short123"))
        assert r.status_code == 422

    def test_privacy_required(self):
        r = requests.post(f"{BASE}/api/firms/register", json=self._payload(privacy_accepted=False))
        assert r.status_code == 400
        assert "privacy" in r.json()["detail"].lower()

    def test_duplicate_email_409(self):
        p = self._payload()
        r1 = requests.post(f"{BASE}/api/firms/register", json=p)
        assert r1.status_code == 200
        _CREATED_USER_IDS.append(r1.json()["user"]["id"])
        r2 = requests.post(f"{BASE}/api/firms/register", json=self._payload(email=p["email"]))
        assert r2.status_code == 409

    def test_brand_color_invalid_hex(self):
        r = requests.post(f"{BASE}/api/firms/register", json=self._payload(brand_color="red"))
        assert r.status_code == 422

    def test_brand_color_empty_allowed(self):
        r = requests.post(f"{BASE}/api/firms/register", json=self._payload(brand_color=""))
        assert r.status_code == 200
        _CREATED_USER_IDS.append(r.json()["user"]["id"])


# ---------------- Logo Upload ----------------
# Minimal 1x1 PNG
PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6300010000000500010d0a2db40000000049454e44ae426082"
)


def _register_firm_admin():
    _clear_rate_limits()
    payload = {
        "firm_name": _unique_firm_name(),
        "fca_number": "654321",
        "principal_name": "", "principal_fca_number": "",
        "brand_color": "#ff0066",
        "name": "LogoUser One",
        "title": "", "phone": "",
        "email": _unique_email("logo"),
        "password": "verySecret1234",
        "privacy_accepted": True,
    }
    # Retry on 500 (known race in unique_code during parallel runs)
    r = requests.post(f"{BASE}/api/firms/register", json=payload)
    if r.status_code == 500:
        time.sleep(0.3)
        payload["firm_name"] = _unique_firm_name()
        payload["email"] = _unique_email("logo")
        r = requests.post(f"{BASE}/api/firms/register", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    _CREATED_USER_IDS.append(body["user"]["id"])
    # fetch firm_id
    prof = requests.get(f"{BASE}/api/adviser/profile",
                        headers={"Authorization": f"Bearer {body['token']}"}).json()
    _CREATED_FIRM_IDS.append(prof["firm_id"])
    return body["token"], body["user"]


class TestFirmLogo:
    def test_upload_png_success_and_public_fetch(self):
        token, user = _register_firm_admin()
        headers = {"Authorization": f"Bearer {token}"}
        files = {"file": ("logo.png", io.BytesIO(PNG_1x1), "image/png")}
        r = requests.post(f"{BASE}/api/firm/logo", headers=headers, files=files)
        if r.status_code == 503:
            pytest.skip("Storage service unavailable in preview env")
        assert r.status_code == 200, r.text
        prof = r.json()
        assert prof["logo_url"].startswith("/api/firm-logo/")
        # Public fetch
        firm_id = prof["firm_id"]
        pub = requests.get(f"{BASE}/api/firm-logo/{firm_id}")
        assert pub.status_code == 200
        assert pub.headers.get("Content-Type", "").startswith("image/")
        assert len(pub.content) > 0

    def test_upload_rejects_text_file(self):
        token, _ = _register_firm_admin()
        headers = {"Authorization": f"Bearer {token}"}
        files = {"file": ("bad.txt", io.BytesIO(b"not an image"), "text/plain")}
        r = requests.post(f"{BASE}/api/firm/logo", headers=headers, files=files)
        assert r.status_code == 400

    def test_upload_rejects_oversize(self):
        token, _ = _register_firm_admin()
        headers = {"Authorization": f"Bearer {token}"}
        big = b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024 + 100)
        files = {"file": ("big.png", io.BytesIO(big), "image/png")}
        r = requests.post(f"{BASE}/api/firm/logo", headers=headers, files=files)
        assert r.status_code == 400
        assert "2 MB" in r.json()["detail"] or "smaller" in r.json()["detail"].lower()

    def test_non_admin_adviser_forbidden(self):
        # Create firm admin -> create a new adviser via /firm/advisers
        token, _ = _register_firm_admin()
        headers = {"Authorization": f"Bearer {token}"}
        new_email = _unique_email("adv")
        r = requests.post(f"{BASE}/api/firm/advisers", headers=headers,
                          json={"name": "Sub Adviser", "email": new_email, "title": "Adviser"})
        assert r.status_code == 200, r.text
        _CREATED_USER_IDS.append(r.json()["id"])
        temp = r.json()["temporary_password"]
        # Login as new adviser (must change password first - but we hit /firm/logo which requires current_user)
        login = requests.post(f"{BASE}/api/auth/login", json={"email": new_email, "password": temp})
        assert login.status_code == 200
        sub_token = login.json()["token"]
        # Change the mandatory password
        cp = requests.post(f"{BASE}/api/auth/change-password",
                           headers={"Authorization": f"Bearer {sub_token}"},
                           json={"current_password": temp, "new_password": "newPass123456"})
        assert cp.status_code == 200, cp.text
        sub_token = cp.json()["token"]
        files = {"file": ("logo.png", io.BytesIO(PNG_1x1), "image/png")}
        r = requests.post(f"{BASE}/api/firm/logo",
                          headers={"Authorization": f"Bearer {sub_token}"}, files=files)
        assert r.status_code == 403

    def test_client_forbidden(self):
        _clear_rate_limits()
        email = _unique_email("client")
        r = requests.post(f"{BASE}/api/auth/register", json={
            "name": "Client X", "email": email, "password": "clientPass1234", "privacy_accepted": True
        })
        assert r.status_code == 200
        _CREATED_USER_IDS.append(r.json()["user"]["id"])
        tok = r.json()["token"]
        files = {"file": ("logo.png", io.BytesIO(PNG_1x1), "image/png")}
        r = requests.post(f"{BASE}/api/firm/logo",
                          headers={"Authorization": f"Bearer {tok}"}, files=files)
        assert r.status_code == 403

    def test_firm_logo_404_for_firm_without_logo(self):
        token, user = _register_firm_admin()
        headers = {"Authorization": f"Bearer {token}"}
        prof = requests.get(f"{BASE}/api/adviser/profile", headers=headers).json()
        firm_id = prof["firm_id"]
        r = requests.get(f"{BASE}/api/firm-logo/{firm_id}")
        assert r.status_code == 404

    def test_firm_logo_404_invalid_id(self):
        r = requests.get(f"{BASE}/api/firm-logo/notavalidid")
        assert r.status_code == 404


# ---------------- PUT /firm brand color ----------------
class TestPutFirm:
    def test_put_firm_brand_color(self):
        token, _ = _register_firm_admin()
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.put(f"{BASE}/api/firm", headers=headers, json={
            "name": "Updated Firm Name TEST", "fca_number": "111111",
            "principal_name": "", "principal_fca_number": "", "brand_color": "#00ff00"
        })
        assert r.status_code == 200, r.text
        assert r.json()["brand_color"] == "#00ff00"

    def test_put_firm_invalid_hex_422(self):
        token, _ = _register_firm_admin()
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.put(f"{BASE}/api/firm", headers=headers, json={
            "name": "X", "fca_number": "", "principal_name": "", "principal_fca_number": "", "brand_color": "lime"
        })
        assert r.status_code == 422


# ---------------- Invite + Start pages include logo/brand ----------------
class TestInviteBranding:
    def test_invite_page_includes_brand(self):
        token, user = _register_firm_admin()
        code = user["adviser_code"]
        headers = {"Authorization": f"Bearer {token}"}
        # Upload logo first
        files = {"file": ("logo.png", io.BytesIO(PNG_1x1), "image/png")}
        up = requests.post(f"{BASE}/api/firm/logo", headers=headers, files=files)
        if up.status_code == 503:
            pytest.skip("Storage service unavailable")
        assert up.status_code == 200
        # Invite
        r = requests.get(f"{BASE}/api/invite/{code}")
        assert r.status_code == 200
        html = r.text
        assert "/api/firm-logo/" in html
        assert "#ff0066" in html.lower() or "#FF0066" in html
        # Start
        # Cache-bust via unique src query param (CF edge caches by URL)
        r2 = requests.get(f"{BASE}/api/start/{code}?src=T{uuid.uuid4().hex[:6]}",
                          headers={"Cache-Control": "no-cache"})
        assert r2.status_code == 200
        assert "/api/firm-logo/" in r2.text


# ---------------- Regression: Mark/SFL ----------------
class TestRegression:
    def test_mark_profile_founder_plan(self):
        _clear_rate_limits()
        r = requests.post(f"{BASE}/api/auth/login", json={"email": MARK_EMAIL, "password": MARK_PASS})
        assert r.status_code == 200, r.text
        tok = r.json()["token"]
        p = requests.get(f"{BASE}/api/adviser/profile", headers={"Authorization": f"Bearer {tok}"})
        assert p.status_code == 200
        prof = p.json()
        assert prof["plan"] == "founder"
        assert prof["trial_days_left"] is None
        assert prof["adviser_code"] == "MARK-SFL"

    def test_tom_login(self):
        _clear_rate_limits()
        r = requests.post(f"{BASE}/api/auth/login", json={"email": "tom@example.com", "password": "test1234"})
        assert r.status_code == 200
        assert "token" in r.json()
