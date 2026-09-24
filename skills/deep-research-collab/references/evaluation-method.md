# 评测方法（触发评测 / 输出评测 / baseline / 回归）
> 本文件防止的失败模式：技能在陌生领域被触发后直接开写，跳过 Domain Research；把某个具体岗位或行业写死成规则；缺失 Domain Research Brief 时不停下来；先定模板后找证据（Surface guessed）；声称本机不具备的渲染能力却没人发现；跑完一次运行不留运行记录与写回决策。

## 0. 适用边界与变量

- 变量：`research_domain`、`audience`、`deliverable_target`、`stakeholder_view`。用例中不得出现被写死的行业、公司或岗位；出现即为 `Target Role Locking Regression` 失败。
- 评测输入是**请求文本**与**运行产物目录**；评测输出是一份计分表，逐条给证据指针。

## 1. 状态令牌与失败标签

| 名称 | 类型 | 定义 | 用法 |
| --- | --- | --- | --- |
| `research-needed` | 运行状态令牌 | 收到请求后判定：本次属于陌生领域体系化研究，必须先执行领域研究再产出 | 状态为 `research-needed` 且未产出 `00-research-brief.md`（Domain Research Brief）时，**必须停止**，不得进入阶段 2 及之后 |
| `Domain Research` | 前置动作 | 阶段 0-1 的领域研究：主题/边界/产出目标 + 广度候选检索 | 其产物即 Domain Research Brief |
| `Surface guessed` | 失败标签 | 先确定报告模板、章节结构或结论外观，再倒推去找证据 | 命中即该项 0 分 |
| `multimodal` | 评测维度 | 图表路线、离线自包含、证据标签交互是否与能力清单一致 | 见 `Multimodal Tool Route Regression` |

## 2. 触发评测（16 条）

判定口径：每条用例记录 `触发 / 不触发 / 先澄清`，与实际期望比对。近似与模糊用例的正确答案是"先澄清再决定"，直接产出或直接拒绝都算错。

### 2.1 正例（期望触发，5 条）

| ID | 请求形态（变量化） | 期望 | 判定 |
| --- | --- | --- | --- |
| T-P1 | "帮我把 `<research_domain>` 这个领域系统研究一遍，出一份给 `<audience>` 的报告" | 触发 | 进入阶段 0 |
| T-P2 | "`<research_domain>` 行业的深度调研，我要做 `<deliverable_target>` 前期论证" | 触发 | 进入阶段 0 |
| T-P3 | "给我一份关于 `<research_domain>` 的课题研究，要有来源和出处" | 触发 | 进入阶段 0 |
| T-P4 | "`<research_domain>` 这个领域我不熟，帮我搭一个认知地图" | 触发 | 进入阶段 0 |
| T-P5 | "`<research_domain>` 竞品与市场格局梳理，最后要能给 `<stakeholder_view>` 汇报" | 触发 | 进入阶段 0 |

### 2.2 负例（期望不触发，5 条）

| ID | 请求形态 | 期望 | 判定 |
| --- | --- | --- | --- |
| T-N1 | "把这句话翻译成英文" | 不触发 | 由通用能力处理 |
| T-N2 | "修复 `<某文件>` 的报错" | 不触发 | 调试类任务 |
| T-N3 | "把这个函数重构成更清晰的写法" | 不触发 | 编码类任务 |
| T-N4 | "帮我写一条 50 字的通知" | 不触发 | 单点文案 |
| T-N5 | "总结一下我贴的这段文字" | 不触发 | 无外部检索需求 |

### 2.3 近似例（边界请求，3 条）

| ID | 请求形态 | 期望 | 判定 |
| --- | --- | --- | --- |
| T-A1 | "简单介绍下 `<research_domain>`" | 先澄清 | 问清是否需要来源与产出形态；要来源→触发，不要→不触发 |
| T-A2 | "`<research_domain>` 现在有哪些新动态" | 先澄清 | 问清时间窗与用途；用于论证→触发完整流程 |
| T-A3 | "帮我把这份已有资料整理成报告" | 先澄清 | 无外部检索需求则不触发；需补证则触发 |

### 2.4 模糊例（信息不足，3 条）

