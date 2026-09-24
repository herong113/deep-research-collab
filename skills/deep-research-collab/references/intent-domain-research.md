# 意图领域研究（intent-domain-research）
> 本文件防止的失败模式：调研一开始就凭模型记忆空写领域框架，把猜测当已知，导致后续所有检索、报告结构、图表都建立在未验证的领域假设上，最后交出一份看起来完整但证据链断裂的报告。

## 1. 适用位置

本文件只服务一个位置：**阶段 0.1 需求对齐之后、阶段 1 广度候选检索之前**。阶段 0.1 负责和用户把需求固定成 `00-alignment-card.md`（主题 / 边界 / 产出目标 / 必答问题 / 证据标准 / 成本预算，状态须为 `aligned` 或 `defaulted`）；本文件负责把它翻译成"可执行的证据路线"。阶段 1 的任何一次检索都必须能指回本文件产出的 `Domain Research Brief` 中某一条。

**前置硬条件**：`00-alignment-card.md` 状态为 `unconfirmed` 时，本文件不得开始撰写——先回阶段 0.1 完成对齐。

执行顺序（不得跳步）：

```
阶段0.1 需求对齐（需求对齐卡：主题/边界/产出目标/必答问题/证据标准/成本预算，经用户确认或显式取默认）
  → Local capability inventory（本机能做什么、不能做什么）
  → Domain Research Brief（含领域假设、已知/未知、证据路线、不可得路径）
  → Network Research Gate（联网事实先 Fetch 再判定）
  → Research-To-Design Chain（研究结论 → 报告结构 → 图表选择）
  → 阶段1 广度候选检索
```

## 2. No Guessing Rule

**No Guessing Rule：在阶段 1 完成之前，不得把任何"领域框架、术语体系、指标口径、玩家名单、市场规模、监管要求"写成确定表述。** 属于猜测的内容只能进 `Domain Research Brief` 的 `领域假设` 字段，并标 `unverified`。

判定规则（逐条自检，任一命中即判定为"猜测"，必须改写）：

| 自检问题 | 命中即 | 允许的写法 |
| --- | --- | --- |
| 这条领域结论我能不能给出原始链接 + 原文片段？ | 不能 | 只能写进 `领域假设`，标 `unverified` |
| 我用的这个词（术语/指标名）是不是 `research_domain` 里的原生说法？ | 不确定 | 标 `term-unconfirmed`，在阶段 1 用一次检索确认原文术语 |
| 我给出的数量级（规模/增速/占比）有来源吗？ | 没有 | 禁止出现该数字；改写为"待证据：需要 X 口径的规模数据" |
| 这条框架是不是我从别的行业迁移过来的？ | 是 | 必须写明迁移来源与迁移风险，标 `analogy-unverified` |
| 我说"通常/一般/业内普遍"时,背后是几条独立来源？ | < 2 | 删掉"通常/一般/业内普遍",改成具体证据 ID 或删除整句 |

`Local capability inventory` 与 `No Guessing Rule` 的关系：本机没有的能力不要假设它有。凡是在证据路线里写了"通过 X 工具获取"，X 必须出现在 `Local capability inventory` 中且 `状态=可用`；否则该路径直接进 `不可得路径`。

## 3. Domain Research Brief

开场先写这份 brief。它是**写给用户看的一页纸**（因此同时是 product-design 中"3 分钟可见结果"的载体），字段固定如下，缺失即不合格。

