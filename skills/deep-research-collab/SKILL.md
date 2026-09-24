---
name: deep-research-collab
description: 证据导向型深度调研协同。用于陌生领域体系化研究、行业深度调研、内容/课程/产品前期论证与课题研究：用三级搜索（一级广度发现 → 二级深度核对 → 三级缺口补充，含微信公众号定向检索）建立带唯一证据 ID 的可溯源证据库，所有结论绑定证据、争议正反并列、缺口自动回退补搜，最终交付内容一致的「文档版 Markdown 报告 + 单文件离线 HTML 交互式报告」。触发词：深度调研、体系化研究、行业研究、竞品调研、市场格局、课题研究、证据溯源、调研报告、deep research、research report、行业全景、认知地图。只要用户要一次快速检索或单工具研究，改用 tavily-research，不要用本技能。
whenToUse: 当用户要"系统梳理并给出带来源的报告"、要求每个结论可溯源、要求交互式 HTML 报告/图表/思维导图，或要做行业/竞品/市场格局/课题研究时使用。不用于单点事实查询、一次网页检索、新闻摘要、翻译润色、写代码或装插件（这些用普通检索或 tavily-research）；也不用于已有材料的总结（输入已是成品时不触发）。
metadata:
  version: "0.2.0"
  category: research
  upstream: local
---

# 证据导向型深度调研协同

> 本文件是路由面：只写触发边界、五阶段流程、资源路由、硬停止和验收口径。细则在 `references/`，模板在 `assets/`，生成器在 `scripts/`。

## 这个技能解决什么

让一次深度调研的**每个结论都能指回原始网页与原文片段**，并且同时交付可归档的文档版与可演示的 HTML 交互版。它防的不是"写不出报告"，是"写出无法溯源的报告"。

用户最终品：一份**双交付物**（文档版 Markdown 报告 + 单文件离线 HTML 交互式报告），加上 `report-payload.json`（结构化交付数据：`evidence[]` / `findings[]` / `charts[]` / `disputes[]`）、图表源数据与运行记录。

## 触发边界

**应当触发**：陌生领域体系化研究、行业深度调研、竞品/市场格局分析、内容/课程/产品前期论证、课题研究；用户要求"每个结论都要有来源""要能溯源""要交互式报告/图表/思维导图"。

**不应当触发**：单个事实的快速查询、一次网页检索、新闻摘要、翻译润色、写代码、装插件。这些用普通检索或 `tavily-research`。

**近似情形（Near-Miss）**：
- "帮我查一下 X 是什么" → 单点查询，不触发；用户补一句"要系统梳理并给带来源的报告" → 触发。
- "把这份 PDF 总结一下" → 输入已经是材料，不触发；"围绕这个话题自己找资料并做交叉验证" → 触发。
- "写一篇公众号文章" → 走 `wechat-article-fact-grounded`；若该文的资料底稿本身需要体系化调研 → 先跑本技能产出证据库，再交给写作技能。

**模糊情形**：用户只说"研究一下 X"时，**先出需求对齐卡**——用一轮 3-5 题的选择面锁定深度档位、交付形态、时间窗、范围收敛方式与证据标准，再按 `research-workflow.md` 的阶段 0-5 执行。默认档（用户说"你定"时）：B 标准档 + 双交付 + 近 18 个月 + 研究方先给候选框架 + 严格证据标准。

**与 tavily-research 的路由边界**：只要一次 Tavily 深度检索就够、不需要中文域/公众号补证、不需要证据 ID 体系与双交付物 → 用 `tavily-research`。需要三级协同、缺口回退、正反证据并列、HTML 可点击溯源 → 用本技能。

## 五阶段流程

