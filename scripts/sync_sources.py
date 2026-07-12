#!/usr/bin/env python3
"""Synchronize redistributable locked sources into this Marketplace repository.

Default mode copies from the local paths in sources.json.  --remote refreshes a
temporary Git checkout first, so CI can update known GitHub sources without
touching the user's installed skills.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENY_NAMES = {".git", ".venv", "venv", "__pycache__", ".env"}
DENY_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}


def safe_copytree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise RuntimeError(f"Source directory missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    def ignore(directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in DENY_NAMES or Path(name).suffix.lower() in DENY_SUFFIXES}
    shutil.copytree(source, destination, ignore=ignore)


def checkout(record: dict[str, object], cache_root: Path) -> Path:
    upstream = record.get("upstream")
    sha = record.get("commit_sha")
    if not upstream or not sha:
        raise RuntimeError(f"{record['name']}: no upstream Git URL and SHA are available")
    directory = cache_root / str(record["name"])
    subprocess.run(["git", "clone", "--no-checkout", str(upstream), str(directory)], check=True)
    subprocess.run(["git", "-C", str(directory), "checkout", "--detach", str(sha)], check=True)
    return directory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", type=Path, default=ROOT / "sources.json")
    parser.add_argument(
        "--local-skills-root",
        type=Path,
        default=Path(os.environ.get("CODEX_SKILLS_ROOT", Path.home() / ".codex" / "skills")),
    )
    parser.add_argument(
        "--itasca-mcp-root",
        type=Path,
        default=Path(os.environ.get("ITASCA_MCP_ROOT", Path.home() / ".codex" / "mcp" / "itasca-mcp")),
    )
    parser.add_argument("--remote", action="store_true", help="clone each GitHub source at its locked SHA before copying")
    parser.add_argument("--check", action="store_true", help="only validate sources and target paths")
    args = parser.parse_args()
    payload = json.loads(args.sources.read_text(encoding="utf-8"))
    temporary = tempfile.TemporaryDirectory(prefix="codex-skill-sync-") if args.remote else None
    try:
        for record in payload["sources"]:
            if record["kind"] != "skill" or record["action"] != "copy":
                continue
            source = args.local_skills_root / str(record["local_relative"])
            if args.remote:
                if not record.get("upstream") or not record.get("commit_sha"):
                    print(f"skipped {record['name']}: no GitHub source lock is available")
                    continue
                source = checkout(record, Path(temporary.name))
            target = ROOT / str(record["target"])
            if args.check:
                if not source.joinpath("SKILL.md").is_file():
                    raise RuntimeError(f"{record['name']}: SKILL.md is missing")
                continue
            safe_copytree(source, target)
            print(f"synced {record['name']} -> {target.relative_to(ROOT)}")
        mcp = next(item for item in payload["sources"] if item["kind"] == "mcp")
        if mcp["action"] == "mcp-config-and-addon" and not args.check:
            mcp_source = checkout(mcp, Path(temporary.name)) if args.remote else args.itasca_mcp_root
            addon = mcp_source / "addon.py"
            if not addon.is_file():
                raise RuntimeError(f"MCP addon missing: {addon}")
            target = ROOT / str(mcp["target"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(addon, target)
            license_file = mcp_source / str(mcp["license_file"])
            shutil.copy2(license_file, target.parent / "itasca-mcp-LICENSE")
            print(f"synced itasca-mcp addon -> {target.relative_to(ROOT)}")
    finally:
        if temporary:
            temporary.cleanup()


if __name__ == "__main__":
    main()
