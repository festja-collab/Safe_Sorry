# Iteration 18: mobile-first website + "trading style of SFL" regulatory wording everywhere
import os
import re
import html as htmlmod
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL", os.environ.get("EXPO_BACKEND_URL", "")).rstrip("/")
WORDING = ("Safe > Sorry is a trading style of Secure for Life Wealth Management Ltd (FRN 912517), which is an "
           "Appointed Representative of Rosemount Financial Solutions (IFA) Limited (FRN 535515), which is "
           "authorised and regulated by the Financial Conduct Authority.")
BANNED = ["App Store", "Google Play", "Coming soon", "coming soon", "#comingsoon"]


def text_of(r):
    t = htmlmod.unescape(r.text)
    return re.sub(r"\s+", " ", t)


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# Landing pages (/start, /start/{code}?src, /invite/{code})
@pytest.mark.parametrize("path,code", [
    ("/api/start", "MARK-SFL"),
    ("/api/start/MARK-SFL?src=IG", "MARK-SFL-IG"),
    ("/api/invite/MARK-SFL?name=Jo", "MARK-SFL-INV"),
])
def test_landing_pages(s, path, code):
    r = s.get(BASE_URL + path)
    assert r.status_code == 200
    t = text_of(r)
    assert WORDING in t, "trading-style wording missing"
    m = re.search(r'<a[^>]*id="start-check"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>', r.text)
    assert m, "start-check button missing"
    assert htmlmod.unescape(m.group(1)) == f"/auth?mode=register&code={code}"
    assert m.group(2).strip() == "Start your free check"
    for b in BANNED:
        assert b not in t, f"banned text {b!r} present"


def test_invite_has_name(s):
    t = text_of(s.get(BASE_URL + "/api/invite/MARK-SFL?name=Jo"))
    assert "Hi Jo," in t


def test_unknown_code_404(s):
    assert s.get(BASE_URL + "/api/start/NOPE-XXXX").status_code == 404
    assert s.get(BASE_URL + "/api/invite/NOPE-XXXX").status_code == 404


# Privacy notice
def test_privacy_who_we_are(s):
    r = s.get(BASE_URL + "/api/privacy")
    assert r.status_code == 200
    sec = {x["heading"]: x["body"] for x in r.json()["sections"]}
    assert WORDING in sec["Who we are"]


# Rosemount review pages
@pytest.mark.parametrize("path", ["/api/presentation", "/api/compliance-pack", "/api/posting-plan"])
def test_review_pages_wording(s, path):
    r = s.get(BASE_URL + path)
    assert r.status_code == 200
    assert WORDING in text_of(r)


def test_posting_plan_no_coming_soon(s):
    t = text_of(s.get(BASE_URL + "/api/posting-plan"))
    assert "coming soon" not in t.lower()
    assert "#comingsoon" not in t.lower()
    assert "link in bio" in t.lower()


def test_landing_pages_no_download_wording_elsewhere(s):
    for p in ["/api/presentation", "/api/compliance-pack"]:
        t = text_of(s.get(BASE_URL + p))
        for b in ["App Store", "Google Play"]:
            assert b not in t, f"{b} in {p}"


# Reels page + range streaming
def test_reels_and_range(s):
    r = s.get(BASE_URL + "/api/reels")
    assert r.status_code == 200
    vids = sorted(set(re.findall(r'<video src="/api/reels/file/([^"]+\.mp4)"', r.text)))
    assert len(vids) == 9, vids
    zips = set(re.findall(r'/api/reels/file/([^"?]+\.zip)', r.text))
    assert len(zips) == 3, zips
    for v in vids:
        rr = s.get(f"{BASE_URL}/api/reels/file/{v}", headers={"Range": "bytes=0-1023"})
        assert rr.status_code == 206, v
        assert rr.headers["Content-Type"] == "video/mp4"
        assert len(rr.content) == 1024
        assert b"ftyp" in rr.content[:64]
    for z in zips:
        rz = s.get(f"{BASE_URL}/api/reels/file/{z}", headers={"Range": "bytes=0-3"})
        assert rz.status_code == 206 and rz.content[:2] == b"PK"


# Regression: desk login
def test_desk_login(s):
    r = s.post(BASE_URL + "/api/desk/login", json={"email": "desk.adviser@example.com", "password": "DeskTest-2026!"})
    assert r.status_code == 200, r.text
    assert r.json().get("token")


# Adviser profile used by app adviser tab (desk test adviser -> firm wording; default adviser -> SFL wording)
def test_client_adviser_regulatory_status(s):
    r = s.post(BASE_URL + "/api/auth/login", json={"email": "desk.client@example.com", "password": "DeskClient-2026"})
    assert r.status_code == 200
    tok = r.json()["token"]
    me = s.get(BASE_URL + "/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert me.status_code == 200
