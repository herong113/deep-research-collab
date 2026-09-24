# 深度调研执行手册（阶段 0-5 / 三级搜索协同）
> 本文件防止的失败模式：把调研做成"搜一批网页然后写观感"；中英文只查一边；争议点只找到单边证据就下结论；关键数据拿二手转述当原始出处；跳过初始化直接输出；文档版与 HTML 各自改一遍导致两版内容不一致。

## 0. 变量、前置与总原则

- 变量：`research_domain`（研究领域）、`audience`（受众）、`deliverable_target`（交付目标）、`stakeholder_view`（干系人视角）。全文任何规则不得写死具体行业、公司或岗位。
- 触发场景：陌生领域体系化研究、行业深度调研、内容/课程/产品前期论证、课题研究。命中后第一步永远是把状态记为 `research-needed`。
- 总原则：**先证据后结论**。任何结论在证据库（`02-evidence-v2.0.md` 与 `report-payload.json` 的 `evidence[]`）里找不到 ≥2 个独立 `EV`，就只能降级为"待验证观察"或写成缺口。
- 工具真名（不得写错、不得编造）：`tvly`（Tavily CLI，注意不是 tavily）、`mcp__metaso__metaso_web_search`、`mcp__metaso__metaso_web_reader`、`mcp__metaso__metaso_chat`、`mcp__metaso__metaso_topic_list`、`mcp__metaso__metaso_topic_search`、`mcp__metaso__metaso_topic_file_content`。
- 成本边界：秘塔每次检索约 3 积分，Tavily 有额度上限。额度紧张时：先用中文域定框架，再用全球域补一手数据。
- 证据字段与合格线见 `references/evidence.md`；工具能力与降级见 `references/multimodal-tooling.md`；门禁见 `references/release-gate.md`；运行记录见 `references/closed-loop-governance.md`。

## 1. 三级搜索协同矩阵

| 层级 | 角色 | 主力工具 | 典型查询式 | 输出产物 | 成本边界 |
| --- | --- | --- | --- | --- | --- |
| 一级广度发现 | 铺开候选池，形成领域轮廓；此层**不产出结论** | `tvly`（全球域）+ `mcp__metaso__metaso_web_search`（中文域） | `<topic> overview report after:<YYYY-MM-DD>`；`<主题> 行业 现状 痛点 2024..2025` | `01-candidate-sources.md`（≥20 条候选） | 秘塔每检索约 3 积分；Tavily 有额度上限，单层检索式预算 ≤ 8 条 |
| 二级深度核对 | 取全文、抽原文片段、生成证据卡与认知地图 | `mcp__metaso__metaso_web_reader`、`tvly extract` | 直接传候选 URL（不做关键词检索） | `02-evidence-v1.0.md`（自 `EV-001` 起）+ `03-cognition-map-v1.0.md` | 每次取全文 1 次调用，优先取一手与署名研究 |
| 三级定向补充 | 补缺口、找反证、取实操细节 | `mcp__metaso__metaso_web_search`（限定 `site:mp.weixin.qq.com`）+ `mcp__metaso__metaso_web_reader` | `<主题> 实操 踩坑 site:mp.weixin.qq.com`；`<争议点> 反对 质疑 site:mp.weixin.qq.com` | `04-counterevidence.md`、`02-evidence-v2.0.md`、`03-cognition-map-v2.0.md` | 仅在触发缺口条件时使用，每次回退 ≤3 条查询 |

辅助工具使用边界：`mcp__metaso__metaso_chat` 只用于生成检索式候选与术语对照，**不得**作为事实来源写进 `EV`；`mcp__metaso__metaso_topic_search` / `metaso_topic_file_content` 只用于用户自有专题库，命中后仍须按一级/二级规则重新取原文与链接。

## 2. 一级广度检索查询式模板

要求：每个主题至少产出 5 条英文式 + 5 条中文式，中英各覆盖"综述 / 数据 / 案例 / 争议 / 从业者"五类意图。

