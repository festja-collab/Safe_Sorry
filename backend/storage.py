"""Emergent Object Storage helpers (firm logos)."""
import os
import logging
import requests

logger = logging.getLogger(__name__)
STORAGE_BASE = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip() or "https://integrations.emergentagent.com"
STORAGE_URL = STORAGE_BASE.rstrip("/") + "/objstore/api/v1/storage"
APP_PREFIX = "safe-sorry"
_key = None


def init_storage() -> str:
    global _key
    if _key:
        return _key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": os.environ.get("EMERGENT_LLM_KEY")}, timeout=30)
    resp.raise_for_status()
    _key = resp.json()["storage_key"]
    return _key


def _call(method: str, path: str, **kw) -> requests.Response:
    global _key
    for attempt in range(2):
        resp = requests.request(method, f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": init_storage(), **kw.pop("headers", {})}, **kw)
        if resp.status_code == 503 and attempt == 0:
            _key = None  # stale key: re-init once
            continue
        resp.raise_for_status()
        return resp
    return resp


def put_object(path: str, data: bytes, content_type: str) -> dict:
    return _call("PUT", path, headers={"Content-Type": content_type}, data=data, timeout=120).json()


def get_object(path: str) -> tuple[bytes, str]:
    resp = _call("GET", path, timeout=60)
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")
