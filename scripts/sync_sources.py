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
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENY_NAMES = {".git", ".venv", "venv", "__pycache__", ".env"}
DENY_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}


def remove_readonly(func, path: str, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    func(path)


def materialize_git_symlinks(repository: Path, sha: str) -> None:
    listing = subprocess.check_output(
        ["git", "-C", str(repository), "ls-tree", "-r", "--full-tree", sha],
        text=True,
    )
    for line in listing.splitlines():
        metadata, relative = line.split("\t", 1)
        mode = metadata.split()[0]
        if mode != "120000":
            continue
        link_path = repository / relative
        target_text = subprocess.check_output(
            ["git", "-C", str(repository), "show", f"{sha}:{relative}"],
            text=True,
        ).strip()
        target_path = (link_path.parent / target_text).resolve()
        if not target_path.is_relative_to(repository.resolve()):
            raise RuntimeError(f"Refusing to materialize an escaping Git symlink: {relative} -> {target_text}")
        if link_path.exists() or link_path.is_symlink():
            if not link_path.is_symlink():
                os.chmod(link_path, stat.S_IWRITE | stat.S_IREAD)
            link_path.unlink()
        if target_path.is_file():
            shutil.copy2(target_path, link_path)
        elif target_path.is_dir():
            shutil.copytree(target_path, link_path)
        else:
            raise RuntimeError(f"Git symlink target is missing: {relative} -> {target_text}")


def safe_copytree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise RuntimeError(f"Source directory missing: {source}")
    destination_resolved = destination.resolve()
    if not destination_resolved.is_relative_to(ROOT.resolve() / "plugins"):
        raise RuntimeError(f"Refusing to replace a path outside plugins/: {destination}")
    for entry in source.rglob("*"):
        if entry.is_symlink():
            raise RuntimeError(f"Refusing to copy symbolic link from an upstream source: {entry}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination, onerror=remove_readonly)
    def ignore(directory: str, names: list[str]) -> set[str]:
        return {
            name
            for name in names
            if name in DENY_NAMES
            or name.startswith(".env.")
            or Path(name).suffix.lower() in DENY_SUFFIXES
        }
    shutil.copytree(source, destination, ignore=ignore)
    for copied in destination.rglob("*"):
        if copied.is_file():
            os.chmod(copied, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


def checkout(
    record: dict[str, object],
    cache_root: Path,
    cache: dict[tuple[str, str], Path],
) -> Path:
    upstream = record.get("upstream")
    sha = record.get("commit_sha")
    if not upstream or not sha:
        raise RuntimeError(f"{record['name']}: no upstream Git URL and SHA are available")
    key = (str(upstream), str(sha))
    if key in cache:
        return cache[key]
    directory = cache_root / f"repo-{len(cache) + 1}"
    subprocess.run(["git", "clone", "--no-checkout", str(upstream), str(directory)], check=True)
    subprocess.run(["git", "-C", str(directory), "checkout", "--detach", str(sha)], check=True)
    materialize_git_symlinks(directory, str(sha))
    cache[key] = directory
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
    checkout_cache: dict[tuple[str, str], Path] = {}
    try:
        for record in payload["sources"]:
            if record["kind"] != "skill" or record["action"] != "copy":
                continue
            source = args.local_skills_root / str(record["local_relative"])
            repository_root = None
            if args.remote:
                if not record.get("upstream") or not record.get("commit_sha"):
                    print(f"skipped {record['name']}: no GitHub source lock is available")
                    continue
                repository_root = checkout(record, Path(temporary.name), checkout_cache)
                source = repository_root
                if record.get("upstream_subpath"):
                    source = (repository_root / str(record["upstream_subpath"])).resolve()
                    if not source.is_relative_to(repository_root.resolve()):
                        raise RuntimeError(f"{record['name']}: upstream_subpath escapes the checkout")
            target = ROOT / str(record["target"])
            if args.check:
                if not source.joinpath("SKILL.md").is_file():
                    raise RuntimeError(f"{record['name']}: SKILL.md is missing")
                continue
            upstream_license = target / "UPSTREAM_LICENSE"
            if not args.remote and record.get("license_scope") == "repository-root":
                raise RuntimeError(f"{record['name']}: repository-root licenses require --remote synchronization")
            safe_copytree(source, target)
            if record.get("license_scope") == "repository-root":
                if args.remote:
                    license_source = (repository_root / str(record["license_file"])).resolve()
                    if not license_source.is_relative_to(repository_root.resolve()):
                        raise RuntimeError(f"{record['name']}: license path escapes the checkout")
                    if not license_source.is_file():
                        raise RuntimeError(f"{record['name']}: repository license is missing: {license_source}")
                    shutil.copy2(license_source, upstream_license)
                    os.chmod(upstream_license, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            print(f"synced {record['name']} -> {target.relative_to(ROOT)}")
        mcp = next(item for item in payload["sources"] if item["kind"] == "mcp")
        if mcp["action"] == "mcp-config-and-addon" and not args.check:
            mcp_source = checkout(mcp, Path(temporary.name), checkout_cache) if args.remote else args.itasca_mcp_root
            addon = mcp_source / "addon.py"
            if not addon.is_file():
                raise RuntimeError(f"MCP addon missing: {addon}")
            target = ROOT / str(mcp["target"])
            if not target.resolve().is_relative_to((ROOT / "plugins/research-toolkit/assets").resolve()):
                raise RuntimeError("MCP target escapes the research-toolkit assets directory")
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