| 意图 | 英文模板 | 中文模板 |
| --- | --- | --- |
| 综述 | `<topic> overview (report OR whitepaper) after:<YYYY-MM-DD>` | `<主题> 行业报告 综述 after:<YYYY-MM-DD>` |
| 数据 | `<topic> statistics market size <year>` | `<主题> 市场规模 数据 增长率 <年份>` |
| 案例 | `<topic> case study (implementation OR postmortem)` | `<主题> 案例 复盘 落地` |
| 争议 | `<topic> criticism (limitations OR controversy)` | `<主题> 争议 质疑 风险` |
| 从业者 | `<topic> practitioner lessons learned (site:medium.com OR site:substack.com)` | `<主题> 从业者 经验 实操` |
| 政策/一手 | `<topic> (regulation OR standard) filetype:pdf site:gov` | `<主题> 政策 规范 site:gov.cn` |

限定符规则：时间窗一律显式写入（如 `after:2024-01-01` 或中文式 `2024..2025`）；来源类型用 `site:` / `filetype:` 限定，不靠事后筛选；每类意图命中不足 3 条时，先换同义词与上位/下位词再换工具，改写轮次上限 3 轮。

## 3. 阶段 0：研究初始化

阶段 0 分两小步，顺序不可颠倒：**0.1 需求对齐（与用户）→ 0.2 领域研究简报（研究侧）**。

### 3.1 阶段 0.1 需求对齐（第一动作）

- **目标**：把一句模糊委托固定成双方都认过的调研契约，避免"搜完才发现边界不对"。
- **安全优先例外（2026-09-16 写回，RUN-20260916-HZ）**：当委托涉及**健康、人身安全、法定时限**且存在时间敏感窗口时（例如用药窗口、诉讼时效、安全整改期限），**先给即时风险提示与前门问题，再完成对齐卡**——不得先问满 3-5 题再回答。此时对齐卡状态先记 `unconfirmed`，提示内容必须与结论内容分离（提示可先给，结论仍受证据门槛约束）。
- **输入**：用户请求文本；可选的既有材料（登记为 `IN-01`、`IN-02`…，只用于提炼规则，不进入证据库）。
- **动作**：
  1. 按 `assets/alignment-question-bank.json` 用宿主原生选择面问 **3-5 题**（每题 2-4 个选项、写清后果）：DSH 用 `ask_user_question`，Codex 用 `request_user_input`，Claude Code 用 `AskUserQuestion`。
  2. 用回答填 `assets/requirements-alignment-card-template.md`，产出 `00-alignment-card.md`：研究主题、`research_domain`、决策用途、`audience`、`stakeholder_view`、`deliverable_target`、必答问题（3-5 条）、`本轮不做`、时间窗、`scope.in/out`、指标体系（3-6 个可核查指标）、证据标准、可接受/拒收来源、深度档位（A 快扫 / B 标准 / C 深度）、成本预算、时间预算。
  3. 用户说"你定"时取问题库默认值，写进 `取默认值的字段`，状态记 `defaulted`；无原生选择工具时贴编号选项并停下，状态记 `unconfirmed`。
- **输出产物**：`00-alignment-card.md`；运行记录 `loop-run-record.md` 的 `Intent Core` 段。
- **完成判据**：状态为 `aligned` 或 `defaulted`；`research_domain`、决策用途、必答问题均非空；`本轮不做` ≥3 项；成本预算已写死。
- **失败与回退**：状态 `unconfirmed` → 停下等待，**不得进入 0.2 或阶段 1**；必答问题写成"全面了解该领域" → 视为未对齐，退回重写；用户中途改需求 → 更新卡片并检查已产出的 `EV` 是否作废。

### 3.2 阶段 0.2 领域研究简报

