# 发布门禁与验收（发布门禁 / 十四项门禁 / 证据扫查 / 验收运行记录 / 就绪规则）
> 本文件防止的失败模式：报告写得很顺但结论没有来源；HTML 与文档版内容不一致却当作交付；用"看起来完整"替代逐项核对；门禁失败后不写回、不记录，下次重复同一个错误。

## 0. 适用边界与变量

- 变量：`research_domain`、`audience`、`deliverable_target`、`stakeholder_view`。
- 门禁在阶段 4 产出后、阶段 5 归档前执行一次；任一门禁不通过即**不得交付**。
- 证据字段见 `references/evidence.md`；运行记录见 `references/closed-loop-governance.md`；工具能力见 `references/multimodal-tooling.md`。

## 1. 十四项门禁

判定只有两个结果：`通过` / `不通过`。没有"基本通过"。

| # | 门禁 | 必须通过 | 证据 | 不通过的处置 |
| --- | --- | --- | --- | --- |
| 1 | 结构 | 六段运行记录齐全：`Intent Core` / `Evidence Fetch` / `Product Surface` / `Package Contract` / `Evidence Review` / `Loop Decision`，且字段非空 | `loop-run-record.json` 全量字段 | 回退补记；无法补记则 `blocked` |
| 2 | 领域研究 | 存在 `00-research-brief.md`（Domain Research Brief），含主题/边界/`deliverable_target`/受众/产出清单 | `00-research-brief.md` 路径 + 字节数 | 回退阶段 0，禁止继续 |
| 3 | 证据完整性 | 每条外部事实有 `EV` 卡；`url` + `quote` + `retrieved_at` 三项齐全；无来源即不合格 | 证据库（`02-evidence-v2.0.md` + payload `evidence[]`）逐条校验输出 | 删除该事实或补搜；缺项条目不得留在正文 |
| 4 | 交叉验证 | 每条核心结论 `findings[]` ≥2 个独立来源（按 Source Map 独立性规则） | `findings[]` ↔ `evidence[]` 映射 + 交叉验证数 | 降级为 `待验证` 观察句或回退阶段 3 |
| 5 | 反证并列 | 每条 `争议观点` 同时有 `support` 与 `refute` 的证据；payload `disputes[].pro/con.evidence` 均非空；单边即不合格 | 证据库按 `type` 分组输出 | 回退阶段 3 定向补搜反证 |
| 6 | 认知地图 | `03-cognition-map-v2.0.md` 与证据库的 `EV` 引用双向一致，无孤立节点 | 地图中的 `EV` 集合 = 证据库 `EV` 集合 | 回退阶段 2 重建地图 |
| 7 | 文档版报告 | `report.md` 为 Markdown，`findings[]` 结论均带 `EV` 标签，无占位符残留（`TODO`/`XXX`/`<待补>`） | 文件路径 + 全文扫查输出 | 回退阶段 4 重写 |
| 8 | HTML 报告 | `report.html` 单文件可离线打开；含内嵌 SVG 图表与证据链路；结论旁 `EV` 标签可点击跳转；支持按类型/可信度筛选与关键词检索 | 浏览器截图 + 交互截图 | 回退重生成；不得只修文字说明 |
| 9 | 双版一致性 | `report.md` 与 `report.html` 内容 100% 一致（结论句、数据、`EV` 编号、图表口径） | `consistency-check.md`（逐节比对清单） | 以文档版为准重新生成 HTML |
| 10 | 图表数据可溯源 | 每张图表的 `evidence` 非空且指向 `evidence[].id`，每个数值可回溯到 `EV-xxx` | `report-payload.json` 的 `charts[]` + `evidence[]`；`build_report.py --strict` 输出 | 删除该图表或补来源 |
| 11 | 离线自包含 | 无 CDN / 在线字体 / 外链脚本；断网可完整渲染 | 全文搜索 `http` 协议外链资源 + 断网截图 | 内联化后重测 |
| 12 | 闭环记录 | `loop_decision` 四选一已落盘（`writeback` / `proposal` / `none-with-reason` / `blocked`），含理由 | `loop-run-record.json.loop_decision` 或 `loop-run-record.md` 第 6 节 | 补记；无理由视为不通过 |
| 13 | 验收运行记录 | 存在 `acceptance-run.md`，字段齐全，命令与真实输出对应 | `acceptance-run.md` | 重跑并如实记录 |
| 14 | 人类确认 | `audience` / `stakeholder_view` 对应的确认人已确认关键结论与交付形态 | 确认人、时间、确认范围 | 挂起交付，标记 `partial` |