| 字段 | 必须写什么 | 缺失后果 |
| --- | --- | --- |
| `原始意图` | 用户原话（逐字引用，不改写）＋ 一句话意图转述 ＋ 意图类型（体系化认知 / 决策支持 / 内容生产 / 课题论证） | 后续所有取舍失去判据，报告会写成"百科"而不是回答用户问题 |
| `领域假设` | 3–7 条对 `research_domain` 的假设；每条标 `unverified` / `verified(EV-xxx)`；禁止写成结论 | 猜测被当成已知，污染全部下游结论 |
| `已知与未知` | `已知`：用户提供或本地可读的信息（材料、数据、内部文档）；`未知`：必须先检索才能写的清单，每条写成可检索的问题 | 无法生成检索词，阶段 1 变成随机搜索 |
| `证据路线` | 三级搜索协同的分工：一级广度（`tvly` 全球域 + 秘塔中文域）→ 二级深度（`mcp__metaso__metaso_web_reader` / `tvly extract`）→ 三级缺口（微信公众号：秘塔搜索限定 `site:mp.weixin.qq.com`，再 web_reader 取全文）；每条路线写清目标问题、预期证据类型、成本 | 检索无目标，成本失控（秘塔约 3 积分/次） |
| `不可得路径` | 明确列出**拿不到**的证据及原因：付费墙、需登录、无中文源、官方未公开、本机无对应工具；每条给出替代动作（换口径 / 改用二手源并降级可信度 / 标 `research-needed`） | 研究中途才发现取不到，导致关键缺口被悄悄跳过 |
| `输出目标` | `deliverable_target`、`audience`、`stakeholder_view`、篇幅上限、必须回答的问题清单（**逐字沿用 `00-alignment-card.md` 的已确认值**，不得在此处重新解释） | 报告结构与受众错配，双交付物无法对齐 |
| `能力与成本边界` | 秘塔积分成本（每次检索约 3 积分）、Tavily 额度上限、本机渲染/浏览器能力、本轮预算内可承受的检索次数上限（**取对齐卡的 `成本预算`**，超预算先回报） | 中途额度耗尽，研究停在半成品状态 |

字段示例（示例领域仅作示例，不进入规则）：

```yaml
原始意图: "老板让我下周讲一下 AI 编程工具这个赛道"（逐字）
意图转述: 为一次内部汇报建立该赛道的体系化认知并给出选型建议
意图类型: 体系化认知 + 决策支持
领域假设:
  - "该赛道可按'IDE 内嵌 / 终端 Agent / 平台化'分类"  # unverified
  - "国内有独立于海外的产品形态"                        # unverified
已知与未知:
  已知: [用户已付费使用 1 个工具, 内部有 3 份试用记录]
  未知: ["主流产品的能力边界差异", "企业采购时的合规约束", "定价结构"]
证据路线: 见第 5 节三级分工表
不可得路径:
  - "厂商内部路线图"（未公开）→ 替代：用公开版本日志推断，标 可信度=中
  - "付费报告原文"（需付费）→ 替代：只用可引用的免费摘要，标 待验证
输出目标: deliverable_target=报告+HTML 双版; audience=管理层; stakeholder_view=采购决策视角
能力与成本边界: 秘塔检索 ≤ 20 次（约 60 积分）; Tavily 单轮 ≤ 5 次; 本机 Chrome 可用
```

## 4. Network Research Gate（Fetch Before）

**Network Research Gate：任何来自联网的事实，在写入结论之前必须先 Fetch。** 无 Fetch 不得写结论。

判定口径（`Online evidence read` 判定，四项全过才算一次合格的 Online evidence read）：

| 判定项 | 通过条件 | 不通过时 |
| --- | --- | --- |
| 可访问原始链接 | `原始链接` 是可直接打开的 URL，且 Fetch 成功返回正文 | 视为未读；降级为"线索"，不得生成 EV |
| 有原文片段 | 抄录了支撑结论的**原文句子**（非转述、非摘要、非模型改写） | 视为未读，不得生成 EV |
| 有可归因主体 | 作者或机构名可识别（个人署名、媒体名、机构名三者之一） | 标 `可信度=待验证` |
| 有时间戳 | 页面发布时间可识别 | 标 `时间未确认`，并在报告中提示时效风险 |

操作规则：

1. `Fetch Before` 是先决条件。搜索摘要（snippet）只能用于**排候选**，不能用于写结论。
2. 二次引用（A 引用 B）必须 Fetch 到 B；Fetch 不到 B 时，写"A 称 B 报告显示…"并降级，禁止写成原始事实。
3. 深读工具：`mcp__metaso__metaso_web_reader` 用于中文页与公众号页；`tvly extract` 用于英文页与批量正文抽取。
4. Fetch 失败（403 / 付费墙 / 动态渲染失败）→ 记入 `不可得路径`，不得用记忆补全内容。

