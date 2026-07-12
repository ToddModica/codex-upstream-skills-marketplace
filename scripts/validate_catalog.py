#!/usr/bin/env python3
"""Validate the local Marketplace structure without importing third-party code."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ("research-toolkit", "writing-toolkit", "codex-utility-toolkit")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


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
    mcp = json.loads((ROOT / "plugins/research-toolkit/.mcp.json").read_text(encoding="utf-8"))
    itasca = mcp.get("mcpServers", {}).get("itasca-mcp", {})
    if itasca.get("command") != "uvx" or itasca.get("args") != ["itasca-mcp"]:
        fail("research-toolkit: invalid itasca-mcp configuration")
    if not (ROOT / "plugins/research-toolkit/assets/itasca-mcp-addon.py").is_file():
        fail("research-toolkit: ITASCA bridge addon is missing")
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    for item in sources["sources"]:
        if item["action"] == "copy" and not (ROOT / item["target"] / "SKILL.md").is_file():
            fail(f"{item['name']}: locked target is missing SKILL.md")
    print("Marketplace, manifests, source lock, and all bundled SKILL.md files are valid.")


if __name__ == "__main__":
    main()