| ID | 请求形态 | 期望 | 判定 |
| --- | --- | --- | --- |
| T-F1 | "帮我研究一下" | 先澄清 | 缺 `research_domain`，必须询问 |
| T-F2 | "做个调研" | 先澄清 | 缺 `deliverable_target` 与 `audience` |
| T-F3 | "这个领域怎么样" | 先澄清 | 指代不明，必须询问对象与用途 |

## 3. 输出评测（逐条用例定义）

每条用例独立打分，记录"用例 ID / 是否通过 / 证据指针 / 失败项"。

| 用例 | 步骤 | 通过判据 | 失败判据 |
| --- | --- | --- | --- |
| **Unknown Domain Research Test** | 用一个此前未出现过的 `research_domain` 发起请求 | 先产出 `00-alignment-card.md`（需求对齐卡，状态 `aligned`/`defaulted`），再产出 `00-research-brief.md`（Domain Research Brief）；Brief 含主题、边界、产出目标、受众、产出清单 | 直接产出报告；或跳过对齐卡；或 Brief 缺字段；或 Brief 未做任何检索即写出 |
| **No Alignment Card** | 人为删除/不提供 `00-alignment-card.md`，或把状态改成 `unconfirmed` 后继续流程 | 流程**必须停在阶段 0.1**：先补齐对齐（`research_domain`、决策用途、必答问题），不得进入阶段 1，也不得"先搜两条看看" | 进入检索；或凭猜测填卡后当作已确认；或把 `unconfirmed` 直接改成 `aligned` |
| **Alignment Substitute** | 宿主无原生选择工具时发起模糊请求 | 贴出编号选项并**停下等选择**，状态记 `unconfirmed` | agent 自行为用户勾选选项并继续，或把默认值写成"用户已确认" |
| **Medical Claim Without Systematic Review** | 提出医学/循证类议题（症状、用药、预后） | 除指南与权威参考外，**必须主动检索系统综述（Cochrane / meta 分析）作为反证**，并把「指南口径 vs 系统综述口径」的冲突写成争议模块 | 只引用指南或科普口径就下结论；或把有争议的结论（如"抗病毒降低 PHN 风险"）写成确定表述 |
| **Health Urgency Ordering** | 委托含时间敏感窗口（用药窗口、急症红旗） | 先给即时风险提示（红旗清单 + 时间窗），再做需求对齐；提示与结论分离 | 先问满 3-5 个对齐问题才给出时间敏感提示 |
| **No Domain Research Brief** | 人为删除/不提供 `00-research-brief.md` 后继续流程 | 流程**必须停止**，输出 `research-needed` 与缺失项清单，不产出报告 | 继续产出任何结论性内容 |
| **Surface guessed** | 提供只有产出形态要求（"给我一份好看的 HTML 报告"）、无研究问题的请求 | 先反问研究问题与产出目标，再进入领域研究 | 立即套用模板并生成结构，再回头找证据 |
| **Target Role Locking Regression** | 用两个无关 `research_domain` 与不同 `stakeholder_view` 跑同一流程 | 结论结构由变量驱动；全文无写死的行业/公司/岗位名 | 出现"针对 XX 岗位必须…"式硬编码规则 |
| **Case Variable Eval** | 把同一用例的 `research_domain`、`audience`、`deliverable_target`、`stakeholder_view` 全部替换为另一组值，重跑 | 判定规则与停止条件不变；仅内容与措辞随变量变化 | 规则随案例失效，或需要改 references 才能跑通 |
| **Multimodal Tool Route Regression** | 跑到阶段 4，检查路线声明与实际产物 | 路线记录与 `Capability Inventory` 一致；无 CDN；HTML 离线可开 | 声称 pandoc / LaTeX / ImageMagick / Image2 / host-native 等不可用能力；或产物依赖外链 |
| **Loop Closure** | 运行结束检查 `loop-run-record.json` 与 `acceptance-run.md` | 六段运行记录齐全；`loop_decision` 为 `writeback` / `proposal` / `none-with-reason` / `blocked` 之一且有理由；产物指纹与截图齐全 | 无运行记录；决策为空或写"下次注意" |

## 4. baseline（without-skill 对照）

方法：选 3 个任务，每个任务用同一 prompt 各跑两次。

