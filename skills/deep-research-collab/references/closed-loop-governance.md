# 闭环治理（闭环定义 / 阶段契约 / 写回决策 / 证据分层 / 漂移信号 / nextRunReuseKey）
> 本文件防止的失败模式：研究做完就结束，经验留在会话里没有落盘；把静态校验通过当成运行成功；把产物截图当成人工确认；四选一决策写成"下次注意"；下一次运行重复同一个失败而不自知。

## 0. 适用边界与变量

- 变量：`research_domain`、`audience`、`deliverable_target`、`stakeholder_view`。
- 本文件定义一次运行如何被记录、被证据化、被写回，并在下一次运行被复用。

## 1. 闭环定义

一次闭环 = 一次完整的运行从意图到决策的**可核对链条**，且链条的下一圈能读到上一圈的结论。判定标准（四条全满足才算闭环成立）：

1. 有 `Intent Core`：意图被写清，含四个变量取值与产出目标。
2. 有 `Evidence Fetch`：取证过程可追溯（层级、工具、检索式、命中数、`EV` 编号）。
3. 有 `Product Surface` + `Package Contract`：产物存在且有指纹与结构校验结果。
4. 有 `Evidence Review` + `Loop Decision`：有复核结论，并落在四选一决策上。

断链判定：任一段缺字段、或该段内容与其他段矛盾（例如 `Evidence Review` 称一致而 `acceptance-run.md` 无不一致比对记录），闭环不成立，本次运行不得记 `ready`。

## 2. 阶段契约（六段运行记录）

运行记录固定落盘为交付目录下的 `loop-run-record.md`（由 `assets/loop-run-record-template.md` 落地；需要机器可读镜像时另存 `loop-run-record.json`，字段名同名）。六段缺一段即门禁 1 不通过。段名对应关系：模板第 5 段写作 `Verification Evidence`，与本文件的 `Evidence Review` 是同一段，两个名字都必须能对上。

| 段 | 目的 | 必填字段 | 完成判据 | 缺失后果 |
| --- | --- | --- | --- | --- |
| **Intent Core** | 锁定意图，防止跑偏 | `run_id`、`research_domain`、`audience`、`deliverable_target`、`stakeholder_view`、`research_needed`（`research-needed` 或 `research-not-needed`）、`inputs[]`（吸收清单 `IN-nn`）、`success_criteria[]`、`stop_conditions[]` | 四个变量均有具体取值；`success_criteria` 可判定 | 不得进入阶段 1（回到阶段 0） |
| **Evidence Fetch** | 记录取证过程 | `tiers[]`（`tier`、`tool`、`query`、`hits`）、`evidence_count`、`source_map_ref`、`rollback_count`、`blocked_sources[]` | 三级搜索层级均有记录，或写明某级未执行的原因 | 证据不可追溯，门禁 3 不通过 |
| **Product Surface** | 记录产物与路线 | `artifacts[]`（`path`、`bytes`、`sha256`）、`route`、`render_proof`、`downgrades[]` | 每个产物有路径 + 字节数 + SHA-256；渲染有截图或明确未产出原因 | 门禁 8/10/11 无法判定 |
| **Package Contract** | 记录包结构与校验 | `structure_check`（命令 + 输出）、`closed_loop_check`（命令 + 输出）、`gate_results[]`（十四项逐项） | 校验命令真实执行且输出被记录 | 门禁 13 不通过 |
| **Evidence Review**（模板名 `Verification Evidence`） | 复核证据与一致性 | `sweep`（孤儿结论/悬空引用/未引用证据/链接抽样）、`consistency`（逐节比对）、`open_gaps[]`、`human_confirmation` | 四项扫查均有输出；不一致项已处置 | 门禁 9 不通过 |
| **Loop Decision** | 决定下一圈 | `decision`、`reason`、`targets[]`、`nextRunReuseKey`、`decided_at` | `decision` ∈ {`writeback`,`proposal`,`none-with-reason`,`blocked`} 且有具体理由 | 门禁 12 不通过 |

