# 示例输出

> 本文件防止的失败模式：把"看起来很像报告"的散文当成交付物。这里给出可核查的产物链与命令证据。

**说明**：以下示例中所有来源链接均为 `https://example.com/...` 占位符，用于演示结构，**不是真实调研结论**。真实运行时必须替换为实际检索到的链接与原文片段。

## 产物链（本次运行的 9 个产物）

| # | 产物 | 路径 | 完成判据 |
|---|---|---|---|
| 1 | 需求对齐卡 | `00-alignment-card.md` | 状态 `aligned`/`defaulted`；`research_domain`、决策用途、必答问题非空；`本轮不做` ≥3 项；成本预算写死 |
| 2 | 领域研究简报 | `00-research-brief.md` | 主题/边界/指标体系/证据路线/交付物形态齐全 |
| 3 | 候选来源清单 | `01-candidate-sources.md` | ≥ 15 条候选，≥ 3 种来源类型 |
| 4 | 证据库 v2.0 | `02-evidence-v2.0.md` | 每条含链接 + 原文片段 + 提取时间 + 层级 |
| 5 | 认知地图 v2.0 | `03-cognition-map-v2.0.md` | 每个分支挂证据 ID |
| 6 | 反证记录 | `04-counterevidence.md` | 每个争议点正反并列 |
| 7 | 文档版报告 | `report.md` | 结论全部带 `[EV-00X]` |
| 8 | HTML 交互式报告 | `report.html` | 离线自包含、证据可点击、图表数据带来源 |
| 9 | 运行记录 | `runs/2026-09-16-run.md` | 六段记录 + 写回决策 |

## 1. 需求对齐卡（节选）

```yaml
状态: aligned
决策用途: 技术选型前的判断依据（会上投屏）
deliverable_target: 双交付（文档版 + HTML 演示版）
必答问题: [真实采用率（分口径）, 成本结构, 效率证据与质量风险, 合规与私有化约束]
本轮不做: [代码质量实测, 报价谈判, 厂商内部路线图]
深度档位: C（含反证回退）
证据标准: 严格（每条结论 ≥2 独立来源 + 原文片段）
成本预算: 秘塔 ≤ 6 次；Tavily ≤ 3 次
```

## 2. 领域研究简报（节选）

```text
主题：AI 编程助手赛道格局与技术选型依据
research_domain：AI 编程助手（国内为主，兼顾海外）
audience：团队技术选型会（stakeholder_view：工程负责人）
deliverable_target：归档 + 演示
time_window：近 18 个月
排除：代码质量实测、报价谈判
指标体系：能力覆盖 / 采用率证据 / 定价模式 / 生态集成 / 风险与合规
证据路线：一级 tvly search + metaso_web_search；二级 metaso_web_reader；三级 site:mp.weixin.qq.com 实操与反证
不可得路径：厂商未公开的内部采用率数据（标注为 unknown，不推测）
```

## 3. 证据库（节选，字段与真实运行一致）

| ID | 内容 | 类型 | 可信度 | 原文片段 | 来源 | 层级 | 工具 |
|---|---|---|---|---|---|---|---|
| EV-001 | 某类工具在企业内的试点比例 | 数据 | 中 | "……" | [示例来源](https://example.com/a) | 一级 | metaso_web_search |
| EV-002 | 主流产品的定价分档 | 数据 | 高 | "……" | [示例来源](https://example.com/b) | 二级 | metaso_web_reader |
| EV-003 | 团队引入后回退的案例 | 案例 | 中 | "……" | [示例来源](https://example.com/c) | 三级 | metaso_web_search (site:mp.weixin.qq.com) |
| EV-004 | 对采用率口径的质疑 | 争议观点 | 待验证 | "……" | [示例来源](https://example.com/d) | 三级 | tvly extract |

## 4. 文档版报告（节选）

```markdown
### 核心发现 2：企业采用呈现"局部深度、整体浅层"特征

试点类工具在单个团队内的渗透速度明显快于跨部门推广速度，
主要瓶颈不在模型能力，而在权限、审计与数据边界流程 [EV-001][EV-005]。
反方观点认为该结论受样本偏差影响，因为公开数据的披露方多为工具厂商 [EV-004]。
```

## 5. HTML 交互式报告（同一份内容的另一种表面）

- 8 个模块：报告概览 / 领域认知地图 / 三级搜索来源溯源 / 核心研究发现 / 争议与反证分析 / 典型案例库 / 完整证据库 / 附录。
- 结论旁的 `EV-001` 标签可点击 → 平滑滚动到证据库对应条目并高亮。
- 图表（柱状/折线/饼图）由 Python 生成内联 SVG，每个数据点带 hover 提示，图下标注来源证据 ID。
- 离线可打开：无 CDN、无外链脚本、无外链字体；唯一外链是证据的原始链接。

生成与校验（真实命令形态）：

```bash
python scripts/build_report.py --payload payload.json --out report.html --strict
# 输出摘要：模块 8 / 结论 12 / 证据 34 / 图表 3 / 争议 2 / 案例 3 / 校验通过
```

示例产物：`examples/report-sample.html`（由 `examples/example-report-payload.json` 生成，本文件是脚本真实输出，不是手写）。

## 6. 闭环运行记录（节选）

```text
Intent Core：用户要"选型前判断"，因此结论必须给出可执行判断而不是行业综述
Evidence Fetch：一级 14 条候选 → 二级 9 条全文 → 三级 6 条（含 2 条反证）
Product Surface：文档版 + HTML 版；图表 3 个（均来自量化证据）
Package Contract：SKILL.md 只做路由；细则在 references/research-workflow.md
Evidence Review：1 个争议点曾单边取证，回退到三级补齐后解决（回退 1 次）
Loop Decision：writeback（把"微信定向检索的有效查询式"写回 references/research-workflow.md）
```

## 前后对照（without-skill vs with-skill）

| 维度 | 不用本技能 | 用本技能 |
|---|---|---|
| 结论来源 | 大部分无链接，或只有聚合站链接 | 每条结论绑定 `[EV-00X]`，可点开到原文片段 |
| 争议处理 | 只写主流说法 | 正反证据并列 + 适用边界 |
| 缺口 | 忽略或凭常识补齐 | 触发回退补搜并记录回退次数（本次 1 次） |
| 交付物 | 一段 Markdown | 文档版 + 离线 HTML（图表/思维导图/证据链路） |
| 可验收性 | 只能"读一读觉得像" | 生成器 `--strict` 校验 + 结构门禁命令可复跑 |