| 阶段 | 目标 | 主要动作 | 产物 | 完成判据 |
|---|---|---|---|---|
| 0.1 需求对齐 | 和用户对齐了再动手 | 用**需求对齐卡**问 3-5 题（宿主原生选择面），锁定深度档位 / 交付形态 / 时间窗 / 证据标准 / 必答问题 | `00-alignment-card.md` | 状态为 `aligned` 或 `defaulted`；`research_domain`、决策用途、必答问题均非空；**无人值守时同样必须落到 `defaulted` 并声明未经确认**（不得停在 `unconfirmed` 而不留产物） |
| 0.2 研究初始化 | 锁定题目与边界 | 先做**意图与领域研究**，写**领域研究简报**与**多模态简报** | `00-research-brief.md`、`multimodal-prompt-brief.md` | 主题、`research_domain`、纳入/排除边界、指标体系、交付物形态都明确；多模态简报含图表清单与降级路线 |
| 1 广度候选检索 | 铺开候选来源 | 一级：`tvly search` 全球域 + `mcp__metaso__metaso_web_search` 中文域 | `01-candidate-sources.md` | 候选来源 **≥20 条**（领域确实窄时 ≥12 条并附窄因说明）且**来源桶覆盖 ≥4 类**；中英双语**各 ≥3 条查询式**（输入侧）且候选**中英文占比各 ≥30%**（产出侧） |
| 2 深度提取与认知地图 | 把页面变成证据 | 二级：`mcp__metaso__metaso_web_reader` / `tvly extract` 取全文，抽取原文片段，编 EV 号 | `02-evidence-v1.0.md`、`03-cognition-map-v1.0.md` | 每条证据有链接 + 原文片段 + 提取时间；认知地图每个分支挂证据 |
| 3 反证验证与缺口补全 | 找反例、补缺口 | 三级：微信定向 `site:mp.weixin.qq.com` + 反证检索；触发**回退** | `04-counterevidence.md`、`02-evidence-v2.0.md`、`03-cognition-map-v2.0.md` | 每个核心结论 ≥ 2 个独立来源；每个争议点正反证据并列 |
| 4 信息取舍与双格式输出 | 出双份交付物 | 先出文档版 `report.md`；再按 `assets/report-payload-template.json` 填出 `report-payload.json`，用生成器出 `report.html`；最后做**一致性校验** | `report.md`、`report-payload.json`、`report.html`、`consistency-check.md` | 两版结论/数据/案例完全一致，EV ID 一一对应；一致性校验已落盘 |
| 5 证据归档与溯源备案 | 可复查 | 归档报告、证据库、图表源数据、证据快照、运行记录 | `archive/`、`acceptance-run.md`、`loop-run-record.md` | 归档清单完整，运行记录含写回决策 |

细则与查询式模板见 `references/research-workflow.md`；证据字段与可信度判据见 `references/evidence.md`。

## 阶段 0 第一动作：需求对齐（先对齐，再检索）

**不要一上来就搜**。先用 `assets/requirements-alignment-card-template.md` 和用户对齐，产物为 `00-alignment-card.md`，状态只能是 `aligned` / `defaulted` / `unconfirmed`。

对齐卡字段（缺 `research_domain`、决策用途、必答问题任一即不合格）：

| 区块 | 字段 |
|---|---|
| A 需求侧 | 研究主题、`research_domain`、决策用途、`audience`、`stakeholder_view`、`deliverable_target`、必答问题（3-5 条）、**本轮不做**、时间窗 |
| B 研究侧 | `scope.in` / `scope.out`、指标体系（3-6 个可核查指标）、证据标准、可接受与拒收来源、深度档位（A 快扫 / B 标准 / C 深度）、成本预算、时间预算 |
| C 确认记录 | 用户改动、取默认值的字段、未决项 |

**怎么问**：一轮 3-5 题、每题 2-4 个选项、每个选项写清后果。DSH 用 `ask_user_question`，Codex 用 `request_user_input`，Claude Code 用 `AskUserQuestion`；题面与选项直接取 `assets/alignment-question-bank.json`（含每题默认值与跳过条件）。没有原生选择工具时，把编号选项贴出来并**停下等选择**，状态记 `unconfirmed`——**不得替用户勾选**。

**用户说"你定"**：取问题库的默认值，写进 `取默认值的字段`，状态记 `defaulted`，并在报告首屏与运行记录 `Intent Core` 段各声明一句。

