import os
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import cache
from analyzers.bus_factor import find_bus_factor
from analyzers.coupling import find_coupling
from analyzers.graph import build_graph
from analyzers.hotspots import find_hotspots
from analyzers.pr_risk import assess_pr
from models import Commit
from tmp_ratelimit import RateLimiter
from repo import RepoError, RepoTooLarge, head_hash, is_new_repo, read_commits, sync_repo
import shutil

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")


app = FastAPI(title="Git History Intelligence")



app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


BAD_REPO = "Could not load that repository. Check the owner and name."
TOO_LARGE = "This repository is too large for this demo. Try one with a smaller history."
TOO_MANY = "Too many requests. Please wait a minute and try again."
TOO_MANY_NEW = "You have analyzed several new repositories recently. Please wait a few minutes."
GRAPH_EDGES = 40

request_limiter = RateLimiter(int(os.environ.get("REQUESTS_PER_MINUTE", "60")), 60)
download_limiter = RateLimiter(int(os.environ.get("NEW_REPOS_PER_10_MIN", "5")), 600)


def enforce_limits(request : Request , owner : str , name : str) -> None:
    ip = request.client.host if request.client else "unknown" 
    if not request_limiter.allow(ip):
        raise HTTPException(status_code=429,detail=TOO_MANY,headers={"Retry-After": "60"})
    if is_new_repo(owner,name) and not download_limiter.allow(ip):
        raise HTTPException(status_code=429,detail=TOO_MANY_NEW,headers={"Retry-After": "600"})
    

class RiskRequest(BaseModel):
    files: list[str] = Field(min_length=1, max_length=2500)
    months: int = Field(24, ge=1, le=600)


@app.get("/")
def root():
    return {"status": "ok", "git": shutil.which("git") is not None}


@app.get("/health")
def health():
    return {"status": "ok"}


def load_history(owner: str, name: str) -> tuple[str, list[Commit]]:
    key = f"{owner}/{name}".lower()
    path = sync_repo(owner, name)
    head = head_hash(path)
    cached = cache.get_history(key)
    if cached and cached[0] == head:
        return cached
    commits = read_commits(path)
    cache.put_history(key, head, commits)
    return head, commits


def recent_commits(commits: list[Commit], months: int) -> list[Commit]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)
    return [c for c in commits if c.date >= cutoff]


def build_result(owner: str, name: str, commits: list[Commit], months: int) -> dict:
    recent = recent_commits(commits, months)
    pairs = find_coupling(recent, top_n=GRAPH_EDGES)
    return {
        "repo": f"{owner}/{name}",
        "commit_count": len(commits),
        "window_months": months,
        "recent_commit_count": len(recent),
        "hotspots": [
            {"path": path, "changes": count}
            for path, count in find_hotspots(recent)
        ],
        "coupling": [
            {"a": a, "b": b, "together": together, "strength": round(strength, 2)}
            for a, b, together, strength in pairs[:10]
        ],
        "graph": build_graph(recent, pairs),
        "bus_factor": [
            {
                "area": area,
                "top_author": author,
                "share": round(share, 2),
                "commits": total,
                "authors": n_authors,
                "last_active": last.date().isoformat(),
            }
            for area, author, share, total, n_authors, last in find_bus_factor(commits)
        ],
    }


@app.get("/analyze/{owner}/{name}")
def analyze(request: Request,owner: str, name: str, months: int = Query(24, ge=1, le=600)):
    enforce_limits(request, owner, name)
    key = f"{owner}/{name}/{months}".lower()
    entry = cache.get(key)
    if entry and cache.is_fresh(entry):
        return entry["result"]

    try:
        head, commits = load_history(owner, name)
    except RepoTooLarge:
        raise HTTPException(status_code=413, detail=TOO_LARGE)
    except RepoError:
        raise HTTPException(status_code=400, detail=BAD_REPO)

    if entry and entry["head"] == head:
        cache.touch(key)
        return entry["result"]

    result = build_result(owner, name, commits, months)
    cache.put(key, head, result)
    return result


@app.post("/risk/{owner}/{name}")
def risk(request : Request,owner: str, name: str, body: RiskRequest):
    enforce_limits(request, owner, name)
    try:
        _, commits = load_history(owner, name)
    except RepoTooLarge:
        raise HTTPException(status_code=413, detail=TOO_LARGE)
    except RepoError:
        raise HTTPException(status_code=400, detail=BAD_REPO)

    result = assess_pr(recent_commits(commits, body.months), body.files)
    return {
        "repo": f"{owner}/{name}",
        "window_months": body.months,
        "score": result.score,
        "level": result.level,
        "reasons": result.reasons,
    }