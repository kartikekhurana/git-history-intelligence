import sys
from collections import Counter
from itertools import combinations
from models import Commit
from pathlib import PurePosixPath
from parser import parse_git_log


MAX_FILES_PER_COMMIT = 50

def same_name(a:str,b:str)->bool:
    return PurePosixPath(a).with_suffix("") == PurePosixPath(b).with_suffix("")

def find_coupling(
        commits : list[Commit] , min_together : int = 2 , top_n : int = 10
) -> list[tuple[str, str, int, float]]:
    file_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str , str]] = Counter()

    for commit in commits:
        files = sorted(set(commit.files))
        file_counts.update(files)
        if len(files) > MAX_FILES_PER_COMMIT:
            continue
        pair_counts.update(combinations(files,2))
    
    results = []
    for (a,b) ,together in pair_counts.items():
        if together < min_together:
            continue
        if same_name(a,b):
            continue
        strength = together / min(file_counts[a],file_counts[b])
        results.append((a,b,together,strength))
    
    results.sort(key=lambda r :(r[3],r[2]),reverse=True)
    return results[:top_n]


if __name__ == "__main__":
    commits = parse_git_log(sys.stdin.read())
    for a,b,together,strength in find_coupling(commits):
        print(f"{strength:5.0%}   {together:3d}x {a}  <->  {b}")