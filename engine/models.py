from dataclasses import dataclass
from datetime import datetime

@dataclass
class Commit:
    hash : str
    author : str
    email : str
    date : datetime
    files : list[str]
