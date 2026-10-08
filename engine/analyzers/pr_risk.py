from collections import Counter , defaultdict
from dataclasses import dataclass , field

from analyzers.bus_factor import area_of
from analyzers.coupling import MAX_FILES_PER_COMMIT
from analyzers.hotspots import find_hotspots
from filter import is_noise
from models import Commit

HOT_TOP_N = 10
MIN_PARTNER_STRENGTH = 0.6
MIN_PARTNER_TOGETHER = 3
BIG_PR_FILES = 15
SOLO_OWNER_SHARE = 0.8
SOLO_OWNER_MIN_COMMITS = 5

@dataclass
class Risk:
    score : int
    level : str
    reasons : list[str] = field(default_factory=list)


def assess_pr(recent: list[Commit] , changed : list[str]) -> Risk:
    changed = sorted({f for f in changed if not is_noise(f)})
    if not changed:
        return Risk(0,"low", ["No meaningful files changed (only lock files, images, or similar)."])
    
    changed_set = set(changed)
    areas = {area_of(f) for f in changed}
    file_counts : Counter[str] = Counter()
    together : defaultdict[str , Counter[str]] = defaultdict(Counter)
    area_people : defaultdict[str, Counter[str]] = defaultdict(Counter)

    for commit in recent:
        files = set(commit.files)
        touched = files & changed_set
        file_counts.update(touched)
        if touched and len(files) <= MAX_FILES_PER_COMMIT:
            for f in touched:
                together[f].update(files - {f})
        if "[bot]" not in commit.author:
            for area in {area_of(f) for f in files} & areas:
                area_people[area][commit.email.lower()] += 1
    
    score = 0
    reasons : list[str] = []

    hot = dict(find_hotspots(recent, HOT_TOP_N))
    hot_hits = [(f, hot[f]) for f in changed if f in hot]
    score += min(30, 15 * len(hot_hits))

    for f , n in hot_hits:
        reasons.append(f"{f} is a hotspot ({n} changes in the window)")
    
    missing : list[tuple[str , str,float]] = []
    for f in changed:
        if not file_counts[f]:
            continue
        for partner , n in together[f].most_common():
            strength = n / file_counts[f]
            if n < MIN_PARTNER_TOGETHER or strength < MIN_PARTNER_STRENGTH:
                break
            if partner not in changed_set:
                missing.append((f , partner ,strength))

    unique_partners = {partner for _, partner, _ in missing}
    score += min(30, 10 * len(unique_partners))
      
    for f, partner, strength in missing[:5]:
        reasons.append(
            f"{f} changes together with {partner} {strength:.0%} of the time "
            f"but {partner} is not in this PR"
        )
    solo = []
    for area, people in area_people.items():
        total = sum(people.values())
        share = max(people.values()) / total
        if total >= SOLO_OWNER_MIN_COMMITS and share >= SOLO_OWNER_SHARE:
            solo.append((area, share, total))        
    
    score += min(20 , 10 * len(solo))

    for area, share ,total in solo:
        reasons.append(
            f"{area} has effectively one recent maintainer ",
            f"({share:.0%} of {total} recent commits)"
        )
    if len(changed) >= BIG_PR_FILES:
        score += 15
        reasons.append(f"Large change: {len(changed)} files")
    
    score =min(score ,100)
    level = "low" if score < 25 else "medium" if score <55 else "high"

    if not reasons:
        reasons.append("No risk signals found in recent history.")
    return Risk(score , level , reasons)