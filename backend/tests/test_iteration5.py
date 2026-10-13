"""Iteration 5: change-password, firm advisers, forced first-login, ad landing, lead tracking."""
import os
import uuid
import pytest
import requests
from pymongo import MongoClient
from bson import ObjectId

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "https://protect-me-17.preview.emergentagent.com").rstrip("/")
MARK_EMAIL = "mark.turner@sflwealth.co.uk"
MARK_PASSWORD = "IupwtaavjJ2CfMKIFjRhfott"
TOM_EMAIL = "tom@example.com"
TOM_PASSWORD = "test1234"

# Direct mongo for cleanup
MONGO = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
DB = MONGO[os.environ.get("DB_NAME", "test_database")]


def _ip():
    """unique IP so rate limits don't bite."""
    return f"203.0.113.{uuid.uuid4().int % 250 + 1}"


def _h(ip=None, token=None):
    h = {"Content-Type": "application/json", "X-Forwarded-For": ip or _ip()}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _reset_limits():
    DB.rate_limits.delete_many({})


@pytest.fixture(autouse=True, scope="session")
def _clear_limits():
    _reset_limits()
    yield
    # Final cleanup done manually at end of iteration


# ---------- helpers ----------
def register_client(name="Test Client", adviser_code="", heard_from=""):
    email = f"TEST_{uuid.uuid4().hex[:10]}@example.com"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": name, "email": email, "password": "TestPass1234",
        "adviser_code": adviser_code, "heard_from": heard_from
    }, headers=_h())
    r.raise_for_status()
    return email, "TestPass1234", r.json()


def mark_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": MARK_EMAIL, "password": MARK_PASSWORD}, headers=_h())
    assert r.status_code == 200, r.text
    return r.json()["token"]


# ===== 1. Change password =====
class TestChangePassword:
    def test_change_password_flow(self):
        email, pw, s = register_client()
        token_old = s["token"]
        try:
            # Wrong current -> 400
            r = requests.post(f"{BASE_URL}/api/auth/change-password",
                              json={"current_password": "wrongwrong", "new_password": "NewSecret99"},
                              headers=_h(token=token_old))
            assert r.status_code == 400

            # Same password -> 400
            r = requests.post(f"{BASE_URL}/api/auth/change-password",
                              json={"current_password": pw, "new_password": pw},
                              headers=_h(token=token_old))
            assert r.status_code == 400

            # Too short new password -> 422
            r = requests.post(f"{BASE_URL}/api/auth/change-password",
                              json={"current_password": pw, "new_password": "short"},
                              headers=_h(token=token_old))
            assert r.status_code == 422

            # Success
            new_pw = "NewSecret99X"
            r = requests.post(f"{BASE_URL}/api/auth/change-password",
                              json={"current_password": pw, "new_password": new_pw},
                              headers=_h(token=token_old))
            assert r.status_code == 200, r.text
            data = r.json()
            assert "token" in data and "user" in data
            token_new = data["token"]
            assert token_new != token_old

            # Old token now 401 on /auth/me
            r = requests.get(f"{BASE_URL}/api/auth/me", headers=_h(token=token_old))
            assert r.status_code == 401, f"Old token should be revoked, got {r.status_code}"

            # New token works
            r = requests.get(f"{BASE_URL}/api/auth/me", headers=_h(token=token_new))
            assert r.status_code == 200
            assert r.json()["email"].lower() == email.lower()

            # Login with new password works
            r = requests.post(f"{BASE_URL}/api/auth/login",
                              json={"email": email, "password": new_pw}, headers=_h())
            assert r.status_code == 200
        finally:
            DB.users.delete_one({"email": email})

    def test_change_password_rate_limit(self):
        email, pw, s = register_client()
        token = s["token"]
        try:
            # 5 wrong attempts -> 429 on 6th
            for i in range(5):
                r = requests.post(f"{BASE_URL}/api/auth/change-password",
                                  json={"current_password": "wrongwrong", "new_password": "AnotherOne11"},
                                  headers=_h(token=token))
                assert r.status_code == 400, f"attempt {i}: {r.status_code}"
            r = requests.post(f"{BASE_URL}/api/auth/change-password",
                              json={"current_password": "wrongwrong", "new_password": "AnotherOne11"},
                              headers=_h(token=token))
            assert r.status_code == 429
        finally:
            DB.users.delete_one({"email": email})


