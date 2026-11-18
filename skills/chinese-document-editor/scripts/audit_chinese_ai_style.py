#!/usr/bin/env python3
"""Read-only scanner for common AI-like patterns in Chinese product prose."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    category: str
    pattern: re.Pattern[str]
    advice: str


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    severity: str
    rule_id: str
    category: str
    match: str
    advice: str
    text: str


RULES = (
    Rule("P0-CHAT", "p0", "聊天回复残留", re.compile(r"(?:当然[，,!！]|没问题[，,!！]|以下是(?:为你|我为你)?|希望(?:以上|这些)?.{0,8}帮助|需要我继续|如果你愿意.{0,8}我可以)"), "删除对话式包装，直接进入文档内容。"),
    Rule("P0-AUTH", "p0", "无来源权威", re.compile(r"(?:专家普遍认为|业内(?:人士)?一致认为|研究表明|众所周知|大量研究证明)"), "补充具体来源；没有来源时删除归因或标记资料不足。"),
    Rule("P0-PROMISE", "p0", "无法证明的承诺", re.compile(r"(?:百分之百|完全准确|确保成功|必然(?:实现|带来|提升)|稳定可用|自动完成全部工作)"), "改成证据范围、验证条件或待验证假设。"),
    Rule("P0-STATUS", "p0", "状态或能力膨胀", re.compile(r"(?:已全面实现|现已完整支持|已经形成成熟(?:体系|闭环)|已彻底解决)"), "回到当前 PRD、原型或状态文件，区分设计、验证和上线。"),
    Rule("P1-SLOGAN", "p1", "空泛宣传", re.compile(r"(?:一站式|赋能|全方位|多维度|生态闭环|无缝(?:衔接|体验)?|行业领先|颠覆(?:性)?|深度融合|持续深耕|具有重要意义)"), "用具体对象、动作、证据和边界替代；没有信息增量时删除。"),
    Rule("P1-GAIN", "p1", "无指标结果词", re.compile(r"(?:大幅|显著|全面|极大)(?:提升|提高|增强|改善|降低|减少|优化)"), "补充指标或证据；否则改成可验证动作。"),
    Rule("P1-META", "p1", "元话语或套话", re.compile(r"(?:值得注意的是|需要指出的是|不可否认|在当今(?:快速发展|日新月异)的|综上所述|总而言之|让我们(?:一起)?(?:来看|深入|探索))"), "删除暖场和总结套话，直接写事实、决定或动作。"),
    Rule("P1-NOUN", "p1", "抽象名词堆叠", re.compile(r"(?:能力建设|体系构建|价值提升|生态打造|机制完善|协同推进|体验赋能)"), "改成执行者、动作、对象和完成证据。"),
    Rule("P2-BALANCE", "p2", "机械对称", re.compile(r"(?:不仅.{0,30}(?:而且|还|更)|既.{0,25}又.{0,25}(?:还|更))"), "检查是否为强行并列；能直说时拆成具体句。"),
    Rule("P2-NEED", "p2", "弱责任表达", re.compile(r"(?:需要|应该|可以)(?:进一步|持续|不断)?(?:加强|完善|提升|优化|推进)"), "补充执行者、对象、时点和完成条件。"),
    Rule("P2-BUILD", "p2", "泛化建设动词", re.compile(r"(?:打造|构建|搭建)(?:一个|起|出)?(?:完整|完善|全新|高效|统一)?(?:的)?(?:体系|生态|能力|平台|机制)"), "确认是否有具体组件和验收；否则改写为实际动作。"),
)

SEVERITY_ORDER = {"p0": 0, "p1": 1, "p2": 2}
TEXT_EXTENSIONS = {".md", ".markdown", ".txt"}


def iter_files(raw_paths: Iterable[str]) -> Iterable[Path]:
    seen: set[Path] = set()
    for raw in raw_paths:
        path = Path(raw).resolve()
        if path.is_file():
            candidates = (path,)
        elif path.is_dir():
            candidates = (p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXTENSIONS)
        else:
            print(f"warning: path does not exist: {raw}", file=sys.stderr)
            continue
        for candidate in candidates:
            if candidate.suffix.lower() not in TEXT_EXTENSIONS or candidate in seen:
                continue
            seen.add(candidate)
            yield candidate


def visible_lines(text: str) -> Iterable[tuple[int, str]]:
    in_fence = False
    fence_marker = ""
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        fence = re.match(r"(```+|~~~+)", stripped)
        if fence:
            marker = fence.group(1)[0]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if in_fence or stripped.startswith(">"):
            continue
        without_inline_code = re.sub(r"`[^`]*`", "", line)
        if without_inline_code.strip():
            yield number, without_inline_code


def scan_file(path: Path) -> tuple[list[Finding], str | None]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return [], str(exc)

    findings: list[Finding] = []
    for line_number, line in visible_lines(text):
        for rule in RULES:
            for match in rule.pattern.finditer(line):
                findings.append(
                    Finding(
                        path=str(path),
                        line=line_number,
                        severity=rule.severity,
                        rule_id=rule.rule_id,
                        category=rule.category,
                        match=match.group(0),
                        advice=rule.advice,
                        text=line.strip(),
                    )
                )
    return findings, None


def print_text(findings: list[Finding], errors: list[dict[str, str]]) -> None:
    counts = {level: sum(1 for item in findings if item.severity == level) for level in SEVERITY_ORDER}
    print(f"findings={len(findings)} p0={counts['p0']} p1={counts['p1']} p2={counts['p2']} errors={len(errors)}")
    for item in findings:
        print(f"{item.severity.upper()} {item.path}:{item.line} [{item.rule_id} {item.category}] {item.match}")
        print(f"  {item.advice}")
        print(f"  {item.text}")
    for error in errors:
        print(f"ERROR {error['path']}: {error['error']}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Markdown/text files or directories to scan")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--fail-on", choices=("none", "p0", "p1", "p2"), default="none")
    args = parser.parse_args()

    findings: list[Finding] = []
    errors: list[dict[str, str]] = []
    for path in iter_files(args.paths):
        file_findings, error = scan_file(path)
        findings.extend(file_findings)
        if error:
            errors.append({"path": str(path), "error": error})

    findings.sort(key=lambda item: (SEVERITY_ORDER[item.severity], item.path.lower(), item.line, item.rule_id))
    if args.format == "json":
        payload = {
            "summary": {
                "filesWithErrors": len(errors),
                "total": len(findings),
                **{level: sum(1 for item in findings if item.severity == level) for level in SEVERITY_ORDER},
            },
            "findings": [asdict(item) for item in findings],
            "errors": errors,
            "notice": "Pattern matches are editing candidates, not proof that text was AI-generated.",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text(findings, errors)

    if errors:
        return 2
    if args.fail_on != "none":
        threshold = SEVERITY_ORDER[args.fail_on]
        if any(SEVERITY_ORDER[item.severity] <= threshold for item in findings):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
