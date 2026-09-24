#!/usr/bin/env python3
"""一条命令跑完本技能的全部结构门禁与可复现性检查。

防止的失败模式：门禁存在但没人执行——四个校验脚本散落在 scripts/ 里，
外部使用者与未来的维护者都不知道它们存在，于是"结构校验通过"变成一句口头声称。
本文件把这些检查收敛成单一入口，退出码即结论（0 = 全通过）。

用法：
    python scripts/verify-all.py            # 全量
    python scripts/verify-all.py --quiet    # 只打印结论行

不做的事：不联网、不写技能目录（临时产物写入系统临时目录并在结束时删除）。
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PY = sys.executable

# Windows 控制台默认用本地代码页（如 cp936）编码输出，中文会变乱码；
# 显式把本进程的 stdout/stderr 切到 UTF-8。子进程输出已按 UTF-8 解码后重印。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def run(label: str, args: list[str], quiet: bool) -> tuple[str, bool, str]:
    """跑一个子进程检查。返回 (label, 是否通过, 摘要行)。"""
    proc = subprocess.run(
        [PY, *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "").strip().splitlines()
    err = (proc.stderr or "").strip().splitlines()
    ok = proc.returncode == 0
    summary = out[0] if out else (err[0] if err else "(no output)")
    if not quiet or not ok:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
        print(f"         {summary}")
        if not ok:
            for line in (out + err)[:8]:
                print(f"         | {line}")
    return label, ok, summary


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_docs_consistency(quiet: bool) -> list[tuple[str, bool, str]]:
    """文档自洽性：同一件事不得有两种说法。

    防止的失败模式：包内四道门禁只查"文件在不在、JSON 合不合法"，不查"同一件事有没有两种说法"。
    2026-09-24 审计实测出 10 处此类矛盾（候选阈值四个版本、阶段 3 产物两个名字、payload 三个名字、
    "九个字段"后列十个、`≥N` 占位符未填…），因此把判据固化成检查。
    """
    files = [ROOT / "SKILL.md"]
    for sub in ("references", "assets"):
        files += sorted(p for p in (ROOT / sub).rglob("*") if p.is_file())
    text = {p: p.read_text(encoding="utf-8", errors="ignore") for p in files}
    blob = "\n".join(text.values())
    out: list[tuple[str, bool, str]] = []

    def check(label: str, ok: bool, detail: str) -> None:
        out.append((label, ok, detail))
        if not quiet or not ok:
            print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
            print(f"         {detail}")

    # 1) 候选阈值必须单值：≥20（窄领域 ≥12），来源桶 ≥4 类
    stale = [p.name for p, t in text.items() if re.search(r'≥\s*15\s*条候选', t)]
    check("候选数阈值统一为 ≥20 条（无残留 ≥15）", not stale, f"残留旧阈值的文件: {stale or '无'}")
    unbound = [p.name for p, t in text.items()
               if re.search(r'(?:候选|来源池)[^\n]{0,30}≥\s*N\s*条|≥\s*N\s*条[^\n]{0,10}候选', t)]
    check("候选阈值无未填的 `≥N` 占位符", not unbound, f"未填占位符: {unbound or '无'}")
    check("来源桶要求统一为 ≥4 类",
          not re.search(r'覆盖\s*≥\s*3\s*(?:种|个)[^\n]*来源', blob),
          "仍存在「≥3 类来源桶」的旧写法" if re.search(r'覆盖\s*≥\s*3\s*(?:种|个)[^\n]*来源', blob) else "一致")

    # 2) 阶段 3 反证产物必须只有一个名字
    check("阶段 3 反证产物命名为 04-counterevidence.md（无 refutation.md 残留）",
          "refutation.md" not in blob, "仍出现 refutation.md" if "refutation.md" in blob else "一致")

    # 3) 交付 payload 必须只有一个名字（排除 report-payload / example-report-payload）
    bare = [p.name for p, t in text.items() if re.search(r'(?<!-)payload\.json', t)]
    check("交付 payload 统一为 report-payload.json（无裸 payload.json）",
          not bare, f"仍出现裸 payload.json: {bare or '无'}")
    check("无 证据库.json 这个别名", "证据库.json" not in blob,
          "仍出现 证据库.json" if "证据库.json" in blob else "一致")

    # 4) EV 字段数表述
    check("EV 字段数表述为「十字段」（无「九字段」）",
          "九字段" not in blob and "九个字段" not in blob,
          "仍出现「九字段/九个字段」" if ("九字段" in blob or "九个字段" in blob) else "一致")

    # 5) 无人值守分支必须存在（否则阶段 0.1 在无人环境会阻塞且不留产物）
    has_unattended = "无人值守" in text[ROOT / "SKILL.md"]
    check("存在无人值守分支的明文规定", has_unattended,
          f"SKILL.md 含「无人值守」规定: {'是' if has_unattended else '否'}（缺它则阶段 0.1 在无人环境会阻塞且不留产物）")

    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="deep-research-collab 全量门禁与可复现性检查")
    ap.add_argument("--quiet", action="store_true", help="只打印结论行")
    ns = ap.parse_args()
    quiet = ns.quiet

    results: list[tuple[str, bool, str]] = []

    print("== 1/4 结构门禁 ==")
    results.append(run("包结构完整（必需文件齐备）", [str(SCRIPTS / "check_meta_skill_package.py"), "."], quiet))
    results.append(run("闭环治理契约", [str(SCRIPTS / "check_closed_loop.py"), "."], quiet))

    print("== 2/4 验收运行门禁 ==")
    runs_dir = ROOT / "evals" / "acceptance" / "runs"
    run_dirs = sorted(p for p in runs_dir.iterdir() if p.is_dir()) if runs_dir.is_dir() else []
    if not run_dirs:
        print("  [FAIL] 未找到任何 acceptance run 目录")
        results.append(("验收运行门禁", False, "no runs found"))
    else:
        for rd in run_dirs:
            rel = rd.relative_to(ROOT)
            results.append(run(f"验收运行 {rel}", [str(SCRIPTS / "check_acceptance_runs.py"), str(rel)], quiet))

    print("== 3/4 报告生成（--strict）==")
    payload = ROOT / "examples" / "example-report-payload.json"
    with tempfile.TemporaryDirectory(prefix="drc-verify-") as tmp:
        a = Path(tmp) / "a.html"
        b = Path(tmp) / "b.html"
        results.append(
            run("--strict 校验（引用不存在的 EV / 结论无证据 / 独立来源不足即失败）",
                [str(SCRIPTS / "build_report.py"), "--payload", str(payload), "--out", str(a), "--strict"], quiet)
        )

        print("== 4/4 可复现性 ==")
        run("第二次生成", [str(SCRIPTS / "build_report.py"), "--payload", str(payload), "--out", str(b), "--strict"], True)
        if a.is_file() and b.is_file():
            same = sha256(a) == sha256(b)
            if not quiet or not same:
                print(f"  [{'PASS' if same else 'FAIL'}] 同一 payload 两次生成逐字节一致")
                print(f"         sha256={sha256(a)[:16]}  bytes={a.stat().st_size}")
            results.append(("可复现性", same, sha256(a)[:16]))
        else:
            print("  [FAIL] 生成物缺失，无法比对")
            results.append(("可复现性", False, "artifact missing"))

    print("== 5/5 文档自洽性 ==")
    results.extend(check_docs_consistency(quiet))

    failed = [r for r in results if not r[1]]
    print()
    print(f"== 结论：{len(results) - len(failed)}/{len(results)} 项通过 ==")
    if failed:
        for label, _, summary in failed:
            print(f"  FAILED: {label} -> {summary}")
        return 1
    print("全部通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
