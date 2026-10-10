

Readme · MD

🔍 Git History Intelligence
Know where your codebase is fragile. Paste a GitHub repo and get hotspots, hidden file coupling, ownership risk and PR risk, all built from commit history alone.
Live Demo
Show Image Show Image Show Image Show Image Show Image

✨ What it does
Reading git log by hand doesn't scale. This tool clones a public GitHub repository, mines its commit history, and turns it into four engineering signals:
Signal	Question it answers
🔥 Hotspots	Which files change the most?
🔗 File coupling	Which files tend to change together, even with no import between them?
👤 Ownership concentration (bus factor)	Which areas of the codebase depend on a single contributor?
⚠️ PR risk check	Given a list of changed files, how risky is this change, and why?
Results can be filtered to the last 6 months, 12 months, 24 months, or all time.
🏗️ Architecture

FastAPI backend (engine/)
GET/analyze/:owner/:name?months=
POST /risk/:owner/:name
hit
miss
git clone / fetch
User
Next.js dashboardReact · TypeScript · Tailwind
api.pyroutes · validation · CORS
Rate limitersliding-window log
Result cachefresh, under 60s?
repo.pyclone / fetchper-repo lock
Bare blobless clonesdata/repos/
git log, then parser.pyand filter.py
History cachesame HEAD?
Analyzershotspots · coupling · graphbus factor · PR risk
GitHub
Request flow for /analyze

GitHub
repo.py
Caches
FastAPI
Client
GitHub
repo.py
Caches
FastAPI
Client
opt
[history cache miss]
alt
[fresh entry (under 60s)]
[miss or stale]
GET /analyze/owner/name?months=24
per-IP rate limits (60/min, 5 new repos/10 min)
result cache lookup
cached JSON
sync_repo (per-repo lock)
clone --bare --filter=blob:none, or fetch
read HEAD
history cache (same HEAD?)
git log --name-only, parse, drop noise
run analyzers on the time window
store result with its HEAD
JSON
⚙️ How it works
1. Getting the history
The repo is cloned as git clone --bare --filter=blob:none. A bare, blobless clone downloads commits and trees but no file contents, because the analysis only needs which files changed in which commit.
Later requests run git fetch instead of re-cloning.
The history is read with git log --no-renames --name-only and parsed into Commit(hash, author, email, date, files) objects.
Noise is removed before analysis: lockfiles, minified files, images, node_modules/dist/build, changelogs, etc. (filter.py).
1. The analyzers
Module	Algorithm	Notes
Hotspots (hotspots.py)	Count commits touching each file (Counter), return the top 10	Counts commits, not lines churned
Coupling (coupling.py)	Count co-occurring file pairs per commit (itertools.combinations). strength = together / min(changes_a, changes_b)	Commits with more than 50 files are skipped for pair counting; pairs seen fewer than 2 times are dropped
Graph (graph.py)	Top coupled pairs become edges; their files become nodes sized by change count	Layout runs client-side with d3-force
Bus factor (bus_factor.py)	Per top-level folder, find the author with the most commits and report their share	Uses full history, ignores bots, needs at least 10 commits in an area. This is an ownership-concentration proxy, not a formal bus-factor computation
PR risk (pr_risk.py)	Weighted heuristic over the files you provide	See the table below
PR risk scoring (0–100, every point maps to a human-readable reason):
Signal	Points	Cap
Changed file is in the top-10 hotspots	15 each	30
A file that usually changes with it (≥3 times, ≥60% of the time) is missing from the PR	10 per partner	30
An area has effectively one recent maintainer (≥80% of ≥5 commits)	10 each	20
Large change (15+ files)	15	n/a
Levels: low below 25, medium below 55, high otherwise. The weights are hand-chosen and have not been validated against real defect data.
1. Caching
Two in-memory LRU caches (cache.py):
Results: keyed by owner/name/months, up to 200 entries. An entry is served directly for 60 seconds. After that it is revalidated by comparing the stored HEAD to the repo's current HEAD.
Histories: keyed by owner/name, up to 4 entries, holding the parsed commits so switching time windows doesn't re-run git log.
1. Protecting the server
Rate limiting (tmp_ratelimit.py): a sliding-window log per client IP, with two limiters, 60 requests/minute overall and 5 new-repo downloads per 10 minutes, because cloning is the expensive operation. Rejected requests get 429 with Retry-After.
Repo size cap: while cloning, folder size is polled; the clone is killed and deleted above MAX_REPO_MB.
Clone timeout: the clone is killed and cleaned up after CLONE_TIMEOUT_SECONDS.
Disk cap with eviction: the least recently used repos are deleted once total disk exceeds MAX_DISK_MB.
Per-repo locks: one threading.Lock per repo directory so concurrent requests can't clone into the same path.
Input hardening: owner/name are validated against a strict regex, the host is hardcoded to github.com, git is called with an argument list (no shell), GIT_TERMINAL_PROMPT=0 prevents credential prompts, and the PR check caps input at 2,500 files.
📡 API
Method	Path	Description
GET	/analyze/{owner}/{name}?months=24	Hotspots, coupling, graph and bus factor. months is 1–600 (600 means "all time" in the UI)
POST	/risk/{owner}/{name}	Body: { "files": ["path/a.js", ...], "months": 24 }. Returns score, level, reasons
GET	/health	Liveness check
🚀 Run it locally
Requirements: Python 3.13, Node.js, and git on your PATH.
bash
# 1. Backend (run from inside engine/, modules use top-level imports)
cd engine
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --reload --port 8000

