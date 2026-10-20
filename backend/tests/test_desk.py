"""Tests for the adviser desk browser page and APIs (iteration 17).

Covers: GET /api/desk HTML + security headers, POST /api/desk/login (adviser 200,
client 403, bad pw 401), /api/desk/refresh, desk token access to
/api/adviser/leads (list/detail/export), cross-adviser 404, lead_email_html with
desk_url passes emailer._assert_safe_email, and a quick auth regression.
"""
import os
import sys
import time

import jwt
import pytest
import requests

BASE_URL = "https://protect-me-17.preview.emergentagent.com"
API = f"{BASE_URL}/api"

ADVISER_EMAIL = "desk.adviser@example.com"
ADVISER_PW = "DeskTest-2026!"
CLIENT_EMAIL = "desk.client@example.com"
CLIENT_PW = "DeskClient-2026"
OTHER_ADVISER_EMAIL = "mark.turner@sflwealth.co.uk"  # do NOT login as them; used only via a cross-adviser lead


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def desk_token(session):
    r = session.post(f"{API}/desk/login", json={"email": ADVISER_EMAIL, "password": ADVISER_PW})
    assert r.status_code == 200, f"desk login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data and "user" in data
    assert data["user"]["role"] == "adviser"
    return data["token"]


# ---- /api/desk HTML page ----
class TestDeskPage:
    def test_html_200_headers(self, session):
        r = session.get(f"{API}/desk")
        assert r.status_code == 200
        ct = r.headers.get("content-type", "")
        assert "text/html" in ct, f"Expected html, got {ct}"
        assert "no-store" in (r.headers.get("cache-control") or ""), r.headers.get("cache-control")
        assert r.headers.get("x-frame-options") == "DENY"

    def test_html_contains_login_markers(self, session):
        html = session.get(f"{API}/desk").text
        for marker in ["login-email", "login-password", "login-submit",
                       "lead-detail", "lead-cover-table", "download-crm",
                       "back-to-list", "lead-row", "sfs_desk", "/api/desk/login",
                       "/api/desk/refresh", "/api/adviser/leads/export"]:
            assert marker in html, f"missing marker in desk HTML: {marker}"


# ---- /api/desk/login ----
class TestDeskLogin:
    def test_adviser_login_200_and_30min_token(self, session):
        r = session.post(f"{API}/desk/login", json={"email": ADVISER_EMAIL, "password": ADVISER_PW})
        assert r.status_code == 200
        tok = r.json()["token"]
        # exp - iat == 1800s (DO NOT verify signature; we just read claims)
        claims = jwt.decode(tok, options={"verify_signature": False})
        assert claims["exp"] - claims["iat"] == 1800, f"desk token ttl != 30min: {claims}"

    def test_client_account_blocked_403(self, session):
        r = session.post(f"{API}/desk/login", json={"email": CLIENT_EMAIL, "password": CLIENT_PW})
        assert r.status_code == 403, f"expected 403 for client, got {r.status_code} {r.text}"

    def test_wrong_password_401(self, session):
        r = session.post(f"{API}/desk/login", json={"email": ADVISER_EMAIL, "password": "WRONG-PW-xx"})
        assert r.status_code == 401, f"expected 401, got {r.status_code} {r.text}"


# ---- /api/desk/refresh ----
class TestDeskRefresh:
    def test_refresh_without_token_401(self, session):
        r = session.post(f"{API}/desk/refresh")
        assert r.status_code == 401

    def test_refresh_returns_new_token(self, session, desk_token):
        time.sleep(1)  # ensure iat differs
        r = session.post(f"{API}/desk/refresh", headers={"Authorization": f"Bearer {desk_token}"})
        assert r.status_code == 200
        tok2 = r.json()["token"]
        c1 = jwt.decode(desk_token, options={"verify_signature": False})
        c2 = jwt.decode(tok2, options={"verify_signature": False})
        assert c2["exp"] - c2["iat"] == 1800
        assert c2["iat"] >= c1["iat"], "refreshed iat should not be older"


