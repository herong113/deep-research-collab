# 多模态产物与工具路由（Capability Inventory / Multimodal Brief Contract / Route Selection Rule / Downgrade proof）
> 本文件防止的失败模式：声称本机不具备的渲染能力（pandoc、LaTeX、Image2 等）并据此交付；用 CDN 让"离线 HTML"实际无法离线打开；图表数据无来源、无法回溯到证据库；降级时不留任何证据，把"没做"说成"做了"。

## 0. 适用边界与变量

- 变量：`research_domain`、`audience`、`deliverable_target`、`stakeholder_view`。
- 本文件只回答两件事：本机**能做什么**（照实写，不得编造）、在多个可行路线之间**怎么选**并留下什么证据。
- 证据字段与报告结构见 `references/evidence.md`；发布拦截见 `references/release-gate.md`。

## 1. Capability Inventory（本机能力清单，照实写）

| 能力 | 状态 | 具体形态 | 可验证方式 |
| --- | --- | --- | --- |
| Python 3.14 运行时 | 可用 | 标准库 + 已装第三方包 | `python -c "import sys;print(sys.version)"` |
| python-docx | 可用 | 生成 `.docx` | `python -c "import docx;print(docx.__version__)"` |
| openpyxl | 可用 | 生成 `.xlsx` 图表源数据/表格 | `python -c "import openpyxl;print(openpyxl.__version__)"` |
| python-pptx | 可用 | 生成 `.pptx` | `python -c "import pptx;print(pptx.__version__)"` |
| markdown | 可用 | Markdown → HTML 片段 | `python -c "import markdown;print(markdown.__version__)"` |
| Pillow | 可用 | 位图读取/裁剪/合成/格式转换 | `python -c "import PIL;print(PIL.__version__)"` |
| Python 标准库单文件 HTML | 可用 | **HTML 报告路线**：`python scripts/build_report.py --payload <report-payload.json> --out report.html`，纯标准库生成单文件 HTML，图表用内嵌 SVG（`kind` 只允许 `bar` / `line` / `pie`），样式内联 `<style>`，交互用内联 `<script>`，**不依赖 CDN**；`--strict` 下证据引用不合法即非零退出 | 断网后 Chrome 直接打开 `report.html`；`--strict` 退出码 0 |
| Chrome | 可用 | `--headless=new --print-to-pdf`、`--screenshot` | `chrome --version`；产物文件字节数 > 0 |
| Edge | 可用 | 同上，作为 Chrome 不可用时的等价替代 | `msedge --version` |
| `tvly` CLI | 可用 | Tavily 检索与 `tvly extract` | `tvly --help` |
| 秘塔 MCP | 可用 | `mcp__metaso__metaso_web_search` / `metaso_web_reader` / `metaso_chat` / `metaso_topic_list` / `metaso_topic_search` / `metaso_topic_file_content` | 工具调用返回内容 |

**不可用（必须照实声明，不得假装可用）**：

| 能力 | 状态 | 影响 | 替代路线 |
| --- | --- | --- | --- |
| pandoc | 不可用 | 无通用 Markdown→docx/pdf 转换 | `.docx` 用 python-docx 直接生成；`.pdf` 用 Chrome 打印 HTML |
| LibreOffice / soffice | 不可用 | 无无头文档转换 | 同上 |
| wkhtmltopdf | 不可用 | 无 HTML→PDF 命令行转换 | Chrome/Edge `--headless=new --print-to-pdf` |
| LaTeX | 不可用 | 无排版级 PDF | 不需要；报告版式由 HTML+CSS 承担 |
| typst | 不可用 | 无 typst 排版 | 同上 |
| ImageMagick | 不可用 | 无命令行图像处理 | Pillow 覆盖裁剪/缩放/格式转换 |
| **Image2 / host-native（图片生成类能力）** | **不可用** | 无法生成插画、封面、示意图位图 | 一律改为**内嵌 SVG 程序化绘制**（流程图、思维导图、证据链路、柱/折线/矩阵图）；确需位图时用 Chrome `--screenshot` 对自绘 HTML 截图 |
| CDN / 在线字体 / 在线 JS 库 | 不可依赖 | 会破坏"单文件离线"要求 | 全部内联；字体只用系统字体栈 |

## 2. Multimodal Brief Contract（多模态需求契约）

阶段 0 必须产出 `multimodal-prompt-brief.md`（按 `assets/multimodal-prompt-brief-template.md`），字段如下（缺字段视为阶段 0 未完成）：

| 字段 | 必填 | 取值/示例 | 约束 |
| --- | --- | --- | --- |
| `report_form` | 是 | `离线单文件 HTML + Markdown` | 由 `deliverable_target` 推导，固定双版 |
| `audience` | 是 | `<audience 变量>` | 决定信息密度与术语层级 |
| `stakeholder_view` | 是 | `<stakeholder_view 变量>` | 决定首页先给什么 |
| `chart_list` | 是 | 列表：`id`（`C-1`…）、`kind`（`bar`/`line`/`pie`）、`title`、`unit`、`evidence`（`EV` 数组）、`caption` | 落到 payload 的 `charts[]`；`evidence` 必填且可回溯到 `evidence[].id` |
| `palette` | 是 | 主色/辅色/强调色/证据色各一个十六进制值 | 自己定义，不得复制外部视觉系统；对比度 ≥ 4.5:1 |
| `font_stack` | 是 | `system-ui, "Segoe UI", "Microsoft YaHei", sans-serif` | 只用系统字体，禁止在线字体 |
| `sizes` | 是 | 画布宽度、PDF 页面尺寸（如 A4 纵向）、单文件大小目标 | 单文件 HTML 目标 ≤ 3 MB |
| `interaction` | 是 | 证据标签跳转、类型筛选、可信度筛选、关键词检索 | 交互必须内联脚本实现 |
| `pdf_route` | 是 | `chrome-headless` / `edge-headless` / `不产出 PDF` | 与能力清单一致 |

