"""Tests for the public adviser invite landing page (GET /api/invite/{code})."""
import os
import pytest
import requests

BASE_URL = (os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "https://protect-me-17.preview.emergentagent.com").rstrip("/")


@pytest.fixture
def http():
    s = requests.Session()
    return s


class TestInviteLanding:
    def test_valid_code_returns_200_html(self, http):
        r = http.get(f"{BASE_URL}/api/invite/MARK-SFL", params={"name": "Sarah"})
        assert r.status_code == 200, r.text
        ct = r.headers.get("content-type", "")
        assert "text/html" in ct.lower()
        html = r.text
        # Personalised greeting
        assert "Hi Sarah," in html
        # Adviser code shown
        assert "MARK-SFL" in html
        # Adviser name
        assert "Mark Turner" in html
        # FCA regulatory line (firm + principal)
        assert "SFL Wealth Management Ltd" in html
        assert "FRN 912517" in html
        assert "Appointed Representative" in html
        assert "Rosemount Financial Solutions (IFA) Limited" in html
        assert "FRN 535515" in html
        # Store links empty in env -> coming soon copy
        assert "Coming soon to the App Store and Google Play." in html

    def test_unknown_code_returns_404(self, http):
        r = http.get(f"{BASE_URL}/api/invite/NOPE-XXX", params={"name": "Sarah"})
        assert r.status_code == 404

    def test_name_param_is_html_escaped(self, http):
        r = http.get(f"{BASE_URL}/api/invite/MARK-SFL", params={"name": "<script>alert(1)</script>"})
        assert r.status_code == 200
        html = r.text
        # Raw <script> must NOT appear with the alert() payload (escaped form will have &lt;)
        assert "<script>alert(1)</script>" not in html
        # Escaped form should appear
        assert "&lt;script&gt;" in html

    def test_no_name_still_renders(self, http):
        r = http.get(f"{BASE_URL}/api/invite/MARK-SFL")
        assert r.status_code == 200
        html = r.text
        # Fallback greeting is just "Hi,"
        assert "Hi," in html
        assert "MARK-SFL" in html

    def test_name_is_truncated_to_40(self, http):
        long_name = "A" * 100
        r = http.get(f"{BASE_URL}/api/invite/MARK-SFL", params={"name": long_name})
        assert r.status_code == 200
        html = r.text
        # The 40-char version should appear
        assert "Hi " + ("A" * 40) + "," in html
        # The 41-char version should NOT appear
        assert "Hi " + ("A" * 41) + "," not in html

    def test_lowercase_code_resolves(self, http):
        # find_adviser_by_code uppercases input, so lowercase should also work
        r = http.get(f"{BASE_URL}/api/invite/mark-sfl", params={"name": "Sarah"})
        assert r.status_code == 200
        assert "MARK-SFL" in r.text


class TestInviteRegression:
    """Smoke checks that other core endpoints still work."""
    def test_config(self, http):
        r = http.get(f"{BASE_URL}/api/config")
        assert r.status_code == 200
        assert r.json().get("app_name") == "Safe > Sorry"

    def test_adviser_login_shape(self, http):
        r = http.post(f"{BASE_URL}/api/auth/login", json={
            "email": "mark.turner@sflwealth.co.uk",
            "password": "IupwtaavjJ2CfMKIFjRhfott",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert "token" in data
        u = data["user"]
        assert u["role"] == "adviser"
        assert u["is_firm_admin"] is True
        assert u["adviser_code"] == "MARK-SFL"

    def test_adviser_stats_and_leads(self, http):
        tok = http.post(f"{BASE_URL}/api/auth/login", json={
            "email": "mark.turner@sflwealth.co.uk",
            "password": "IupwtaavjJ2CfMKIFjRhfott",
        }).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        s = http.get(f"{BASE_URL}/api/adviser/stats", headers=h)
        assert s.status_code == 200
        for k in ("new", "contacted", "closed", "total", "clients"):
            assert k in s.json()
        l = http.get(f"{BASE_URL}/api/adviser/leads", headers=h)
        assert l.status_code == 200
        assert isinstance(l.json(), list)

    def test_client_login_and_my_adviser(self, http):
        tok = http.post(f"{BASE_URL}/api/auth/login", json={
            "email": "tom@example.com",
            "password": "test1234",
        }).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        r = http.get(f"{BASE_URL}/api/my-adviser", headers=h)
        assert r.status_code == 200
        assert r.json()["adviser_code"] == "MARK-SFL"