门禁 14 之外，附加一条**原创边界**检查（不单独占编号，作为门禁 9 的前置）：全文不得出现外部材料的命名体系、页面结构、视觉系统、提示词、示例、商业话术；判定方法见 `references/source-abstraction-boundary.md`。

## 2. 证据扫查（Evidence Sweep）

发布前对 `report.md` 与 `report.html` 各执行一次，记录命令与实际输出：

1. **孤儿结论扫查**：抓取两版中所有结论句，检查是否都带 `EV-\d{3}` 标签。任一结论无标签 → 不合格。
2. **悬空引用扫查**：抓取正文全部 `EV-\d{3}`，与证据库的 `id` 集合求差集。差集非空 → 不合格；先跑 `python scripts/build_report.py --payload .\report-payload.json --out .\report.html --strict` 让脚本先拦一遍。
3. **未引用证据扫查**：证据库中存在但正文与 payload 未引用的 `EV`，允许保留，但必须在 `Evidence Review` 中逐条写明"未引用原因"或标"备查"。
4. **链接抽样复核**：随机抽 20%（不少于 5 条）的 `source_url` 重开一次，确认 `snippet` 仍可定位；失败条目降级为 `待验证` 并记录 `checked_at`。
5. **一致性扫查**：按节比对 `report.md` 与 `report.html`，输出"节标题 | 结论逐字一致 Y/N | 数据一致 Y/N"清单。

示例命令（只读检查，不改产物）：

```powershell
# 悬空引用扫查（示意：正文 EV 集合 vs 证据库 EV 集合）
Select-String -Path .\report.md, .\report.html -Pattern 'EV-\d{3}' -AllMatches |
  ForEach-Object { $_.Matches.Value } | Sort-Object -Unique
```

## 3. 验收运行记录

验收运行记录有两种形态，缺一不可：

**① 运行目录**（可被脚本校验的验收证据）：`evals/acceptance/runs/<run-id>/`，必需 7 个文件，每个文件非空且不少于 120 字符：

| 文件 | 内容要求 |
| --- | --- |
| `input.md` | 本次运行的原始请求与四个变量取值 |
| `evidence-sweep.md` | 证据扫查结果，按来源类别分列，含反证（Counterevidence）栏 |
| `without-skill-output.md` | `baseline` 组（不加载本技能）的原始输出 |
| `with-skill-output.md` | 实验组输出，必须出现 `Domain Research Brief`、`Evidence sweep`、`Skillization Decision` 三项 |
| `reviewer-notes.md` | 必须含可解析的评分行：`Without-skill: <整数>`、`With-skill: <整数>`、`Delta: <整数>`，且 `Delta ≥ 4`；含 `Pass / partial / fail` 判定 |
| `release-gate.md` | 必须含 `Structure`、`Domain research`、`Baseline`、`Ready decision`；`Ready decision` 只能是 `pass` 或 `partial`；若提到 `quick_validate`，必须同时写明 `product readiness`，两者不得混为一谈 |
| `validation.md` | 实际执行的命令与真实输出，含 `Validation` 与 `Result` |

校验命令：`python scripts/check_acceptance_runs.py <run_dir>`（逐条对照上表；结构不合法即非零退出）。

**② 交付目录汇总表**（人读）：交付目录根下 `acceptance-run.md`，对照 `assets/acceptance-run-template.md` 填写，必需字段：