**无人值守（关键分支，勿省）**：当执行环境里**没有可问的人**——自动化流水线、子 Agent、批处理、定时任务——时：

1. **不要调用选择面工具**（`ask_user_question` / `request_user_input` / `AskUserQuestion`）。在无人环境里它不会返回，执行会**停在第一个动作上且不留下任何产物**，从外面看与"没跑"无法区分。
2. 直接取 `alignment-question-bank.json` 的默认值落盘 `00-alignment-card.md`，状态记 `defaulted`。
3. 在 `取默认值的字段`、报告首屏、运行记录 `Intent Core` 三处**同时**声明「**本轮未经用户确认，全部取默认档**」。
4. 若委托涉及**健康、人身安全、法定时限**等时间敏感领域，先按下方"安全优先例外"给即时风险提示再落卡；此时**不得**因无人确认而跳过提示。

> 为什么单列这条：原文档只有"有人可问"与"停下等选择"两条路，两者在无人环境里都会阻塞。
> 2026-09-24 实测：一个无对话上下文的执行者在阶段 0.1 处跨两轮零产出，产出目录已建、文件数 0。

**硬门禁**：状态 `unconfirmed`，或必答问题为空、或写成"全面了解该领域"，**不得进入阶段 1**，也不得以"先搜两条看看"绕过。用户中途改需求 → 更新卡片、记改动点，并检查已产出证据是否作废（作废的 `EV` 不得进入 v2.0）。

worked example 见 `examples/example-alignment-card.md`。

## 创建 / 重构本技能包时

本技能也用于把它自己做成可复用能力包。这条路线按阶段契约走，且顺序不可颠倒：

1. **Critical Thinking**：判定任务是 `new-skill` / `refactor-skill` / `evaluate-skill` / `package-plan` / `release-prep`，写清用户结果、范围、非目标与第一证据路线。
2. **Fetch**：只收集会改变包决策的证据（用户材料、本机能力、官方文档、高信号样例、反证），并记录不可得路径。
3. **Deep Thinking**：把证据合成为触发边界、产物链、工具路线与验收计划。
4. **Build**：只动必须动的文件，先写**包计划**（`assets/package-plan-template.md`：文件 → 防止的失败模式 → 证据 → 校验命令 → 删除/合并决策），再落笔。
5. **Review**：跑结构门禁与产物校验；对外交付、发布或声称可迁移之前必须过**发布门禁**（`references/release-gate.md`）。

依赖图表、图片、演示文稿、PDF 等渲染产物时，先写**多模态简报**（`assets/multimodal-prompt-brief-template.md`：能力清单 / 产物简报 / 提示词变体 / 验证），再决定渲染路线；本机不具备的能力一律标降级，不得默认可用。

字段名以脚本为准：HTML 生成器读取的字段是 `findings` / `evidence` / `charts` / `disputes` / `cases`（见 `assets/report-payload-template.json`），文档里出现的 `Key Findings`、`结论` 均指同一组数据。

## 三级工具协同（成本边界）

| 层级 | 角色 | 工具 | 成本边界 |
|---|---|---|---|
| 一级 | 候选发现者 | `tvly search`、`mcp__metaso__metaso_web_search` | 秘塔每次检索约 3 积分；Tavily 有额度上限 → 先中英双语各 2-3 条查询式，再按命中率加投 |
| 二级 | 深度核对者 | `mcp__metaso__metaso_web_reader`、`tvly extract` | 优先核对一级命中的高价值页面，不做全量抓取 |
| 三级 | 缺口补充者 | 秘塔搜索限定 `site:mp.weixin.qq.com` + `metaso_web_reader`、`mcp__metaso__metaso_chat` 交叉质询 | 只在缺口/反证需求明确时调用 |

## 资源路由（渐进加载）

只读当前阶段需要的文件：

