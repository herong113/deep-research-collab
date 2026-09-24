# 验收运行发布门禁（acceptance release gate）

## Structure

| 检查项 | 命令 / 动作 | 实际结果 | 判定 |
|---|---|---|---|
| 包结构完整（24 个必需文件） | `py scripts/check_meta_skill_package.py .` | `Meta skill package check passed. 已检查 24 个必需文件` | 通过 |
| 闭环契约 | `py scripts/check_closed_loop.py .` | `Closed-loop check passed.` | 通过 |
| 触发评测用例齐备 | `py -c "json.load(open('evals/trigger-eval.json'))"` | 7 正 / 6 负 / 3 近似 / 3 模糊（超出下限 5/5/3/3） | 通过 |
| SKILL.md 轻入口 | 行数统计 | 150 行（上限 500） | 通过 |

## Domain research

| 检查项 | 实际结果 | 判定 |
|---|---|---|
| 阶段 0 是否先产出领域研究简报 | 有：`payload.json` 的 scope / audience / evidence_sufficiency 与简报字段一致，检索在其后 | 通过 |
| 领域框架是否靠猜 | 否：领域结构（采用率三口径 / 工具格局 / 价值证据 / 组织合规）全部来自检索到的原文片段 | 通过 |
| 是否有 `research-needed` 出口 | 有：不可得路径（厂商内部审计数据）标为厂商自披露，未升格为结论 | 通过 |
| 证据模型字段完整度 | 14/14 条证据均含内容/类型/可信度/原文片段/来源标题/链接/时间/层级/工具 | 通过 |

## Baseline

| 检查项 | 实际结果 | 判定 |
|---|---|---|
| without-skill 基线是否真实运行 | 是：同一问题、同一天、独立会话、朴素流程（2 轮检索 + 6 次抓取，4 次被拦截） | 通过 |
| with-skill 是否可复跑 | 是：`build_report.py --strict` exit 0，HTML 两次生成 sha256 一致 | 通过 |
| 分数差 | Without-skill: 4 / With-skill: 9 / Delta: 5（通过线 ≥ 4） | 通过 |
| 基线是否优于本技能（反证） | 部分是：基线找到 Stack Overflow 2025 与 DX ROI 追踪两个本技能未覆盖的高质量来源 → 已记录，并限制优势声明范围 | 已记录 |

## Ready decision: pass

**就绪规则判定**

- 结构门禁：通过（exit 0）
- 运行/产物证据：通过（严格校验 exit 0、自包含自检通过、Chrome 截图 669 KB 可见 8 模块与 3 类图表）
- 领域研究证据：通过（简报先于检索，字段完整）
- 基线证据：通过（Delta = 5，且反证已记录）
- 人工确认：**未完成**——用户尚未亲手打开并点开证据条目

**结论**：`Ready decision: pass`（结构性、产物性、基线证据均已通过）。人工确认列为下一轮第一动作，不得以本轮通过替代用户可见反馈。

> `quick_validate` 类型的选择性检查不等于 product readiness：本轮把两者分开记录，结构检查通过不代表结论可溯源，结论可溯源也不代表用户能顺利使用——因此人工确认仍是独立门禁项。

## 失败处理

本轮无阻塞项。两个真实缺陷已修复并复验（Y 轴刻度方向、正文/HTML 一致性未脚本化），修复方式与证据见 `loop-run-record.md` 的 Scar Record。