- **目标**：把已确认的对齐卡翻译成可执行的证据路线，判定 `research-needed`。
- **输入**：`00-alignment-card.md`（未 `aligned`/`defaulted` 不得开始）。
- **动作**：
  1. 从卡片抄录 `research_domain` / `audience` / `deliverable_target` / `stakeholder_view`，不得再自行改动；需要改动必须回到 0.1。
  2. 判定状态：属于本技能四类触发场景 → `research-needed`；否则回到通用能力处理，不启动本流程。
  3. 按 `references/intent-domain-research.md` 写 `Domain Research Brief`：`领域假设`（3-7 条，标 `unverified`）、`已知与未知`、`证据路线`、`不可得路径`。
  4. 定义 `success_criteria` 与 `stop_conditions`（可判定，不写"尽量全面"）。
  5. 产出 `multimodal-prompt-brief.md`：报告形态、图表清单（`kind` 只允许 bar/line/pie）、配色、字体、尺寸、交互、PDF 路线。
  6. 预置中英双语检索词表（各 ≥5 条，按 §2 五类意图铺开）。
- **输出产物**：`00-research-brief.md`（按 `assets/domain-research-brief-template.md`）、`multimodal-prompt-brief.md`（按 `assets/multimodal-prompt-brief-template.md`）。
- **完成判据**：四变量与卡片一致；`research_needed` 已判定；`scope.in/out` 非空；产出清单同时含 `report.md` 与 `report.html`；每条 `success_criteria` 都能被证据或产物判定。
- **失败与回退**：变量缺失 → 回到 0.1 提问，禁止猜测填空；用户拒绝给出 `audience` → 记为 `unspecified` 并在报告首屏声明该限制；状态为 `research-not-needed` → 终止并说明原因（不得半途产出报告）。

## 4. 阶段 1：广度候选检索（一级）

- **目标**：得到一个足够宽、来源类型均衡的候选池，此阶段**不写任何结论**。
- **输入**：`00-research-brief.md` 的检索词表与边界。
- **动作**：
  1. 用 `tvly` 跑英文式，用 `mcp__metaso__metaso_web_search` 跑中文式，双语并行、分别记录。
  2. 每条查询记录：`tool`、`query`、`hits`、`found_at`、`layer=一级`。
  3. 把命中写入 `01-candidate-sources.md`，逐条含：`cand_id`、标题、链接、域名、语言、来源桶、摘要线索、工具、检索式、在结果中的位次。
  4. 初步分桶：一手/官方、署名研究或行业媒体、垂直社区与从业者、微信公众号、其他在线内容。
  5. 排除明显不合格域（聚合站、内容农场、无日期页），但保留其链接供审计。
- **输出产物**：`01-candidate-sources.md`（≥20 条；领域确实窄时 ≥12 条并附窄因说明）。
- **完成判据**：候选数达阈值；**中英双语各 ≥3 条查询式（输入侧）**；中英文候选**占比各 ≥30%（产出侧）**；来源桶覆盖 ≥4 类；每条候选链接可点击。
  > 两条判据是**不同维度**，必须都满足：前者量的是"你搜得够不够宽"（查询式条数），后者量的是"搜回来的东西够不够均衡"（候选占比）。`release-gate.md` 只写了前者的数字，本条为准。
- **失败与回退**：候选不足 → 按 §2 改写查询式，最多 3 轮；仍不足 → 记录 `blocked_sources`，转入阶段 3 定向补充；检索额度受限 → 优先中文域铺量，全球域仅保留数据与一手来源查询。

## 5. 阶段 2：深度提取与认知地图（二级）

- **目标**：把候选页转成合格证据卡，并第一次形成结构化认知。
- **输入**：`01-candidate-sources.md`。
- **动作**：
  1. 排序候选：一手/官方 > 署名研究或行业媒体 > 垂直社区与从业者 > 其他；取前 10-20 条进入深度核对。
  2. 用 `mcp__metaso__metaso_web_reader` 或 `tvly extract` 取全文（不做关键词检索，直接给 URL）。
  3. 逐字摘取原文片段（≥15 字，可省略中间但不得改词），分配证据 ID：`EV-001`、`EV-002`…（三位递增、不跳号、不复用）。
  4. 为每条 `EV` 填齐 `evidence.md` 规定的字段，判定 `type`（共识结论/争议观点/案例/数据）、`credibility`（高/中/待验证）、`stance`。
  5. 构建认知地图 v1.0：主题分簇 → 节点=结论候选 → 节点挂 `EV` → 标注支撑/反驳边；写不清的节点标为缺口而不是删掉。
  6. 同步把证据写入 `report-payload.json` 的 `evidence[]`（字段名见 `assets/report-payload-template.json`），并记录 `rollback_count`（本阶段从 0 起算）。