# ===== 2. Firm admin add adviser =====
class TestFirmAdvisers:
    created_emails = []

    def test_add_adviser_and_list(self):
        token = mark_token()
        name = f"TestAdviser{uuid.uuid4().hex[:4]}"
        email = f"TEST_{uuid.uuid4().hex[:8]}@sflwealth.co.uk"
        self.created_emails.append(email)
        r = requests.post(f"{BASE_URL}/api/firm/advisers",
                          json={"name": name, "email": email, "title": "Protection Adviser"},
                          headers=_h(token=token))
        assert r.status_code == 200, r.text
        data = r.json()
        assert "adviser_code" in data and data["adviser_code"].endswith("-SFL")
        assert "temporary_password" in data and len(data["temporary_password"]) >= 10
        assert data["email"] == email.lower()

        # Duplicate -> 409
        r2 = requests.post(f"{BASE_URL}/api/firm/advisers",
                           json={"name": name, "email": email, "title": "x"},
                           headers=_h(token=token))
        assert r2.status_code == 409

        # List
        r3 = requests.get(f"{BASE_URL}/api/firm/advisers", headers=_h(token=token))
        assert r3.status_code == 200
        advisers = r3.json()
        new = [a for a in advisers if a["email"] == email.lower()]
        assert len(new) == 1
        assert new[0]["pending_setup"] is True

    def test_dedupe_code(self):
        token = mark_token()
        base_name = f"Dedupe{uuid.uuid4().hex[:4]}"
        codes = []
        for i in range(2):
            email = f"TEST_dupe{uuid.uuid4().hex[:6]}@sflwealth.co.uk"
            self.created_emails.append(email)
            r = requests.post(f"{BASE_URL}/api/firm/advisers",
                              json={"name": base_name, "email": email, "title": "x"},
                              headers=_h(token=token))
            assert r.status_code == 200, r.text
            codes.append(r.json()["adviser_code"])
        assert codes[0] != codes[1]
        # Second should have digit before -SFL
        assert any(c.rstrip("-SFL")[-1].isdigit() for c in codes[1:])

    def test_non_admin_cannot_add(self):
        # Register a plain client, confirm 403
        email, pw, s = register_client()
        try:
            r = requests.post(f"{BASE_URL}/api/firm/advisers",
                              json={"name": "Nope", "email": f"nope{uuid.uuid4().hex[:5]}@x.com", "title": "x"},
                              headers=_h(token=s["token"]))
            assert r.status_code == 403
        finally:
            DB.users.delete_one({"email": email})

    @classmethod
    def teardown_class(cls):
        for e in cls.created_emails:
            DB.users.delete_one({"email": e.lower()})


# ===== 3. Forced first-login =====
class TestForcedFirstLogin:
    def test_new_adviser_must_change_password(self):
        token = mark_token()
        email = f"TEST_forced{uuid.uuid4().hex[:6]}@sflwealth.co.uk"
        name = f"ForcedAdv{uuid.uuid4().hex[:4]}"
        r = requests.post(f"{BASE_URL}/api/firm/advisers",
                          json={"name": name, "email": email, "title": "Protection Adviser"},
                          headers=_h(token=token))
        assert r.status_code == 200
        temp = r.json()["temporary_password"]
        try:
            # Login with temp
            r2 = requests.post(f"{BASE_URL}/api/auth/login",
                               json={"email": email, "password": temp}, headers=_h())
            assert r2.status_code == 200
            data = r2.json()
            assert data["user"]["must_change_password"] is True
            new_token = data["token"]

            # Protected endpoints blocked
            r3 = requests.get(f"{BASE_URL}/api/adviser/stats", headers=_h(token=new_token))
            assert r3.status_code == 403
            r4 = requests.get(f"{BASE_URL}/api/assessments", headers=_h(token=new_token))
            assert r4.status_code == 403

            # /auth/me still works
            r5 = requests.get(f"{BASE_URL}/api/auth/me", headers=_h(token=new_token))
            assert r5.status_code == 200
            assert r5.json()["must_change_password"] is True

            # Change password works
            r6 = requests.post(f"{BASE_URL}/api/auth/change-password",
                               json={"current_password": temp, "new_password": "FreshPass123A"},
                               headers=_h(token=new_token))
            assert r6.status_code == 200
            final_token = r6.json()["token"]
            assert r6.json()["user"]["must_change_password"] is False

            # Now stats work
            r7 = requests.get(f"{BASE_URL}/api/adviser/stats", headers=_h(token=final_token))
            assert r7.status_code == 200
        finally:
            DB.users.delete_one({"email": email.lower()})


