#!/usr/bin/env python3
"""检查仓库结构、计数、链接、用例编号和元数据是否同步。"""

import html
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "tasks", "assets"}
SKIP_FILES = {"evals/run-manifest.md", "CHANGELOG.md"}

# 每项依次为：文件、捕获计数的 regex、期望值来源、预期命中数。
ANCHORS = (
    ("README.md", r"benchmark-(\d+)%20cases", "total", 1),
    ("README.md", r'alt="Benchmark: (\d+) cases"', "total", 1),
    ("README.md", r"scenario%20samples-(\d+)", "rs", 1),
    ("README.md", r'alt="Scenario samples: (\d+)"', "rs", 1),
    ("README.md", r"^当前评测集共 (\d+) 条：$", "total", 1),
    ("README.md", r"^\| SF \| (\d+) \|", "sf", 1),
    ("README.md", r"^\| SNF \| (\d+) \|", "snf", 1),
    ("README.md", r"^\| 场景样本 \| (\d+) \|", "rs", 1),
    ("README.md", r"an (\d+)-case benchmark", "total", 1),
    ("evals/run-eval.md", r"^### 对 Should Fix（SF-01 到 SF-(\d+)）：$", "sf", 1),
    ("evals/run-eval.md", r"^### 对 Should NOT Fix（SNF-01 到 SNF-(\d+)）：$", "snf", 1),
    ("evals/run-eval.md", r"^- SF 通过率：X/(\d+)$", "sf", 1),
    ("evals/run-eval.md", r"^- SNF 误杀率：X/(\d+)$", "snf", 1),
    ("evals/run-eval.md", r"^注意：token .*一次跑完 (\d+) 条", "total", 1),
    ("evals/real-samples.md", r"^> v1\.7\.2 新增.*v1\.8\.5 扩到 (\d+) 条。", "rs", 1),
    ("evals/real-samples.md", r"^\| 数量 \| (\d+) 条，持续扩充 \|", "total", 1),
    ("evals/real-samples.md", r"^\| 数量 \| \d+ 条，持续扩充 \| (\d+) 条，质量优先 \|", "rs", 1),
    ("evals/real-samples.md", r"^> 现在覆盖 .*?(\d+) 条 benchmark。", "total", 1),
    ("evals/real-samples.md", r"^### RS-(19)\b", "rs", 1),
    ("evals/benchmark-blind.md", r"^> 共 (\d+) 条。", "total", 1),
    ("evals/benchmark-map.md", r"^> 共 (\d+) 条 = \d+ SF \+ \d+ SNF。$", "total", 1),
    ("evals/benchmark-map.md", r"^> 共 \d+ 条 = (\d+) SF \+ \d+ SNF。$", "sf", 1),
    ("evals/benchmark-map.md", r"^> 共 \d+ 条 = \d+ SF \+ (\d+) SNF。$", "snf", 1),
    ("automation/eval/README.md", r"^\| `B65-(\d+)` \| B-65 到 B-\1 \|$", "total", 1),
)

LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^)\s]+)")
HTML_LINK_RE = re.compile(r'(?:href|src)="([^"]+)"')
CASE_ID_RE = re.compile(r"\b(?:SF|SNF|RS)-\d+\b")
FUTURE_ID_RE = re.compile(r"新增从\s+((?:SF|SNF|RS)-\d+)\s+起")


def line_number(text, offset):
    return text.count("\n", 0, offset) + 1


def add_issue(issues, path, line, check_id, message):
    issues.append(f"{path}:{line} [{check_id}] {message}")


def read_text(relative, issues, check_id):
    try:
        return (ROOT / relative).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        add_issue(issues, relative, "-", check_id, f"无法读取：{exc}")
        return None


def check_blind_sync(issues):
    script = ROOT / "automation" / "eval" / "make_blind.py"
    result = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    if result.returncode:
        for message in output.splitlines() or [f"退出码 {result.returncode}"]:
            add_issue(issues, "automation/eval/make_blind.py", "-", "blind-sync", message)
    elif output:
        print(output)


