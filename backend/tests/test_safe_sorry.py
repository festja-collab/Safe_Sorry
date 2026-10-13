"""End-to-end backend tests for Safe > Sorry API."""
import time
import uuid
import pytest


# -------- health / config --------
def test_root(api, base_url):
    r = api.get(f"{base_url}/api/")
    assert r.status_code == 200
    assert "Safe" in r.json().get("message", "")


def test_config(api, base_url):
    r = api.get(f"{base_url}/api/config")
    assert r.status_code == 200
    d = r.json()
    assert d["calendly_url"].startswith("http")
    assert d["app_name"]


# -------- auth --------
@pytest.fixture(scope="module")
def existing_user_token():
    import requests
    base = pytest.importorskip("os").environ.get("EXPO_PUBLIC_BACKEND_URL") or \
        "https://protect-me-17.preview.emergentagent.com"
    base = base.rstrip("/")
    r = requests.post(f"{base}/api/auth/login",
                      json={"email": "tom@example.com", "password": "test1234"})
    if r.status_code != 200:
        pytest.skip(f"existing user login failed: {r.status_code} {r.text}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def new_user():
    import requests
    base = (pytest.importorskip("os").environ.get("EXPO_PUBLIC_BACKEND_URL") or
            "https://protect-me-17.preview.emergentagent.com").rstrip("/")
    email = f"test_{uuid.uuid4().hex[:10]}@example.com"
    r = requests.post(f"{base}/api/auth/register",
                      json={"name": "TEST User", "email": email, "password": "secret1234", "privacy_accepted": True})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["user"]["email"] == email
    assert data["token"]
    return {"token": data["token"], "email": email, "id": data["user"]["id"], "base": base}


def test_register_duplicate(api, base_url, new_user):
    r = api.post(f"{base_url}/api/auth/register",
                 json={"name": "x", "email": new_user["email"], "password": "secret1234", "privacy_accepted": True})
    assert r.status_code == 409


def test_login_wrong_password(api, base_url, new_user):
    r = api.post(f"{base_url}/api/auth/login",
                 json={"email": new_user["email"], "password": "wrongpass"})
    assert r.status_code == 401


def test_me_requires_auth(api, base_url):
    r = api.get(f"{base_url}/api/auth/me")
    assert r.status_code in (401, 403)


def test_me_ok(api, base_url, new_user):
    r = api.get(f"{base_url}/api/auth/me",
                headers={"Authorization": f"Bearer {new_user['token']}"})
    assert r.status_code == 200
    assert r.json()["email"] == new_user["email"]


def test_existing_user_login(existing_user_token):
    assert existing_user_token


# -------- assessment --------
SAMPLE = {
    "first_name": "Tom", "age": 36, "relationship": "married",
    "partner_name": "Sarah", "partner_income": 30000,
    "children": [{"name": "Lily", "age": 4}, {"name": "Max", "age": 7}],
    "employment": "employed", "annual_income": 55000,
    "monthly_outgoings": 2200, "housing": "mortgage",
    "mortgage_balance": 220000, "monthly_housing": 1300,
    "mortgage_years": 22, "other_debts": 4000, "savings": 8000,
    "life_cover": 100000, "death_in_service": 3, "sick_pay_months": 3,
    "income_protection": 0, "critical_illness": 0, "worry": "house",
}


@pytest.fixture(scope="module")
def assessment(new_user):
    import requests
    r = requests.post(f"{new_user['base']}/api/assessments", json=SAMPLE,
                      headers={"Authorization": f"Bearer {new_user['token']}"})
    assert r.status_code == 200, r.text
    return r.json()


def test_assessment_shape(assessment):
    assert assessment["id"]
    r = assessment["results"]
    assert "headline" in r and isinstance(r["headline"], str)
    assert "runway_months" in r
    assert "gaps" in r and {"life", "income", "critical"} <= set(r["gaps"])
    assert "impacts" in r and isinstance(r["impacts"], list)
    assert "milestones" in r and isinstance(r["milestones"], list)
    assert r["gaps"]["life"]["gap"] >= 0


def test_assessment_list(api, base_url, new_user, assessment):
    r = api.get(f"{base_url}/api/assessments",
                headers={"Authorization": f"Bearer {new_user['token']}"})
    assert r.status_code == 200
    data = r.json()
    assert any(a["id"] == assessment["id"] for a in data)
    item = next(a for a in data if a["id"] == assessment["id"])
    assert "headline" in item and "runway_label" in item


def test_assessment_get_persisted(api, base_url, new_user, assessment):
    r = api.get(f"{base_url}/api/assessments/{assessment['id']}",
                headers={"Authorization": f"Bearer {new_user['token']}"})
    assert r.status_code == 200
    assert r.json()["id"] == assessment["id"]


def test_assessment_ownership(api, base_url, assessment):
    # register another user and try to access
    import requests
    email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    reg = requests.post(f"{base_url}/api/auth/register",
                        json={"name": "Other", "email": email, "password": "secret1234", "privacy_accepted": True})
    assert reg.status_code == 200
    tok = reg.json()["token"]
    r = api.get(f"{base_url}/api/assessments/{assessment['id']}",
                headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 404


# -------- story (AI, slow) --------
def test_story_generation(api, base_url, new_user, assessment):
    r = api.post(f"{base_url}/api/assessments/{assessment['id']}/story",
                 headers={"Authorization": f"Bearer {new_user['token']}"},
                 timeout=120)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["title"] and isinstance(data["paragraphs"], list) and len(data["paragraphs"]) >= 1
    assert data["closing"]
    # cached call should be fast
    t0 = time.time()
    r2 = api.post(f"{base_url}/api/assessments/{assessment['id']}/story",
                  headers={"Authorization": f"Bearer {new_user['token']}"})
    assert r2.status_code == 200
    assert r2.json()["title"] == data["title"]
    assert time.time() - t0 < 10


# -------- articles --------
def test_articles_list(api, base_url):
    r = api.get(f"{base_url}/api/articles")
    assert r.status_code == 200
    arts = r.json()
    assert isinstance(arts, list) and len(arts) > 0
    assert "slug" in arts[0] and "body" not in arts[0]


def test_article_detail(api, base_url):
    r = api.get(f"{base_url}/api/articles")
    slug = r.json()[0]["slug"]
    r = api.get(f"{base_url}/api/articles/{slug}")
    assert r.status_code == 200
    assert r.json()["slug"] == slug
    assert r.json().get("body")


def test_article_404(api, base_url):
    r = api.get(f"{base_url}/api/articles/nope-xyz")
    assert r.status_code == 404


# -------- leads --------
def test_create_lead(api, base_url, new_user, assessment):
    body = {"name": "TEST Lead", "phone": "+447123456789",
            "preferred_time": "Evenings", "message": "please help",
            "assessment_id": assessment["id"], "consent": True}
    r = api.post(f"{base_url}/api/leads", json=body,
                 headers={"Authorization": f"Bearer {new_user['token']}"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["id"]
    assert "email_sent" in d  # may be False (known billing issue)


# -------- delete assessment --------
def test_delete_assessment(api, base_url, new_user, assessment):
    r = api.delete(f"{base_url}/api/assessments/{assessment['id']}",
                   headers={"Authorization": f"Bearer {new_user['token']}"})
    assert r.status_code == 200
    r2 = api.get(f"{base_url}/api/assessments/{assessment['id']}",
                 headers={"Authorization": f"Bearer {new_user['token']}"})
    assert r2.status_code == 404
