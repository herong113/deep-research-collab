# 证据卡与在线证据标准（Evidence Card Shape / Online Evidence Standard / Source Map）
> 本文件防止的失败模式：先有结论后补证据；用"业内普遍认为"代替可点击链接；把转载站、聚合页、AI 摘要页当成独立来源凑交叉验证；证据卡字段缺项，导致 HTML 报告出现无证据 ID 的结论而无人发现。

## 0. 适用边界与变量

- 变量：`research_domain`（研究领域）、`audience`（受众）、`deliverable_target`（交付目标）、`stakeholder_view`（干系人视角）。本文件所有规则对上述变量中立：换任何 `research_domain` 都成立。
- 本文件定义证据的"形状"与"合格线"；取证动作见 `references/research-workflow.md`；发布拦截见 `references/release-gate.md`；运行记录与写回见 `references/closed-loop-governance.md`。
- 唯一合法证据载体是证据库：人读形态为 Markdown 主表（模板 `assets/evidence-library-template.md`），机器形态为报告 payload 的 `evidence[]` 数组（模板 `assets/report-payload-template.json`）。报告正文与 HTML 不得存在两者之外的事实。

## 1. Evidence Card Shape（证据卡结构）

一条来自外部的可陈述事实 = 一张证据卡 = 一个证据 ID。ID 形如 `EV-001`、`EV-002`，三位十进制递增；不跳号、不复用、作废不回填编号。**ID 与字段名必须与 payload 的 `evidence[]` 条目一一对应**，否则 HTML 生成脚本无法校验引用。

| 中文名 | payload 键 | 必填 | 取值 / 格式 | 不合格示例 |
| --- | --- | --- | --- | --- |
| 证据编号 | `id` | 是 | `EV-\d{3}`，全局唯一 | `EV-1`、`EV-001a`、重号 |
| 信息内容 | `content` | 是 | 一句话可独立读懂的事实陈述，≤80 字 | "该领域非常火热" |
| 类型 | `type` | 是 | `共识结论` / `争议观点` / `案例` / `数据` | "其他"、留空 |
| 可信度 | `credibility` | 是 | `高` / `中` / `待验证`，口径见 §3 | 自造档位"较高" |
| 原文片段 | `quote` | 是 | 逐字原文，加引号，≥15 字，可在来源页搜索定位 | 改写过的转述、拼接句 |
| 来源标题 | `source_title` | 是 | 页面真实标题，非站点名 | "某网站" |
| 原始链接 | `url` | 是 | 以 `http` 开头的直达链接 | 首页、搜索结果页、短链 |
| 提取时间 | `retrieved_at` | 是 | `YYYY-MM-DD`（或 ISO 8601 带时区），为实际读取日 | 只写发布时间、留空 |
| 检索层级 | `layer` | 是 | `一级` / `二级` / `三级` | 留空 |
| 检索工具 | `tool` | 是 | 工具真名，见 §1.2 白名单 | "搜索引擎"、"AI" |
| 交叉验证数 | `cross_check_count` | 是（Markdown 主表必填；payload 可携带） | 整数 ≥1，含本条，按 §4 独立性计数 | 把同源转载计为 2 |
| 可信度判据 | `confidence_reason` | 是（Markdown 主表必填；payload 可携带） | 一句话写明为什么给这个可信度 | "感觉比较可靠" |

可选字段（出现即校验）：`stance`（`support` / `refute` / `neutral`，争议点并列时必填）、`checked_at`（链接复核日）、`snapshot_path`（证据快照相对路径）、`notes`（回退次数与原因）。

payload 中的最小证据条目（照抄可直接被 `scripts/build_report.py` 消费）：

```json
{ "id": "EV-001", "content": "信息内容", "type": "数据", "credibility": "高",
  "quote": "原文片段", "source_title": "来源标题", "url": "https://…",
  "retrieved_at": "2026-01-01", "layer": "一级", "tool": "mcp__metaso__metaso_web_search" }
```

### 1.1 引用检查（由 HTML 生成脚本强制）

