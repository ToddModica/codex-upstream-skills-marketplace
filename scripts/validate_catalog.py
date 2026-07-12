#!/usr/bin/env python3
"""Validate the local Marketplace structure without importing third-party code."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from pathlib import PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ("research-toolkit", "writing-toolkit", "codex-utility-toolkit")
REQUIRED_SKILLS = {
    "research-toolkit": {
        "academic-paper",
        "academic-paper-reviewer",
        "academic-pipeline",
        "academic-research-suite",
        "deep-research",
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
    "writing-toolkit": {"humanizer", "humanizer-zh", "shuorenhua", "stop-slop"},
    "codex-utility-toolkit": {
        "bilibili-page-reader",
        "design-taste-frontend",
        "doc",
        "imagegen",
        "openai-docs",
        "pdf",
        "powershell-safe-invocation",
        "skill-creator",
        "skill-installer",
    },
}
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
SHA = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_LICENSES = {"MIT", "Apache-2.0", "CC-BY-NC-4.0"}
FORBIDDEN_NAMES = {".env", "credentials.json", "id_rsa", "id_ed25519"}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def skill_name(text: str) -> str | None:
    match = re.search(r"(?m)^name:\s*['\"]?(.+?)['\"]?\s*$", text)
    return match.group(1).strip() if match else None


def safe_relative(value: str | None) -> bool:
    if not value:
        return True
    path = PurePosixPath(value.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts


def main() -> None:
    marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    entries = {item["name"]: item for item in marketplace.get("plugins", [])}
    for plugin in PLUGINS:
        manifest_path = ROOT / "plugins" / plugin / ".codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("name") != plugin or not SEMVER.match(manifest.get("version", "")):
            fail(f"{plugin}: invalid name or semantic version")
        for key in ("description", "author", "interface"):
            if not manifest.get(key):
                fail(f"{plugin}: missing {key}")
        if plugin not in entries or entries[plugin].get("source", {}).get("path") != f"./plugins/{plugin}":
            fail(f"{plugin}: Marketplace entry missing or has the wrong path")
        for skill_md in (ROOT / "plugins" / plugin / "skills").rglob("SKILL.md"):
            text = skill_md.read_text(encoding="utf-8")
            if not re.search(r"(?m)^name:\s*.+$", text) or not re.search(r"(?m)^description:\s*.+$", text):
                fail(f"{skill_md.relative_to(ROOT)}: invalid Skill front matter")
    for path in (ROOT / "plugins").rglob("*"):
        if path.is_symlink():
            fail(f"{path.relative_to(ROOT)}: symbolic links are not allowed")
        if path.is_file() and (path.name in FORBIDDEN_NAMES or path.name.startswith(".env.") or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}):
            fail(f"{path.relative_to(ROOT)}: forbidden credential-like file")
    mcp = json.loads((ROOT / "plugins/research-toolkit/.mcp.json").read_text(encoding="utf-8"))
    itasca = mcp.get("mcpServers", {}).get("itasca-mcp", {})
    if itasca.get("command") != "uvx" or itasca.get("args") != ["itasca-mcp"]:
        fail("research-toolkit: invalid itasca-mcp configuration")
    if not (ROOT / "plugins/research-toolkit/assets/itasca-mcp-addon.py").is_file():
        fail("research-toolkit: ITASCA bridge addon is missing")
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    names = [item["name"] for item in sources["sources"]]
    if len(names) != len(set(names)):
        fail("sources.json contains duplicate source names")
    copy_targets = [item["target"] for item in sources["sources"] if item.get("action") == "copy"]
    if len(copy_targets) != len(set(copy_targets)):
        fail("sources.json contains duplicate copy targets")
    source_by_name = {item["name"]: item for item in sources["sources"]}
    for plugin, names in REQUIRED_SKILLS.items():
        for name in names:
            item = source_by_name.get(name)
            expected_target = f"plugins/{plugin}/skills/{name}"
            if not item or item.get("action") != "copy" or item.get("target") != expected_target:
                fail(f"{name}: source lock does not enable automatic copy into {plugin}")
            if item.get("license_scope") == "repository-root":
                license_path = ROOT / expected_target / "UPSTREAM_LICENSE"
                if not license_path.is_file():
                    fail(f"{name}: repository-level UPSTREAM_LICENSE is missing")
    for item in sources["sources"]:
        if item.get("commit_sha") and not SHA.match(str(item["commit_sha"])):
            fail(f"{item['name']}: invalid commit SHA")
        if not safe_relative(item.get("upstream_subpath")) or not safe_relative(item.get("target")):
            fail(f"{item['name']}: unsafe source or target path")
        if item["action"] == "copy" and not (ROOT / item["target"] / "SKILL.md").is_file():
            fail(f"{item['name']}: locked target is missing SKILL.md")
        if item["action"] == "copy":
            target = ROOT / item["target"]
            if not target.resolve().is_relative_to((ROOT / "plugins").resolve()):
                fail(f"{item['name']}: target escapes plugins/")
            text = (target / "SKILL.md").read_text(encoding="utf-8")
            if skill_name(text) != item["name"]:
                fail(f"{item['name']}: SKILL.md name does not match the source lock")
            if item.get("license") not in ALLOWED_LICENSES:
                fail(f"{item['name']}: copy action has an unapproved license")
            if item.get("license_scope") == "skill-root":
                license_path = target / str(item.get("license_file"))
                if not license_path.is_file():
                    fail(f"{item['name']}: Skill license file is missing")
    print("Marketplace, manifests, source lock, and all bundled SKILL.md files are valid.")


if __name__ == "__main__":
    main()