## 5. 三级搜索协同的分工表

| 层级 | 目的 | 工具（真名） | 输出 | 停止条件 |
| --- | --- | --- | --- | --- |
| 一级 广度发现 | 找到候选来源与领域语汇 | `tvly`（Tavily CLI，全球域）；`mcp__metaso__metaso_web_search`（中文域） | 一级候选来源清单 | 新检索不再产生新来源即停；或触及成本上限 |
| 二级 深度核对 | 把候选变成合格证据 | `mcp__metaso__metaso_web_reader`；`tvly extract` | 证据库 v1.0（EV-001…） | 每个待答问题至少 2 条独立来源，或标记缺口 |
| 三级 缺口补充 | 反证、实操细节、中文一手实践 | 秘塔搜索限定 `site:mp.weixin.qq.com` → `mcp__metaso__metaso_web_reader` 取全文 | 反证清单 + 实操补充证据 | 缺口清单清空，或每条剩余缺口有明确的 `research-needed` 记录 |

知识与经验类问题可用 `mcp__metaso__metaso_chat` 与 `mcp__metaso__metaso_topic_list` / `mcp__metaso__metaso_topic_search` / `mcp__metaso__metaso_topic_file_content`（专题库内检索与原文下载）。**注意**：`metaso_chat` 的输出是**线索**，不是证据；凡是要写入报告的事实，仍必须走 `Fetch Before`。

## 6. research-needed：证据不足时的唯一合法出口

**判定规则**：以下任一成立，该问题必须标记 `research-needed` 并**停止为该问题写结论**。

- 该问题下合格的 `Online evidence read` 数量 < 2；
- 现有来源互相矛盾且尚未取到第三方；
- 关键口径（指标定义、统计范围）无法从任何来源确认；
- 三级补搜的收获为零（检索词已换 3 种以上仍无新来源）。

`research-needed` 记录字段（固定）：

| 字段 | 说明 |
| --- | --- |
| `question` | 待答问题，一句话 |
| `attempted_queries` | 已试检索词与层级（一级/二级/三级） |
| `sources_seen` | 已见来源与失败原因（付费墙/无正文/口径不符） |
| `blocking_reason` | 为什么不足：来源数不足 / 口径不明 / 相互矛盾 |
| `next_action` | 下一步具体动作（换语言 / 换关键词 / 找替代口径 / 问用户补材料） |
| `owner` | 谁来做：本技能继续 / 需要用户补充材料 |

`research-needed` 在输出中的表现：文档版写成"待补证"小节；HTML 版连同证据标签一起渲染为 `待补证` 徽标。禁止把 `research-needed` 的问题写成确定性结论，也禁止悄悄删除该问题。

## 7. Research-To-Design Chain

**Research-To-Design Chain：研究结论 → 报告结构 → 图表选择。三步单向流动，每一步只允许引用上一步已存在的产物。**

| 步 | 输入 | 输出 | 完成判据 | 违反时的表现 |
| --- | --- | --- | --- | --- |
| 1 结论 | 证据库（EV 列表） | `conclusions[]`：每条含 `claim`、`bound_evidence_ids`、`confidence`、`type`（共识结论 / 争议观点 / 案例 / 数据） | 每条 `claim` 至少绑定 1 个 EV；核心结论 ≥ 2 个独立 EV | 出现无 EV 的结论 |
| 2 结构 | `conclusions[]` | 报告章节树：每章 = 一个论证目标，章内列出该章要回答的问题与对应 EV | 每个章节能指回至少 1 条 `claim`；无 `claim` 支撑的章节删除或标 `research-needed` | 章节按"看起来专业"的模板排，与结论无关 |
| 3 图表 | 章节树 + `conclusions[].type` | 图表清单：每图＝图类型 + 数据来源 EV + 一句话结论 | 图表选择表（见下）命中，且每图有 EV 来源 | 图表是装饰，无法回溯到证据 |

图表选择表（本包统一口径）：

