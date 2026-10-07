from fnmatch import fnmatch

IGNORED_DIRS = {"node_modules", "dist", "build", "vendor", "coverage", "__pycache__"}
IGNORED_NAMES = {
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "cargo.lock", "go.sum", "gemfile.lock", "composer.lock",
    "history.md", "changelog.md", "changes.md",
}
IGNORED_PATTERNS = (
    "*.lock", "*.min.js", "*.min.css", "*.map",
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.svg",
)


def is_noise(path: str) -> bool:
    parts = path.lower().split("/")
    if any(part in IGNORED_DIRS for part in parts[:-1]):
        return True
    name = parts[-1]
    return name in IGNORED_NAMES or any(fnmatch(name, pat) for pat in IGNORED_PATTERNS)