import time
from typing import Any
from models import Commit

FRESH_SECONDS = 60

_results : dict[str,dict[str,Any]] = {}
_histories : dict[str, tuple[str,list[Commit]]] = {}



def get(key : str) -> dict[str , Any] | None:
    return _results.get(key)

def is_fresh(entry: dict[str , Any]) -> bool:
    return time.time() - entry['checked_at'] < FRESH_SECONDS

def put(key : str , head : str, result : dict[str,Any])->None:
    _results[key] = {"head" : head , "result" : result, "checked_at" : time.time()}

def touch(key : str) -> None:
    _results[key]["checked_at"] = time.time()

def get_history(key : str) -> tuple[str , list[Commit]] | None:
   return _histories.get(key)

def put_history(key : str, head : str , commits : list[Commit]) -> None:
    _histories[key] = (head , commits)
