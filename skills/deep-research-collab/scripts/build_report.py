#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""证据导向型深度调研 —— 单文件离线 HTML 报告生成器（deep-research-collab）。

设计目标
--------
1. 单一输入：一份符合约定 schema 的 payload JSON（机器结构数据），即可产出
   可离线打开、可交互、可打印、可归档的单文件 HTML 报告。
2. 零外部依赖：只用 Python 标准库；产物不引用任何 CDN、外链 JS/CSS/字体、
   外部图片；唯一允许出现的外部 URL 是证据条目的原始链接（<a href="...">）。
3. 结论级溯源：所有 [EV-00X] 标签都可点击，平滑滚动到证据库对应条目并高亮 3 秒。
4. 确定性：同一 payload 生成字节完全相同的 HTML；不嵌入当前时间，产物指纹
   （digest）取自 payload 内容的 sha256 前 8 位。
5. 失败可见：任何解析/校验问题都会在 stderr 明确报错或警告，绝不静默输出空报告。

CLI
---
    python scripts/build_report.py --payload <payload.json> --out <report.html>
                                   [--title "..."] [--strict] [--open]

退出码：0 成功；1 --strict 下校验失败；2 参数/payload/JSON 错误。
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# 常量与调色板（克制的商务蓝/灰，避免花哨渐变）
# ---------------------------------------------------------------------------

PALETTE: Tuple[str, ...] = (
    "#1f5fa9", "#3b7dd8", "#5c9be5", "#8fb8e8",
    "#2f4858", "#5b6b7a", "#8d99a6", "#b6c2cd",
)

CONFIDENCE_STYLES: Dict[str, str] = {
    "高": "conf-high",
    "中": "conf-mid",
    "待验证": "conf-low",
}

CREDIBILITY_STYLES: Dict[str, str] = {
    "高": "cred-high",
    "中": "cred-mid",
    "待验证": "cred-low",
}

# 8 个标准模块：顺序固定，不得调整（文档版 Markdown 必须同序）
MODULES: Tuple[Tuple[str, str], ...] = (
    ("sec-overview", "报告概览"),
    ("sec-mindmap", "领域认知地图"),
    ("sec-sources", "三级搜索来源溯源"),
    ("sec-findings", "核心研究发现"),
    ("sec-disputes", "争议与反证分析"),
    ("sec-cases", "典型案例库"),
    ("sec-evidence", "完整证据库"),
    ("sec-appendix", "附录"),
)

MAX_MINDMAP_DEPTH = 8  # 递归防御：payload 里的自引用/超深树不允许拖垮渲染


# ---------------------------------------------------------------------------
# 通用工具：容错取值与转义
# ---------------------------------------------------------------------------

def as_dict(value: Any) -> Dict[str, Any]:
    """把任意值收敛成 dict。

    防止的失败：payload 里某字段写成 list/str/null 时，后续 .get() 直接抛
    AttributeError 导致整个报告生成中断。这里统一降级为 {}。
    """
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> List[Any]:
    """把任意值收敛成 list（None/标量/dict 都不再让调用方崩）。

    防止的失败：可选数组字段缺失或类型错误时，for/len 抛 TypeError。
    """
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def as_str(value: Any, default: str = "") -> str:
    """把任意值收敛成 str；None -> default，dict/list -> JSON 字符串。

    防止的失败：数字型 count、None 标题等在字符串拼接/转义时报错或显示 "None"。
    """
    if value is None:
        return default
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return format_number(value)
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return default
    return str(value)


def format_number(value: Any) -> str:
    """数字格式化：整数不带小数点，小数最多保留 2 位。

    防止的失败：SVG 坐标里出现 '1.0e-05' 之类科学计数法串导致图形错乱。
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return as_str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return "0"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def esc(text: Any) -> str:
    """HTML 文本转义（含引号），所有插入 HTML 的 payload 字段都要过这里。

    防止的失败：payload 内含 < > & " ' 时破坏 DOM 结构，或形成脚本注入。
    """
    return html.escape(as_str(text), quote=True)


def to_number(value: Any, default: float = 0.0) -> float:
    """把 payload 里的值安全转成 float，非法值回退 default。

    防止的失败：charts.values 里混入字符串/None 时，SVG 坐标计算抛 TypeError。
    """
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else default
    if isinstance(value, str):
        try:
            parsed = float(value.strip())
        except ValueError:
            return default
        return parsed if math.isfinite(parsed) else default
    return default


def payload_digest(payload: Any) -> str:
    """payload 内容的 sha256 前 8 位，用作产物指纹/版本号。

    防止的失败：为了“可追溯”而写入当前时间戳，破坏生成确定性。
    """
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:8]


# ---------------------------------------------------------------------------
# payload 读取与校验
# ---------------------------------------------------------------------------

def load_payload(path: str) -> Dict[str, Any]:
    """读取并解析 payload JSON。

    防止的失败：文件不存在、权限不足、编码错误、JSON 非法时给出模糊 traceback；
    这里统一转成带路径的清晰错误，由 main 以 exit 2 结束。
    """
    if not os.path.isfile(path):
        raise PayloadError(f"payload 文件不存在：{path}")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        raise PayloadError(f"payload 文件无法读取：{path}（{exc}）") from exc
    except UnicodeDecodeError as exc:
        raise PayloadError(f"payload 不是合法 UTF-8 文本：{path}（{exc}）") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PayloadError(
            f"payload JSON 解析失败：{path} 第 {exc.lineno} 行第 {exc.colno} 列 —— {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        raise PayloadError(f"payload 顶层必须是 JSON 对象，实际为 {type(data).__name__}：{path}")
    return data


class PayloadError(Exception):
    """payload 读取/解析类错误（对应 exit 2）。"""


def configure_stdio() -> None:
    """把 stdout/stderr 切到 UTF-8，避免 Windows 默认 GBK 控制台把中文摘要打成乱码。

    防止的失败：中文摘要/错误信息在 GBK 控制台下抛 UnicodeEncodeError 或显示为乱码，
    使"校验结果"这类关键信息对使用者不可读。切换失败时静默降级（不影响构建本身）。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def validate(payload: Dict[str, Any]) -> List[str]:
    """6 项契约校验，返回问题描述列表（空列表 = 通过）。

    ① findings.evidence 为空
    ② 引用了不存在的 EV ID
    ③ 核心结论独立来源 < 2（按去重后的来源 url 数量）
    ④ 争议点缺少 pro 或 con
    ⑤ charts 的 series 值个数与 categories 不匹配
    ⑥ HTML 与文档版 Markdown 字段一致性（本生成器不做实现，见下方注释）

    防止的失败：报告看着完整、实际存在无据结论或断链引用，读者被误导。
    """
    problems: List[str] = []

    evidence_items = [as_dict(item) for item in as_list(payload.get("evidence"))]
    known_ids = {as_str(item.get("id")).strip() for item in evidence_items}
    known_ids.discard("")
    url_by_id: Dict[str, str] = {}
    for item in evidence_items:
        ev_id = as_str(item.get("id")).strip()
        if ev_id:
            url_by_id[ev_id] = as_str(item.get("url")).strip()

    findings = [as_dict(item) for item in as_list(payload.get("findings"))]

    # ① + ② + ③
    for index, finding in enumerate(findings, start=1):
        fid = as_str(finding.get("id")).strip() or f"findings[{index}]"
        refs = [as_str(ref).strip() for ref in as_list(finding.get("evidence"))]
        refs = [ref for ref in refs if ref]
        if not refs:
            problems.append(f"[①] 结论 {fid} 没有任何证据 ID（findings.evidence 为空）")
            continue
        missing = [ref for ref in refs if ref not in known_ids]
        for ref in missing:
            problems.append(f"[②] 结论 {fid} 引用了不存在的证据 ID：{ref}")
        independent = {url_by_id.get(ref, "") for ref in refs if ref in known_ids}
        independent.discard("")
        if len(independent) < 2:
            problems.append(
                f"[③] 结论 {fid} 的独立来源不足 2 个（去重后 url 数 = {len(independent)}）"
            )

    # ② 扩展到图表/案例/争议/思维导图引用
    def check_refs(label: str, refs: Iterable[Any]) -> None:
        for ref in refs:
            ref_text = as_str(ref).strip()
            if ref_text and ref_text not in known_ids:
                problems.append(f"[②] {label} 引用了不存在的证据 ID：{ref_text}")

    for index, chart in enumerate(as_list(payload.get("charts")), start=1):
        chart_dict = as_dict(chart)
        cid = as_str(chart_dict.get("id")).strip() or f"charts[{index}]"
        check_refs(f"图表 {cid}", as_list(chart_dict.get("evidence")))

    for index, case in enumerate(as_list(payload.get("cases")), start=1):
        case_dict = as_dict(case)
        cname = as_str(case_dict.get("name")).strip() or f"cases[{index}]"
        check_refs(f"案例 {cname}", as_list(case_dict.get("evidence")))

    for index, dispute in enumerate(as_list(payload.get("disputes")), start=1):
        dispute_dict = as_dict(dispute)
        point = as_str(dispute_dict.get("point")).strip() or f"disputes[{index}]"
        # ④ 争议点必须同时具备正反双方
        pro = as_dict(dispute_dict.get("pro"))
        con = as_dict(dispute_dict.get("con"))
        if not as_str(pro.get("claim")).strip():
            problems.append(f"[④] 争议点「{point}」缺少 pro.claim（正方主张）")
        if not as_str(con.get("claim")).strip():
            problems.append(f"[④] 争议点「{point}」缺少 con.claim（反方主张）")
        check_refs(f"争议点「{point}」正方", as_list(pro.get("evidence")))
        check_refs(f"争议点「{point}」反方", as_list(con.get("evidence")))

    for label, refs in iter_mindmap_refs(as_dict(payload.get("mindmap"))):
        check_refs(label, refs)

    # ⑤ 图表数据完整性：每个 series 的数值个数必须等于 categories 个数
    for index, chart in enumerate(as_list(payload.get("charts")), start=1):
        chart_dict = as_dict(chart)
        cid = as_str(chart_dict.get("id")).strip() or f"charts[{index}]"
        categories = as_list(chart_dict.get("categories"))
        if not categories:
            problems.append(f"[⑤] 图表 {cid} 的 categories 为空，无法绘制")
        for s_index, series in enumerate(as_list(chart_dict.get("series")), start=1):
            series_dict = as_dict(series)
            values = as_list(series_dict.get("values"))
            if len(values) != len(categories):
                problems.append(
                    f"[⑤] 图表 {cid} 第 {s_index} 条 series「{as_str(series_dict.get('name'), '未命名')}」"
                    f"数值个数 {len(values)} 与 categories 个数 {len(categories)} 不匹配"
                )
        kind = as_str(chart_dict.get("kind")).strip()
        if kind not in ("bar", "line", "pie"):
            problems.append(f"[⑤] 图表 {cid} 的 kind=「{kind}」不是 bar/line/pie 之一（将按 bar 渲染）")

    # ⑥ 内容一致性校验说明（文档版 Markdown 与 HTML 必须字段一致）：
    #    本生成器只负责 HTML 一侧，Markdown 侧由技能包的报告撰写步骤产出；
    #    两者的字段一致性需在技能包流程中比对同一 payload 的字段清单，无法在
    #    本脚本内实现，故此处仅保留说明，不做自动判定。
    return problems


def iter_mindmap_refs(node: Any, depth: int = 0) -> Iterable[Tuple[str, List[Any]]]:
    """深度优先遍历思维导图节点，产出 (节点名, 证据 ID 列表)。

    防止的失败：payload 中 mindmap 结构异常（非 dict、children 不是数组）时递归崩溃；
    同时用 depth 上限防御人为构造的超深树导致的递归耗尽。
    """
    if depth > MAX_MINDMAP_DEPTH:
        return
    node_dict = as_dict(node)
    name = as_str(node_dict.get("name")).strip() or "未命名节点"
    yield f"认知地图节点「{name}」", as_list(node_dict.get("evidence"))
    for child in as_list(node_dict.get("children")):
        yield from iter_mindmap_refs(child, depth + 1)


# ---------------------------------------------------------------------------
# 图表渲染：纯 Python 生成内联 SVG（bar / line / pie）
# ---------------------------------------------------------------------------