| 结论类型 | 首选图形 | 说明 |
| --- | --- | --- |
| 阶段 / 决策链 / 转化路径 | 流程图 | 节点写阶段名，节点附 EV 标签 |
| 分类体系 / 概念关系 | 思维导图 | 分支层级 ≤ 3，叶子节点尽量挂 EV |
| 多主体同维度对比 | 对比表 | 每个单元格可标注来源；HTML 版做成可筛选表 |
| 时间 / 版本 / 事件演进 | 时间线 | 每个时间点带日期与来源 |
| 两个维度的定位 | 矩阵 | 轴定义必须来自证据，不能自造 |
| 数量 / 占比（有来源） | 柱状图 / 饼图 | 无来源的量级禁止作图 |
| 争议点 | 正反对置面板 | 左右各挂证据 ID，禁止只画一方 |

跨步禁令（Hard Stop）：**不得先定模板再找证据**。若发现自己在"先画好一个漂亮框架，再去填证据"，立刻回退到步 1，把框架降级为 `领域假设`。

## 8. Local capability inventory

字段（固定，逐条实测填写，禁止凭印象）：

| 字段 | 必须写什么 | 示例值（示例） |
| --- | --- | --- |
| `capability` | 能力用途，一句话 | 生成 HTML→PDF 版报告 |
| `name` / `version` | 工具或程序真名与版本 | `tvly` / tavily-cli 0.1.8 |
| `invoke` | 具体调用方式（命令或工具名） | `tvly extract <url>` |
| `input` / `output` | 输入形态与输出形态 | `url list` → `json` |
| `limits` | 明确限制（语言、长度、并发、需登录） | 单次 ≤ N 条 URL；需网络 |
| `cost` | 成本口径 | 秘塔：约 3 积分/次检索；Tavily：计费额度上限 |
| `usable` | `可用` / `部分可用` / `不可用` | `可用` |
| `fallback` | 不可用或超限时的替代动作 | 超限 → 降级为二级精读，减少一级轮次 |

实测参考（写入 brief 前应重新验证一次，环境可能变化）：

- `tvly`（Tavily CLI，可执行文件名是 `tvly`，**不是** `tavily`）：本机可用，`tvly --version` 返回 `tavily-cli 0.1.8`。用途：一级广度发现（全球域）、`tvly extract` 二级正文抽取。成本：受 Tavily 计划额度上限约束。
- 秘塔 MCP：`mcp__metaso__metaso_web_search`、`mcp__metaso__metaso_web_reader`、`mcp__metaso__metaso_chat`、`mcp__metaso__metaso_topic_list`、`mcp__metaso__metaso_topic_search`、`mcp__metaso__metaso_topic_file_content`。用途：一级中文域广度、二级中文/公众号深读、专题库内检索。成本：每次检索约 3 积分。
- Chrome：本机存在（`C:\Program Files\Google\Chrome\Application\chrome.exe`），可做 HTML→PDF 与截图。用途：交付物归档与版式核验。
- 文档版报告：Markdown。
- `python`：**当前不在 PATH 中**（探测结果 NOT FOUND）。包根目录校验命令 `python scripts/check_meta_skill_package.py .` 与 `python scripts/check_closed_loop.py .` 如无法直接执行，先用 `py -3 --version` 或本机 Python 绝对路径确认解释器，再执行；不得因为"命令报 not found"而宣称已通过校验。

## 9. 停止条件汇总

| 条件 | 动作 |
| --- | --- |
| `Local capability inventory` 未实测填写 | 不得开始阶段 1 |
| `Domain Research Brief` 任一必填字段为空 | 不得进入阶段 1 |
| 某事实无 `Online evidence read` | 不得写成结论；转 `research-needed` |
| 某问题 `research-needed` 未补搜 | 不得推进到阶段 4 输出（关键缺口未补搜不得推进） |
| 本机能力不支持某证据路线 | 写入 `不可得路径` 并给替代动作，不得静默跳过 |
| 预算（积分/额度）接近上限 | 停止新增检索，转入阶段 4，并在报告中披露证据覆盖度 |