`scripts/build_report.py --payload <report-payload.json> --out report.html --strict` 会检查：`findings[].evidence`、`charts[].evidence`、`cases[].evidence`、`disputes[].pro/con.evidence`、`mindmap` 各节点的 `evidence` 是否都存在于 `evidence[].id`。命中不存在或空引用即报错，`--strict` 下以非零退出。因此"悬空引用"不是靠人眼发现的，而是生成阶段就拦截。

### 1.2 工具真名白名单（照实写，不得虚构）

- 一级广度：`tvly search`（Tavily CLI，可执行文件名 `tvly`，不是 `tavily`）、`mcp__metaso__metaso_web_search`
- 二级深度：`mcp__metaso__metaso_web_reader`、`tvly extract`
- 三级定向：`mcp__metaso__metaso_web_search`（限定 `site:mp.weixin.qq.com`）+ `mcp__metaso__metaso_web_reader`
- 辅助（不得单独作为事实来源）：`mcp__metaso__metaso_chat`、`mcp__metaso__metaso_topic_list`、`mcp__metaso__metaso_topic_search`、`mcp__metaso__metaso_topic_file_content`

## 2. Online Evidence Standard（在线证据合格线）

一条在线证据同时满足以下四条才算合格，缺一条即 `credibility` 最高只能记 `待验证`，且不得进入核心结论：

1. **可访问链接**：`url` 能打开，且打开后 3 次检索内能定位到 `quote`。
2. **原文片段**：`quote` 为逐字原文，含上下文关键词；只允许省略号省略中间部分，不允许改词、不允许拼接多段。
3. **提取时间**：`retrieved_at` 为本次运行的真实读取日，与 `checked_at` 分离。
4. **来源可归属**：能写出对内容负责的主体（机构 / 作者 / 官方账号），且该主体非内容农场。

不算独立来源、不得用于凑 `cross_check_count` 的形态：

| 形态 | 判定 | 理由 |
| --- | --- | --- |
| 转载、镜像、聚合站 | 不计独立来源 | 与原发同源，一致不构成交叉验证 |
| 无日期的页面 | 不计独立来源 | 无法排除已失效结论 |
| AI 摘要页 / 问答生成页 | 不计独立来源，且不得作为唯一来源 | 无原文责任主体 |
| 搜索结果页、列表页 | 不合格证据 | 无稳定片段 |
| 短视频文案、口头转述 | `credibility` 最高 `待验证` | 无法逐字定位 |
| 同一机构的多篇稿件 | 计 1 个独立来源 | 同一责任主体 |
| 官方原始文件 / 一手数据 | 计 1 个独立来源，优先级最高 | 首选 |

判定顺序：先判"是否一手"，再判"责任主体是否独立"，最后判"链接与片段是否可定位"。任一步失败立即在 `notes` 记录失败原因，不得静默降级。

## 3. credibility 判定口径

- `高`：一手来源（官方文件、原始数据、当事方公告）且片段完整；或 ≥2 个独立来源一致。
- `中`：单一可信二手来源（署名研究、行业媒体），无相互矛盾证据。
- `待验证`：来源匿名、无日期、片段不完整、仅有转述，或存在未解决的反驳证据。
- 交叉验证数上限规则：`cross_check_count = 1` 时，`credibility` 不得为 `高`；只有 1 个独立来源的信息只能作为"待验证观察"。
- 争议双方各自独立记卡，`type` 均为 `争议观点`，`stance` 分别为 `support` / `refute`；**禁止**把双方合并成一张"存在争议"的卡。
- 每条证据必须能回答"为什么是这个可信度"（`confidence_reason`），写不出即降级。

## 4. Source Map（来源地图）

Source Map 承载来源分布，人读形态写在报告"三级搜索来源溯源"模块，机器形态对应 payload 的 `sources_stats`：`by_layer[{layer, tools[], count}]`、`by_type[{name, count}]`。

