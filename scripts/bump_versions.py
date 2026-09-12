#!/usr/bin/env python3
"""Increment patch versions for plugins whose content changed."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def bump(version: str) -> str:
    base, *build = version.split("+", 1)
    major, minor, patch = base.split("-", 1)[0].split(".")
    suffix = "-" + base.split("-", 1)[1] if "-" in base else ""
    return f"{major}.{minor}.{int(patch) + 1}{suffix}" + (f"+{build[0]}" if build else "")


def main() -> None:
    for name in sys.argv[1:]:
        path = ROOT / "plugins" / name / ".codex-plugin" / "plugin.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["version"] = bump(payload["version"])
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{name} -> {payload['version']}")


if __name__ == "__main__":
    main()