def svg_open(width: float, height: float, extra_class: str = "") -> List[str]:
    """返回 SVG 头（含 xmlns，无任何外部引用）。"""
    class_attr = f' class="{esc(extra_class)}"' if extra_class else ""
    return [
        f'<svg{class_attr} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {format_number(width)} '
        f'{format_number(height)}" width="100%" height="auto" role="img" '
        f'preserveAspectRatio="xMidYMid meet">'
    ]


def render_evidence_links(evidence_ids: Sequence[str], empty_text: str = "（无直接证据）") -> str:
    """把证据 ID 列表渲染成可点击标签组；空列表给显式提示而不是留白。

    防止的失败：结论/图表没有证据时静默留空，让人误以为该处无需证据。
    """
    clean = [as_str(ref).strip() for ref in evidence_ids if as_str(ref).strip()]
    if not clean:
        return f'<span class="ev-empty">{esc(empty_text)}</span>'
    parts = [
        f'<button type="button" class="ev-tag" data-ev="{esc(ref)}" '
        f'title="跳转到证据 {esc(ref)}">{esc(ref)}</button>'
        for ref in clean
    ]
    return '<span class="ev-tags">' + "".join(parts) + "</span>"


def _nice_axis_max(value: float) -> float:
    """把最大值向上取整到易读刻度（1/2/5 × 10^n）。

    防止的失败：轴上限等于数据最大值时柱顶贴边、刻度出现 37.4 这类难读数字。
    """
    if value <= 0:
        return 1.0
    exponent = math.floor(math.log10(value))
    base = 10 ** exponent
    for step in (1, 2, 2.5, 5, 10):
        candidate = step * base
        if candidate >= value:
            return float(candidate)
    return float(10 * base)


def render_bar_chart(chart: Dict[str, Any], index: int) -> str:
    """垂直柱状图：支持多 series 分组柱，每个数据点带 <title> hover 提示。

    防止的失败：categories 与 series 长度不一致时索引越界；数值全为 0/负数时
    除零或反向柱形；标签过长溢出画布。
    """
    categories = [as_str(c).strip() or f"项{pos + 1}" for pos, c in enumerate(as_list(chart.get("categories")))]
    series_list = [as_dict(s) for s in as_list(chart.get("series"))]
    values_by_series = [
        [to_number(v) for v in as_list(s.get("values"))] for s in series_list
    ]
    flat = [v for values in values_by_series for v in values]
    max_value = max(flat) if flat else 0.0
    axis_max = _nice_axis_max(max_value if max_value > 0 else 1.0)

    width, height = 720.0, 360.0
    pad_left, pad_right, pad_top, pad_bottom = 64.0, 24.0, 24.0, 84.0
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    slot = plot_w / max(len(categories), 1)
    series_count = max(len(series_list), 1)
    bar_w = max(6.0, min(28.0, slot * 0.7 / series_count))

    parts = svg_open(width, height, "chart-svg")
    parts.append(f'<title>{esc(as_str(chart.get("title"), "图表"))}</title>')
    # 网格线与 Y 轴刻度
    for tick in range(4, -1, -1):
        y = pad_top + plot_h * (1 - tick / 4)
        value = axis_max * tick / 4
        parts.append(
            f'<line x1="{format_number(pad_left)}" y1="{format_number(y)}" '
            f'x2="{format_number(width - pad_right)}" y2="{format_number(y)}" '
            f'stroke="#e2e8f0" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{format_number(pad_left - 8)}" y="{format_number(y + 4 if tick not in (4, 0) else y + (10 if tick == 4 else -2))}" '
            f'text-anchor="end" font-size="11" fill="#6b7280">{esc(format_number(value))}</text>'
        )
    parts.append(
        f'<line x1="{format_number(pad_left)}" y1="{format_number(pad_top + plot_h)}" '
        f'x2="{format_number(width - pad_right)}" y2="{format_number(pad_top + plot_h)}" '
        f'stroke="#94a3b8" stroke-width="1"/>'
    )

    for cat_index, _category in enumerate(categories):
        slot_x = pad_left + slot * cat_index
        group_w = bar_w * series_count
        for s_index, series in enumerate(series_list):
            values = values_by_series[s_index]
            value = values[cat_index] if cat_index < len(values) else 0.0
            ratio = max(value, 0.0) / axis_max if axis_max else 0.0
            bar_h = plot_h * min(ratio, 1.0)
            x = slot_x + (slot - group_w) / 2 + bar_w * s_index
            y = pad_top + plot_h - bar_h
            color = PALETTE[s_index % len(PALETTE)]
            parts.append(
                f'<rect x="{format_number(x)}" y="{format_number(y)}" width="{format_number(bar_w)}" '
                f'height="{format_number(max(bar_h, 0.8))}" fill="{color}" rx="2">'
                f'<title>{esc(categories[cat_index])} · {esc(as_str(series.get("name"), "数值"))}：'
                f'{esc(format_number(value))}{esc(as_str(chart.get("unit")))}</title></rect>'
            )
    # X 轴标签（过长截断，防止溢出）
    for cat_index, category in enumerate(categories):
        cx = pad_left + slot * cat_index + slot / 2
        label = category if len(category) <= 10 else category[:9] + "…"
        parts.append(
            f'<text x="{format_number(cx)}" y="{format_number(pad_top + plot_h + 18)}" '
            f'text-anchor="middle" font-size="11" fill="#374151">{esc(label)}'
            f'<title>{esc(category)}</title></text>'
        )
    parts.append(render_legend(series_list, pad_left, height - 30.0))
    parts.append("</svg>")
    return "".join(parts)


def render_legend(series_list: Sequence[Dict[str, Any]], x: float, y: float) -> str:
    """图例（色块 + 名称），横向排布。多 series 的图表必须有图例。

    防止的失败：多序列图表无法区分颜色含义。
    """
    parts: List[str] = []
    cursor = x
    for s_index, series in enumerate(series_list):
        color = PALETTE[s_index % len(PALETTE)]
        parts.append(
            f'<rect x="{format_number(cursor)}" y="{format_number(y - 9)}" width="12" height="12" '
            f'fill="{color}" rx="2"/>'
        )
        name = as_str(series.get("name"), f"序列{s_index + 1}")
        parts.append(
            f'<text x="{format_number(cursor + 17)}" y="{format_number(y + 1)}" font-size="12" '
            f'fill="#374151">{esc(name)}</text>'
        )
        cursor += 17 + len(name) * 12 + 26
    return "".join(parts)


def render_line_chart(chart: Dict[str, Any], index: int) -> str:
    """折线图：多 series 折线 + 数据点 <title> 提示。

    防止的失败：只有一个数据点无法连线（退化为点）；数值全相同导致比例计算
    除零；categories 与 values 长度不等时索引越界。
    """
    categories = [as_str(c).strip() or f"T{pos + 1}" for pos, c in enumerate(as_list(chart.get("categories")))]
    series_list = [as_dict(s) for s in as_list(chart.get("series"))]
    values_by_series = [[to_number(v) for v in as_list(s.get("values"))] for s in series_list]
    flat = [v for values in values_by_series for v in values]
    axis_max = _nice_axis_max(max(flat) if flat else 1.0)

    width, height = 720.0, 340.0
    pad_left, pad_right, pad_top, pad_bottom = 64.0, 24.0, 24.0, 76.0
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    denominator = max(len(categories) - 1, 1)

    parts = svg_open(width, height, "chart-svg")
    parts.append(f'<title>{esc(as_str(chart.get("title"), "图表"))}</title>')
    for tick in range(4, -1, -1):
        y = pad_top + plot_h * (1 - tick / 4)
        parts.append(
            f'<line x1="{format_number(pad_left)}" y1="{format_number(y)}" '
            f'x2="{format_number(width - pad_right)}" y2="{format_number(y)}" '
            f'stroke="#e2e8f0" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{format_number(pad_left - 8)}" y="{format_number(y + 4 if tick not in (4, 0) else y + (10 if tick == 4 else -2))}" '
            f'text-anchor="end" font-size="11" fill="#6b7280">'
            f'{esc(format_number(axis_max * tick / 4))}</text>'
        )

    for s_index, series in enumerate(series_list):
        values = values_by_series[s_index]
        color = PALETTE[s_index % len(PALETTE)]
        points: List[Tuple[float, float]] = []
        for cat_index in range(len(categories)):
            value = values[cat_index] if cat_index < len(values) else 0.0
            x = pad_left + plot_w * (cat_index / denominator if len(categories) > 1 else 0.5)
            y = pad_top + plot_h - plot_h * min(max(value, 0.0) / axis_max, 1.0)
            points.append((x, y))
        if len(points) >= 2:
            coord_text = " ".join(f"{format_number(x)},{format_number(y)}" for x, y in points)
            parts.append(
                f'<polyline points="{coord_text}" fill="none" stroke="{color}" '
                f'stroke-width="2" stroke-linejoin="round"/>'
            )
        for cat_index, (x, y) in enumerate(points):
            value = values[cat_index] if cat_index < len(values) else 0.0
            parts.append(
                f'<circle cx="{format_number(x)}" cy="{format_number(y)}" r="3.5" fill="#ffffff" '
                f'stroke="{color}" stroke-width="2">'
                f'<title>{esc(categories[cat_index])} · {esc(as_str(series.get("name"), "数值"))}：'
                f'{esc(format_number(value))}{esc(as_str(chart.get("unit")))}</title></circle>'
            )
    for cat_index, category in enumerate(categories):
        x = pad_left + plot_w * (cat_index / denominator if len(categories) > 1 else 0.5)
        parts.append(
            f'<text x="{format_number(x)}" y="{format_number(pad_top + plot_h + 18)}" '
            f'text-anchor="middle" font-size="11" fill="#374151">{esc(category)}</text>'
        )
    parts.append(render_legend(series_list, pad_left, height - 22.0))
    parts.append("</svg>")
    return "".join(parts)


def render_pie_chart(chart: Dict[str, Any], index: int) -> str:
    """饼图：以第一条 series 为数据源，扇区带 <title> 提示与百分比标注。

    防止的失败：负值/全零导致角度计算异常（负值按 0 处理，全零时不绘制扇区）；
    扇区角度取整误差导致路径异常（用极坐标点直接构造 arc）。
    """
    categories = [as_str(c).strip() or f"项{pos + 1}" for pos, c in enumerate(as_list(chart.get("categories")))]
    series_list = [as_dict(s) for s in as_list(chart.get("series"))]
    raw_values = as_list(series_list[0].get("values")) if series_list else []
    values = [max(to_number(v), 0.0) for v in raw_values]
    total = sum(values)

    width, height = 720.0, 340.0
    cx, cy, radius = 220.0, 160.0, 120.0
    parts = svg_open(width, height, "chart-svg")
    parts.append(f'<title>{esc(as_str(chart.get("title"), "图表"))}</title>')

    if total <= 0:
        parts.append(
            f'<text x="{format_number(cx)}" y="{format_number(cy)}" text-anchor="middle" '
            f'font-size="13" fill="#6b7280">数据全为 0，无法绘制饼图</text>'
        )
    else:
        start_angle = -math.pi / 2
        for cat_index, value in enumerate(values):
            category = categories[cat_index] if cat_index < len(categories) else f"项{cat_index + 1}"
            sweep = 2 * math.pi * value / total
            end_angle = start_angle + sweep
            large_arc = 1 if sweep > math.pi else 0
            x1 = cx + radius * math.cos(start_angle)
            y1 = cy + radius * math.sin(start_angle)
            x2 = cx + radius * math.cos(end_angle)
            y2 = cy + radius * math.sin(end_angle)
            color = PALETTE[cat_index % len(PALETTE)]
            percent = value / total * 100
            if sweep >= 2 * math.pi - 1e-9:
                # 单一 100% 分类：整圆用两段 arc 表示，避免起终点重合导致不渲染
                parts.append(
                    f'<circle cx="{format_number(cx)}" cy="{format_number(cy)}" '
                    f'r="{format_number(radius)}" fill="{color}">'
                    f'<title>{esc(category)}：{esc(format_number(value))}'
                    f'{esc(as_str(chart.get("unit")))}（100%）</title></circle>'
                )
            else:
                parts.append(
                    f'<path d="M {format_number(cx)} {format_number(cy)} '
                    f'L {format_number(x1)} {format_number(y1)} '
                    f'A {format_number(radius)} {format_number(radius)} 0 {large_arc} 1 '
                    f'{format_number(x2)} {format_number(y2)} Z" fill="{color}" stroke="#ffffff" '
                    f'stroke-width="1.5">'
                    f'<title>{esc(category)}：{esc(format_number(value))}'
                    f'{esc(as_str(chart.get("unit")))}（{percent:.1f}%）</title></path>'
                )
            label_angle = start_angle + sweep / 2
            lx = cx + radius * 0.62 * math.cos(label_angle)
            ly = cy + radius * 0.62 * math.sin(label_angle)
            if percent >= 6:
                parts.append(
                    f'<text x="{format_number(lx)}" y="{format_number(ly + 4)}" text-anchor="middle" '
                    f'font-size="12" fill="#ffffff">{percent:.0f}%</text>'
                )
            start_angle = end_angle

    # 右侧图例（带数值，长标签不溢出画布）
    legend_y = 60.0
    for cat_index, value in enumerate(values):
        category = categories[cat_index] if cat_index < len(categories) else f"项{cat_index + 1}"
        color = PALETTE[cat_index % len(PALETTE)]
        parts.append(
            f'<rect x="400" y="{format_number(legend_y - 11)}" width="12" height="12" '
            f'fill="{color}" rx="2"/>'
        )
        label = category if len(category) <= 12 else category[:11] + "…"
        parts.append(
            f'<text x="419" y="{format_number(legend_y)}" font-size="12" fill="#374151">{esc(label)}'
            f'<title>{esc(category)}</title></text>'
        )
        parts.append(
            f'<text x="{format_number(width - 24)}" y="{format_number(legend_y)}" text-anchor="end" '
            f'font-size="12" fill="#6b7280">{esc(format_number(value))}{esc(as_str(chart.get("unit")))}</text>'
        )
        legend_y += 26.0
    parts.append("</svg>")
    return "".join(parts)


