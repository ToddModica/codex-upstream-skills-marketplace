#!/usr/bin/env python3
"""Refresh Git source lock SHAs. Copying remains explicit via sync_sources.py."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def remote_head(url: str) -> str | None:
    result = subprocess.run(["git", "ls-remote", url, "HEAD"], capture_output=True, text=True, check=True)
    return result.stdout.split()[0] if result.stdout.split() else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=ROOT / "sources.json")
    args = parser.parse_args()
    payload = json.loads(args.sources.read_text(encoding="utf-8"))
    changed = False
    for item in payload["sources"]:
        url = item.get("upstream")
        if not url:
            continue
        sha = remote_head(str(url))
        if sha and sha != item.get("commit_sha"):
            print(f"updated lock: {item['name']} {item.get('commit_sha')} -> {sha}")
            item["commit_sha"] = sha
            changed = True
    if changed:
        payload["generated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        args.sources.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    raise SystemExit(0 if changed else 2)


if __name__ == "__main__":
    main()