`chart_list` 数量规则：核心结论数 ≥3 时至少 1 张思维导图或流程图 + 1 张数据图；证据数 ≥8 时必须有证据链路图（来源分层/类型分布）。图形载体统一为 payload 的 `mindmap` 与 `charts[]`，由 `scripts/build_report.py` 渲染为内嵌 SVG；不产出独立图片文件作为唯一载体（避免双份数据源）。

## 3. Route Selection Rule（路线选择规则）

按顺序判定，命中即停，**不得跳级**：

1. **本地确定性脚本**（Python 标准库 / Pillow / python-docx 等）：只要能力清单标记"可用"且结果可复现，一律优先。适用于全部 HTML/SVG 生成、图表、docx/xlsx/pptx、图片裁剪。
2. **宿主原生**：宿主直接提供且不依赖外网的能力（文件读写、进程调用本机 Chrome/Edge、CLI）。适用于 HTML→PDF（Chrome `--headless=new --print-to-pdf`）与截图（`--screenshot`）。
3. **MCP / 在线**：仅用于**取数**（检索与取全文），不用于渲染。可用于 `mcp__metaso__*` 与 `tvly`。
4. **降级**：前三级都无法满足时，采用降级形态并留下 `Downgrade proof`（见 §5）。

强制条款：

- 禁止使用能力清单标记"不可用"的工具；禁止以"通常环境里应该有"为理由调用 pandoc / LaTeX / ImageMagick / Image2。
- 每个产物必须在 `loop-run-record.json` 的 `product_surface.route` 中记录实际使用的路线与该路线的判定依据。
- 任一次调用失败后不得静默改路线：必须记录失败输出，再按顺序降一级。

## 4. Output evidence（产物证据要求）

每个产物必须同时具备以下四类可核对证据，缺一类视为未产出：

| 证据类型 | 具体形式 | 落盘位置 |
| --- | --- | --- |
| 存在性与体量 | 文件相对路径 + 字节数（`Length`） | `loop-run-record.json.product_surface.artifacts[]` |
| 指纹 | 每个产物的 SHA-256 | 同上 |
| 渲染证据 | Chrome/Edge 截图命令与输出路径、退出码 | `loop-run-record.json.product_surface.render_proof` |
| 校验输出 | 命令原文 + 实际输出（如 `python scripts/check_meta_skill_package.py .`、`python scripts/check_closed_loop.py .`、`python scripts/build_report.py --payload … --strict` 的退出码） | `acceptance-run.md` |

命令示例（照抄可用）：

```powershell
# 1) 由 payload 生成单文件离线 HTML（--strict：证据引用不合法则非零退出）
python scripts/build_report.py --payload .\report-payload.json --out .\report.html --strict
# 2) 单文件 HTML 生成后：体量与指纹
Get-Item .\report.html | Select-Object FullName, Length
(Get-FileHash .\report.html -Algorithm SHA256).Hash
# 3) 离线渲染证据（截图 + PDF）
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --window-size=1440,2400 --screenshot="$PWD\proof\report-top.png" "file:///$($PWD.Path -replace '\\','/')/report.html"
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="$PWD\report.pdf" "file:///$($PWD.Path -replace '\\','/')/report.html"
```

截图必须覆盖：报告首页、图表区、证据库区（证明标签可跳转）。

## 5. Image2 / host-native 与 Downgrade proof

- **Image2 / host-native 图片生成在本机不可用**。任何"用 Image2 出图""由宿主原生生成配图"的表述都是不合格声称。
- 替代路线顺序：① 内嵌 SVG 程序化绘制（首选，可缩放、可筛选、可带 `data-ev` 属性）；② HTML+CSS 绘制后用 Chrome `--screenshot` 出位图；③ Pillow 合成/裁切已有位图。三条都不可行时，文字化描述并在报告中显式标注该图形缺失。
- **Downgrade proof（降级证明）** —— 只要本条路线低于 `Route Selection Rule` 的第 1 级，就必须留下以下全部内容，写入 `loop-run-record.json.product_surface.downgrades[]`：

| 字段 | 含义 | 必填 |
| --- | --- | --- |
| `capability_missing` | 缺失的能力名（写实，如 `Image2 / host-native`） | 是 |
| `attempted` | 已尝试的命令与完整失败输出 | 是 |
| `route_used` | 实际使用的替代路线（1/2/3/降级） | 是 |
| `limitation` | 替代路线明确不能做到的事 | 是 |
| `artifact_evidence` | 替代产物的路径 + 字节数 + 截图路径 | 是 |
| `human_confirmed` | 人工确认人/时间 | 是 |

- 禁止声称未验证的能力：出现"支持导出 PPT/PDF/图片"之类表述时，必须在同一段落给出对应的命令与实际产物证据；拿不出即视为失败，按 `references/release-gate.md` 第九、十一项处置。