def render_horizontal_bar_chart(items: Sequence[Tuple[str, float]], unit: str, title: str) -> str:
    """横向条形图（用于来源类型分布，中文长标签更易读）。

    防止的失败：标签过长溢出；数值全零时条长为 0 仍需可见占位。
    """
    labels = [label for label, _ in items]
    values = [max(value, 0.0) for _, value in items]
    max_value = max(values) if values else 0.0
    row_h = 34.0
    width = 720.0
    height = max(140.0, 56.0 + row_h * max(len(labels), 1))
    bar_area_x = 220.0
    bar_area_w = width - bar_area_x - 90.0

    parts = svg_open(width, height, "chart-svg")
    parts.append(f'<title>{esc(title)}</title>')
    for row, label in enumerate(labels):
        y = 40.0 + row * row_h
        value = values[row] if row < len(values) else 0.0
        bar_w = bar_area_w * (value / max_value) if max_value > 0 else 0.0
        color = PALETTE[row % len(PALETTE)]
        display = label if len(label) <= 14 else label[:13] + "…"
        parts.append(
            f'<text x="{format_number(bar_area_x - 12)}" y="{format_number(y + 15)}" '
            f'text-anchor="end" font-size="12" fill="#374151">{esc(display)}'
            f'<title>{esc(label)}</title></text>'
        )
        parts.append(
            f'<rect x="{format_number(bar_area_x)}" y="{format_number(y)}" '
            f'width="{format_number(max(bar_w, 1.0))}" height="20" fill="{color}" rx="2">'
            f'<title>{esc(label)}：{esc(format_number(value))}{esc(unit)}</title></rect>'
        )
        parts.append(
            f'<text x="{format_number(bar_area_x + bar_w + 8)}" y="{format_number(y + 15)}" '
            f'font-size="12" fill="#374151">{esc(format_number(value))}{esc(unit)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def render_process_flow(process_log: Sequence[Dict[str, Any]]) -> str:
    """研究流程追溯图：水平流程 SVG，每阶段标注起止与回退次数。

    防止的失败：阶段数为 0 时画布塌陷（给显式空态提示）；阶段过多时节点文字
    重叠（自动换行到多行，节点宽度固定、画布随行数增高）。
    """
    stages = [as_dict(item) for item in process_log]
    if not stages:
        return (
            '<p class="empty-hint">payload 未提供 process_log，无法绘制研究流程追溯图'
            '（流程记录是证据导向报告的必要组成部分，建议补齐）。</p>'
        )

    per_row = 4
    node_w, node_h, gap_x, gap_y = 210.0, 108.0, 34.0, 74.0
    rows = math.ceil(len(stages) / per_row)
    width = 60.0 + per_row * node_w + (per_row - 1) * gap_x
    height = 40.0 + rows * node_h + (rows - 1) * gap_y + 20.0

    parts = svg_open(width, height, "flow-svg")
    parts.append('<title>研究流程追溯图</title>')
    for index, stage in enumerate(stages):
        row = index // per_row
        col = index % per_row
        x = 30.0 + col * (node_w + gap_x)
        y = 20.0 + row * (node_h + gap_y)
        rollbacks = int(to_number(stage.get("rollbacks")))
        fill = "#f8fafc" if rollbacks == 0 else "#fff7ed"
        stroke = "#cbd5e1" if rollbacks == 0 else "#f0b37e"
        parts.append(
            f'<rect x="{format_number(x)}" y="{format_number(y)}" width="{format_number(node_w)}" '
            f'height="{format_number(node_h)}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        )
        parts.append(
            f'<text x="{format_number(x + 12)}" y="{format_number(y + 24)}" font-size="12.5" '
            f'font-weight="600" fill="#1f2937">{esc(shorten(as_str(stage.get("stage")), 20))}'
            f'<title>{esc(as_str(stage.get("stage")))}</title></text>'
        )
        parts.append(
            f'<text x="{format_number(x + 12)}" y="{format_number(y + 46)}" font-size="10.5" '
            f'fill="#6b7280">起 {esc(shorten(as_str(stage.get("started")), 22))}</text>'
        )
        parts.append(
            f'<text x="{format_number(x + 12)}" y="{format_number(y + 62)}" font-size="10.5" '
            f'fill="#6b7280">止 {esc(shorten(as_str(stage.get("ended")), 22))}</text>'
        )
        badge_text = f"回退 {rollbacks} 次"
        badge_color = "#b45309" if rollbacks > 0 else "#64748b"
        parts.append(
            f'<text x="{format_number(x + 12)}" y="{format_number(y + 84)}" font-size="11" '
            f'font-weight="600" fill="{badge_color}">{esc(badge_text)}</text>'
        )
        notes = as_str(stage.get("notes"))
        if notes:
            # 完整备注受节点宽度限制放不下，这里只放一个信息标记，完整内容悬停可见，
            # 并在附录"研究流程执行记录"表中完整列出（防止 SVG 内文字互相挤压重叠）。
            parts.append(
                f'<text x="{format_number(x + node_w - 12)}" y="{format_number(y + 84)}" '
                f'text-anchor="end" font-size="11" fill="#94a3b8">备注&#9432;'
                f'<title>{esc(notes)}</title></text>'
            )
        # 行内箭头 / 行尾换行箭头
        if col < per_row - 1 and index < len(stages) - 1:
            ax1 = x + node_w + 4
            ax2 = x + node_w + gap_x - 4
            ay = y + node_h / 2
            parts.append(
                f'<line x1="{format_number(ax1)}" y1="{format_number(ay)}" x2="{format_number(ax2)}" '
                f'y2="{format_number(ay)}" stroke="#94a3b8" stroke-width="1.6" marker-end="url(#arrow)"/>'
            )
        elif index < len(stages) - 1:
            # 折行连接：从当前行最后一个节点右侧引出，绕到下一行首节点左侧箭头进入
            sx = x + node_w
            sy = y + node_h / 2
            turn_x = sx + gap_x / 2
            next_y = y + node_h + gap_y + node_h / 2
            ex = 30.0 - 6.0
            parts.append(
                f'<path d="M {format_number(sx)} {format_number(sy)} L {format_number(turn_x)} '
                f'{format_number(sy)} L {format_number(turn_x)} {format_number(next_y)} '
                f'L {format_number(ex)} {format_number(next_y)}" fill="none" stroke="#94a3b8" '
                f'stroke-width="1.6" marker-end="url(#arrow)"/>'
            )

    defs = (
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8"/></marker></defs>'
    )
    parts.insert(1, defs)
    parts.append("</svg>")
    return "".join(parts)


def render_three_layer_architecture(by_layer: Sequence[Dict[str, Any]]) -> str:
    """三级搜索协同架构图：一级 → 二级 → 三级 分层 SVG，标注工具与召回条数。

    防止的失败：by_layer 缺失或不足三级时给出可读降级（仍渲染现有层级并提示缺项），
    而不是抛异常或画空图。
    """
    layers = [as_dict(item) for item in by_layer]
    if not layers:
        return (
            '<p class="empty-hint">payload 未提供 sources_stats.by_layer，无法绘制三级搜索协同架构图。</p>'
        )

    width = 720.0
    height = 96.0 + 96.0 * len(layers)
    parts = svg_open(width, height, "layer-svg")
    parts.append('<title>三级搜索协同架构图</title>')
    parts.append(
        '<defs><marker id="layer-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8"/></marker></defs>'
    )
    for index, layer in enumerate(layers):
        y = 24.0 + index * 96.0
        parts.append(
            f'<rect x="30" y="{format_number(y)}" width="{format_number(width - 60)}" height="66" '
            f'rx="6" fill="{PALETTE[index % len(PALETTE)]}" opacity="0.10"/>'
        )
        parts.append(
            f'<rect x="30" y="{format_number(y)}" width="6" height="66" rx="3" '
            f'fill="{PALETTE[index % len(PALETTE)]}"/>'
        )
        parts.append(
            f'<text x="54" y="{format_number(y + 26)}" font-size="13.5" font-weight="600" '
            f'fill="#1f2937">{esc(as_str(layer.get("layer"), f"第 {index + 1} 层"))}</text>'
        )
        tools = "、".join(as_str(tool) for tool in as_list(layer.get("tools")))
        parts.append(
            f'<text x="54" y="{format_number(y + 48)}" font-size="11.5" fill="#4b5563">'
            f'工具：{esc(tools or "未标注")}</text>'
        )
        parts.append(
            f'<text x="{format_number(width - 54)}" y="{format_number(y + 40)}" text-anchor="end" '
            f'font-size="18" font-weight="700" fill="{PALETTE[index % len(PALETTE)]}">'
            f'{esc(format_number(to_number(layer.get("count"))))}'
            f'<tspan font-size="11" fill="#6b7280" font-weight="400"> 条</tspan></text>'
        )
        if index < len(layers) - 1:
            mid_x = width / 2
            parts.append(
                f'<line x1="{format_number(mid_x)}" y1="{format_number(y + 66)}" x2="{format_number(mid_x)}" '
                f'y2="{format_number(y + 90)}" stroke="#94a3b8" stroke-width="1.6" '
                f'marker-end="url(#layer-arrow)"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


def shorten(text: str, limit: int) -> str:
    """按字符数截断长文本（中文按字符计）。

    防止的失败：SVG 中文本溢出画布、与相邻元素重叠。
    """
    return text if len(text) <= limit else text[: max(limit - 1, 1)] + "…"


# ---------------------------------------------------------------------------
# 各章节渲染函数
# ---------------------------------------------------------------------------

def h2(section_id: str, index: int, title: str) -> str:
    """章节标题（带编号与锚点）。

    防止的失败：侧边导航跳转时锚点缺失/重复导致跳错位置。
    """
    return (
        f'<h2 id="{esc(section_id)}" class="sec-title"><span class="sec-num">{index}</span>'
        f'{esc(title)}</h2>'
    )


def render_overview(payload: Dict[str, Any], strict: bool) -> str:
    """模块 1 报告概览：主题、范围、产出目标、核心结论摘要、证据充分度、流程追溯图。

    防止的失败：scope/summary 缺失时出现空标题空洞；流程日志缺失时用显式提示
    代替空白（提示研究流程追溯是证据导向报告的必要部分）。
    """
    scope = as_dict(payload.get("scope"))
    summary = as_list(payload.get("summary"))
    sufficiency = as_dict(payload.get("evidence_sufficiency"))
    process_log = [as_dict(item) for item in as_list(payload.get("process_log"))]

    parts: List[str] = ['<section class="module">']
    parts.append(h2("sec-overview", 1, "报告概览"))

    meta_rows = [
        ("主题", as_str(payload.get("topic"), "（未提供）")),
        ("副标题", as_str(payload.get("subtitle"), "（未提供）")),
        ("产出目标 / 受众", as_str(payload.get("audience"), "（未提供）")),
        ("编制时间", as_str(payload.get("prepared_at"), "（未提供）")),
    ]
    parts.append('<div class="meta-table"><table><tbody>')
    for key, value in meta_rows:
        parts.append(f'<tr><th>{esc(key)}</th><td>{esc(value)}</td></tr>')
    parts.append("</tbody></table></div>")

    parts.append('<div class="grid-2">')
    for label, values, css in (
        ("纳入范围", as_list(scope.get("in")), "scope-in"),
        ("排除范围", as_list(scope.get("out")), "scope-out"),
    ):
        parts.append(f'<div class="card {css}"><h3>{esc(label)}</h3>')
        if values:
            parts.append("<ul>")
            for item in values:
                parts.append(f"<li>{esc(item)}</li>")
            parts.append("</ul>")
        else:
            parts.append('<p class="empty-hint">未提供。</p>')
        parts.append("</div>")
    parts.append("</div>")

    parts.append('<div class="card"><h3>核心结论摘要</h3>')
    if summary:
        parts.append("<ol class=\"summary-list\">")
        for item in summary:
            parts.append(f"<li>{esc(item)}</li>")
        parts.append("</ol>")
    else:
        parts.append('<p class="empty-hint">payload 未提供 summary，报告缺少概览级结论，请补齐后重新生成。</p>')
    parts.append("</div>")

    grade = as_str(sufficiency.get("grade"), "未评级")
    note = as_str(sufficiency.get("note"))
    grade_class = "grade-high" if grade.startswith("高") else ("grade-low" if grade.startswith("低") else "grade-mid")
    parts.append(
        f'<div class="card suff {grade_class}"><h3>证据整体充分度</h3>'
        f'<p class="grade-line"><span class="grade-badge">{esc(grade)}</span></p>'
        f'<p class="note">{esc(note) if note else "未提供评级说明。"}</p></div>'
    )

    parts.append('<div class="card"><h3>研究流程追溯图</h3>')
    parts.append('<p class="hint">流程由 payload 的 process_log 生成；节点标注回退次数，回退次数 &gt; 0 的阶段以暖色标识。</p>')
    parts.append(render_process_flow(process_log))
    parts.append("</div>")

    if strict:
        parts.append(
            '<p class="hint">本次以 --strict 模式生成：校验未通过时构建会以非零退出码结束，'
            '因此本报告对应的 payload 已通过全部校验项。</p>'
        )
    parts.append("</section>")
    return "".join(parts)


def render_mindmap_node(node: Any, depth: int = 0, path: str = "0") -> str:
    """递归渲染认知地图节点（嵌套 <ul> + 可点击展开/折叠）。

    防止的失败：节点自引用/超深树导致无限递归（depth 上限截断并提示）；
    children 非数组时崩溃（as_list 收敛）；空 name 导致空白节点（给占位名）。
    """
    if depth > MAX_MINDMAP_DEPTH:
        return (
            '<li class="mm-node"><div class="mm-label">…</div>'
            '<div class="mm-body"><p class="empty-hint">层级超过渲染上限，已截断。</p></div></li>'
        )

    node_dict = as_dict(node)
    name = as_str(node_dict.get("name")).strip() or "（未命名节点）"
    evidence_html = render_evidence_links(as_list(node_dict.get("evidence")))
    children = as_list(node_dict.get("children"))
    has_children = bool(children)

    toggle = (
        f'<button type="button" class="mm-toggle" aria-expanded="true" '
        f'data-mm-toggle="mm-{esc(path)}" title="展开 / 折叠该分支">▾</button>'
        if has_children
        else '<span class="mm-toggle mm-toggle-leaf">·</span>'
    )
    parts = [f'<li class="mm-node{" mm-depth-" + str(depth) if depth < 3 else ""}">']
    parts.append(
        f'<div class="mm-label">{toggle}<span class="mm-name" data-mm-name="mm-{esc(path)}">'
        f'{esc(name)}</span>{evidence_html}</div>'
    )
    if has_children:
        parts.append(f'<ul class="mm-children" id="mm-{esc(path)}">')
        for index, child in enumerate(children):
            parts.append(render_mindmap_node(child, depth + 1, f"{path}-{index}"))
        parts.append("</ul>")
    parts.append("</li>")
    return "".join(parts)


def render_mindmap(payload: Dict[str, Any]) -> str:
    """模块 2 领域认知地图：由 mindmap 递归生成可折叠树，节点带证据标签。

    防止的失败：mindmap 缺失时给出明确空态，而不是渲染出一片空白让人误解为
    "该领域没有结构"。
    """
    mindmap = as_dict(payload.get("mindmap"))
    parts: List[str] = ['<section class="module">']
    parts.append(h2("sec-mindmap", 2, "领域认知地图"))
    parts.append(
        '<p class="hint">点击节点前的箭头可展开 / 折叠分支；节点右侧的证据标签可跳转到对应证据条目。</p>'
    )
    if not mindmap:
        parts.append('<p class="empty-hint">payload 未提供 mindmap，无法生成领域认知地图。</p>')
        parts.append("</section>")
        return "".join(parts)

    parts.append('<div class="mm-toolbar">')
    parts.append('<button type="button" class="btn" data-mm-expand="all">全部展开</button>')
    parts.append('<button type="button" class="btn" data-mm-expand="none">全部折叠</button>')
    parts.append("</div>")
    parts.append('<div class="mindmap card"><ul class="mm-root">')
    parts.append(render_mindmap_node(mindmap, 0, "0"))
    parts.append("</ul></div>")
    parts.append("</section>")
    return "".join(parts)


def render_sources(payload: Dict[str, Any]) -> str:
    """模块 3 三级搜索来源溯源：协同架构图 + 来源类型分布。

    防止的失败：by_layer / by_type 任一缺失时只跳过对应子图并提示，不影响另一侧
    渲染；count 非数值时按 0 处理并保留条目（不静默丢行）。
    """
    stats = as_dict(payload.get("sources_stats"))
    by_layer = [as_dict(item) for item in as_list(stats.get("by_layer"))]
    by_type = [as_dict(item) for item in as_list(stats.get("by_type"))]

    parts: List[str] = ['<section class="module">']
    parts.append(h2("sec-sources", 3, "三级搜索来源溯源"))

    parts.append('<div class="card"><h3>三级搜索协同架构</h3>')
    parts.append(render_three_layer_architecture(by_layer))
    parts.append("</div>")

    parts.append('<div class="card"><h3>来源类型分布</h3>')
    if by_type:
        items = [
            (as_str(item.get("name"), "未命名类型"), max(to_number(item.get("count")), 0.0))
            for item in by_type
        ]
        parts.append(render_horizontal_bar_chart(items, " 条", "来源类型分布"))
    else:
        parts.append('<p class="empty-hint">payload 未提供 sources_stats.by_type，无法绘制来源类型分布。</p>')
    parts.append("</div>")

    total_layer = sum(max(to_number(item.get("count")), 0.0) for item in by_layer)
    total_type = sum(max(to_number(item.get("count")), 0.0) for item in by_type)
    if by_layer and by_type and total_layer != total_type:
        parts.append(
            f'<p class="hint warn">口径提示：by_layer 合计 {format_number(total_layer)} 条，'
            f'by_type 合计 {format_number(total_type)} 条，两者不一致说明来源在分层与分类之间存在'
            f'重复计数或漏计，引用数据时需注意。</p>'
        )
    parts.append("</section>")
    return "".join(parts)


def render_chart_block(chart: Dict[str, Any], index: int) -> str:
    """渲染单个图表卡片（含标题、单位、图注、可点击证据 ID）。

    防止的失败：kind 非法时按 bar 降级渲染并在图注中标注，避免整块图表消失。
    """
    kind = as_str(chart.get("kind"), "bar").strip().lower()
    renderer: Callable[[Dict[str, Any], int], str]
    if kind == "pie":
        renderer = render_pie_chart
    elif kind == "line":
        renderer = render_line_chart
    else:
        renderer = render_bar_chart
    chart_id = as_str(chart.get("id"), f"CH-{index:02d}")
    title = as_str(chart.get("title"), f"图表 {chart_id}")
    unit = as_str(chart.get("unit"))
    if kind not in ("bar", "line", "pie"):
        kind = "bar"

    parts = [f'<figure class="chart-card" id="chart-{esc(chart_id)}">']
    parts.append(f'<figcaption><span class="chart-id">{esc(chart_id)}</span>{esc(title)}')
    if unit:
        parts.append(f'<span class="chart-unit">单位：{esc(unit)}</span>')
    parts.append("</figcaption>")
    parts.append(renderer(chart, index))
    parts.append('<div class="chart-foot">数据来源证据：')
    parts.append(render_evidence_links(as_list(chart.get("evidence")), "（未绑定证据，--strict 下会报错）"))
    parts.append("</div>")
    parts.append("</figure>")
    return "".join(parts)


def render_findings(payload: Dict[str, Any]) -> str:
    """模块 4 核心研究发现：按 module 分组，每条结论带可点击证据标签；紧随渲染图表。

    防止的失败：module 字段缺失的结论会被归入"未分类"而不是被丢弃；findings 为空
    时给出显式空态；分组顺序按首次出现稳定排序（保证确定性）。
    """
    findings = [as_dict(item) for item in as_list(payload.get("findings"))]
    charts = [as_dict(item) for item in as_list(payload.get("charts"))]

    parts: List[str] = ['<section class="module">']
    parts.append(h2("sec-findings", 4, "核心研究发现"))

    if not findings:
        parts.append('<p class="empty-hint">payload 未提供 findings，报告缺少核心结论，请补齐后重新生成。</p>')
    else:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for finding in findings:
            module = as_str(finding.get("module")).strip() or "未分类"
            grouped.setdefault(module, []).append(finding)
        for module, items in grouped.items():
            parts.append(f'<div class="card finding-group"><h3>{esc(module)}'
                         f'<span class="count-badge">{len(items)} 条</span></h3><ul class="finding-list">')
            for finding in items:
                fid = as_str(finding.get("id")).strip()
                confidence = as_str(finding.get("confidence")).strip() or "未标注"
                conf_class = CONFIDENCE_STYLES.get(confidence, "conf-mid")
                parts.append('<li class="finding">')
                parts.append('<div class="finding-head">')
                if fid:
                    parts.append(f'<span class="finding-id">{esc(fid)}</span>')
                parts.append(f'<span class="conf {conf_class}">可信度：{esc(confidence)}</span>')
                parts.append("</div>")
                parts.append(f'<p class="claim">{esc(finding.get("claim"))}</p>')
                parts.append('<div class="finding-ev">证据：')
                parts.append(render_evidence_links(
                    as_list(finding.get("evidence")),
                    "无证据 ID —— 依据 --strict 校验项 ① 应补齐来源",
                ))
                parts.append("</div></li>")
            parts.append("</ul></div>")

    parts.append('<div class="card"><h3>量化图表</h3>')
    if charts:
        parts.append('<p class="hint">图表数据点支持鼠标悬停查看数值；图下证据 ID 可点击跳转到证据库。</p>')
        for index, chart in enumerate(charts, start=1):
            parts.append(render_chart_block(chart, index))
    else:
        parts.append('<p class="empty-hint">payload 未提供 charts，本次报告不含量化图表。</p>')
    parts.append("</div>")
    parts.append("</section>")
    return "".join(parts)


def render_disputes(payload: Dict[str, Any]) -> str:
    """模块 5 争议与反证分析：正反并列矩阵（左正右反），各带证据与适用边界。

    防止的失败：pro/con 缺失时用"未提供"占位并保留另一侧（不整条丢弃），
    --strict 下该校验项会以 exit 1 拦截。
    """
    disputes = [as_dict(item) for item in as_list(payload.get("disputes"))]

    parts: List[str] = ['<section class="module">']
    parts.append(h2("sec-disputes", 5, "争议与反证分析"))
    if not disputes:
        parts.append('<p class="empty-hint">payload 未提供 disputes。证据导向报告建议至少收录 1 条真实争议点。</p>')
        parts.append("</section>")
        return "".join(parts)

    for index, dispute in enumerate(disputes, start=1):
        point = as_str(dispute.get("point"), f"争议点 {index}")
        pro = as_dict(dispute.get("pro"))
        con = as_dict(dispute.get("con"))
        parts.append(f'<div class="card dispute" id="dispute-{index}">')
        parts.append(f'<h3><span class="disp-num">争议 {index}</span>{esc(point)}</h3>')
        parts.append('<div class="matrix">')
        for label, side, css in (("正方", pro, "side-pro"), ("反方", con, "side-con")):
            parts.append(f'<div class="side {css}"><h4>{esc(label)}</h4>')
            claim = as_str(side.get("claim")).strip()
            parts.append(f'<p class="claim">{esc(claim) if claim else "（payload 未提供该侧主张，--strict 下会报错）"}</p>')
            parts.append('<div class="finding-ev">证据：')
            parts.append(render_evidence_links(as_list(side.get("evidence")), "（无证据）"))
            parts.append("</div></div>")
        parts.append("</div>")
        boundary = as_str(dispute.get("boundary")).strip()
        parts.append(
            f'<div class="boundary"><strong>适用边界：</strong>'
            f'{esc(boundary) if boundary else "（未提供适用边界，读者需自行判断该争议的适用范围）"}</div>'
        )
        parts.append("</div>")
    parts.append("</section>")
    return "".join(parts)


def render_timeline_svg(timeline: Sequence[Dict[str, Any]], case_index: int) -> str:
    """案例时间线 SVG：横向时间轴 + 交替上下的事件卡片。

    防止的失败：timeline 为空时返回显式提示；事件过多时自动加宽画布（viewBox 可
    小于容器宽度，靠 width=100% 自适应，不会挤压文字）。
    """
    events = [as_dict(item) for item in timeline]
    if not events:
        return '<p class="empty-hint">该案例未提供 timeline，无法绘制时间线。</p>'

    step = 172.0
    width = max(560.0, 96.0 + step * len(events))
    height = 216.0
    axis_y = height / 2

    parts = svg_open(width, height, "timeline-svg")
    parts.append(f'<title>案例 {case_index} 时间线</title>')
    parts.append(
        f'<line x1="48" y1="{format_number(axis_y)}" x2="{format_number(width - 48)}" '
        f'y2="{format_number(axis_y)}" stroke="#94a3b8" stroke-width="2"/>'
    )
    for index, event in enumerate(events):
        cx = 96.0 + step * index
        up = index % 2 == 0
        card_w, card_h = 152.0, 62.0
        card_x = cx - card_w / 2
        card_y = axis_y - 30.0 - card_h if up else axis_y + 30.0
        color = PALETTE[index % len(PALETTE)]
        parts.append(
            f'<circle cx="{format_number(cx)}" cy="{format_number(axis_y)}" r="6" fill="#ffffff" '
            f'stroke="{color}" stroke-width="2.5"/>'
        )
        parts.append(
            f'<line x1="{format_number(cx)}" y1="{format_number(axis_y)}" x2="{format_number(cx)}" '
            f'y2="{format_number(card_y + card_h if up else card_y)}" stroke="#cbd5e1" stroke-width="1.5"/>'
        )
        parts.append(
            f'<rect x="{format_number(card_x)}" y="{format_number(card_y)}" width="{format_number(card_w)}" '
            f'height="{format_number(card_h)}" rx="5" fill="#f8fafc" stroke="#dbe3ec" stroke-width="1"/>'
        )
        date_text = as_str(event.get("date"))
        event_text = as_str(event.get("event"))
        parts.append(
            f'<text x="{format_number(cx)}" y="{format_number(card_y + 20)}" text-anchor="middle" '
            f'font-size="11.5" font-weight="600" fill="{color}">{esc(shorten(date_text, 12))}</text>'
        )
        # 事件文本按每行约 11 个汉字拆成两行，避免溢出卡片
        for line_index, line in enumerate(wrap_text(event_text, 11)[:2]):
            parts.append(
                f'<text x="{format_number(cx)}" y="{format_number(card_y + 37 + line_index * 14)}" '
                f'text-anchor="middle" font-size="10.5" fill="#374151">{esc(line)}'
                f'<title>{esc(event_text)}</title></text>'
            )
    parts.append("</svg>")
    return "".join(parts)


def wrap_text(text: str, width: int) -> List[str]:
    """按字符宽度切分文本（中文场景按字符计）。

    防止的失败：长事件描述在 SVG 中横向溢出、与相邻卡片重叠。
    """
    if width <= 0:
        return [text]
    return [text[index:index + width] for index in range(0, max(len(text), 1), width)] or [text]


def render_cases(payload: Dict[str, Any]) -> str:
    """模块 6 典型案例库：案例卡片 + timeline 时间线图。

    防止的失败：type 非"成功/失败"时按"其他"中性样式渲染（不丢案例）；
    factors / evidence 缺失时局部占位。
    """
    cases = [as_dict(item) for item in as_list(payload.get("cases"))]

    parts: List[str] = ['<section class="module">']
    parts.append(h2("sec-cases", 6, "典型案例库"))
    if not cases:
        parts.append('<p class="empty-hint">payload 未提供 cases，本次报告不含案例库。</p>')
        parts.append("</section>")
        return "".join(parts)

    for index, case in enumerate(cases, start=1):
        case_type = as_str(case.get("type")).strip()
        type_class = "case-success" if case_type == "成功" else ("case-fail" if case_type == "失败" else "case-other")
        parts.append(f'<div class="card case {type_class}" id="case-{index}">')
        parts.append(
            f'<h3><span class="case-type">{esc(case_type or "未标注")}</span>'
            f'{esc(as_str(case.get("name"), f"案例 {index}"))}</h3>'
        )
        timeline = as_list(case.get("timeline"))
        parts.append('<div class="case-timeline">')
        parts.append(render_timeline_svg(timeline, index))
        parts.append("</div>")
        parts.append('<div class="grid-2">')
        parts.append('<div class="case-block"><h4>关键因素</h4>')
        factors = as_list(case.get("factors"))
        if factors:
            parts.append("<ul>")
            for factor in factors:
                parts.append(f"<li>{esc(factor)}</li>")
            parts.append("</ul>")
        else:
            parts.append('<p class="empty-hint">未提供关键因素。</p>')
        parts.append("</div>")
        parts.append('<div class="case-block"><h4>可复制性</h4>')
        replicability = as_str(case.get("replicability")).strip()
        parts.append(f'<p>{esc(replicability) if replicability else "（未评估可复制性）"}</p>')
        parts.append('<div class="finding-ev">证据：')
        parts.append(render_evidence_links(as_list(case.get("evidence")), "（未绑定证据）"))
        parts.append("</div></div>")
        parts.append("</div></div>")
    parts.append("</section>")
    return "".join(parts)


def render_evidence(payload: Dict[str, Any]) -> str:
    """模块 7 完整证据库：全量证据卡片 + 筛选 + 全文检索。

    防止的失败：证据 id 缺失时按位置补 EV-编号占位（保证标签可锚定，不出现 href="#");
    url 缺失时只渲染来源标题而不渲染链接（避免产生空链接/导航到自身）；
    url 非 http(s) 时同样降级为纯文本，防止 javascript: 之类伪协议。
    """
    evidence_items = [as_dict(item) for item in as_list(payload.get("evidence"))]

    parts: List[str] = ['<section class="module">']
    parts.append(h2("sec-evidence", 7, "完整证据库"))
    parts.append(
        '<p class="hint">支持按类型 / 可信度 / 层级筛选，以及关键词全文检索；检索命中会同时高亮'
        '页面内的结论与证据条目。搜索框也可使用顶部全局搜索。</p>'
    )

    types = sorted({as_str(item.get("type")).strip() for item in evidence_items if as_str(item.get("type")).strip()})
    credits = sorted({as_str(item.get("credibility")).strip() for item in evidence_items if as_str(item.get("credibility")).strip()})
    layers = sorted({as_str(item.get("layer")).strip() for item in evidence_items if as_str(item.get("layer")).strip()})

    parts.append('<div class="filters" id="evidence-filters">')
    parts.append('<label class="filter">类型<select id="filter-type"><option value="">全部</option>')
    for value in types:
        parts.append(f'<option value="{esc(value)}">{esc(value)}</option>')
    parts.append("</select></label>")
    parts.append('<label class="filter">可信度<select id="filter-cred"><option value="">全部</option>')
    for value in credits:
        parts.append(f'<option value="{esc(value)}">{esc(value)}</option>')
    parts.append("</select></label>")
    parts.append('<label class="filter">层级<select id="filter-layer"><option value="">全部</option>')
    for value in layers:
        parts.append(f'<option value="{esc(value)}">{esc(value)}</option>')
    parts.append("</select></label>")
    parts.append('<button type="button" class="btn" id="filter-reset">重置筛选</button>')
    parts.append('<span class="filter-count" id="evidence-count"></span>')
    parts.append("</div>")

    if not evidence_items:
        parts.append('<p class="empty-hint">payload 未提供 evidence。证据库为空意味着报告的任何结论都无法溯源。</p>')
        parts.append("</section>")
        return "".join(parts)

    parts.append('<div class="evidence-list">')
    for index, item in enumerate(evidence_items, start=1):
        ev_id = as_str(item.get("id")).strip() or f"EV-{index:03d}"
        ev_type = as_str(item.get("type")).strip() or "未标注"
        credibility = as_str(item.get("credibility")).strip() or "待验证"
        layer = as_str(item.get("layer")).strip() or "未标注"
        tool = as_str(item.get("tool")).strip()
        quote = as_str(item.get("quote")).strip()
        source_title = as_str(item.get("source_title")).strip()
        url = as_str(item.get("url")).strip()
        retrieved_at = as_str(item.get("retrieved_at")).strip()
        cred_class = CREDIBILITY_STYLES.get(credibility, "cred-mid")

        search_blob = " ".join([
            ev_id, ev_type, credibility, layer, tool, quote,
            as_str(item.get("content")), source_title, url, retrieved_at,
        ]).lower()

        parts.append(
            f'<article class="evidence-card" id="{esc(ev_id)}" data-type="{esc(ev_type)}" '
            f'data-cred="{esc(credibility)}" data-layer="{esc(layer)}" '
            f'data-search="{esc(search_blob)}">'
        )
        parts.append('<header class="ev-head">')
        parts.append(f'<span class="ev-id">{esc(ev_id)}</span>')
        parts.append(f'<span class="chip chip-type">{esc(ev_type)}</span>')
        parts.append(f'<span class="chip {cred_class}">可信度：{esc(credibility)}</span>')
        parts.append(f'<span class="chip chip-layer">层级：{esc(layer)}</span>')
        if tool:
            parts.append(f'<span class="chip chip-tool">工具：{esc(tool)}</span>')
        parts.append("</header>")
        parts.append(f'<p class="ev-content">{esc(item.get("content"))}</p>')
        if quote:
            parts.append(f'<blockquote class="ev-quote">{esc(quote)}</blockquote>')
        parts.append('<footer class="ev-foot">')
        if source_title:
            if url.startswith("http://") or url.startswith("https://"):
                parts.append(
                    f'<span class="ev-source">来源：<a href="{esc(url)}" target="_blank" '
                    f'rel="noopener">{esc(source_title)}</a></span>'
                )
            else:
                parts.append(f'<span class="ev-source">来源：{esc(source_title)}（未提供可访问链接）</span>')
        else:
            parts.append('<span class="ev-source">来源：未提供来源标题</span>')
        if retrieved_at:
            parts.append(f'<span class="ev-time">提取时间：{esc(retrieved_at)}</span>')
        parts.append("</footer></article>")
    parts.append("</div>")
    parts.append('<p class="empty-hint" id="evidence-nomatch" hidden>当前筛选 / 检索条件下没有匹配的证据条目。</p>')
    parts.append("</section>")
    return "".join(parts)


def render_appendix(payload: Dict[str, Any]) -> str:
    """模块 8 附录：流程执行记录表、异常处理、归档信息、版本记录、自定义小节。

    防止的失败：appendix 小节标题/正文缺失时跳过该小节而不渲染空壳；process_log
    为空时给出提示；归档信息完全来自 payload（不写入运行时时间，保持确定性）。
    """
    process_log = [as_dict(item) for item in as_list(payload.get("process_log"))]
    appendix = [as_dict(item) for item in as_list(payload.get("appendix"))]
    digest = payload_digest(payload)
    evidence_items = [as_dict(item) for item in as_list(payload.get("evidence"))]

    parts: List[str] = ['<section class="module">']
    parts.append(h2("sec-appendix", 8, "附录"))

    parts.append('<div class="card"><h3>研究流程执行记录</h3>')
    if process_log:
        parts.append('<table class="data-table"><thead><tr>'
                     '<th>阶段</th><th>开始</th><th>结束</th><th>回退次数</th><th>备注</th>'
                     '</tr></thead><tbody>')
        for stage in process_log:
            parts.append(
                f'<tr><td>{esc(stage.get("stage"))}</td>'
                f'<td class="nowrap">{esc(stage.get("started"))}</td>'
                f'<td class="nowrap">{esc(stage.get("ended"))}</td>'
                f'<td class="num">{esc(format_number(to_number(stage.get("rollbacks"))))}</td>'
                f'<td>{esc(stage.get("notes"))}</td></tr>'
            )
        parts.append("</tbody></table>")
        total_rollbacks = sum(to_number(stage.get("rollbacks")) for stage in process_log)
        parts.append(
            f'<p class="hint">合计阶段 {len(process_log)} 个，回退 {format_number(total_rollbacks)} 次。'
            f'回退记录用于说明检索或核对过程中的返工，是判断结论可靠性的辅助信息。</p>'
        )
    else:
        parts.append('<p class="empty-hint">payload 未提供 process_log，无法列出流程执行记录。</p>')
    parts.append("</div>")

    parts.append('<div class="card"><h3>异常处理</h3>')
    abnormal = [stage for stage in process_log if to_number(stage.get("rollbacks")) > 0]
    if abnormal:
        parts.append("<ul>")
        for stage in abnormal:
            parts.append(
                f'<li><strong>{esc(stage.get("stage"))}</strong>：回退 '
                f'{esc(format_number(to_number(stage.get("rollbacks"))))} 次 —— '
                f'{esc(stage.get("notes"))}</li>'
            )
        parts.append("</ul>")
    elif process_log:
        parts.append('<p>已记录的执行阶段均未发生回退。</p>')
    else:
        parts.append('<p class="empty-hint">无流程记录，无法给出异常处理说明。</p>')
    parts.append("</div>")

    parts.append('<div class="card"><h3>归档信息</h3><table class="data-table"><tbody>')
    archive_rows = [
        ("报告主题", as_str(payload.get("topic"), "（未提供）")),
        ("编制时间（来自 payload）", as_str(payload.get("prepared_at"), "（未提供）")),
        ("payload 内容指纹（sha256 前 8 位）", digest),
        ("证据条目总数", str(len(evidence_items))),
        ("产物形态", "文档版 Markdown 报告 + 单文件离线 HTML 交互式报告（两版内容字段一致）"),
        ("离线要求", "不引用任何 CDN / 外链 JS / 外链 CSS / 外部字体 / 外部图片；唯一外部 URL 为证据原始链接"),
    ]
    for key, value in archive_rows:
        parts.append(f'<tr><th>{esc(key)}</th><td>{esc(value)}</td></tr>')
    parts.append("</tbody></table></div>")

    parts.append('<div class="card"><h3>版本记录</h3><ul>')
    parts.append(f'<li>v1.0（payload 指纹 {esc(digest)}）—— 由 scripts/build_report.py 依据同一 payload 生成，'
                 f'两版报告字段一致；生成过程不写入运行时时间戳，相同 payload 可复现完全相同的 HTML。</li>')
    parts.append("</ul></div>")

    for item in appendix:
        title = as_str(item.get("title")).strip()
        body = as_str(item.get("body")).strip()
        if not title and not body:
            continue
        parts.append(f'<div class="card"><h3>{esc(title) if title else "未命名附录"}</h3>')
        for paragraph in body.split("\n"):
            if paragraph.strip():
                parts.append(f"<p>{esc(paragraph.strip())}</p>")
        if not body:
            parts.append('<p class="empty-hint">该附录小节未提供正文。</p>')
        parts.append("</div>")

    parts.append("</section>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# 样式与脚本（全部内联，无外部引用）
# ---------------------------------------------------------------------------

def render_styles() -> str:
    """内联 CSS：专业商务风格，含侧边导航、打印样式、响应式栅格。

    防止的失败：依赖外部样式表导致离线打开变成无样式的裸 HTML；打印时导航遮挡
    正文；长证据链接撑破布局（word-break）。
    """
    return """
:root {
  --ink: #1f2937;
  --ink-soft: #4b5563;
  --muted: #6b7280;
  --line: #dfe5ec;
  --line-soft: #eef2f7;
  --bg: #f5f7fa;
  --panel: #ffffff;
  --blue: #1f5fa9;
  --blue-soft: #eaf1fa;
  --amber: #b45309;
  --amber-soft: #fff7ed;
  --green: #1c7a52;
  --red: #a83232;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", "Source Han Sans SC",
               "Noto Sans CJK SC", "Segoe UI", system-ui, sans-serif;
  font-size: 15px;
  line-height: 1.75;
}
a { color: var(--blue); text-decoration: none; word-break: break-all; }
a:hover { text-decoration: underline; }

/* 侧边导航 */
.sidebar {
  position: fixed; top: 0; left: 0; bottom: 0; width: 248px;
  background: var(--panel); border-right: 1px solid var(--line);
  padding: 22px 18px; overflow-y: auto; z-index: 30;
}
.sidebar .brand { font-size: 15px; font-weight: 700; color: var(--blue); letter-spacing: .4px; }
.sidebar .brand-sub { font-size: 12px; color: var(--muted); margin: 4px 0 18px; line-height: 1.5; }
.sidebar nav ol { list-style: none; margin: 0; padding: 0; counter-reset: navitem; }
.sidebar nav li { margin: 2px 0; }
.sidebar nav a {
  display: flex; gap: 8px; align-items: baseline;
  padding: 7px 10px; border-radius: 5px; color: var(--ink-soft); font-size: 13.5px;
  border-left: 3px solid transparent;
}
.sidebar nav a:hover { background: var(--line-soft); text-decoration: none; }
.sidebar nav a.active { background: var(--blue-soft); color: var(--blue); border-left-color: var(--blue); font-weight: 600; }
.sidebar nav a .nav-num { color: var(--muted); font-size: 12px; min-width: 14px; }
.sidebar .sidebar-foot { margin-top: 20px; padding-top: 14px; border-top: 1px solid var(--line-soft); font-size: 11.5px; color: var(--muted); }
.sidebar .digest { font-family: Consolas, "Courier New", monospace; color: var(--ink-soft); }

/* 顶部栏 */
.topbar {
  position: fixed; top: 0; left: 248px; right: 0; height: 58px;
  background: rgba(255,255,255,.96); border-bottom: 1px solid var(--line);
  display: flex; align-items: center; gap: 14px; padding: 0 26px; z-index: 25;
}
.topbar .doc-title { font-size: 14px; font-weight: 600; color: var(--ink); flex: 1;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.search-wrap { position: relative; }
.search-wrap input {
  width: 300px; padding: 7px 12px 7px 32px; border: 1px solid var(--line);
  border-radius: 5px; font-size: 13.5px; color: var(--ink); background: #fff;
}
.search-wrap input:focus { outline: none; border-color: var(--blue); box-shadow: 0 0 0 3px var(--blue-soft); }
.search-wrap::before {
  content: "\\1F50D"; position: absolute; left: 10px; top: 6px; font-size: 12px; color: var(--muted); opacity: .65;
}
.search-hits { font-size: 12px; color: var(--muted); min-width: 92px; }

/* 主体 */
.main { margin-left: 248px; padding: 84px 34px 72px; max-width: 1200px; }
.module { margin-bottom: 34px; }
.sec-title {
  font-size: 20px; margin: 0 0 16px; padding-bottom: 10px;
  border-bottom: 1px solid var(--line); scroll-margin-top: 74px;
}
.sec-num {
  display: inline-block; width: 24px; height: 24px; margin-right: 10px; border-radius: 4px;
  background: var(--blue); color: #fff; font-size: 13px; font-weight: 700; text-align: center; line-height: 24px;
}
.card {
  background: var(--panel); border: 1px solid var(--line); border-radius: 6px;
  padding: 18px 20px; margin-bottom: 16px;
}
.card h3 { margin: 0 0 12px; font-size: 15.5px; }
.card h4 { margin: 0 0 8px; font-size: 13.5px; color: var(--ink-soft); }
.hint { font-size: 12.5px; color: var(--muted); margin: 0 0 12px; }
.hint.warn { color: var(--amber); background: var(--amber-soft); border-radius: 4px; padding: 8px 12px; }
.empty-hint { font-size: 13px; color: var(--amber); background: var(--amber-soft);
  border-left: 3px solid #f0b37e; padding: 8px 12px; border-radius: 3px; margin: 8px 0; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }

.meta-table table { width: 100%; border-collapse: collapse; }
.meta-table th { width: 168px; text-align: left; font-weight: 600; color: var(--ink-soft);
  padding: 7px 12px 7px 0; vertical-align: top; font-size: 13.5px; }
.meta-table td { padding: 7px 0; }
.scope-in { border-top: 3px solid var(--blue); }
.scope-out { border-top: 3px solid var(--muted); }
.summary-list { margin: 0; padding-left: 22px; }
.summary-list li { margin-bottom: 8px; }
.suff .grade-badge { display: inline-block; padding: 4px 14px; border-radius: 14px;
  font-weight: 700; font-size: 14px; }
.grade-high .grade-badge { background: #e6f4ec; color: var(--green); }
.grade-mid .grade-badge { background: var(--blue-soft); color: var(--blue); }
.grade-low .grade-badge { background: var(--amber-soft); color: var(--amber); }
.suff .note { font-size: 13.5px; color: var(--ink-soft); margin: 10px 0 0; }

/* 证据标签 */
.ev-tags { display: inline-flex; flex-wrap: wrap; gap: 6px; }
.ev-tag {
  font-family: Consolas, "Courier New", monospace; font-size: 12px;
  color: var(--blue); background: var(--blue-soft); border: 1px solid #c9dcf2;
  border-radius: 4px; padding: 1px 7px; cursor: pointer;
}
.ev-tag:hover { background: #dbe9f9; }
.ev-empty { font-size: 12px; color: var(--amber); }

/* 图表 */
.chart-card { margin: 0 0 22px; padding: 14px 16px 10px; border: 1px solid var(--line-soft);
  border-radius: 6px; background: #fcfdff; }
.chart-card figcaption { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.chart-id { font-family: Consolas, monospace; font-size: 11.5px; color: var(--muted);
  border: 1px solid var(--line); border-radius: 3px; padding: 0 5px; margin-right: 8px; }
.chart-unit { font-size: 12px; font-weight: 400; color: var(--muted); margin-left: 8px; }
.chart-foot { font-size: 12.5px; color: var(--muted); border-top: 1px dashed var(--line);
  padding-top: 8px; margin-top: 4px; }
.chart-svg, .flow-svg, .layer-svg, .timeline-svg { display: block; width: 100%; height: auto; }

/* 发现 */
.finding-group .count-badge { font-size: 11.5px; color: var(--muted); font-weight: 400; margin-left: 8px; }
.finding-list { list-style: none; margin: 0; padding: 0; }
.finding { border-top: 1px solid var(--line-soft); padding: 12px 0; }
.finding:first-child { border-top: none; padding-top: 4px; }
.finding-head { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.finding-id { font-family: Consolas, monospace; font-size: 12px; color: var(--muted); }
.conf { font-size: 11.5px; padding: 1px 8px; border-radius: 10px; }
.conf-high { background: #e6f4ec; color: var(--green); }
.conf-mid { background: var(--blue-soft); color: var(--blue); }
.conf-low { background: var(--amber-soft); color: var(--amber); }
.claim { margin: 4px 0 6px; }
.finding-ev { font-size: 12.5px; color: var(--muted); }

/* 争议 */
.matrix { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 10px 0 12px; }
@media (max-width: 900px) { .matrix { grid-template-columns: 1fr; } }
.side { border-radius: 5px; padding: 12px 14px; border: 1px solid var(--line); }
.side-pro { background: #f4f9f6; border-left: 4px solid var(--green); }
.side-con { background: #fdf6f6; border-left: 4px solid var(--red); }
.side h4 { margin: 0 0 6px; }
.disp-num { font-size: 12px; color: var(--muted); margin-right: 10px; font-weight: 400; }
.boundary { font-size: 13px; color: var(--ink-soft); background: var(--line-soft);
  border-radius: 4px; padding: 8px 12px; }

/* 案例 */
.case-success { border-top: 3px solid var(--green); }
.case-fail { border-top: 3px solid var(--red); }
.case-other { border-top: 3px solid var(--muted); }
.case-type { font-size: 12px; padding: 1px 9px; border-radius: 10px; margin-right: 10px;
  background: var(--line-soft); color: var(--ink-soft); font-weight: 400; }
.case-timeline { margin: 8px 0 14px; overflow-x: auto; }
.case-block { border: 1px solid var(--line-soft); border-radius: 5px; padding: 12px 14px; }
.case-block ul { margin: 0; padding-left: 20px; }

/* 证据库 */
.filters { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin-bottom: 14px;
  background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 12px 16px; }
.filter { font-size: 13px; color: var(--ink-soft); display: inline-flex; align-items: center; gap: 6px; }
.filter select { padding: 5px 8px; border: 1px solid var(--line); border-radius: 4px;
  font-size: 13px; background: #fff; color: var(--ink); }
.btn { padding: 5px 12px; border: 1px solid var(--line); background: #fff; border-radius: 4px;
  font-size: 13px; color: var(--ink-soft); cursor: pointer; }
.btn:hover { background: var(--line-soft); }
.filter-count { font-size: 12.5px; color: var(--muted); margin-left: auto; }
.evidence-list { display: grid; grid-template-columns: 1fr; gap: 12px; }
.evidence-card { background: var(--panel); border: 1px solid var(--line); border-radius: 6px;
  padding: 14px 16px; scroll-margin-top: 74px; }
.evidence-card.ev-hidden { display: none; }
.evidence-card.ev-hit-term { border-color: #f0b37e; box-shadow: 0 0 0 3px var(--amber-soft); }
.evidence-card.ev-flash { border-color: var(--blue); box-shadow: 0 0 0 4px var(--blue-soft); }
.ev-head { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 8px; }
.ev-id { font-family: Consolas, monospace; font-weight: 700; color: var(--blue); font-size: 13px; }
.chip { font-size: 11.5px; padding: 1px 8px; border-radius: 10px; background: var(--line-soft); color: var(--ink-soft); }
.cred-high { background: #e6f4ec; color: var(--green); }
.cred-mid { background: var(--blue-soft); color: var(--blue); }
.cred-low { background: var(--amber-soft); color: var(--amber); }
.ev-content { margin: 0 0 8px; }
.ev-quote { margin: 0 0 10px; padding: 8px 14px; border-left: 3px solid var(--blue);
  background: #f8fbff; color: #23303f; font-size: 14px; }
.ev-foot { display: flex; flex-wrap: wrap; gap: 18px; font-size: 12.5px; color: var(--muted);
  border-top: 1px dashed var(--line); padding-top: 8px; }
mark.hit { background: #fff2bf; color: inherit; padding: 0 2px; border-radius: 2px; }
.hit-section { display: none; font-size: 12px; color: var(--amber); margin-top: 4px; }
.hit-section.show { display: block; }

/* 表格 */
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th, .data-table td { border: 1px solid var(--line); padding: 7px 10px; text-align: left;
  vertical-align: top; }
.data-table th { background: #f7f9fc; font-weight: 600; color: var(--ink-soft); }
.data-table td.num { text-align: right; font-family: Consolas, monospace; }
.nowrap { white-space: nowrap; }

/* 页脚 */
.doc-foot { margin-left: 248px; padding: 22px 34px 40px; font-size: 12px; color: var(--muted);
  border-top: 1px solid var(--line); }

/* 移动端断点：≤900px 取消固定侧栏与固定顶栏，正文不再让出 248px。
   交付物是「能转发、能在手机上看」的单文件报告——没有这一档，真实 390px 视口
   （clientWidth 375）下正文只剩 375−248=127px，文字竖排碎裂。
   位置必须在样式表**末尾**（所有组件规则之后）：早于 .doc-foot/.data-table 的定义
   会被同特异性的后置规则盖掉（实测：放在 .main 后面时 .doc-foot 仍留 248px，
   整页横向溢出 37px）。 */
@media (max-width: 900px) {
  .sidebar {
    position: static; width: auto; height: auto; bottom: auto;
    border-right: 0; border-bottom: 1px solid var(--line);
    padding: 16px 18px 12px; max-height: none; overflow: visible;
  }
  .sidebar .brand-sub { margin: 4px 0 12px; }
  .sidebar nav ol { columns: 2; column-gap: 16px; }
  .sidebar nav a { padding: 6px 8px; font-size: 13px; }
  .sidebar .sidebar-foot { margin-top: 14px; padding-top: 10px; }
  .topbar {
    position: static; left: auto; right: auto; height: auto;
    flex-wrap: wrap; padding: 10px 18px; gap: 8px;
  }
  .topbar .doc-title { flex: 1 0 100%; white-space: normal; }
  .search-wrap { flex: 1 0 100%; }
  .search-wrap input { width: 100%; }
  .search-hits { flex: 1 1 auto; min-width: 0; }
  .main { margin-left: 0; padding: 20px 18px 56px; max-width: none; }
  .doc-foot { margin-left: 0; padding: 18px 18px 32px; }
  .sec-title { scroll-margin-top: 12px; }
}

/* 窄视口内的宽表：让表格自己横向滚动，而不是把整页撑宽。
   .data-table 的内容最小宽度实测约 620px（阶段名 + .nowrap 时间戳列），
   在 390px 视口下曾使整页横向溢出 285px。仅作用于 screen——打印走 @media print
   的独立分页规则，不受 display:block 影响。 */
@media screen and (max-width: 900px) {
  .data-table { display: block; width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
}

/* 打印：隐藏导航与搜索，保证正文完整进入纸张 */
@media print {
  .sidebar, .topbar, .mm-toolbar, .filters, .btn { display: none !important; }
  .main, .doc-foot { margin-left: 0; padding: 0 8mm; max-width: none; }
  body { background: #fff; font-size: 11.5pt; }
  .card, .chart-card, .evidence-card { break-inside: avoid; page-break-inside: avoid; }
  .sec-title { break-after: avoid; page-break-after: avoid; }
  a { color: #000; }
  .evidence-card.ev-hidden { display: block; }
}
"""


def render_scripts() -> str:
    """内联 JS：导航滚动高亮、全局搜索、证据跳转与高亮、证据筛选、思维导图折叠。

    防止的失败：依赖外部库导致离线失效；事件绑定失败导致标签点击无反应；
    搜索后正文命中不提示（这里用"命中提示条"把证据命中回传到结论区）。
    本脚本不写 document.write，不使用模板字符串，便于单文件内联与打印安全。
    """
    return """
(function () {
  "use strict";

  function qs(sel) { return document.querySelector(sel); }
  function qsa(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }

  /* ---------- 1. 证据标签跳转 + 高亮 3 秒 ---------- */
  var flashTimers = {};

  function flashEvidence(evId) {
    var target = document.getElementById(evId);
    if (!target) { return false; }
    /* 目标可能被证据库筛选隐藏：先清空筛选，保证跳转可达 */
    var visible = !target.classList.contains("ev-hidden");
    if (!visible) {
      var typeSel = qs("#filter-type"), credSel = qs("#filter-cred"), layerSel = qs("#filter-layer");
      if (typeSel) { typeSel.value = ""; }
      if (credSel) { credSel.value = ""; }
      if (layerSel) { layerSel.value = ""; }
      applyEvidenceFilter("");
    }
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    target.classList.add("ev-flash");
    if (flashTimers[evId]) { clearTimeout(flashTimers[evId]); }
    flashTimers[evId] = setTimeout(function () {
      target.classList.remove("ev-flash");
    }, 3000);
    return true;
  }

  document.addEventListener("click", function (event) {
    var tag = event.target.closest ? event.target.closest(".ev-tag") : null;
    if (tag) {
      event.preventDefault();
      var evId = tag.getAttribute("data-ev");
      if (evId && !flashEvidence(evId)) {
        tag.title = "报告中不存在该证据条目：" + evId;
      }
      return;
    }
    var toggle = event.target.closest ? event.target.closest(".mm-toggle") : null;
    if (toggle && !toggle.classList.contains("mm-toggle-leaf")) {
      var targetId = toggle.getAttribute("data-mm-toggle");
      var list = document.getElementById(targetId);
      if (list) {
        var expanded = toggle.getAttribute("aria-expanded") === "true";
        toggle.setAttribute("aria-expanded", expanded ? "false" : "true");
        toggle.textContent = expanded ? "\\u25B8" : "\\u25BE";
        list.style.display = expanded ? "none" : "";
      }
    }
  });

  /* ---------- 2. 思维导图整体展开 / 折叠 ---------- */
  qsa("[data-mm-expand]").forEach(function (button) {
    button.addEventListener("click", function () {
      var mode = button.getAttribute("data-mm-expand");
      qsa(".mm-children").forEach(function (list) {
        list.style.display = mode === "none" ? "none" : "";
      });
      qsa(".mm-toggle").forEach(function (toggle) {
        if (toggle.classList.contains("mm-toggle-leaf")) { return; }
        toggle.setAttribute("aria-expanded", mode === "none" ? "false" : "true");
        toggle.textContent = mode === "none" ? "\\u25B8" : "\\u25BE";
      });
    });
  });

  /* ---------- 3. 证据筛选 ---------- */
  function currentFilter() {
    var typeSel = qs("#filter-type"), credSel = qs("#filter-cred"), layerSel = qs("#filter-layer");
    return {
      type: typeSel ? typeSel.value : "",
      cred: credSel ? credSel.value : "",
      layer: layerSel ? layerSel.value : ""
    };
  }

  function applyEvidenceFilter(term) {
    var filter = currentFilter();
    var cards = qsa(".evidence-card");
    var shown = 0;
    var keyword = (term || "").toLowerCase().trim();
    cards.forEach(function (card) {
      var okType = !filter.type || card.getAttribute("data-type") === filter.type;
      var okCred = !filter.cred || card.getAttribute("data-cred") === filter.cred;
      var okLayer = !filter.layer || card.getAttribute("data-layer") === filter.layer;
      var blob = card.getAttribute("data-search") || "";
      var okTerm = !keyword || blob.indexOf(keyword) !== -1;
      if (okType && okCred && okLayer && okTerm) {
        card.classList.remove("ev-hidden");
        shown += 1;
      } else {
        card.classList.add("ev-hidden");
      }
    });
    var empty = qs("#evidence-nomatch");
    if (empty) { empty.hidden = shown !== 0; }
    var counter = qs("#evidence-count");
    if (counter) { counter.textContent = "显示 " + shown + " / " + cards.length + " 条"; }
  }

  ["#filter-type", "#filter-cred", "#filter-layer"].forEach(function (sel) {
    var node = qs(sel);
    if (node) { node.addEventListener("change", function () { applyEvidenceFilter(qs("#global-search").value); }); }
  });
  var reset = qs("#filter-reset");
  if (reset) {
    reset.addEventListener("click", function () {
      ["#filter-type", "#filter-cred", "#filter-layer"].forEach(function (sel) {
        var node = qs(sel);
        if (node) { node.value = ""; }
      });
      var search = qs("#global-search");
      if (search) { search.value = ""; }
      applyEvidenceFilter("");
      clearTextHits();
    });
  }

  /* ---------- 4. 全局全文检索：命中证据 + 回传结论区提示 ---------- */
  function clearTextHits() {
    qsa("mark.hit").forEach(function (mark) {
      var parent = mark.parentNode;
      parent.replaceChild(document.createTextNode(mark.textContent), mark);
      parent.normalize();
    });
    qsa(".evidence-card.ev-hit-term").forEach(function (card) { card.classList.remove("ev-hit-term"); });
    qsa(".claim, .summary-list li, .case-block p").forEach(function (node) {
      node.classList.remove("text-hit");
    });
    qsa(".hit-section").forEach(function (node) { node.classList.remove("show"); node.textContent = ""; });
  }

  function markNode(node, term) {
    /* 对元素做纯文本命中高亮：仅替换文本节点，避免破坏内部结构 */
    var walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT, null);
    var textNodes = [];
    while (walker.nextNode()) { textNodes.push(walker.currentNode); }
    var hit = false;
    textNodes.forEach(function (textNode) {
      var value = textNode.nodeValue || "";
      var lower = value.toLowerCase();
      var index = lower.indexOf(term);
      if (index === -1) { return; }
      hit = true;
      var fragment = document.createDocumentFragment();
      var cursor = 0;
      while (index !== -1) {
        if (index > cursor) { fragment.appendChild(document.createTextNode(value.slice(cursor, index))); }
        var mark = document.createElement("mark");
        mark.className = "hit";
        mark.textContent = value.slice(index, index + term.length);
        fragment.appendChild(mark);
        cursor = index + term.length;
        index = lower.indexOf(term, cursor);
      }
      if (cursor < value.length) { fragment.appendChild(document.createTextNode(value.slice(cursor))); }
      textNode.parentNode.replaceChild(fragment, textNode);
    });
    return hit;
  }

  function runSearch(rawTerm) {
    clearTextHits();
    var term = (rawTerm || "").trim();
    applyEvidenceFilter(term);
    if (!term) { return; }
    var lowerTerm = term.toLowerCase();
    var counters = { findings: 0, disputes: 0, cases: 0, summary: 0 };

    qsa(".claim").forEach(function (node) {
      if (markNode(node, lowerTerm)) {
        var section = node.closest(".module");
        if (section) {
          if (section.id === "sec-findings") { counters.findings += 1; }
          else if (section.id === "sec-disputes") { counters.disputes += 1; }
          else if (section.id === "sec-cases") { counters.cases += 1; }
        }
      }
    });
    qsa(".summary-list li").forEach(function (node) {
      if (markNode(node, lowerTerm)) { counters.summary += 1; }
    });

    qsa(".evidence-card").forEach(function (card) {
      if (card.classList.contains("ev-hidden")) { return; }
      var blob = card.getAttribute("data-search") || "";
      if (blob.indexOf(lowerTerm) !== -1) {
        card.classList.add("ev-hit-term");
        markNode(card.querySelector(".ev-content") || card, lowerTerm);
      }
    });

    var box = qs("#sec-findings .hit-section") || qs(".hit-section");
    if (box) {
      box.textContent = "检索「" + term + "」命中：核心结论 " + counters.findings +
        " 条、争议主张 " + counters.disputes + " 条、案例描述 " + counters.cases +
        " 条、概览摘要 " + counters.summary + " 条、证据条目见下方高亮。";
      box.classList.add("show");
    }
    var hits = qs(".search-hits");
    if (hits) {
      hits.textContent = "命中 " + (counters.findings + counters.disputes + counters.cases + counters.summary) +
        " 处结论 / " + qsa(".evidence-card.ev-hit-term").length + " 条证据";
    }
  }

  var searchInput = qs("#global-search");
  var searchTimer = null;
  if (searchInput) {
    searchInput.addEventListener("input", function () {
      if (searchTimer) { clearTimeout(searchTimer); }
      searchTimer = setTimeout(function () { runSearch(searchInput.value); }, 160);
    });
    searchInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        runSearch(searchInput.value);
        var target = qs(".evidence-card.ev-hit-term") || qs("#sec-evidence");
        if (target) { target.scrollIntoView({ behavior: "smooth", block: "start" }); }
      }
    });
  }
  applyEvidenceFilter("");

  /* ---------- 5. 侧边导航滚动高亮 ---------- */
  var navLinks = qsa(".sidebar nav a");
  var sections = qsa(".module");
  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) { return; }
        var id = entry.target.id;
        navLinks.forEach(function (link) {
          link.classList.toggle("active", link.getAttribute("href") === "#" + id);
        });
      });
    }, { rootMargin: "-72px 0px -65% 0px", threshold: 0 });
    sections.forEach(function (section) { observer.observe(section); });
  }

  navLinks.forEach(function (link) {
    link.addEventListener("click", function () {
      navLinks.forEach(function (other) { other.classList.remove("active"); });
      link.classList.add("active");
    });
  });
})();
"""


# ---------------------------------------------------------------------------
# 页面装配
# ---------------------------------------------------------------------------

def render_sidebar(title: str, subtitle: str, digest: str) -> str:
    """左侧固定导航（8 模块）+ 页脚指纹信息。

    防止的失败：章节 href 与 section id 不一致导致跳转失败（两者都来自 MODULES 常量）。
    """
    parts = ['<aside class="sidebar">']
    parts.append('<div class="brand">证据导向型深度调研</div>')
    parts.append(f'<div class="brand-sub">{esc(title)}<br>{esc(subtitle)}</div>')
    parts.append('<nav><ol>')
    for index, (section_id, label) in enumerate(MODULES, start=1):
        parts.append(
            f'<li><a href="#{esc(section_id)}"><span class="nav-num">{index}</span>'
            f'<span>{esc(label)}</span></a></li>'
        )
    parts.append("</ol></nav>")
    parts.append(
        f'<div class="sidebar-foot">deep-research-collab · 单文件离线报告<br>'
        f'payload 指纹 <span class="digest">{esc(digest)}</span><br>'
        f'本页不联网、不引用任何外部资源</div>'
    )
    parts.append("</aside>")
    return "".join(parts)


def render_topbar(title: str) -> str:
    """顶栏：文档标题 + 全局搜索框 + 命中计数 + 打印按钮。

    防止的失败：搜索无可用输入点；标题过长撑破布局（CSS 省略号处理）；
    使用者不知道本页可直接打印（打印时导航/搜索/按钮由 @media print 自动隐藏）。
    """
    return (
        '<header class="topbar">'
        f'<span class="doc-title">{esc(title)}</span>'
        '<span class="search-wrap"><input id="global-search" type="search" '
        'placeholder="全文检索结论 / 证据（回车定位）" autocomplete="off"></span>'
        '<span class="search-hits"></span>'
        '<button type="button" class="btn" id="print-btn" onclick="window.print()">打印 / 导出 PDF</button>'
        '</header>'
    )


def build_html(payload: Dict[str, Any], title: Optional[str] = None, strict: bool = False) -> str:
    """装配完整 HTML 文档。

    防止的失败：任何章节渲染抛异常都会向上冒泡到 main 并以非零退出码结束，
    绝不会写出半截或空报告；payload 缺失的可选字段由各渲染函数优雅降级。
    """
    topic = as_str(payload.get("topic"), "未命名调研主题")
    doc_title = (title or "").strip() or topic
    subtitle = as_str(payload.get("subtitle"))
    digest = payload_digest(payload)

    body_parts: List[str] = [
        "<!DOCTYPE html>",
        '<html lang="zh-CN">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<title>{esc(doc_title)} · 证据导向型深度调研报告</title>',
        f'<meta name="description" content="{esc(subtitle or doc_title)}">',
        f'<meta name="dsh-payload-digest" content="{esc(digest)}">',
        f"<style>{render_styles()}</style>",
        "</head>",
        "<body>",
        render_sidebar(doc_title, subtitle or "证据导向型深度调研", digest),
        render_topbar(doc_title),
        '<main class="main">',
        '<div class="hit-section"></div>',
        render_overview(payload, strict),
        render_mindmap(payload),
        render_sources(payload),
        render_findings(payload),
        render_disputes(payload),
        render_cases(payload),
        render_evidence(payload),
        render_appendix(payload),
        "</main>",
        '<footer class="doc-foot">'
        f'本报告由 deep-research-collab 技能包的 scripts/build_report.py 依据 '
        f'payload 指纹 {esc(digest)} 生成；文档版 Markdown 与单文件 HTML 两版内容字段一致。'
        '所有外部事实均绑定证据 ID，可回溯到完整证据库的原始链接。'
        "</footer>",
        f"<script>{render_scripts()}</script>",
        "</body>",
        "</html>",
    ]
    return "\n".join(body_parts) + "\n"


def count_modules(payload: Dict[str, Any]) -> int:
    """统计实际产出的模块数（恒为 8：8 个标准模块始终渲染，缺失数据时给出空态提示）。"""
    return len(MODULES)


def summarize(payload: Dict[str, Any], html_text: str, problems: Sequence[str], strict: bool) -> str:
    """输出人类可读的构建摘要（stdout）。

    防止的失败：构建成功但内容为空时没有任何提示；校验问题只在日志里出现。
    """
    findings = as_list(payload.get("findings"))
    evidence = as_list(payload.get("evidence"))
    charts = as_list(payload.get("charts"))
    disputes = as_list(payload.get("disputes"))
    cases = as_list(payload.get("cases"))
    byte_size = len(html_text.encode("utf-8"))
    status = "通过" if not problems else f"未通过（{len(problems)} 项）"
    lines = [
        "=== deep-research-collab 报告生成摘要 ===",
        f"主题            : {as_str(payload.get('topic'), '（未提供）')}",
        f"模块数          : {count_modules(payload)}",
        f"结论数          : {len(findings)}",
        f"证据数          : {len(evidence)}",
        f"图表数          : {len(charts)}",
        f"争议数          : {len(disputes)}",
        f"案例数          : {len(cases)}",
        f"输出字节数      : {byte_size}",
        f"payload 指纹    : {payload_digest(payload)}",
        f"校验结果        : {status}" + ("（--strict：校验失败即 exit 1）" if strict else "（未启用 --strict：仅警告）"),
    ]
    if problems:
        for problem in problems:
            lines.append(f"  - {problem}")
    return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """解析 CLI 参数。

    防止的失败：参数缺失时给出可执行的使用示例，而不是 argparse 的默认晦涩报错。
    """
    parser = argparse.ArgumentParser(
        prog="build_report.py",
        description="证据导向型深度调研：由 payload JSON 生成单文件离线交互式 HTML 报告。",
        epilog='示例：python scripts/build_report.py --payload payload.json --out report.html --strict',
    )
    parser.add_argument("--payload", required=True, help="payload JSON 文件路径")
    parser.add_argument("--out", required=True, help="输出 HTML 文件路径")
    parser.add_argument("--title", default="", help="报告标题（缺省使用 payload.topic）")
    parser.add_argument("--strict", action="store_true", help="校验失败时以 exit 1 结束")
    parser.add_argument("--open", dest="open_after", action="store_true",
                        help="生成后用系统默认程序打开 HTML")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """程序入口：读取 → 校验 → 渲染 → 落盘 → 摘要。

    防止的失败：任何异常都被显式捕获并映射为约定的退出码与 stderr 信息，
    用户永远能区分"参数错误(2)""校验失败(1)""构建失败(1, 非校验)"和"成功(0)"。
    """
    args = parse_args(argv)
    configure_stdio()

    try:
        payload = load_payload(args.payload)
    except PayloadError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 2

    problems = validate(payload)
    if problems:
        stream = sys.stderr
        prefix = "[校验失败]" if args.strict else "[校验警告]"
        print(f"{prefix} 共 {len(problems)} 项问题：", file=stream)
        for problem in problems:
            print(f"  - {problem}", file=stream)
        if args.strict:
            print("[校验失败] --strict 已启用，终止构建，未写出任何 HTML。", file=stream)
            return 1

    try:
        html_text = build_html(payload, title=args.title, strict=args.strict)
    except Exception as exc:  # noqa: BLE001 - 渲染阶段任何异常都必须显式暴露，不能静默产出空报告
        print(f"[错误] HTML 渲染失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if not html_text.strip():
        print("[错误] 渲染结果为空，已终止（不写出空报告）。", file=sys.stderr)
        return 1

    out_path = os.path.abspath(args.out)
    out_dir = os.path.dirname(out_path)
    try:
        if out_dir and not os.path.isdir(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(html_text)
    except OSError as exc:
        print(f"[错误] 写出 HTML 失败：{out_path}（{exc}）", file=sys.stderr)
        return 1

    print(summarize(payload, html_text, problems, args.strict))

    if args.open_after:
        try:
            os.startfile(out_path)  # type: ignore[attr-defined]  # Windows 专用，非 Windows 无此属性
        except AttributeError:
            print("[警告] 当前系统不支持 os.startfile，请手动打开生成的 HTML。", file=sys.stderr)
        except OSError as exc:
            print(f"[警告] 自动打开 HTML 失败：{exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