# ===== 4. Ad landing page =====
class TestAdLanding:
    def test_start_with_code_and_src(self):
        r = requests.get(f"{BASE_URL}/api/start/MARK-SFL?src=fb", headers=_h())
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        assert "MARK-SFL-FB" in r.text
        # Ad copy present
        assert "Most families never ask" in r.text

    def test_start_default(self):
        r = requests.get(f"{BASE_URL}/api/start", headers=_h())
        assert r.status_code == 200
        assert "MARK-SFL" in r.text

    def test_start_unknown_code(self):
        r = requests.get(f"{BASE_URL}/api/start/UNKNOWN-XX", headers=_h())
        assert r.status_code == 404

    def test_src_sanitised(self):
        # non-alphanumeric stripped, max 12
        r = requests.get(f"{BASE_URL}/api/start/MARK-SFL?src=<fb!@#01234567890123>", headers=_h())
        assert r.status_code == 200
        # Should produce MARK-SFL-FB012345678901 (max 12 after strip)
        assert "MARK-SFL-FB" in r.text
        assert "<fb" not in r.text  # escaped/stripped

    def test_invite_shows_inv_suffix(self):
        r = requests.get(f"{BASE_URL}/api/invite/MARK-SFL", headers=_h())
        assert r.status_code == 200
        assert "MARK-SFL-INV" in r.text


# ===== 5. Lead tracking =====
class TestLeadTracking:
    created_emails = []

    def _reg_and_lead(self, adviser_code, heard=""):
        email, pw, s = register_client(adviser_code=adviser_code, heard_from=heard)
        self.created_emails.append(email)
        token = s["token"]
        r = requests.post(f"{BASE_URL}/api/leads",
                          json={"name": "Lead Test", "phone": "07123456789", "preferred_time": "evenings", "message": "hi"},
                          headers=_h(token=token))
        assert r.status_code == 200, r.text
        return email, token, r.json()["id"]

    def test_source_labels(self):
        token = mark_token()
        # Campaign FB
        _, _, lid_fb = self._reg_and_lead("MARK-SFL-FB", heard="Facebook / Instagram")
        # Invite
        _, _, lid_inv = self._reg_and_lead("MARK-SFL-INV")
        # Exact code
        _, _, lid_code = self._reg_and_lead("MARK-SFL")
        # Blank
        _, _, lid_blank = self._reg_and_lead("")

        r = requests.get(f"{BASE_URL}/api/adviser/leads", headers=_h(token=token))
        assert r.status_code == 200
        leads_by_id = {l["id"]: l for l in r.json()}

        fb = leads_by_id[lid_fb]
        assert fb["source_label"] == "Campaign: FB", fb
        assert fb["source_code"] == "MARK-SFL-FB"
        assert fb["heard_from"] == "Facebook / Instagram"

        assert leads_by_id[lid_inv]["source_label"] == "Invite link"
        assert leads_by_id[lid_code]["source_label"] == "Adviser code"
        assert leads_by_id[lid_blank]["source_label"] == "No code"

    def test_stats_by_source(self):
        token = mark_token()
        _, _, _ = self._reg_and_lead("MARK-SFL-FB", heard="Google")
        r = requests.get(f"{BASE_URL}/api/adviser/stats", headers=_h(token=token))
        assert r.status_code == 200
        data = r.json()
        assert "by_source" in data and isinstance(data["by_source"], list)
        assert "by_heard" in data and isinstance(data["by_heard"], list)
        labels = [x["label"] for x in data["by_source"]]
        assert any("Campaign" in l for l in labels)

    @classmethod
    def teardown_class(cls):
        for e in cls.created_emails:
            u = DB.users.find_one({"email": e.lower()})
            if u:
                DB.leads.delete_many({"user_id": str(u["_id"])})
                DB.users.delete_one({"_id": u["_id"]})


# ===== 6. Regression =====
class TestRegression:
    def test_tom_login(self):
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": TOM_EMAIL, "password": TOM_PASSWORD}, headers=_h())
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        # my-adviser
        r2 = requests.get(f"{BASE_URL}/api/my-adviser", headers=_h(token=token))
        assert r2.status_code == 200
        assert r2.json()["adviser_code"] == "MARK-SFL"

    def test_mark_dashboard(self):
        token = mark_token()
        r = requests.get(f"{BASE_URL}/api/adviser/stats", headers=_h(token=token))
        assert r.status_code == 200
        r = requests.get(f"{BASE_URL}/api/adviser/leads", headers=_h(token=token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)
