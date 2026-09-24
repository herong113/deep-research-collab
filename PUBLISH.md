# 发布清单（把本目录变成一个公开的 Agent Skill 仓库）

本目录已经是**结构完整、可安装、可自验**的 Skill 仓库。发布只差两步：填上你的 GitHub 用户名、推送。

## 0. 发布前状态（已实测，无需重做）

| 检查 | 结果 |
|---|---|
| 技能包结构门禁 | 5/5 通过（`python skills/deep-research-collab/scripts/verify-all.py`） |
| 报告生成 `--strict` | 通过；同一 payload 两次生成逐字节一致 |
| 样例可点击溯源 | 16 条证据外链 / 14 个真实独立域名 / 0 个 `example.com` |
| 零 CDN 依赖 | 通过（0 个外部资源加载，图表为内联 SVG） |
| 私有路径 / 凭据 | 全包 0 命中 |
| **安装形状** | **已用 `npx skills add <本地路径>` 实测：`Local path validated` → `Found 1 skill` → 45/45 文件就位 → 装出的副本自跑门禁 5/5** |
| 79 个宿主探测 | 成功（universal + symlink 分类正常） |

## 1. 填上你的用户名（唯一占位符）

```powershell
# 在仓库根执行；把 <你的GitHub用户名> 换掉
python scripts/set-owner.py <你的GitHub用户名>
```

脚本会替换 README.md(3) / CHANGELOG.md(1) / .claude-plugin/marketplace.json(5) 里共 **9 处** `<OWNER>`，并打印替换处数。
先看会改什么：`python scripts/set-owner.py <用户名> --dry-run`

> 用 `grep -r '<OWNER>'` 自查时还会命中 `PUBLISH.md` 与 `scripts/set-owner.py`——那两处是在**描述**这个占位符，不是待替换项。以脚本报告的处数为准。

## 2. 建立本地仓库并提交

```powershell
git init
git add -A
git -c user.name="<你的名字>" -c user.email="<你的邮箱>" commit -m "feat: deep-research-collab 0.2.0 - evidence-grounded deep research with clickable provenance"
```

> 本机没有配置全局 git 身份（`user.name`/`user.email` 均为空），所以上面用 `-c` 显式传入；
> 只想配一次就 `git config --global user.name/…`。
> **不要**用 `dev <dev@local>` 这类占位身份提交——推上去之后改历史很麻烦。

## 3. 推到 GitHub

```powershell
gh auth login                                   # 或手动在 GitHub 建空仓库
gh repo create <你的GitHub用户名>/deep-research-collab --public --source=. --push
```

## 4. 验证「一行装」（这一步不通过就不算发布完成）

```powershell
npx skills add <你的GitHub用户名>/deep-research-collab
```

期望：`Local path validated` 换成远端拉取、`Found 1 skill`、`Installed 1 skill`。

## 5. 上 skills.sh

skills.sh（Vercel）**从公开 GitHub 仓库自动发现**，无需注册或投递：

1. 确认仓库 public，且 `SKILL.md` 能被匿名访问；
2. 打开 `https://skills.sh/<你的GitHub用户名>/deep-research-collab` 确认已收录；
3. README 顶部徽章已经从 `<OWNER>` 换成你的用户名，收录后会自动显示安装量。

ClawHub（可选，第二流量池，中文友好）：`npm i -g clawhub && clawhub login && clawhub skill publish ./skills/deep-research-collab --slug deep-research-collab --version 0.2.0`

## 6. 重新录制 demo（可选）

`assets/demo.gif` 目前是**降级路线**产物（本机无 `vhs`，改用 Chrome 逐帧截图 + ffmpeg）：

```bash
bash assets/record-demo.sh
```
需要 `google-chrome`/`chromium`、`ffmpeg`、`python3`。脚本内的帧位置是硬编码的，重录结果确定。

## 仍未验证的一项（发布后建议补上）

**没有端到端跑完一次完整调研（阶段 0–5 + 运行记录）。** 本轮重建了样例 payload 与产物，但「它能否稳定产出好研究」尚未验证。建议发布后按 `skills/deep-research-collab/references/research-workflow.md` 完整跑一题，把运行记录作为第二个 acceptance run 入库。
