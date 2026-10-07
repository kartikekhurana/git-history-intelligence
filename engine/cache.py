import time
from typing import Any

FRESH_SECONDS = 60

_store: dict[str , dict[str,Any]] = {}


def get(key : str) -> dict[str , Any] | None:
    return _store.get(key)

def is_fresh(entry: dict[str , Any]) -> bool:
    return time.time() - entry['checked_at'] < FRESH_SECONDS

def put(key : str , head : str, result : dict[str,Any])->None:
    _store[key] = {"head" : head , "result" : result, "checked_at" : time.time()}

def touch(key : str) -> None:
    _store[key]["checked_at"] = time.time()