# 2. Frontend (in a second terminal)
cd dashboard
npm install
echo "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000" > .env.local
npm run dev            # http://localhost:3000
Configuration (environment variables, backend)
Variable	Default	Purpose
MAX_REPO_MB	100	Max size of a single clone
CLONE_TIMEOUT_SECONDS	300	Clone time limit
MAX_DISK_MB	1000	Total disk budget before eviction
MAX_RESULTS	200	Result cache entries
MAX_HISTORIES	4	Parsed-history cache entries
REQUESTS_PER_MINUTE	60	Per-IP request limit
NEW_REPOS_PER_10_MIN	5	Per-IP new-repo download limit
ALLOWED_ORIGINS	http://localhost:3000,http://127.0.0.1:3000	CORS allowlist (comma-separated)
📁 Project structure
git-history-intelligence/
├── engine/                  # FastAPI backend
│   ├── api.py               # routes, caching flow, rate-limit enforcement
│   ├── repo.py              # clone/fetch, size and timeout guards, eviction
│   ├── parser.py            # git log text to Commit objects
│   ├── filter.py            # noise filtering (lockfiles, assets, build dirs)
│   ├── cache.py             # LRU result and history caches
│   ├── tmp_ratelimit.py     # sliding-window rate limiter
│   ├── models.py            # Commit dataclass
│   └── analyzers/
│       ├── hotspots.py
│       ├── coupling.py
│       ├── graph.py
│       ├── bus_factor.py
│       └── pr_risk.py
└── dashboard/               # Next.js frontend
    ├── app/page.tsx         # search, time window, results
    ├── components/          # Hotspots, Coupling, CouplingGraph, BusFactor, PrRisk cards
    └── lib/                 # API client, d3-force graph layout
🧭 Design decisions and trade-offs
Blobless bare clone: far less data than a full clone, at the cost of not being able to analyze file contents or line-level churn.
60-second freshness plus HEAD check: avoids a git fetch on every request while still noticing new commits.
Skipping commits with more than 50 files for coupling: large refactors and merges would create false coupling and an O(files²) blowup.
Separate limiter for new clones: cloning costs far more than serving a cached analysis, so it gets its own, stricter budget.
Explainable PR scoring: a transparent heuristic whose every point has a stated reason, instead of an opaque model with no training data.
Client-side graph layout: the server sends only nodes and edges (at most 80 nodes); d3-force positions them in the browser.
⚠️ Limitations
Being upfront about what this project does not do:
Analysis accuracy
Only the default branch is analyzed. Merge commits list no files, so they add nothing to the analyzers.
Renames are not tracked (--no-renames), so a renamed file's history is split. Hotspots can include files that no longer exist.
Bus factor is a proxy: it reports the top author's share per top-level folder. It is not the minimum number of people whose departure would stall the project. Authors are identified by email with no .mailmap support, and monorepos with most code under one folder collapse into a single area.
Coupling strength uses the smaller of the two files' change counts, so rarely changed files can reach 100% on little evidence.
PR risk takes a pasted list of file paths. It does not read real GitHub pull requests, and its weights are unvalidated heuristics.
Hotspots count commits touching a file, not lines changed.
The time window uses 30-day months, and "All time" is implemented as 600 months.
Architecture and scale
All state is in-memory and per-process. With multiple workers, caches are duplicated, rate limits multiply, and the per-repo locks don't coordinate across processes.
Rate limiting is keyed on the client IP seen by the app. Behind a reverse proxy this needs correct forwarded-header handling.
Analysis is CPU-bound Python running in a threadpool, so it doesn't parallelize under the GIL. Two simultaneous cache misses for the same repo both do the work.
git log output is buffered fully in memory rather than streamed.
Eviction walks every cached repo on each sync and runs without coordinating with readers.
Clone size is polled every 0.5s, so the cap can be slightly overshot.
Only public GitHub repositories are supported.
There is currently no automated test suite.
🗺️ Roadmap
 Unit tests for the analyzers (they are pure functions of list[Commit])
 Redis for shared caching and rate limiting; distributed lock for clones
 Background job queue with progress updates instead of a blocking request
 Incremental analysis (git log <last_head>..HEAD) with parsed commits stored in a database
 Churn-weighted hotspots via --numstat, and .mailmap support
 True bus-factor computation (minimum authors covering 50% of commits)
 Real GitHub PR integration for the risk check
 Dockerfile and CI

Built by Kartike Khurana
</div>
Claude finished the response