| 现在要做什么 | 读哪个 |
|---|---|
| **开场和用户对齐需求** | `assets/requirements-alignment-card-template.md`、`assets/alignment-question-bank.json`、`examples/example-alignment-card.md` |
| 搞清楚调研怎么做 | `references/research-workflow.md` |
| 证据字段、可信度、来源独立性 | `references/evidence.md` |
| 开题：领域研究规则与简报 | `references/intent-domain-research.md`、`assets/domain-research-brief-template.md` |
| 定义产物表面与图表清单 | `references/experience-surface-model.md`、`references/product-design.md` |
| 本地渲染能力与降级路线 | `references/multimodal-tooling.md`、`assets/multimodal-prompt-brief-template.md` |
| 生成 HTML 报告 | `scripts/build_report.py`、`assets/report-payload-template.json` |
| 写文档版报告 | `assets/document-report-template.md` |
| 记录证据库 | `assets/evidence-library-template.md` |
| 创建/重构本技能包 | `references/creation-rule-standard.md`、`references/skill-contract.md`、`assets/skill-contract-template.md`、`assets/package-plan-template.md`、`assets/product-design-board-template.md` |
| 使用外部案例或竞品材料 | `references/source-abstraction-boundary.md` |
| 设计**触发评测**/输出评测/基线对比 | `references/evaluation-method.md`、`evals/trigger-eval.json` |
| 声称可交付、要发布或验收 | `references/release-gate.md`、`assets/acceptance-run-template.md` |
| 收尾：闭环治理、写回决策 | `references/closed-loop-governance.md`、`assets/loop-run-record-template.md` |

## 本地能力清单（本机实测）

- 有：Python 3.14（标准库 + python-docx / openpyxl / python-pptx / Pillow / markdown）、Chrome 与 Edge（`--headless=new --print-to-pdf`、`--screenshot`）、`tvly` CLI、秘塔 MCP 六个工具。
- 没有：pandoc、LibreOffice、wkhtmltopdf、LaTeX、typst、ImageMagick。
- 因此 HTML 报告走 **Python 标准库生成单文件**（图表全部内联 SVG），**不依赖 CDN**；需要 PDF 时用 Chrome headless 打印。任何声称"用某渲染器生成"的说法都必须有产物证据，否则标注降级。详见 `references/multimodal-tooling.md`。

## 硬停止

遇到以下情况先停下并说明，不要硬写报告：

- **需求对齐卡未确认**（状态 `unconfirmed`），或缺 `research_domain`、决策用途、必答问题 → 先对齐，不得进入阶段 1（"先搜两条看看"也不行）。
- 用户没给 `research_domain`，也没给可推断的题目范围。
- 关键结论连一条合格在线证据都没有 → 标 `research-needed`，回到阶段 1/3 补搜。
- 外部事实缺原始链接或原文片段 → 不得写进报告。
- 核心结论独立来源不足 2 个 → 不得写成确定性结论。
- 争议点只有单边证据 → 必须补反证，否则只呈现为"未决问题"。
- HTML 报告与文档版不一致 → 以文档版为准修正渲染，不得两份都交。
- 生成器校验失败且无法修复 → 交付文档版 + 明确说明 HTML 未生成（`blocked`）。

## 验收（跑命令，不看感觉）

```bash
# 报告生成与严格校验（引用不存在的 EV / 结论无证据 / 独立来源不足 → 非零退出）
python scripts/build_report.py --payload report-payload.json --out report.html --strict

# 技能包结构门禁
python scripts/check_meta_skill_package.py .
python scripts/check_closed_loop.py .
```

证据分层（不得互相替代）：结构校验通过 ≠ 产物可用；产物存在 ≠ 结论可溯源；**人工确认**（用户能打开 HTML、能点开证据、能核对原文）才是最终判据。

## 闭环治理

每轮调研结束都要填 `assets/loop-run-record-template.md`（**运行记录**），并给出一个**写回决策**：`writeback`（把可复用学习写回 references/assets/scripts/evals 或 examples）、`proposal`（只提议不动手）、`none-with-reason`（说明为什么不需要写回）、`blocked`（写清阻塞条件）。聊天总结不算闭环，必须落到文件。漂移信号与判定口径见 `references/closed-loop-governance.md`。
