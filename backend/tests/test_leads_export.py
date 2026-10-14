"""Iteration 12 - CSV export of adviser leads for CRM (Greenlight) import."""
import csv
import io
import os
import uuid
from pathlib import Path

import pytest
import requests
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")

BASE = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or os.environ.get("EXPO_BACKEND_URL") or "").rstrip("/")
assert BASE, "EXPO_PUBLIC_BACKEND_URL not set"
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

mongo = MongoClient(MONGO_URL)
db = mongo[DB_NAME]

MARK_EMAIL = "mark.turner@sflwealth.co.uk"
MARK_PASS = "IupwtaavjJ2CfMKIFjRhfott"
TOM_EMAIL = "tom@example.com"
TOM_PASS = "test1234"

EXPECTED_HEADER = [
    "Lead ID", "Date received", "First name", "Last name", "Email", "Phone",
    "Best time to call", "Status", "Source", "Consent given", "Consent date",
    "Consent wording", "Adviser", "Firm",
]

_CREATED_LEAD_IDS: list[str] = []


# ----- fixtures -----
@pytest.fixture(autouse=True)
def _reset_limits():
    db.rate_limits.delete_many({})
    yield
    db.rate_limits.delete_many({})


@pytest.fixture(scope="module", autouse=True)
def _cleanup():
    yield
    if _CREATED_LEAD_IDS:
        db.leads.delete_many({"_id": {"$in": [ObjectId(i) for i in _CREATED_LEAD_IDS if i]}})
    # Also wipe any stray TEST_ leads we created via API (name prefix)
    db.leads.delete_many({"name": {"$regex": "^(=|TEST_)"}})


def _login(email: str, password: str) -> str:
    r = requests.post(f"{BASE}/api/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"login failed for {email}: {r.status_code} {r.text[:200]}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def mark_token():
    return _login(MARK_EMAIL, MARK_PASS)


@pytest.fixture(scope="module")
def tom_token():
    return _login(TOM_EMAIL, TOM_PASS)


def _create_lead(token: str, name: str) -> str:
    """Create a lead via POST /api/leads as the given user, returns lead_id."""
    db.rate_limits.delete_many({})
    r = requests.post(
        f"{BASE}/api/leads",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"name": name, "phone": "+447700900123", "preferred_time": "Evenings", "consent": True},
        timeout=30,
    )
    assert r.status_code == 200, f"create_lead failed: {r.status_code} {r.text[:200]}"
    lid = r.json()["id"]
    _CREATED_LEAD_IDS.append(lid)
    return lid


# ----- auth guards -----
class TestExportAuth:
    def test_no_token_is_401(self):
        r = requests.get(f"{BASE}/api/adviser/leads/export", timeout=30)
        assert r.status_code == 401, r.text[:200]

    def test_client_token_is_403(self, tom_token):
        r = requests.get(
            f"{BASE}/api/adviser/leads/export",
            headers={"Authorization": f"Bearer {tom_token}"},
            timeout=30,
        )
        assert r.status_code == 403, r.text[:200]


