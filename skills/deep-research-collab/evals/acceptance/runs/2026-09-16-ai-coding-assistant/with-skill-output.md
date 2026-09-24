# With-skill 输出（使用 deep-research-collab 的真实运行）

- 运行 ID：RUN-20260916-01
- 运行日期：2026-09-16
- 产物目录（本次运行实例）：`<run-root>/2026-09-16-ai-coding-assistant-adoption/`（`run-root` 由调用方指定；此处不留本机绝对路径）

## 1. Domain Research Brief（阶段 0 产出，节选）

| 字段 | 本次取值 |
|---|---|
| 主题 | AI 编程助手的采用率：口径之争与真实渗透 |
| `research_domain` | AI 编程助手（采用率与真实渗透） |
| `audience` / `stakeholder_view` | 内容与产品前期论证 / 团队技术选型参考（工程负责人视角） |
| `deliverable_target` | 归档 + 演示（文档版 + 单文件离线 HTML，双交付） |
| 范围纳入 | 公开采用率数据与口径、海外/国内工具格局、效率与质量证据、企业投入结构 |
| 范围排除 | 代码质量实测、报价谈判、未公开的内部采用率 |
| 时间窗 | 以近期公开数据为主（含 2026 年数据） |
| 指标体系 | 采用率（三口径）/ 工具格局 / 效率 / 质量 / 投入结构 |
| 不可得路径 | 厂商内部渗透率的第三方审计数据 → 标为厂商自披露，不升格 |

## 2. Evidence sweep（三级检索实际执行）

| 层级 | 工具（真名） | 实际动作 | 产出 | 成本 |
|---|---|---|---|---|
| 一级 广度发现 | `mcp__metaso__metaso_web_search` | 中文域查询「AI 编程助手 企业采用率 现状 调研」 | 8 条候选 | 3 积分 |
| 一级 广度发现 | `tvly search` | 全球域查询「AI coding assistant enterprise adoption survey 2026」 | 5 条候选 | 1 次 |
| 二级 深度核对 | `mcp__metaso__metaso_web_reader` | 取《财经》全文并抽取原文片段 | 6 条带片段证据 | 按篇 |
| 三级 缺口补充 | `mcp__metaso__metaso_web_search` + `site:mp.weixin.qq.com` | 定向检索反证 | 6 条候选 → 1 条关键反证 | 3 积分 |

**回退**：阶段 3 回退 1 次（企业采用率原先只有乐观单边数据，按「争议点必须正反并列」红线回退补反证）。

## 3. 交付物（含机器可核查证据）

| 产物 | 路径 | 校验证据 |
|---|---|---|
| 领域研究简报/证据/流程 | `payload.json`（14 条证据 / 5 条结论 / 3 图 / 2 争议 / 2 案例） | `py validate_payload.py payload.json` → 自检通过 |
| 文档版报告 | `报告-AI编程助手采用率.md` | 结论逐条带 `[EV-00X]`；争议正反并列 |
| HTML 交互式报告 | `报告-AI编程助手采用率.html`（91,498 B） | `build_report.py --strict` exit 0；`check_selfcontained.py` 通过（无 CDN/外链脚本/字体/图片，`EV-` 出现 163 次） |
| 离线可打开证明 | `report-screenshot-full.png`（669 KB，Chrome headless 1440×9000） | 截图可见 8 模块、柱/折/饼 SVG 图表、争议正反对置、案例时间线、证据库筛选器 |
| 确定性 | 连跑两次 HTML | sha256 一致（同一 payload → 同一字节） |

## 4. Skillization Decision（本轮对技能包的写回决定）

**决策：`writeback`**（详见本文件夹内的 `loop-run-record.md`）。

写回内容：

1. **图表刻度方向缺陷**（真实伤痕）：柱状/折线图的 Y 轴刻度标签上下颠倒（网格线对称所以肉眼易漏），已修 `scripts/build_report.py` 两处 `y = pad_top + plot_h * (1 - tick / 4)`；修复后重新生成产物并截图复验。
2. **技能价值边界**（真实反证）：without-skill 基线找到了本技能没找到的高质量一手来源（Stack Overflow 2025 调查、DX ROI 追踪），说明本技能的价值在**可核查结构**而非"来源更强"。已写回 `references/release-gate.md` 与 `references/evaluation-method.md`：不得声称本技能在来源发现上优于普通检索，只声称可溯源性可验证。

## 5. 与 without-skill 基线的差异（同一问题、同一天）

| 维度 | without-skill（朴素流程） | with-skill（本技能） |
|---|---|---|
| 结论 | 6 条，实质性质量高，来源不弱 | 5 条，逐条绑定证据 ID |
| 证据结构 | 无证据库，链接内嵌在正文 | 14 条证据卡，含原文片段/时间/层级/工具 |
| 交叉验证 | 未按结论核对独立来源数 | 每条结论 ≥ 2 个独立来源（脚本强制） |
| 争议处理 | 有"可核查性不足"自述，但无正反对置 | 2 个争议点正反并列 + 适用边界 |
| 缺口回退 | 无（抓取失败 4 次即放弃并声明未核实） | 触发 1 次回退并补到关键反证 |
| 交付物 | 单个 Markdown | 文档版 + 离线 HTML（图表/思维导图/证据链路） |
| 机器可核查 | 无（0 条可自动校验） | `--strict` 校验通过，可复跑 |
