import sys
from collections import Counter
from models import Commit
from parser import parse_git_log

def find_hotspots(commits : list[Commit],top_n : int = 10) -> list[tuple[str , int]]:
    counts : Counter[str] = Counter()
    for commit in commits:
        counts.update(commit.files)
    
    return counts.most_common(top_n)


if __name__ == "__main__":
    commits = parse_git_log(sys.stdin.read())
    for path , count in find_hotspots(commits):
        print(f"{count : 4d}   {path}")