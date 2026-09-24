# Validation（校验记录）

## Validation

| 校验 ID | 目标 | 命令 / 动作 | Result（实际输出摘要） |
|---|---|---|---|
| V-1 | payload 结构与引用完整性 | `py validate_payload.py payload.json` | Result：`自检通过：所有结论绑定证据、引用完整、独立来源 ≥2、图表点数匹配。`（证据 14 / 结论 5 / 图表 3 / 争议 2 / 案例 2） |
| V-2 | HTML 生成 + 严格校验 | `py scripts/build_report.py --payload payload.json --out 报告.html --strict` | Result：exit 0；`模块数 8 / 结论数 5 / 证据数 14 / 图表数 3 / 校验结果：通过`；输出 91,498 B |
| V-3 | 离线自包含 | `py check_selfcontained.py 报告.html` | Result：`自包含自检通过：无外部脚本/样式/字体/图片`；内联 style 1 / script 1；外链 `<a>` 9 个全为证据链接；`EV-` 出现 163 次 |
| V-4 | 确定性 | 连跑两次生成到临时文件后比对 | Result：`determinism: True`（sha256 一致） |
| V-5 | 渲染可见性 | Chrome `--headless=new --window-size=1440,9000 --screenshot` | Result：生成 `report-screenshot-full.png` 669,405 B；可见 8 模块、柱/折/饼 SVG、争议正反对置、案例时间线、证据库筛选器 |
| V-6 | 图表刻度方向（修复后复验） | 重新生成 + 重新截图 + 目视核对 | Result：Y 轴自上而下为 100→0、柱形自基线向上生长、折线随数值上升（修复前为反向） |
| V-7 | 技能包结构门禁 | `py scripts/check_meta_skill_package.py .` | Result：`passed`（24 个必需文件） |
| V-8 | 闭环契约门禁 | `py scripts/check_closed_loop.py .` | Result：`passed` |
| V-9 | 验收运行文件夹门禁 | `py scripts/check_acceptance_runs.py evals/acceptance/runs/2026-09-16-ai-coding-assistant` | Result：`Acceptance run check passed.`（分数差 5 ≥ 4） |

## 证明层级说明

- **结构证据**：V-1、V-7、V-8、V-9（证明包与数据的形状正确，不证明内容正确）。
- **产物证据**：V-2、V-3、V-5、V-6（证明文件真实存在、可离线渲染、图表方向正确）。
- **运行证据**：V-4（证明结果可复现，不是一次性手工产物）。
- **人工确认**：**尚未取得**——等待用户亲手打开 `报告-AI编程助手采用率.html`、点开至少 2 条证据标签并核对原文。

## 结论

- Result：`pass`（结构性 / 产物性 / 运行性证据全部通过；人工确认仍为未完成项，已写入下一轮第一动作）。
- 未通过或未执行项：无阻塞项；`双版一致性`为人工逐模块比对，尚未脚本化（记入 reviewer-notes 待改进项 1）。