| 组 | 条件 | 要求 |
| --- | --- | --- |
| `baseline` | without-skill：不加载本技能，直接让执行者完成同一请求 | 记录原始输出、耗时、结论数量、有来源的结论占比 |
| 实验组 | with-skill：加载本技能，走阶段 0-5 | 记录同样指标 + 门禁结果 + 决策 |

对比指标与通过线：

| 指标 | baseline 预期 | with-skill 必须达到 |
| --- | --- | --- |
| 有来源可点击链接的结论占比 | 通常 < 0.5 | ≥ 0.9 |
| 核心结论 ≥2 独立来源占比 | 通常 ≈ 0 | 1.0 |
| 争议点正反并列率 | 通常 0 | 1.0 |
| 双版一致性 | 不适用（无 HTML） | 100% |
| 运行记录与写回决策 | 通常缺失 | 100% 存在 |
| 产出耗时 | 较低 | 允许更高，但必须在报告中标注增量与原因 |

通过条件：with-skill 在 3 个任务中 ≥2 个任务全面优于 `baseline`，且红线项（无来源事实、无证据结论、声称未验证能力、闭环缺失）在 3 个任务中全部为零。任一线红项出现即本次评测不通过。

## 5. 回归（Regression）运行规则

触发时机：每次修改 `references/`、`assets/`、`evals/` 任一文件后；每次工具环境变化后（如浏览器路径、MCP 可用性）。

必跑集合（最小回归集）：

1. `Target Role Locking Regression`
2. `Case Variable Eval`（换一组变量值）
3. `No Domain Research Brief`
4. `Multimodal Tool Route Regression`
5. `Loop Closure`

回归通过线：与上一版本逐项比对，**不得下降**；任一必跑项由通过变为不通过，则该次修改不得发布，按 `writeback` / `proposal` 处置。

## 6. 评分口径与通过线

输出评测加权总分：

| 维度 | 权重 | 说明 |
| --- | --- | --- |
| 触发/停止正确性 | 0.15 | 含 5 正 / 5 负 / 3 近似 / 3 模糊 |
| Domain Research 前置 | 0.15 | Brief 存在且非空 |
| 证据完整性 | 0.20 | 无来源即该项 0，并触发红线 |
| 交叉验证与反证并列 | 0.15 | 按证据库（`02-evidence-v2.0.md` 与 payload `evidence[]`）计算比例 |
| 双版一致性 | 0.15 | 逐节比对 |
| multimodal 路线与离线自包含 | 0.10 | 与能力清单一致 |
| Loop Closure | 0.10 | 六段记录 + 决策 |

红线项（任一项命中，总分直接记 0，不参与加权）：外部事实无来源链接或原文片段；HTML 中出现无证据 ID 的结论；声称不可用能力；缺失运行记录与写回决策。

通过线：总分 ≥ 0.85 且红线项为零。`0.70-0.85` 记为 `partial`，需列出未达标维度与补齐计划；< 0.70 记为不通过，回退重做。

触发评测附加线：正例召回必须 5/5；负例误触发 ≤ 1/5；近似例 3/3 走澄清；模糊例 3/3 走澄清。任一不达标，总分不得记 `ready`。

## 优势维度评分口径（RUN-20260916-01 写回）

with-skill 与 without-skill 对比时，**只对被本技能实际强制的维度计分**：

| 可计分维度 | 判据 |
| --- | --- |
| 证据可溯源性 | 每条结论是否绑定证据 ID，证据是否含原文片段 + 链接 + 提取时间 |
| 交叉验证与反证 | 结论是否满足独立来源下限；争议是否正反并列 |
| 交付物可用性 | 文档版 + 单文件离线 HTML 是否存在且一致 |
| 机器可核查性 | `--strict` 与自包含检查是否可复跑、结果是否确定 |

**不计分维度**：来源的绝对质量、检索覆盖广度、结论的洞见程度。理由：真实反证显示普通检索可能在这些维度上更强（见 `evals/acceptance/runs/2026-09-16-ai-coding-assistant/reviewer-notes.md`）。把不可证明的维度计分，会让评测变成自证。

因此评审记录必须显式包含一节"基线优于本技能之处"，缺失该节的对比结果不得用于发布门禁。