- **输出产物**：`02-evidence-v1.0.md` + `report-payload.json.evidence[]`（版本 `v1.0`）、`03-cognition-map-v1.0.md`（版本 `v1.0`）。
- **完成判据**：每个主题簇至少 1 条 `EV`；每条 `EV` 的**十个字段**（`id`/`content`/`type`/`credibility`/`quote`/`source_title`/`url`/`retrieved_at`/`layer`/`tool`）齐全；地图每个节点要么绑 `EV`，要么显式标为缺口。
- **失败与回退**：页面取不到全文（付费墙/403/需登录）→ 换等价来源，并在 `blocked_sources` 记录失败输出；只有标题与摘要 → 不得升级为 `EV`，退回 `01-candidate-sources.md` 作为线索；证据类型严重倾斜（例如全为案例、无数据）→ 回退阶段 1 定向补该类型，回退次数 +1。

## 6. 阶段 3：反证验证与缺口补全（三级，含回退）

- **目标**：主动找反证、补齐交叉验证、把认知地图升级到可支撑结论的版本。
- **输入**：`02-evidence-v1.0.md`、`03-cognition-map-v1.0.md`。
- **动作**：
  1. 列出全部结论候选与争议点，逐条标注当前独立来源数。
  2. 交叉验证：为每条核心结论找到第 2 个**独立**来源（独立性判定见 `evidence.md` §4），更新交叉验证数。
  3. 反证检索：对每个争议点检索反方证据，补齐 `support` / `refute` 两侧。
  4. 三级定向补充（中文实操与反证主力）：用 `mcp__metaso__metaso_web_search` 加限定词 `site:mp.weixin.qq.com`，例如 `<主题> 落地 踩坑 site:mp.weixin.qq.com`、`<争议点> 反对 风险 site:mp.weixin.qq.com`；命中后用 `mcp__metaso__metaso_web_reader` 取全文，摘取实操细节与反证，`layer` 记 `三级`。
  5. 更新证据库到 `v2.0`、认知地图到 `v2.0`，产出 `04-counterevidence.md`：每条争议点列出正方 `EV` / 反方 `EV` / 双方共同承认的事实 / 尚未解决的分歧。
  6. 同步写入 payload 的 `disputes[]`（`pro` / `con` 各自带 `evidence`）。
- **输出产物**：`04-counterevidence.md`、`02-evidence-v2.0.md`（+ payload `evidence[]` v2.0）、`03-cognition-map-v2.0.md`。
- **完成判据**：每条核心结论独立来源 ≥2；每个争议点正反证据并列；关键数据有原始出处；`layer=三级` 至少有 1 条来自微信公众号的实操或反证证据（该领域确无中文实操内容时，必须写明检索式与空结果）。
- **失败与回退**：见 §7，逐条记录触发条件、回退层级、检索式、结果与次数。

## 7. 缺口回退触发条件（回退规则）

| 触发条件 | 回退目标层级 | 动作 | 上限 |
| --- | --- | --- | --- |
| 某结论独立来源 < 2 | 一级（补候选）或三级（定向） | 换同义词/上位词重搜，或用 `site:mp.weixin.qq.com` 定向找第二来源 | 同一结论 ≤3 次 |
| 争议只有单边证据 | 三级定向 | 以反方立场词重搜（"反对/质疑/失败/风险"），并优先找原始当事方说法 | 同一争议点 ≤3 次 |
| 关键数据无原始出处 | 二级 | 回到一手来源取全文，替换二手转述 `EV` | 同一数据 ≤2 次 |
| 认知地图存在孤立节点 | 一级 + 二级 | 为该节点补检索式与深度核对，或标注为缺口 | ≤2 次 |
| 证据类型分布失衡 | 一级 | 定向补缺失类型（数据/案例/争议） | ≤2 次 |

