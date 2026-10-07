import os 
import re
import subprocess
from pathlib import Path
from models import Commit
from parser import parse_git_log


DATA_DIR = Path(__file__).parent / "data" / "repos"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
LOG_FORMAT = "--%H|%an|%ae|%ad"


class RepoError(Exception):
    pass


def _validate(part : str) -> str:
    if not NAME_RE.fullmatch(part):
        raise RepoError(f"invalid name: {part!r}")
    return part

def _git(*args: str, cwd: Path | None = None, timeout: int = 300) -> str:
    result = subprocess.run(
        ["git",*args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ,"GIT_TERMINAL_PROMPT": "0"},
    )
    if result.returncode != 0:
        raise RepoError(result.stderr.strip() or "git command failed")
    return result.stdout

def sync_repo(owner : str,name : str) -> Path:
    owner , name = _validate(owner) , _validate(name)
    path = DATA_DIR / f"{owner}__{name}.git"
    if path.exists():
        _git("fetch", "--quiet", "origin", "+refs/heads/*:refs/heads/*", cwd=path)
    else:
        DATA_DIR.mkdir(parents=True,exist_ok=True)
        _git(
            "clone", "--bare", "--filter=blob:none", "--quiet",
            f"https://github.com/{owner}/{name}.git", str(path),
        )
    return path

def load_commits(owner : str , name : str) -> list[Commit]:
    path = sync_repo(owner,name)
    raw = _git(
        "log", "--no-renames", "--name-only",
        f"--pretty=format:{LOG_FORMAT}", "--date=iso",
        cwd=path,
    )
    return parse_git_log(raw)