## 3. 写回决策（四选一判定口径）

按顺序判定，命中即停：

| 顺序 | 决策 | 触发条件（须同时满足） | 落盘动作 |
| --- | --- | --- | --- |
| 1 | `blocked` | 存在关键缺口（核心结论独立来源 < 2 / 争议单边 / 关键数据无原始出处）且本次无法补齐（来源不可达、额度耗尽、需外部授权） | 写 `blocked` + 缺口清单 + 已尝试检索式 + 恢复条件；不得交付完整结论 |
| 2 | `writeback` | 有可复用新知，且满足：换 `research_domain` 仍成立、已由本次运行证据或产物证明、与现有条目无语义重复 | 更新 `references/*.md` / `evals/` / `assets/`，并记录被更新条目与理由 |
| 3 | `proposal` | 改进方向成立但**未验证**，或会改变包契约（新增流程阶段、变更字段、变更交付形态） | 记录提案 + 验证计划 + 影响面，不直接改 references |
| 4 | `none-with-reason` | 本次无新增可复用知识，或新知只对单一案例成立 | 写 `none-with-reason` + 具体理由（说明为何上述三条都不成立） |

强制条款：

- `writeback` 的内容必须经过 `references/source-abstraction-boundary.md` 的抽象三问；未过三问的一律改为 `none-with-reason`。
- 禁止把 `blocked` 用于"懒得补搜"；`blocked` 必须附上已尝试的检索式与失败输出。
- 每次运行只能有一个最终决策；过程中的临时判断写入 `Evidence Review.open_gaps`，不写进 `decision`。

## 4. 证据分层（四层不得互相替代）

| 层级 | 名称 | 形式 | 能证明什么 | 不能证明什么 |
| --- | --- | --- | --- | --- |
| L1 | 结构校验 | `python scripts/check_meta_skill_package.py .`、`python scripts/check_closed_loop.py .` 的输出 | 包结构与闭环字段合规 | 不能证明研究做对了 |
| L2 | 运行证据 | `loop-run-record.json` 的六段记录、检索式、命中数、回退次数 | 过程真实发生过 | 不能证明产物质量 |
| L3 | 产物证据 | 文件路径 + 字节数 + SHA-256 + 截图 + PDF | 产物存在且形态符合声明 | 不能证明内容正确 |
| L4 | 人工确认 | 确认人、时间、确认范围（关键结论与交付形态） | 结论对 `audience` / `stakeholder_view` 有效 | 不能替代 L1-L3 |

替代禁止：L1 通过不得推断 L3 存在；L3 存在不得推断 L4 已确认；L4 确认不得推断 L2 记录完整。汇报时必须逐层标注"已具备/缺失"。

## 5. 漂移信号清单

出现任一信号即启动处置，不允许"记录后忽略"。

| 信号 | 检出方式 | 处置 |
| --- | --- | --- |
| 误触发 | 触发评测负例被触发 | 收敛触发条件，写 `writeback` 或 `proposal` |
| 漏触发 | 正例未触发 | 同上 |
| 结论无证据 | 证据扫查发现无 `EV` 标签的结论 | 立即停止交付，回退阶段 2-3 |
| 图表数据无来源 | payload `charts[].series[].values` 无法回溯 `evidence[].id` | `build_report.py --strict` 已拦截；删除图表或补来源 |
| 双版不一致 | 逐节比对出现差异 | 以文档版为准重生成 HTML |
| 声称未验证能力 | 出现 pandoc / LaTeX / ImageMagick / Image2 / host-native 等表述，或声称具备未实测能力 | 撤回表述，按 `Downgrade proof` 补齐证据 |
| 闭环缺失 | 六段记录缺段或 `decision` 为空 | 补记；无法补记则 `blocked` |
| 规则僵化 | 用第二个 `research_domain` 跑同一流程失败 | 触发 `Case Variable Eval`，改写为变量驱动 |
| 形式复制 | 出现外部命名/结构/视觉/提示词/示例/话术 | 按原创边界重写 |