回退纪律：每次回退必须记录 `rollback_count` 的增量、触发条件、检索式原文与命中结果（`loop-run-record.md` 的 `Evidence Fetch` 段有回退明细表）；达到上限仍未补齐 → 把该结论降级为"待验证观察"或写入 `open_gaps`，并把 `Loop Decision` 记为 `blocked` 或 `none-with-reason`，**禁止**用"普遍认为"式表述绕过。

## 8. 证据库与认知地图的版本差异规则（v1.0 → v2.0）

| 对象 | 允许的变更 | 禁止的变更 |
| --- | --- | --- |
| 证据库（`02-evidence-v1.0.md` → `02-evidence-v2.0.md`，含 payload `evidence[]`） | 新增 `EV`（续编号，从 `EV-0NN` 继续）；更新 `credibility`、交叉验证数、`stance`、被引用位置、`checked_at`、`snapshot_path` | 删除记录、重编号、改写历史 `quote`、把 `待验证` 静默升为 `高` |
| 需剔除的 `EV` | 标记"已作废" + 作废原因（如来源失效），记录保留在原位 | 直接从文件中移除 |
| 认知地图（`03-cognition-map-v1.0.md` → `03-cognition-map-v2.0.md`，含 payload `mindmap`） | 新增节点、修正边、把争议节点补成双侧边、新增缺口标注 | 删除已绑 `EV` 的节点而不留说明 |
| 差异留痕 | 在 v2.0 文件末尾追加"v1.0 → v2.0 变更"小节：`新增/修正/降级/作废` 四类逐条列出，每条附 `EV` 或缺口编号 | 用"内容优化"一类模糊措辞替代逐条差异 |

版本号唯一来源是阶段进度：阶段 2 产出一律标 `v1.0`；只有经过阶段 3 回退与补全的版本才允许标 `v2.0`。未发生任何回退时，必须在 `loop-run-record.json` 的 `evidence_fetch.rollback_count` 记 0 并说明"无需回退"，而不是无依据地宣称 v2.0。

## 9. 阶段 4：信息取舍与双格式输出

**取舍规则**（先删后写，删掉的也必须留痕）：

| 保留 | 剔除 | 判定 |
| --- | --- | --- |
| 核心结论：`findings[]` 项，≥2 独立来源 | 单一来源且无法交叉验证的边角观察 | 移入证据库保留但不进正文，在 `Evidence Review` 写明未引用原因 |
| 关键数据：支撑结论的量级、增速、占比 | 无出处的数字、口径不明的百分比 | 无原始出处即剔除或降级 |
| 典型案例：能改变判断的 1-3 个实例 | 同质重复案例（保留最早/最权威的一个） | 同类 >3 个时按来源可信度择优 |
| 争议点：正反并列的完整表述 | 只有单边的争议描述 | 单边即回退阶段 3，不得写进正文 |
| 缺口：明确列出未补齐项 | 用模糊词掩盖的猜测 | 缺口必须显式呈现 |

**双格式输出顺序**（严格串行，禁止并行改两版）：

1. 先产出文档版 `report.md`（Markdown，按 `assets/document-report-template.md` 的模块骨架）：核心结论逐条绑定 `EV` 标签，每条附适用条件与反证情况。
2. 定稿前先把 `report.md` 的内容整理成 `report-payload.json`（结论、图表、争议、案例、证据、流程记录都以结构化字段表达；模板见 `assets/report-payload-template.json`）。
3. 再由 payload 生成 HTML：`python scripts/build_report.py --payload .\report-payload.json --out .\report.html --strict`，得到单文件离线 HTML（内嵌 SVG 图表、思维导图、流程图、证据链路；结论旁证据标签可点击跳转证据库；支持按类型与可信度筛选、关键词检索；样式与脚本全部内联）。
4. 最后跑**一致性校验**：逐节比对 `report.md` 与 `report.html`（结论句、数据、`EV` 编号、图表口径），输出 `consistency-check.md`；任何差异以文档版为准重新生成 HTML，禁止在 HTML 里单独"优化"措辞。

