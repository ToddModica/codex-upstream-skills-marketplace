#!/usr/bin/env python3
"""Create a reproducible source lock from the local cc-switch skill installation."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

USER_EXCLUDED = {"agently-mail", "agents", "commands", "shared", "netease-uu-booster"}
INCLUDED = {
    "research-toolkit": {"scipilot-cite-skill", "scipilot-figure-skill", "scipilot-writing-skill"},
    "writing-toolkit": {"humanizer", "humanizer-zh", "shuorenhua", "stop-slop"},
    "codex-utility-toolkit": {"doc", "imagegen", "openai-docs", "pdf", "skill-creator", "skill-installer"},
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
    return "CUSTOM", license_file.name


def plugin_for(name: str) -> str | None:
    for plugin, skills in INCLUDED.items():
        if name in skills:
            return plugin
    return None


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
    records: list[dict[str, object]] = []
    for skill_md in sorted(source_root.rglob("SKILL.md")):
        relative_parts = skill_md.relative_to(source_root).parts
        name = frontmatter_name(skill_md)
        if not name:
            continue
        source_dir = skill_md.parent
        license_name, license_file = license_id(source_dir)
        explicitly_excluded = relative_parts[0] in USER_EXCLUDED
        plugin = plugin_for(name)
        allowed = license_name in {"MIT", "Apache-2.0"}
        action = "copy" if plugin and allowed and not explicitly_excluded else "record-only"
        reason = None
        if explicitly_excluded:
            reason = "Explicitly excluded by the user from plugin packaging."
        elif not plugin:
            reason = "No redistribution target: license not verified for this source." if not allowed else "Not selected for a plugin."
        elif not allowed:
            reason = "No redistributable license file found at the locked source revision."
        records.append({
            "kind": "skill",
            "name": name,
            "upstream": git(source_dir, "remote", "get-url", "origin"),
            "branch": git(source_dir, "branch", "--show-current"),
            "commit_sha": git(source_dir, "rev-parse", "HEAD"),
            "local_relative": source_dir.relative_to(source_root).as_posix(),
            "target": f"plugins/{plugin}/skills/{name}" if action == "copy" else None,
            "license": license_name,
            "license_file": license_file,
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
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "user_excluded": sorted(USER_EXCLUDED),
        "sources": records,
    }
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