## 6. 原创循环与原创边界

- **原创循环**：`Intent Core` → 取证 → 产物 → 复核 → 抽象 → `writeback`/`proposal` → 下一圈复用。每一圈必须至少新增或合并一条可判定规则；否则本圈标记 `none-with-reason`。
- **原创边界**：只带走"规则"，不带走"形式"。判定方法（抽象三问）与禁止复制清单见 `references/source-abstraction-boundary.md`。
- 循环质量的唯一指标：下一圈在**不读上一圈会话记录**的情况下，仅凭包内文件即可复现上一圈的判定。

## 7. nextRunReuseKey 命名规则

用途：让下一次运行能定位并复用本次已验证有效的检索路径（有效检索式、高价值来源、图表源数据结构、写回条目）。

格式（与 `assets/loop-run-record-template.md` 第 8 节一致）：

```
drc-{domain_abbr}-{topic}-{source_type}-{YYYYMMDD}
```

| 片段 | 生成规则 |
| --- | --- |
| `drc` | 固定前缀，标识本技能包，全小写 |
| `domain_abbr` | `research_domain` 归一化：保留字母/数字/汉字，空格与标点替换为 `-`，连续 `-` 合并，去首尾 `-`，上限 16 字符 |
| `topic` | 本轮议题缩写，取自 `deliverable_target` 的核心名词，上限 12 字符 |
| `source_type` | 下一轮优先复用的来源类型，只允许 `official` / `research` / `practitioner` / `wechat` / `mixed` |
| `YYYYMMDD` | 该复用键首次登记日期（用于时效判定） |

规则：

1. **字段别名**：治理文件与门禁命令使用契约名 `nextRunReuseKey`；运行记录、报告附录与模板使用落盘名 `next_run_reuse_key`。两者是同一个字段，值必须逐字相同。
2. **可复现**：同一议题在同一天重复登记必须得到同一个 key；跨天重新登记时只允许 `YYYYMMDD` 段不同。
3. **时效**：登记后 90 天内可直接复用；超过 90 天必须重新抽检 ≥20% 的来源链接，并在运行记录写明抽检结果。
4. **禁止**：包含会话 ID、个人信息、真实 URL、外部材料名称或外部命名体系；不得用"最新""综合"一类无信息量的词充当 `topic`。
5. **复用前提**：key 必须与"已跑过的无效关键词""已验证有效来源""下一轮第一动作""复用前提"四项同段记录，单独一个 key 不构成可复用资产。

## 8. loop-run-record.json 结构骨架

人读记录按 `assets/loop-run-record-template.md` 填写；机器可读镜像如下（段名与模板章节同名，第 5 段用模板名 `verification_evidence`，即本文件的 `Evidence Review`）：

```json
{
  "run_id": "<run_id>",
  "intent_core": {
    "research_domain": "<变量>", "audience": "<变量>",
    "deliverable_target": "<变量>", "stakeholder_view": "<变量>",
    "research_needed": "research-needed",
    "scope": { "in": [], "out": [] },
    "inputs": ["IN-01"], "success_criteria": [], "stop_conditions": []
  },
  "evidence_fetch": { "tiers": [], "evidence_count": 0, "source_map_ref": "report-payload.json#sources_stats", "rollback_count": 0, "blocked_sources": [] },
  "product_surface": { "artifacts": [], "route": {}, "render_proof": [], "downgrades": [] },
  "package_contract": { "structure_check": "", "closed_loop_check": "", "gate_results": [] },
  "verification_evidence": { "sweep": {}, "consistency": {}, "open_gaps": [], "human_confirmation": {} },
  "loop_decision": { "decision": "none-with-reason", "reason": "", "targets": [], "next_run_reuse_key": "", "decided_at": "" },
  "scar_record": { "scars": [], "avoid_next_time": [] }
}
```

骨架中的 `decision` 只允许四选一取值；写其他值视为门禁 12 不通过。
