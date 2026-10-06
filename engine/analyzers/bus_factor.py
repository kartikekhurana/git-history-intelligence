import sys
from collections import Counter, defaultdict

from models import Commit
from parser import parse_git_log


def area_of(path: str, depth : str = 1) -> str:
    folders = path.split("/")[:-1]
    if not folders:
        return "(root)"
    return "/".join(folders[:depth])


def find_bus_factor(
    commits: list[Commit], depth: int = 1, min_commits: int = 10, top_n: int = 10
) -> list[tuple[str, str, float, int, int]]:
    area_authors: defaultdict[str, Counter[str]] = defaultdict(Counter)
    names: dict[str, str] = {}

    for commit in commits:
        if "[bot]" in commit.author:
            continue
        person = commit.email.lower()
        names.setdefault(person, commit.author)
        areas = {area_of(f, depth) for f in commit.files}
        for area in areas:
            area_authors[area][person] += 1

    results = []
    for area, people in area_authors.items():
        total = sum(people.values())
        if total < min_commits:
            continue
        top_person, top_count = people.most_common(1)[0]
        results.append((area, names[top_person], top_count / total, total, len(people)))

    results.sort(key=lambda r: (r[2], r[3]), reverse=True)
    return results[:top_n]

if __name__ == "__main__":
    commits = parse_git_log(sys.stdin.read())
    for area , author , share, total , n_authors in find_bus_factor(commits):
        print(f"{share:5.0%}   {author:<22}  {total:5d} commits  {n_authors:3d} authors   {area}")
    
