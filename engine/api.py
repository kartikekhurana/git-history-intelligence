from datetime import datetime, timedelta, timezone
from fastapi import FastAPI , HTTPException, Query
from pydantic import BaseModel, Field
import cache
from analyzers.bus_factor import find_bus_factor
from analyzers.coupling import find_coupling
from analyzers.hotspots import find_hotspots
from analyzers.pr_risk import assess_pr
from models import Commit
from repo import RepoError, head_hash, read_commits, sync_repo



app = FastAPI(title="Git History Intelligence")

BAD_REPO = "Could not load that repository. Check the owner and name."

class RiskRequest(BaseModel):
    files : list[str] = Field(min_length=1 , max_length=2500)
    months: int = Field(24, ge=1, le=600)

@app.get("/")
def root():
    return {"name": "Git History Intelligence API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status" : "ok"}


def load_history(owner : str , name : str) -> tuple[str , list[Commit]]:
    key = f"{owner}/{name}".lower()
    path = sync_repo(owner,name)
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


def build_result(owner: str, name: str, commits: list[Commit] , months : int) -> dict:
    recent = recent_commits(commits, months)
    return {
        "repo": f"{owner}/{name}",
        "commit_count": len(commits),
        "window_months" : months,
        "recent_commit_count": len(recent),
        "hotspots": [
            {"path": path, "changes": count}
            for path, count in find_hotspots(recent)
        ],
        "coupling": [
            {"a": a, "b": b, "together": together, "strength": round(strength, 2)}
            for a, b, together, strength in find_coupling(recent)
        ],
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
def analyze(owner:str , name:str , months: int = Query(24, ge=1, le=600)):
    key = f"{owner}/{name}/{months}".lower()
    entry = cache.get(key)
    if entry and cache.is_fresh(entry):
        return entry["result"]
    
    try:
        head , commits = load_history(owner,name)
    except RepoError:
        raise HTTPException(status_code=400, detail=BAD_REPO)
    if entry and entry["head"] == head:
        cache.touch(key)
        return entry["result"]

    result = build_result(owner, name, commits, months)
    cache.put(key, head, result)
    return result

@app.post("/risk/{owner}/{name}")
def risk(owner : str , name : str , body : RiskRequest):
    try:
        _, commits = load_history(owner,name)
    except RepoError:
        raise HTTPException(status_code=400, detail=BAD_REPO)
    result = assess_pr(recent_commits(commits,body.months),body.files)
    return {
        "repo" : f"{owner}/{name}",
        "window_months": body.months,
        "score": result.score,
        "level": result.level,
        "reasons": result.reasons,
    }
