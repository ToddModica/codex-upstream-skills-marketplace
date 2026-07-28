#!/usr/bin/env python3
"""Refresh Git source lock SHAs. Copying remains explicit via sync_sources.py."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def remote_branch_head(url: str, branch: str) -> str:
    ref = f"refs/heads/{branch}"
    result = subprocess.run(["git", "ls-remote", url, ref], capture_output=True, text=True, check=True)
    fields = result.stdout.split()
    if not fields:
        raise RuntimeError(f"Remote branch was not found: {url} {ref}")
    return fields[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=ROOT / "sources.json")
    parser.add_argument("--name", action="append", help="refresh only the named source; may be repeated")
    args = parser.parse_args()
    payload = json.loads(args.sources.read_text(encoding="utf-8"))
    selected = set(args.name or [])
    known_names = {str(item["name"]) for item in payload["sources"]}
    unknown = selected - known_names
    if unknown:
        raise RuntimeError(f"Unknown source name(s): {', '.join(sorted(unknown))}")
    changed = False
    heads: dict[tuple[str, str], str] = {}
    for item in payload["sources"]:
        if selected and str(item["name"]) not in selected:
            continue
        if item.get("action") not in {"copy", "copy-plugin", "mcp-config-and-addon"}:
            continue
        url = item.get("upstream")
        if not url:
            continue
        branch = item.get("branch")
        if not branch:
            raise RuntimeError(f"{item['name']}: upstream branch is missing")
        key = (str(url), str(branch))
        if key not in heads:
            heads[key] = remote_branch_head(*key)
        sha = heads[key]
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
