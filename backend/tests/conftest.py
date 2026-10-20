import os
import pytest
import requests

BASE_URL = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or "https://protect-me-17.preview.emergentagent.com"
BASE_URL = BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---- Protect the real adviser account (Mark) ----------------------------------------------
# Older suites log in as Mark using a test-only stand-in password and some change it. Before the
# session we snapshot Mark's real user + firm documents, swap in the stand-in password (same
# password_version, so his live sessions stay valid), and afterwards restore both documents
# exactly - his own password, sessions, profile and firm details are never left changed.
TEST_STANDIN_PASSWORD = "IupwtaavjJ2CfMKIFjRhfott"


@pytest.fixture(scope="session", autouse=True)
def _protect_real_adviser():
    import bcrypt
    from dotenv import load_dotenv
    from pymongo import MongoClient
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    cli = MongoClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    email = os.environ["DEFAULT_ADVISER_EMAIL"].lower()
    user = db.users.find_one({"email": email})
    firm = db.firms.find_one({"_id": __import__("bson").ObjectId(user["firm_id"])}) if user and user.get("firm_id") else None
    if user:
        db.users.update_one({"_id": user["_id"]}, {"$set": {
            "password_hash": bcrypt.hashpw(TEST_STANDIN_PASSWORD.encode(), bcrypt.gensalt()).decode(),
            "must_change_password": False}})
    try:
        yield
    finally:
        if user:
            db.users.replace_one({"_id": user["_id"]}, user)
        if firm:
            db.firms.replace_one({"_id": firm["_id"]}, firm)
        db.password_resets.delete_many({"user_id": str(user["_id"])} if user else {"_never": 1})
        cli.close()