| 字段 | 内容 |
| --- | --- |
| `run_id` | 本次运行标识（与运行目录名一致） |
| `research_domain` / `audience` / `deliverable_target` / `stakeholder_view` | 四个变量的实际取值 |
| `baseline` 对照 | `Without-skill` / `With-skill` / `Delta` 三个整数（与 `reviewer-notes.md` 一致），口径见 `references/evaluation-method.md` |
| 命令与输出 | 逐条列出执行的命令原文 + 真实输出（含 `python scripts/check_meta_skill_package.py .`、`python scripts/check_closed_loop.py .`、`python scripts/build_report.py --payload … --strict` 的退出码） |
| 门禁结果表 | 十四项逐项 `通过/不通过` + 证据指针 |
| 产物指纹 | 每个产物的路径、字节数、SHA-256 |
| 渲染证据 | 截图路径、PDF 路径（若有）、浏览器与版本 |
| 降级记录 | 若发生降级，附 `Downgrade proof` 字段（见 multimodal-tooling） |
| 未解决缺口 | 缺口描述、影响范围、恢复条件 |
| 确认记录 | 确认人、时间、确认范围 |

禁止把"预计""应该""已按要求"写进验收记录；只写实际执行过的命令与真实输出。评分行必须来自真实评测，不得倒推填写。

## 4. 就绪规则（ready / partial / blocked）

| 状态 | 判定条件 | 允许动作 |
| --- | --- | --- |
| `ready` | 十四项门禁全通过，且无未解决缺口 | 交付并归档；写 `writeback` 或 `none-with-reason` |
| `partial` | 非红线门禁不通过（如门禁 14 未确认、门禁 10 单张图表待补来源），但已明确标注缺口与影响 | 交付时必须在报告首屏列出"未完成项与影响"，且不得对外称已完成 |
| `blocked` | 任一红线门禁不通过：3 证据完整性、4 交叉验证、5 反证并列、9 双版一致性、11 离线自包含、12 闭环记录 | 停止交付；写 `blocked` 与恢复条件 |

红线门禁定义不可协商；把红线项记为 `partial` 视为本次运行失败。

## 5. 失败时的 writeback 或 none-with-reason

每次运行（含失败运行）都必须落在四选一决策上：

- 门禁暴露了**可复用的判定漏洞**（例如某类来源系统性被误判为独立来源）→ `writeback`：更新 `references/evidence.md` 的独立性规则，并在 `evals/` 增加对应用例。
- 改进方向成立但**未验证**或会改动包契约 → `proposal`：写入 `evals/` 或包内提案记录，附验证计划。
- 本次失败只由**偶发外因**造成（如某站临时不可访问）且无可复用新知 → `none-with-reason`：写明具体理由与不写回的依据。
- 缺口无法在本次补齐（额度耗尽、来源不可达且无替代）→ `blocked`：列出缺口清单、已尝试的检索式、恢复所需条件。

禁止以"下次注意"作为结论；禁止无理由的 `writeback`。

## 6. 优势声明边界（RUN-20260916-01 写回）

门禁同时管住**怎么宣称收益**。本技能的可证明优势只有一条：**可核查结构**（证据卡、独立来源计数、正反对置、脚本校验、双交付物、运行记录）。

- 禁止宣称"本技能找到的来源比普通检索更好"。真实反证：一次 without-skill 基线运行找到了本技能漏掉的 Stack Overflow 2025 开发者调查与 DX 的 ROI 追踪，实质内容更贴决策。
- 只允许宣称：同一问题下，结论是否**可点开到原文片段**、是否**通过独立来源下限**、是否**有正反证据**、产物是否**可离线复现**。
- 因此发布门禁的 Baseline 栏必须同时记录"基线优于本技能之处"；只写分数的 Baseline 视为不合格证据。
- 由此派生一条硬要求：阶段 1 的完成判据包含**输入侧**的"中英双语各 ≥ 3 条查询式"，避免因查询式过窄漏检一手来源；它与**产出侧**的"中英文候选占比各 ≥30%"是两条不同判据，必须都满足（口径见 `research-workflow.md` §4）。（本次运行只用了 2 条，记入 proposal 待验证）
