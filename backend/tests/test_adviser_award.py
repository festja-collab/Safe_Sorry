"""Tests for the adviser 'award' field (iteration 10)."""
import os
import pytest

EXPECTED_AWARD = "Protection Adviser of the Year 2026 \u00b7 Next Intelligence Awards"
TOM_EMAIL = "tom@example.com"
TOM_PASSWORD = "test1234"
MARK_EMAIL = "mark.turner@sflwealth.co.uk"
MARK_PASSWORD = "IupwtaavjJ2CfMKIFjRhfott"


@pytest.fixture
def tom_token(base_url, api):
    r = api.post(f"{base_url}/api/auth/login", json={"email": TOM_EMAIL, "password": TOM_PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture
def mark_token(base_url, api):
    r = api.post(f"{base_url}/api/auth/login", json={"email": MARK_EMAIL, "password": MARK_PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["token"]


# -------- Public config endpoint (no award at /config, but adviser profile ones) --------
class TestAwardOnProfileEndpoints:
    """Verify the 'award' key is present and correct in all adviser profile responses."""

    def test_my_adviser_includes_award_for_client(self, base_url, api, tom_token):
        r = api.get(f"{base_url}/api/my-adviser", headers={"Authorization": f"Bearer {tom_token}"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "award" in data, f"'award' key missing in /my-adviser response: {list(data.keys())}"
        assert data["award"] == EXPECTED_AWARD, f"Unexpected award: {data['award']!r}"

    def test_adviser_profile_includes_award_for_adviser(self, base_url, api, mark_token):
        r = api.get(f"{base_url}/api/adviser/profile", headers={"Authorization": f"Bearer {mark_token}"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "award" in data
        assert data["award"] == EXPECTED_AWARD

    def test_config_endpoint(self, base_url, api):
        # /api/config currently only returns app_name; verify it still works (regression)
        r = api.get(f"{base_url}/api/config")
        assert r.status_code == 200
        assert "app_name" in r.json()


# -------- Edit / validation / restore flow --------
class TestAwardEditFlow:
    """Edit the award, verify persistence, restore original."""

    def _get_profile(self, base_url, api, token):
        r = api.get(f"{base_url}/api/adviser/profile", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        return r.json()

    def _put_profile(self, base_url, api, token, award):
        prof = self._get_profile(base_url, api, token)
        body = {
            "name": prof["name"],
            "title": prof["title"],
            "bio": prof["bio"],
            "award": award,
            "photo_url": prof["photo_url"],
            "phone": prof["phone"],
            "calendly_url": prof["calendly_url"],
            "lead_email": prof["email"],
        }
        return api.put(f"{base_url}/api/adviser/profile", json=body, headers={"Authorization": f"Bearer {token}"})

    def test_update_persist_restore(self, base_url, api, mark_token):
        # 1. Change
        new_award = "TEST_Award Winner 2026"
        r = self._put_profile(base_url, api, mark_token, new_award)
        assert r.status_code == 200, r.text
        assert r.json()["award"] == new_award

        # 2. Verify persisted via GET /my-adviser
        r2 = api.get(f"{base_url}/api/my-adviser", headers={"Authorization": f"Bearer {mark_token}"})
        assert r2.status_code == 200
        assert r2.json()["award"] == new_award

        # 3. Verify adviser/profile shows the same
        r3 = self._get_profile(base_url, api, mark_token)
        assert r3["award"] == new_award

        # 4. Empty award -> card should hide (API side: award == "")
        r4 = self._put_profile(base_url, api, mark_token, "")
        assert r4.status_code == 200
        assert r4.json()["award"] == ""

        # 5. Restore to original
        r5 = self._put_profile(base_url, api, mark_token, EXPECTED_AWARD)
        assert r5.status_code == 200
        assert r5.json()["award"] == EXPECTED_AWARD

        # 6. Final confirmation via /my-adviser (as a client would see it)
        r6 = api.get(f"{base_url}/api/my-adviser", headers={"Authorization": f"Bearer {mark_token}"})
        assert r6.status_code == 200
        assert r6.json()["award"] == EXPECTED_AWARD

    def test_award_too_long_returns_422(self, base_url, api, mark_token):
        over = "A" * 121
        r = self._put_profile(base_url, api, mark_token, over)
        assert r.status_code == 422, f"Expected 422 for >120-char award, got {r.status_code}: {r.text}"

        # Confirm nothing changed
        prof = self._get_profile(base_url, api, mark_token)
        assert prof["award"] == EXPECTED_AWARD, "Award was mutated by a request that should have been rejected"

    def test_award_at_boundary_120_accepted(self, base_url, api, mark_token):
        boundary = "B" * 120
        r = self._put_profile(base_url, api, mark_token, boundary)
        assert r.status_code == 200, r.text
        assert r.json()["award"] == boundary
        # Restore
        r2 = self._put_profile(base_url, api, mark_token, EXPECTED_AWARD)
        assert r2.status_code == 200
        assert r2.json()["award"] == EXPECTED_AWARD


# -------- Light regression: adviser screen call-back + firm info still work --------
class TestAdviserScreenRegression:
    def test_my_adviser_has_firm_info(self, base_url, api, tom_token):
        r = api.get(f"{base_url}/api/my-adviser", headers={"Authorization": f"Bearer {tom_token}"})
        assert r.status_code == 200
        d = r.json()
        for k in ("name", "bio", "photo_url", "firm_name", "fca_number", "phone", "calendly_url", "email"):
            assert k in d, f"missing key {k}"
        assert d["firm_name"]  # non-empty

    def test_assessments_list_works(self, base_url, api, tom_token):
        r = api.get(f"{base_url}/api/assessments", headers={"Authorization": f"Bearer {tom_token}"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)