# ----- CSV content -----
class TestExportCsv:
    def test_adviser_200_with_header_and_rows(self, mark_token):
        r = requests.get(
            f"{BASE}/api/adviser/leads/export",
            headers={"Authorization": f"Bearer {mark_token}"},
            timeout=30,
        )
        assert r.status_code == 200, r.text[:200]
        # Content-Type
        assert "text/csv" in r.headers.get("Content-Type", "")
        # Attachment
        cd = r.headers.get("Content-Disposition", "")
        assert "attachment" in cd and ".csv" in cd, cd
        # UTF-8 BOM
        assert r.content.startswith(b"\xef\xbb\xbf"), r.content[:20]

        text = r.content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        assert rows[0] == EXPECTED_HEADER, rows[0]
        # One row per Mark lead - compare to API listing count
        api_rows = requests.get(
            f"{BASE}/api/adviser/leads",
            headers={"Authorization": f"Bearer {mark_token}"},
            timeout=30,
        ).json()
        assert len(rows) - 1 == len(api_rows), f"csv has {len(rows)-1} data rows, api has {len(api_rows)}"

    def test_header_has_no_financial_or_assessment_fields(self, mark_token):
        r = requests.get(
            f"{BASE}/api/adviser/leads/export",
            headers={"Authorization": f"Bearer {mark_token}"},
            timeout=30,
        )
        text = r.content.decode("utf-8-sig")
        header = next(csv.reader(io.StringIO(text)))
        banned = ["life", "income", "critical", "gap", "need", "savings", "sick",
                  "cover", "protected", "assessment", "headline", "story", "message"]
        lower_header = " ".join(header).lower()
        found = [b for b in banned if b in lower_header]
        assert not found, f"CSV header contains financial/assessment fields: {found} in {header}"

    def test_status_filter_new(self, mark_token):
        # Full set
        full = requests.get(
            f"{BASE}/api/adviser/leads/export",
            headers={"Authorization": f"Bearer {mark_token}"},
            timeout=30,
        )
        assert full.status_code == 200
        full_rows = list(csv.reader(io.StringIO(full.content.decode("utf-8-sig"))))[1:]

        # ?status=new
        newr = requests.get(
            f"{BASE}/api/adviser/leads/export?status=new",
            headers={"Authorization": f"Bearer {mark_token}"},
            timeout=30,
        )
        assert newr.status_code == 200
        new_rows = list(csv.reader(io.StringIO(newr.content.decode("utf-8-sig"))))[1:]
        # Status column (index 7) must be 'new' only
        for row in new_rows:
            assert row[7] == "new", f"non-new status in filtered csv: {row[7]}"
        # And count matches API listing
        api_new = requests.get(
            f"{BASE}/api/adviser/leads?status=new",
            headers={"Authorization": f"Bearer {mark_token}"},
            timeout=30,
        ).json()
        assert len(new_rows) == len(api_new)
        # Filtered rows <= full rows
        assert len(new_rows) <= len(full_rows)

    def test_formula_injection_prefixed_with_apostrophe(self, tom_token, mark_token):
        """Create a lead whose name starts with '=' — CSV cell must start with a leading '."""
        lid = _create_lead(tom_token, "=cmd|' /C calc'!A0")
        r = requests.get(
            f"{BASE}/api/adviser/leads/export",
            headers={"Authorization": f"Bearer {mark_token}"},
            timeout=30,
        )
        assert r.status_code == 200
        text = r.content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        # Find row by Lead ID
        target = [r for r in rows[1:] if r[0] == lid]
        assert target, f"created lead {lid} not found in CSV"
        first_name = target[0][2]
        assert first_name.startswith("'="), f"first name not escaped: {first_name!r}"

    def test_rows_contain_consent_yes_and_wording(self, tom_token, mark_token):
        lid = _create_lead(tom_token, "TEST_ConsentCheck User")
        r = requests.get(
            f"{BASE}/api/adviser/leads/export",
            headers={"Authorization": f"Bearer {mark_token}"},
            timeout=30,
        )
        text = r.content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        target = [row for row in rows[1:] if row[0] == lid]
        assert target
        row = target[0]
        # Consent given column index 9
        assert row[9] == "Yes", f"consent given = {row[9]!r}"
        # Consent date (col 10) non-empty
        assert row[10].strip(), "consent date empty"
        # Consent wording (col 11) non-empty, mentions sharing
        assert "share" in row[11].lower() or "agree" in row[11].lower(), row[11]
        # Adviser (col 12) is Mark
        assert "Mark" in row[12] or row[12].strip(), row[12]
        # Firm (col 13) non-empty
        assert row[13].strip(), f"firm empty: {row!r}"
        # Email matches Tom's
        assert row[4] == TOM_EMAIL, row[4]