def check_counts(issues):
    benchmark = read_text("evals/benchmark.md", issues, "counts")
    samples = read_text("evals/real-samples.md", issues, "counts")
    if benchmark is None or samples is None:
        return None, None, None, None, 0

    case_matches = list(re.finditer(r"^### ((SF|SNF)-\d+) \|", benchmark, re.MULTILINE))
    rs_matches = list(re.finditer(r"^#{2,4} (RS-\d+)\b", samples, re.MULTILINE))
    if not case_matches:
        add_issue(issues, "evals/benchmark.md", "-", "counts", "没有解析到 benchmark 用例标题")
    if not rs_matches:
        add_issue(issues, "evals/real-samples.md", "-", "counts", "没有解析到 RS 样本标题")

    sf = sum(match.group(2) == "SF" for match in case_matches)
    snf = len(case_matches) - sf
    expected = {"total": len(case_matches), "sf": sf, "snf": snf, "rs": len(rs_matches)}
    anchor_count = 0
    for relative, pattern, source, expected_hits in ANCHORS:
        text = read_text(relative, issues, "counts")
        if text is None:
            continue
        matches = list(re.finditer(pattern, text, re.MULTILINE))
        if len(matches) != expected_hits:
            line = line_number(text, matches[0].start()) if matches else "-"
            add_issue(
                issues,
                relative,
                line,
                "counts",
                f"锚点失配：{pattern!r} 预期命中 {expected_hits} 次，实际 {len(matches)} 次",
            )
            continue
        anchor_count += len(matches)
        for match in matches:
            actual = int(match.group(1))
            if actual != expected[source]:
                add_issue(
                    issues,
                    relative,
                    line_number(text, match.start()),
                    "counts",
                    f"计数应为 {expected[source]}，实际为 {actual}",
                )
    return case_matches, rs_matches, sf, snf, anchor_count


def markdown_files(issues):
    files = []
    for path in ROOT.rglob("*.md"):
        relative = path.relative_to(ROOT)
        relative_text = relative.as_posix()
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if relative_text in SKIP_FILES or (
            relative.parent.as_posix() == "evals" and relative.name.startswith("results-")
        ):
            continue
        try:
            files.append((relative_text, path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError) as exc:
            add_issue(issues, relative_text, "-", "links", f"无法读取：{exc}")
    return files


def strip_inline_code(line):
    return re.sub(r"(`+)[^`]*?\1", "", line)


def local_target(target):
    target = html.unescape(target.strip())
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if target.startswith(("http://", "https://", "mailto:", "data:", "#")):
        return None
    return unquote(target.split("#", 1)[0].split("?", 1)[0]) or None


def check_links(files, issues):
    checked = 0
    for relative, text in files:
        source = ROOT / relative
        in_fence = False
        for number, raw_line in enumerate(text.splitlines(), 1):
            if re.match(r"^\s*(```|~~~)", raw_line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            line = strip_inline_code(raw_line)
            targets = [match.group(1) for match in LINK_RE.finditer(line)]
            if relative == "README.md":
                targets += [match.group(1) for match in HTML_LINK_RE.finditer(line)]
            for target in targets:
                path_text = local_target(target)
                if path_text is None:
                    continue
                checked += 1
                destination = source.parent / path_text
                if not destination.exists():
                    add_issue(issues, relative, number, "links", f"相对链接目标不存在：{path_text}")
    return checked


def check_case_ids(files, case_matches, rs_matches, issues):
    if case_matches is None or rs_matches is None:
        return
    valid = {match.group(1) for match in case_matches}
    valid.update(match.group(1) for match in rs_matches)
    for relative, text in files:
        # “新增从 RS-20 起”描述的是下一个可用编号，不是对现有用例的引用。
        future_spans = {match.span(1) for match in FUTURE_ID_RE.finditer(text)}
        for match in CASE_ID_RE.finditer(text):
            if match.span() in future_spans:
                continue
            if match.group(0) not in valid:
                add_issue(
                    issues,
                    relative,
                    line_number(text, match.start()),
                    "case-ids",
                    f"用例编号不存在：{match.group(0)}",
                )


def check_meta(issues):
    skill = read_text("SKILL.md", issues, "meta")
    if skill is not None:
        lines = skill.splitlines()
        if not lines or lines[0] != "---" or "---" not in lines[1:]:
            add_issue(issues, "SKILL.md", 1, "meta", "frontmatter 不存在或未闭合")
        else:
            end = lines[1:].index("---") + 1
            metadata = {}
            for number, line in enumerate(lines[1:end], 2):
                match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
                if match:
                    metadata[match.group(1)] = (match.group(2).strip(), number)
            for key in ("name", "description"):
                value, number = metadata.get(key, ("", 1))
                if not value:
                    add_issue(issues, "SKILL.md", number, "meta", f"frontmatter 的 {key} 不能为空")

    for relative in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        text = read_text(relative, issues, "meta")
        if text is None:
            continue
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            add_issue(issues, relative, exc.lineno, "meta", f"JSON 无法解析：{exc.msg}")


def main():
    issues = []
    check_blind_sync(issues)
    case_matches, rs_matches, sf, snf, anchors = check_counts(issues)
    files = markdown_files(issues)
    links = check_links(files, issues)
    check_case_ids(files, case_matches, rs_matches, issues)
    check_meta(issues)

    if issues:
        print("\n".join(issues))
        print(f"check_repo: FAIL（{len(issues)} 个问题）")
        return 1
    total = sf + snf
    print(f"check_repo: OK（{total} 用例 / {len(rs_matches)} 样本 / {anchors} 锚点 / {links} 链接）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
