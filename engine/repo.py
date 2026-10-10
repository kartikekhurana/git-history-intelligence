import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

from filter import is_noise
from models import Commit
from parser import parse_git_log


DATA_DIR = Path(__file__).parent / "data" / "repos"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
LOG_FORMAT = "--%H|%an|%ae|%ad"

MAX_REPO_BYTES = int(os.environ.get("MAX_REPO_MB", "100")) * 1024 * 1024
CLONE_TIMEOUT = int(os.environ.get("CLONE_TIMEOUT_SECONDS", "300"))
MAX_DISK_BYTES = int(os.environ.get("MAX_DISK_MB", "1000")) * 1024 * 1024
_locks: dict[str, threading.Lock] = {}

class RepoError(Exception):
    pass

class RepoTooLarge(RepoError):
    pass


def _validate(part : str) -> str:
    if not NAME_RE.fullmatch(part):
        raise RepoError(f"invalid name: {part!r}")
    return part

def _git(*args: str, cwd: Path | None = None, timeout: int = 300) -> str:
    try:
        result = subprocess.run(
            ["git",*args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ,"GIT_TERMINAL_PROMPT": "0"},
        )
    except subprocess.TimeoutExpired:
        raise RepoError("git took too long") from None
    if result.returncode != 0:
        raise RepoError(result.stderr.strip() or "git command failed")
    return result.stdout

def _folder_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total

def _clone(url:str , path : Path) -> None:
    process = subprocess.Popen(
        ["git", "clone", "--bare", "--filter=blob:none", "--quiet", url, str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    started = time.monotonic()
    try:
        while process.poll() is None:
            if time.monotonic() - started > CLONE_TIMEOUT:
                raise RepoError("git took too long")
            if path.exists() and _folder_size(path) > MAX_REPO_BYTES:
                raise RepoTooLarge("Repository is too large")
            time.sleep(0.5)
        if process.returncode != 0:
            raise RepoError((process.stderr.read() or "").strip() or "git clone failed")
    except BaseException:
        process.kill()
        process.wait()
        shutil.rmtree(path,ignore_errors=True)
        raise

def repo_path(owner : str , name : str) -> Path:
    owner , name = _validate(owner) , _validate(name)
    return DATA_DIR / f"{owner}__{name}.git".lower()

def is_new_repo(owner : str , name : str) -> bool:
    try:
        return not repo_path(owner , name).exists()
    except RepoError:
        return False

def _evict_old(keep: Path) -> None:
    repos = [p for p in DATA_DIR.glob("*.git") if p.is_dir()]
    sizes = {p: _folder_size(p) for p in repos}
    total = sum(sizes.values())
    for p in sorted(repos, key=lambda p: p.stat().st_mtime):
        if total <= MAX_DISK_BYTES:
            break
        if p == keep:
            continue
        lock = _locks.setdefault(p.stem, threading.Lock())
        if lock.acquire(blocking=False):
            try:
                shutil.rmtree(p, ignore_errors=True)
                total -= sizes[p]
            finally:
                lock.release()



def sync_repo(owner: str, name: str) -> Path:
    path = repo_path(owner, name)

    with _locks.setdefault(path.stem, threading.Lock()):
        if path.exists():
            _git("fetch", "--quiet", "origin", "+refs/heads/*:refs/heads/*", cwd=path)
        else:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            _clone(f"https://github.com/{owner}/{name}.git", path)
        os.utime(path, None)
    _evict_old(keep=path)
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