# ---- adviser leads via desk token ----
class TestAdviserLeadsWithDeskToken:
    def test_list_leads(self, session, desk_token):
        r = session.get(f"{API}/adviser/leads", headers={"Authorization": f"Bearer {desk_token}"})
        assert r.status_code == 200, r.text
        leads = r.json()
        assert isinstance(leads, list)
        # test adviser should have at least one lead (Jane Client)
        assert len(leads) >= 1, "test adviser should have at least one seeded lead"
        names = [l.get("name") for l in leads]
        assert any("Jane" in (n or "") for n in names), f"expected Jane Client lead, got names={names}"
        # No MongoDB _id leaked
        for l in leads:
            assert "_id" not in l

    def test_lead_detail(self, session, desk_token):
        r = session.get(f"{API}/adviser/leads", headers={"Authorization": f"Bearer {desk_token}"})
        lead_id = r.json()[0]["id"]
        d = session.get(f"{API}/adviser/leads/{lead_id}", headers={"Authorization": f"Bearer {desk_token}"})
        assert d.status_code == 200
        body = d.json()
        for k in ("id", "name", "email", "phone", "status"):
            assert k in body
        assert body["id"] == lead_id

    def test_export_csv(self, session, desk_token):
        r = session.get(f"{API}/adviser/leads/export",
                        headers={"Authorization": f"Bearer {desk_token}"})
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "").lower(), r.headers
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd.lower() and ".csv" in cd.lower(), cd

    def test_cross_adviser_lead_404(self, session, desk_token):
        # A real lead id owned by a different adviser (found via db query)
        other_id = "6acdf449c72d62cf6cc852fa"
        r = session.get(f"{API}/adviser/leads/{other_id}",
                        headers={"Authorization": f"Bearer {desk_token}"})
        assert r.status_code == 404, f"expected 404 for other-adviser lead, got {r.status_code}"
        # the browser JS matches on literal "Lead not found"
        detail = r.json().get("detail", "")
        assert "not found" in detail.lower(), f"detail should say not found: {detail!r}"


# ---- lead_email_html contains View lead button and passes safe-email checks ----
class TestLeadEmailHtml:
    def test_view_lead_button_and_safety(self):
        sys.path.insert(0, "/app/backend")
        from server import lead_email_html  # noqa: WPS433
        from emailer import _assert_safe_email  # noqa: WPS433

        class _Lead:
            name = "Jane Client"
            email = "jane@example.com"
            phone = "07000 000000"
            preferred_time = "Evening"
            message = "Please call back"
        desk_url = "https://protect-me-17.preview.emergentagent.com/api/desk#lead=6ad755f93f289e4fb34cd701"
        html = lead_email_html(_Lead(), None, "Desk Test Firm", "", desk_url)
        assert "View lead" in html
        assert desk_url in html
        # Must pass the G2/G3 safety scanner
        _assert_safe_email("New Safe > Sorry adviser request: Jane Client", html)


# ---- regression: core app auth still works ----
class TestAuthRegression:
    def test_auth_login_app_token(self, session):
        r = session.post(f"{API}/auth/login", json={"email": "tom@example.com", "password": "test1234"})
        assert r.status_code == 200
        tok = r.json()["token"]
        claims = jwt.decode(tok, options={"verify_signature": False})
        # app token should be a long-lived 7d token, not the 30-min desk token
        assert claims["exp"] - claims["iat"] > 24 * 3600

    def test_adviser_leads_with_app_token(self, session):
        r = session.post(f"{API}/auth/login", json={"email": ADVISER_EMAIL, "password": ADVISER_PW})
        assert r.status_code == 200
        tok = r.json()["token"]
        r2 = session.get(f"{API}/adviser/leads", headers={"Authorization": f"Bearer {tok}"})
        assert r2.status_code == 200
