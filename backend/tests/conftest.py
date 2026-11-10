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
# Older suites log in as Mark using a test-only stand-in password and some change it. The FIRST test
# session (even with parallel workers) saves Mark's real user + firm documents into a guard record in
# Mongo; every session counts itself in/out; only the LAST one out restores the saved originals exactly.
# A stale guard (crashed run, >2h old) is restored before anything else, so originals are never lost.
TEST_STANDIN_PASSWORD = "IupwtaavjJ2CfMKIFjRhfott"
_GUARD_ID = "real-adviser"


def _restore(db, g):
    if g.get("user"):
        db.users.replace_one({"_id": g["user"]["_id"]}, g["user"])
        db.password_resets.delete_many({"user_id": str(g["user"]["_id"])})
    if g.get("firm"):
        db.firms.replace_one({"_id": g["firm"]["_id"]}, g["firm"])
    db.test_guard.delete_one({"_id": _GUARD_ID})


@pytest.fixture(scope="session", autouse=True)
def _protect_real_adviser():
    import time
    import bcrypt
    from bson import ObjectId
    from dotenv import load_dotenv
    from pymongo import MongoClient, ReturnDocument
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    cli = MongoClient(os.environ["MONGO_URL"])
    db = cli[os.environ["DB_NAME"]]
    stale = db.test_guard.find_one({"_id": _GUARD_ID, "started": {"$lt": time.time() - 7200}})
    if stale:
        _restore(db, stale)
    user = db.users.find_one({"email": os.environ["DEFAULT_ADVISER_EMAIL"].lower()})
    firm = db.firms.find_one({"_id": ObjectId(user["firm_id"])}) if user and user.get("firm_id") else None
    g = db.test_guard.find_one_and_update(
        {"_id": _GUARD_ID}, {"$inc": {"n": 1}, "$setOnInsert": {"user": user, "firm": firm, "started": time.time()}},
        upsert=True, return_document=ReturnDocument.AFTER)
    if g["n"] == 1 and user:   # first session in: swap in the stand-in password
        db.users.update_one({"_id": user["_id"]}, {"$set": {
            "password_hash": bcrypt.hashpw(TEST_STANDIN_PASSWORD.encode(), bcrypt.gensalt()).decode(),
            "must_change_password": False}})
    try:
        yield
    finally:
        g = db.test_guard.find_one_and_update({"_id": _GUARD_ID}, {"$inc": {"n": -1}}, return_document=ReturnDocument.AFTER)
        if g and g["n"] <= 0:  # last session out: put the real account back exactly
            _restore(db, g)
        cli.close()
