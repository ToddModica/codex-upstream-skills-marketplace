#!/usr/bin/env python3
"""Refresh public Marketplace source locks from a local Skill installation."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

INCLUDED = {
    "research-toolkit": {
        "academic-paper",
        "academic-paper-reviewer",
        "academic-pipeline",
        "academic-research-suite",
        "deep-research",
        "patent-disclosure-skill",
        "nature-academic-search",
        "nature-citation",
        "nature-data",
        "nature-figure",
        "nature-paper2ppt",
        "nature-polishing",
        "nature-reader",
        "nature-response",
        "nature-writing",
        "scipilot-cite-skill",
        "scipilot-figure-skill",
        "scipilot-writing-skill",
    },
    "writing-toolkit": {"ai-flavor-remover", "humanizer", "humanizer-zh", "shuorenhua", "stop-slop"},
    "codex-utility-toolkit": {
        "bilibili-page-reader",
        "design-taste-frontend",
        "doc",
        "imagegen",
        "openai-docs",
        "pdf",
        "ppt-master",
        "powershell-safe-invocation",
        "skill-creator",
        "skill-installer",
    },
}


def merge_records(previous: list[dict[str, object]], generated: list[dict[str, object]]) -> list[dict[str, object]]:
    by_name = {str(item["name"]): item for item in generated}
    if len(by_name) != len(generated):
        raise RuntimeError("Generated source names must be unique")
    merged = [by_name.pop(str(item["name"]), item) for item in previous]
    return merged + list(by_name.values())

MONOREPO_RULES = {
    "https://github.com/yuan1z0825/nature-skills": {
        "license": "Apache-2.0",
        "license_file": "LICENSE",
        "skill_prefix": "skills",
    },
    "https://github.com/misaka-mikoto-tech/agent-skills": {
        "license": "MIT",
        "license_file": "LICENSE",
        "skill_prefix": "skills",
    },
    "https://github.com/imbad0202/academic-research-skills": {
        "license": "CC-BY-NC-4.0",
        "license_file": "LICENSE",
        "skill_prefix": ".",
    },
    "https://github.com/imbad0202/academic-research-skills-codex": {
        "license": "CC-BY-NC-4.0",
        "license_file": "LICENSE",
        "skill_prefix": "skills",
    },
    "https://github.com/leonxlnx/taste-skill": {
        "license": "MIT",
        "license_file": "LICENSE",
        "skill_prefix": "skills",
        "subpaths": {
            "design-taste-frontend": "skills/taste-skill",
        },
    },
    "https://github.com/hugohe3/ppt-master": {
        "license": "MIT",
        "license_file": "LICENSE",
        "skill_prefix": "skills",
    },
}


def git(path: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(["git", "-C", str(path), *args], text=True, stderr=subprocess.DEVNULL).strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def frontmatter_name(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip('"\'')
    return None


def license_id(directory: Path) -> tuple[str, str | None]:
    candidates = [p for p in directory.iterdir() if p.is_file() and p.name.lower().split(".")[0] in {"license", "licence", "copying"}]
    if not candidates:
        return "UNKNOWN", None
    license_file = candidates[0]
    text = license_file.read_text(encoding="utf-8", errors="ignore")[:4096].lower()
    if "apache license" in text and "version 2.0" in text:
        return "Apache-2.0", license_file.name
    if "mit license" in text:
        return "MIT", license_file.name
    if "attribution-noncommercial 4.0 international" in text or "cc by-nc 4.0" in text:
        return "CC-BY-NC-4.0", license_file.name
    return "CUSTOM", license_file.name


def plugin_for(name: str) -> str | None:
    for plugin, skills in INCLUDED.items():
        if name in skills:
            return plugin
    return None


def normalized_remote(url: str | None) -> str | None:
    if not url:
        return None
    return url.removesuffix(".git").rstrip("/").lower()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("sources.json"))
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=Path(os.environ.get("CODEX_SKILLS_ROOT", Path.home() / ".codex" / "skills")),
    )
    parser.add_argument(
        "--mcp-root",
        type=Path,
        default=Path(os.environ.get("ITASCA_MCP_ROOT", Path.home() / ".codex" / "mcp" / "itasca-mcp")),
    )
    args = parser.parse_args()
    source_root = args.skills_root.resolve()
    mcp_root = args.mcp_root.resolve()
    if not source_root.is_dir():
        raise SystemExit(f"Skill root does not exist: {source_root}")
    if not mcp_root.is_dir():
        raise SystemExit(f"ITASCA MCP root does not exist: {mcp_root}")
    previous_records: list[dict[str, object]] = []
    previous: dict[str, dict[str, object]] = {}
    if args.output.is_file():
        old_payload = json.loads(args.output.read_text(encoding="utf-8"))
        previous_records = old_payload.get("sources", [])
        previous = {item["name"]: item for item in previous_records}
    records: list[dict[str, object]] = []
    for skill_md in sorted(source_root.rglob("SKILL.md")):
        name = frontmatter_name(skill_md)
        if not name:
            continue
        if not plugin_for(name) and name not in previous:
            continue
        source_dir = skill_md.parent
        origin = git(source_dir, "remote", "get-url", "origin")
        local_snapshot_sha = git(source_dir, "rev-parse", "HEAD")
        branch = git(source_dir, "config", "--get", "skill.upstreamBranch") or git(source_dir, "branch", "--show-current")
        license_name, license_file = license_id(source_dir)
        license_scope = "skill-root" if license_file else None
        upstream_subpath = None
        monorepo = MONOREPO_RULES.get(normalized_remote(origin))
        if monorepo:
            subpaths = monorepo.get("subpaths", {})
            upstream_subpath = git(source_dir, "config", "--get", "skill.upstreamPrefix") or subpaths.get(name)
            if not upstream_subpath:
                prefix = str(monorepo["skill_prefix"])
                upstream_subpath = name if prefix in {"", "."} else f"{prefix}/{name}"
            if not license_file:
                license_name = str(monorepo["license"])
                license_file = str(monorepo["license_file"])
                license_scope = "repository-root"
        plugin = plugin_for(name)
        allowed = license_name in {"MIT", "Apache-2.0", "CC-BY-NC-4.0"}
        action = "copy" if plugin and allowed else "record-only"
        reason = None
        if not plugin:
            reason = "No redistribution target: license not verified for this source." if not allowed else "Not selected for a plugin."
        elif not allowed:
            reason = "No redistributable license file found at the locked source revision."
        old = previous.get(name, {})
        old_origin = normalized_remote(str(old.get("upstream"))) if old.get("upstream") else None
        commit_sha = old.get("commit_sha") if monorepo and old_origin == normalized_remote(origin) else local_snapshot_sha
        records.append({
            "kind": "skill",
            "name": name,
            "upstream": origin,
            "branch": branch,
            "commit_sha": commit_sha,
            "local_snapshot_sha": local_snapshot_sha,
            "upstream_subpath": upstream_subpath,
            "local_relative": source_dir.relative_to(source_root).as_posix(),
            "target": f"plugins/{plugin}/skills/{name}" if action == "copy" else None,
            "license": license_name,
            "license_file": license_file,
            "license_scope": license_scope,
            "action": action,
            "reason": reason,
        })
    mcp_license, mcp_license_file = license_id(mcp_root)
    records.append({
        "kind": "mcp",
        "name": "itasca-mcp",
        "upstream": git(mcp_root, "remote", "get-url", "origin"),
        "branch": git(mcp_root, "branch", "--show-current"),
        "commit_sha": git(mcp_root, "rev-parse", "HEAD"),
        "local_relative": None,
        "target": "plugins/research-toolkit/assets/itasca-mcp-addon.py",
        "license": mcp_license,
        "license_file": mcp_license_file,
        "action": "mcp-config-and-addon" if mcp_license == "MIT" else "record-only",
        "reason": "Plugin config uses uvx itasca-mcp; the MIT-licensed bridge addon is retained as an asset.",
    })
    records = merge_records(previous_records, records)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "user_excluded": [],
        "sources": records,
    }
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
