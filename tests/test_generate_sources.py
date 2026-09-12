#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from generate_sources import merge_records

previous = [{"name": "tracked", "sha": "keep"}, {"name": "local", "sha": "old"}]
generated = [{"name": "local", "sha": "new"}, {"name": "added", "sha": "new"}]

assert merge_records(previous, generated) == [
    {"name": "tracked", "sha": "keep"},
    {"name": "local", "sha": "new"},
    {"name": "added", "sha": "new"},
]
print("generate_sources merge: OK")