- **完成判据**：两版内容 100% 一致；HTML 中出现无证据 ID 的结论数 = 0（由 `--strict` 拦截）；断网可完整渲染。
- **失败与回退**：HTML 与文档版不一致 → 回退第 3 步重新生成；payload 校验报错（悬空引用、空 `evidence`）→ 回退阶段 3 补证据或删除该结论/图表；HTML 依赖外链 → 内联化后重测。

## 10. 阶段 5：证据归档与溯源备案

- **目标**：让任意一条结论在离线状态下都能一路点回原文片段与来源。
- **动作**：按 §11 结构归档；为每条 `EV` 保存证据快照（`snapshots/EV-0NN.html` 或 `.txt`，含标题、链接、提取时间、原文片段）；填写 `acceptance-run.md` 与 `loop-run-record.md`；把本轮验收证据放进 `evals/acceptance/runs/<run-id>/`（文件清单与字段见 `references/release-gate.md` §3）。
- **输出产物**：全部文件落盘，运行记录六段齐全，验收记录字段齐全，`next_run_reuse_key` 已填写。
- **完成判据**：目录结构完整；`EV` 与快照一一对应；`report.html` 中的证据标签在离线状态下可跳到证据库并显示原文片段；`Loop Decision` 已落盘为四选一。
- **失败与回退**：快照缺失 → 重新取全文并补快照；来源已失效 → 记 `checked_at` 与失效说明，该 `EV` 降级为 `待验证` 并在报告中标注；无法补齐 → `blocked`。

## 11. 归档目录结构

```
<deliverable_root>/
├── report.md                       # 阶段 4：文档版研究报告（Markdown）
├── report.html                     # 阶段 4：单文件离线 HTML 交互式报告
├── report-payload.json             # 阶段 4：HTML 生成输入，含 evidence[]/findings[]/charts[]
├── 00-research-brief.md            # 阶段 0：Domain Research Brief
├── multimodal-prompt-brief.md      # 阶段 0：多模态与工具路线简报
├── 01-candidate-sources.md         # 阶段 1：广度候选清单
├── 02-evidence-v1.0.md             # 阶段 2：证据库 v1.0
├── 02-evidence-v2.0.md             # 阶段 3：证据库 v2.0（含 v1.0 → v2.0 变更）
├── 03-cognition-map-v1.0.md        # 阶段 2：认知地图 v1.0
├── 03-cognition-map-v2.0.md        # 阶段 3：认知地图 v2.0
├── 04-counterevidence.md           # 阶段 3：反证表
├── consistency-check.md            # 阶段 4：双版一致性校验
├── acceptance-run.md               # 阶段 5：验收运行记录汇总
├── loop-run-record.md              # 阶段 5：六段闭环运行记录
├── loop-run-record.json            # 阶段 5：机器可读镜像（可选）
├── snapshots/                      # 证据快照
│   ├── EV-001.html
│   └── EV-002.html
└── proof/                          # 产物证据：Chrome 截图、PDF 等
    ├── report-top.png
    └── report-evidence-panel.png
```

`evals/acceptance/runs/<run-id>/` 与交付目录分开存放：前者是包作者自己的验收证据（baseline 对照），后者是本次交付物。

## 12. 阶段停止条件汇总

| 条件 | 停止点 | 必须做的动作 |
| --- | --- | --- |
| 状态判定为 `research-not-needed` | 阶段 0 | 结束本流程并说明理由 |
| `00-research-brief.md` 缺失或字段不全 | 阶段 0 之后 | 禁止进入阶段 1（对应评测 `No Domain Research Brief`） |
| 关键缺口未补搜（独立来源 < 2 等） | 阶段 3 | 回退补搜；达上限则降级表述或 `blocked`，不得推进阶段 4 |
| `build_report.py --strict` 报错 | 阶段 4 | 回退阶段 3 补证据或删除该结论/图表 |
| 一致性校验未通过 | 阶段 4 | 以文档版为准重新生成 HTML |
| 门禁任一项不通过 | 阶段 5 前 | 按 `references/release-gate.md` 处置并记录 `writeback` / `none-with-reason` |

包根目录校验命令（由包提供脚本，本手册只负责在验收记录中如实登记输出）：`python scripts/check_meta_skill_package.py .`、`python scripts/check_closed_loop.py .`。
