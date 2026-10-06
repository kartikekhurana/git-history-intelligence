import sys
from datetime import datetime

from models import Commit

def parse_git_log(raw : str) -> list[Commit]:
    commits : list[Commit] = []
    current : Commit | None = None

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith("--"):
            # new line begins , save the previous ones
            if current is not None:
                commits.append(current)
            
            commit_hash , author ,email , date_str = line[2:].split("|",3)
            current = Commit(
                hash=commit_hash,
                author=author,
                email=email,
                date= datetime.strptime(date_str,"%Y-%m-%d %H:%M:%S %z"),
                files=[],
            )
        elif current is not None:
            current.files.append(line)
    if current is not None:
        commits.append(current)
    
    return commits

if __name__ == "__main__":
    commits = parse_git_log(sys.stdin.read())
    print(f"Parsed {len(commits)} commits")
    print(commits[0])