来源桶固定为：`一手/官方`、`署名研究或行业媒体`、`垂直社区与从业者`、`微信公众号`、`其他在线内容`。

独立性判定（逐条执行）：

1. 不同域名 + 不同责任主体 → 独立。
2. 不同域名 + 同一责任主体 → 同源，计 1。
3. 同域名不同路径 → 同源，计 1。
4. 内容高度重合（相同数据、相同措辞 ≥60%）→ 同源，计 1。
5. 无法判断责任主体 → 不计独立，标记 `待验证`。

Source Map 的硬约束：任一来源桶的独立来源数为 0 时，该桶所有证据不得支撑核心结论；`微信公众号` 桶必须至少有 1 条 `layer=三级` 证据，否则视为三级补充未执行（该领域确无中文实操内容时，必须写明检索式与空结果）。

## 5. Key Findings 汇总规则

`Key Findings`（核心发现）是从证据库到结论的唯一通道，与 payload 的 `findings[]` 一一对应：`id`（`F-1`、`F-2`…）、`module`（所属模块/分支）、`claim`（一句话结论）、`evidence`（`EV` 引用数组）、`confidence`（高/中/待验证）。

| 规则 | 判定 |
| --- | --- |
| 结论绑定 | 每条 `claim` 必须带 `evidence` 数组，至少 2 个 `EV`，且满足 §4 独立性；HTML 中结论旁证据标签可点击跳转到证据库 |
| 交叉验证 | 独立来源 < 2 的，只能降级为"待验证观察"，不得进入 `findings` |
| 争议并列 | 争议点必须正反并列，写入 payload 的 `disputes[]`（`pro` / `con` 各自带 `evidence`），缺一边即不合格 |
| 无证据不结论 | 允许三种写法：绑定证据的确定句、标注 `待验证` 的观察句、显式写出的缺口 |
| 双向可查 | 任一 `EV` 被哪些 `findings` / `charts` / `cases` / `mindmap` 节点引用，必须可反查；未被引用的 `EV` 要么标注"备查"，要么说明原因 |
| 充分度评级 | 报告概览必须给出 `evidence_sufficiency.grade`（`充分` / `基本充分` / `不足`）与理由，并写明该评级下结论可被使用到什么程度 |
| 领域拒收加严（医学/法律/金融，2026-09-16 写回） | 这三类领域中，**剂量、数额、期限、罚则等可执行数值只能用一手规范来源**（说明书、指南原文、法条/监管文件）；内容站/聚合站的同类数值一律拒收并在附录写明纠错记录。实测反例：中文科普站把普瑞巴林最大剂量写成 2400 mg/d（与说明书不符） |

## 6. Write-In Decision（写回决策）

一次运行结束后，只有以下四选一，且必须落盘（字段名与 `assets/loop-run-record-template.md` 一致）：

| 决策 | 触发条件 | 写到哪里 |
| --- | --- | --- |
| `writeback` | 出现可复用的新判定规则、新失败模式、新检索式模板，且已在本次运行中被验证 | `references/*.md` 追加规则；`evals/` 增补用例；`assets/` 增补模板或图表源数据 |
| `proposal` | 改进方向正确但未验证，或会改变包契约 | `evals/` 或包内提案记录，附验证计划，不直接改 references |
| `none-with-reason` | 本次运行无新增可复用知识，或知识只对单一 `research_domain` 成立 | 在运行记录中写 `none-with-reason` 与具体理由 |
| `blocked` | 存在未补齐的关键缺口、未解决的反证缺失、工具额度耗尽 | 写 `blocked`，附缺口清单与恢复所需条件 |

写回门槛（三者同时满足才允许 `writeback`）：可复用（换 `research_domain` 仍成立）、已验证（有本次运行的运行证据或产物证据）、非重复（不与现有条目语义重合）。

`none-with-reason` 是合法结论，不是失败；**禁止**为了显得有产出而写空泛规则。写回内容不得复制外部命名、页面结构、视觉系统、提示词、示例或商业话术，边界见 `references/source-abstraction-boundary.md`。
