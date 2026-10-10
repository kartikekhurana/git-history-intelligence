import time
from collections import defaultdict , deque
from threading import Lock

MAX_TRACKED_KEYS = 10_000

class RateLimiter:
    def __init__(self , limit : int , window_seconds : int):
        self.limit = limit
        self.window = window_seconds
        self._hits : defaultdict[str , deque[float]] = defaultdict(deque)
        self._lock = Lock()
    
    def allow(self , key : str) -> bool:
        now = time.monotonic()
        with self._lock:
            if len(self._hits) > MAX_TRACKED_KEYS:
                self._forget_idle(now)
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True
    
    def _forget_idle(self , now : float) -> None:
        idle = [k for k, h in self._hits.items() if not h or now - h[-1] > self.window]
        for k in idle:
            del self._hits[k]