#!/usr/bin/env python3
"""把仓库里的 <OWNER> 占位符替换成你的 GitHub 用户名。

用法：
    python scripts/set-owner.py <github-owner> [--dry-run]

为什么需要它：本仓库的 README 徽章(3)、CHANGELOG(1) 与 marketplace.json(5) 里共 9 处 <OWNER>，
发布前必须替换；手工改容易漏。本脚本只做这一件事，跑完即打印每处改动。

注意：`grep -r '<OWNER>'` 还会命中本文件与 PUBLISH.md —— 那是在**描述**这个占位符，不是待替换项。
可替换的只有上面三个文件（即本脚本 TARGETS 列表）。

安全：只改这三个文件、只替换字面量 <OWNER>；不碰技能正文（skills/ 目录内不出现占位符）。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "README.md",
    ROOT / "CHANGELOG.md",
    ROOT / ".claude-plugin" / "marketplace.json",
]
PLACEHOLDER = "<OWNER>"
OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description="替换仓库内的 <OWNER> 占位符")
    ap.add_argument("owner", help="GitHub 用户名或组织名")
    ap.add_argument("--dry-run", action="store_true", help="只报告会改什么，不写盘")
    ns = ap.parse_args()

    if not OWNER_RE.match(ns.owner):
        print(f"✘ 不是合法的 GitHub 用户名：{ns.owner!r}", file=sys.stderr)
        print("  规则：字母或数字开头，可含连字符，最长 39 字符。", file=sys.stderr)
        return 2

    total = 0
    for path in TARGETS:
        if not path.is_file():
            print(f"  [跳过] 不存在：{path.relative_to(ROOT)}", file=sys.stderr)
            continue
        text = path.read_text(encoding="utf-8")
        n = text.count(PLACEHOLDER)
        if n == 0:
            print(f"  [无占位] {path.relative_to(ROOT)}")
            continue
        print(f"  [{ '将替换' if ns.dry_run else '已替换' } {n} 处] {path.relative_to(ROOT)}")
        total += n
        if not ns.dry_run:
            path.write_text(text.replace(PLACEHOLDER, ns.owner), encoding="utf-8")

    if total == 0:
        print("\n没有找到 <OWNER> 占位符——可能已经替换过了。")
        return 0

    print(f"\n共 {total} 处。")
    if ns.dry_run:
        print("（--dry-run：未写盘）")
    else:
        print(f"完成。下一步见 PUBLISH.md 第 2 步：初始化仓库并提交。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
