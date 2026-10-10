import os
import threading
import time
from collections import OrderedDict
from typing import Any
from models import Commit

FRESH_SECONDS = 60
MAX_RESULTS = int(os.environ.get("MAX_RESULTS", "200"))
MAX_HISTORIES = int(os.environ.get("MAX_HISTORIES", "4"))


_lock = threading.Lock()
_results : OrderedDict[str,dict[str,Any]] = OrderedDict()
_histories : OrderedDict[str, tuple[str,list[Commit]]] = OrderedDict()



def get(key : str) -> dict[str , Any] | None:
    with _lock:
        entry = _results.get(key)
        if entry is not None:
            _results.move_to_end(key)
        return entry


def is_fresh(entry: dict[str , Any]) -> bool:
    return time.time() - entry['checked_at'] < FRESH_SECONDS


def put(key: str, head: str, result: dict[str, Any]) -> None:
    with _lock:
        _results[key] = {"head": head, "result": result, "checked_at": time.time()}
        _results.move_to_end(key)
        while len(_results) > MAX_RESULTS:
            _results.popitem(last=False)

def touch(key: str) -> None:
    with _lock:
        if key in _results:
            _results[key]["checked_at"] = time.time()


def get_history(key : str) -> tuple[str , list[Commit]] | None:
    with _lock:
        entry = _histories.get(key)
        if entry is not None:
            _histories.move_to_end(key)
        return entry

def put_history(key : str, head : str , commits : list[Commit]) -> None:
    with _lock:
        _histories[key] = (head, commits)
        _histories.move_to_end(key)
        while len(_histories) > MAX_HISTORIES:
            _histories.popitem(last=False)
