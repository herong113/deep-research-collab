#!/usr/bin/env bash
# 重新录制 assets/demo.gif —— 可复现，不需要手工摆拍。
#
# 为什么不是 vhs：本机没有安装 vhs（`command -v vhs` 为空），而 demo 必须能重录，
# 所以走**降级路线**：Chrome headless 按固定 scrollY 逐帧截图 → ffmpeg 合成 GIF。
# 这条路线的确定性更强（帧位置是写死的数字，不是终端交互回放），代价是只能展示
# 页面滚动，不能展示终端里的命令执行过程。
#
# 依赖：google-chrome / chromium、ffmpeg、python3
# 用法：bash assets/record-demo.sh            （在仓库根执行）

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$REPO_ROOT/skills/deep-research-collab"
REPORT="$SKILL/examples/report-sample.html"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

CHROME="${CHROME:-$(command -v google-chrome || command -v chromium || command -v chromium-browser)}"
if [[ -z "${CHROME:-}" ]]; then
  echo "✘ 找不到 Chrome/Chromium；设置 CHROME=/path/to/chrome 后重试" >&2
  exit 1
fi

# 1) 先确保样例报告与当前生成器一致（避免录到过期产物）
python3 "$SKILL/scripts/build_report.py" \
  --payload "$SKILL/examples/example-report-payload.json" \
  --out "$REPORT" --strict

# 2) 造一个只负责滚动 iframe 的取景页 —— iframe 宽度即真实视口宽度。
#    （注意：Chrome headless 的 --window-size 有最小宽度限制，直接用它截不到 390px 的真实布局。）
cat > "$WORK/frame.html" <<'HTML'
<!doctype html><meta charset="utf-8">
<style>html,body{margin:0;padding:0;overflow:hidden}iframe{border:0;display:block;width:1200px;height:760px}</style>
<iframe id="f" src="report.html"></iframe>
<script>
var y = parseInt(new URLSearchParams(location.search).get('y')||'0',10);
document.getElementById('f').onload = function(){ this.contentWindow.scrollTo(0, y); };
</script>
HTML
cp "$REPORT" "$WORK/report.html"

# 3) 逐帧截图（帧位置写死 → 每次重录结果一致）
YS=(0 700 1500 2400 3300 4200 5200 6200)
i=0
for y in "${YS[@]}"; do
  printf -v n '%03d' "$i"
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --allow-file-access-from-files --window-size=1200,760 \
    --virtual-time-budget=3500 \
    --screenshot="$WORK/f$n.png" "file://$WORK/frame.html?y=$y" >/dev/null 2>&1
  i=$((i + 1))
done

# 4) 合成 GIF（调色板两遍法，控制体积）
mkdir -p "$REPO_ROOT/assets"
ffmpeg -y -framerate 1.2 -i "$WORK/f%03d.png" \
  -vf "fps=8,scale=1000:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer" \
  -loop 0 "$REPO_ROOT/assets/demo.gif" 2>&1 | tail -2

echo "✔ 已生成 $REPO_ROOT/assets/demo.gif ($(wc -c < "$REPO_ROOT/assets/demo.gif") 字节)"
