import os 
import re
import subprocess
from pathlib import Path
from models import Commit
from parser import parse_git_log
from filter import is_noise


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
    path = DATA_DIR / f"{owner.lower()}__{name.lower()}.git"
    if path.exists():
        _git("fetch", "--quiet", "origin", "+refs/heads/*:refs/heads/*", cwd=path)
    else:
        DATA_DIR.mkdir(parents=True,exist_ok=True)
        _git(
            "clone", "--bare", "--filter=blob:none", "--quiet",
            f"https://github.com/{owner}/{name}.git", str(path),
        )
    return path

def head_hash(path: Path) -> str:
    return _git("rev-parse", "HEAD", cwd=path).strip()

def read_commits(path: Path) -> list[Commit]:
    raw = _git(
        "log", "--no-renames", "--name-only",
        f"--pretty=format:{LOG_FORMAT}", "--date=iso",
        cwd=path,
    )
    commits =  parse_git_log(raw)
    for commit in commits:
        commit.files = [f for f in commit.files if not is_noise(f)]
    return commits

def load_commits(owner : str , name : str) -> list[Commit]:
    return read_commits(sync_repo(owner, name))