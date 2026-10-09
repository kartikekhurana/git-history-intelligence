from collections import Counter
from analyzers.bus_factor import area_of
from models import Commit

def build_graph(commits : list[Commit] , pairs:list[tuple[str , str , int , float]]) -> dict:
    names = {name for a,b ,_,_ in pairs for name in (a,b)}
    counts : Counter[str] = Counter()
    for commit in commits:
        counts.update(names.intersection(commit.files))

    return {
        "nodes" : [
            {"id" : name , "area": area_of(name), "changes": counts[name]}
            for name in sorted(names)
        ],
        "edges" : [
            {"source" : a , "target" : b , "together" : together ,  "strength": round(strength, 2)}
            for a,b , together , strength in pairs
        ]
    }