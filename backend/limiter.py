"""MongoDB-backed fixed-window rate limiter shared by all workers."""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
from pymongo.errors import DuplicateKeyError


def _window(seconds: int):
    now = datetime.now(timezone.utc)
    epoch = int(now.timestamp())
    start = datetime.fromtimestamp(epoch - epoch % seconds, timezone.utc)
    retry = max(1, int((start + timedelta(seconds=seconds) - now).total_seconds()))
    return start, retry


def _doc_id(namespace: str, key: str, start: datetime) -> str:
    return f"{namespace}:{key}:{start.isoformat()}"


def _too_many(message: str, retry: int) -> HTTPException:
    return HTTPException(status_code=429, detail=message, headers={"Retry-After": str(retry)})


async def take(coll, *, namespace: str, key: str, limit: int, window: int, message: str) -> None:
    """Atomically consume one unit; raise 429 if the window is full."""
    start, retry = _window(window)
    filt = {"_id": _doc_id(namespace, key, start), "count": {"$lt": limit}}
    update = {"$inc": {"count": 1}, "$setOnInsert": {"expires_at": start + timedelta(seconds=window + 60)}}
    try:
        res = await coll.update_one(filt, update, upsert=True)
    except DuplicateKeyError:  # window already full, or concurrent first insert
        res = await coll.update_one(filt, update, upsert=False)
    if res.matched_count == 0 and res.upserted_id is None:
        raise _too_many(message, retry)


async def check(coll, *, namespace: str, key: str, limit: int, window: int, message: str) -> None:
    """Raise 429 if the window is already full, without consuming a unit."""
    start, retry = _window(window)
    doc = await coll.find_one({"_id": _doc_id(namespace, key, start)})
    if doc and doc.get("count", 0) >= limit:
        raise _too_many(message, retry)


async def record(coll, *, namespace: str, key: str, window: int) -> None:
    """Count one event (e.g. a failed login) without enforcing a limit."""
    start, _ = _window(window)
    await coll.update_one(
        {"_id": _doc_id(namespace, key, start)},
        {"$inc": {"count": 1}, "$setOnInsert": {"expires_at": start + timedelta(seconds=window + 60)}},
        upsert=True,
    )


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    ip = fwd.split(",")[0].strip()
    return ip or (request.client.host if request.client else "unknown")
