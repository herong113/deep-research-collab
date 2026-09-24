# Changelog

本文件记录**为什么改**，不只是改了什么。版本号与 `skills/deep-research-collab/SKILL.md` 的 `metadata.version` 保持一致。

## [0.2.0] - 2026-09-24

本轮为「可发布」打磨：补齐出生证、修掉一个交付物缺陷、把门禁变成外人可复跑的命令。

### 修复

- **私有路径泄漏**：`evals/acceptance/runs/2026-09-16-ai-coding-assistant/with-skill-output.md` 里写着本机绝对路径 `C:\Users\<用户名>\Desktop\DSH 测试\runs\...`。改为占位符 `<run-root>/`。**原因**：公开 Skill 不得携带作者本机路径；这也是本技能自己出生证清单的必备项。
- **单文件 HTML 在手机宽度下排版崩坏**（真实缺陷，实测定位）：产物只有两条 `@media (max-width: 900px)`，分别处理 `.grid-2` 与 `.matrix`，**没有任何一条处理 248px 的固定侧栏**。真实 390px 视口（clientWidth 375）下正文只剩 `375−248=127px`。
  - 新增移动端断点：侧栏与顶栏转为静态、导航转两列、正文占满宽度。
  - **踩到的第二个坑**：断点最初放在 `.main` 之后，被样式表**后面**的 `.doc-foot { margin-left: 248px }` 按同特异性盖掉，整页仍横向溢出 37px。已把移动端规则移到样式表**末尾**（所有组件规则之后），并在注释里写明这条顺序约束。
  - **宽表溢出**：`.data-table` 内容最小宽度实测约 620px（阶段名 + `.nowrap` 时间戳列），390px 下把整页撑宽 285px。新增 `@media screen and (max-width: 900px)` 让表格自身横向滚动；作用域限定 `screen`，打印分页规则不受影响。
  - **修复后实测**：横向溢出在 320 / 360 / 390 / 414 / 768 / 1024 / 1440 七个宽度**全部为 0**；桌面 1440 渲染与修复前**逐字节相同**（无回归）。
- **版本号两处不一致**：`SKILL.md` frontmatter 没有版本，`evals/trigger-eval.json` 写 `0.1.0`。现统一为 `0.2.0`，并在 frontmatter 补 `metadata.version`。

### 新增

- `README.md`：安装前销售页 + 安装后操作入口（此前仓库无任何安装说明，无法被理解为一件可安装的资产）。
- `LICENSE`（MIT）。
- `CHANGELOG.md`（本文件）。
- `.claude-plugin/marketplace.json`：plugin marketplace 双通道。
- `SKILL.md` frontmatter 补 `whenToUse`（DeepSeek Harness 单独解析并用于触发提示）。

### 验证方式（可复跑）

```bash
# 四道结构门禁
python skills/deep-research-collab/scripts/check_meta_skill_package.py skills/deep-research-collab
python skills/deep-research-collab/scripts/check_closed_loop.py skills/deep-research-collab
python skills/deep-research-collab/scripts/check_acceptance_runs.py skills/deep-research-collab/evals/acceptance/runs/2026-09-16-ai-coding-assistant

# 严格校验 + 样例可复现（同 payload 两次生成必须逐字节一致）
python skills/deep-research-collab/scripts/build_report.py \
  --payload skills/deep-research-collab/examples/example-report-payload.json \
  --out /tmp/report.html --strict
```

### 收尾前仍需人工完成

- `LICENSE` 与 README 徽章里的 `herong113` 占位符需替换为真实 GitHub 用户名。
- `examples/report-sample.html` 的截图需在 390 / 1440 双宽度重新录制并挂进 README。

## [0.1.0] - 2026-09-16

首个可用版本：五阶段流程、三级检索协同、证据 ID 体系、双交付物（Markdown + 单文件离线 HTML）、四道结构门禁、闭环治理与写回决策，以及一次完整的 acceptance run（without-skill 4 / with-skill 9 / Δ5，并在 release gate 中记录了不利于本技能的反证）。
