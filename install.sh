#!/usr/bin/env bash
# 把本仓库的 skills 装到你的 AI 工具里。
#
#   bash install.sh                  # 自动识别已装的工具，全部装上
#   bash install.sh workbuddy        # 只装到指定工具
#   bash install.sh --project        # 装到当前项目而不是用户全局
#
# 支持：workbuddy / codebuddy / codex / claude
# Claude Code 和 Codex 更推荐用各自的插件市场安装（见 README），
# 本脚本是通用兜底，也是 WorkBuddy / CodeBuddy 的主要方式。
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/skills"
[ -d "$SRC" ] || { echo "❌ 找不到 skills/ 目录，请在仓库根目录运行"; exit 1; }

SCOPE="user"
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --project) SCOPE="project" ;;
    --user)    SCOPE="user" ;;
    workbuddy|codebuddy|codex|claude) TARGETS+=("$arg") ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "❌ 不认识的参数: $arg"; exit 1 ;;
  esac
done

# 各工具的技能目录
skills_dir() {
  case "$1" in
    workbuddy) [ "$SCOPE" = project ] && echo ".workbuddy/skills" || echo "$HOME/.workbuddy/skills" ;;
    codebuddy) [ "$SCOPE" = project ] && echo ".codebuddy/skills" || echo "$HOME/.codebuddy/skills" ;;
    codex)     [ "$SCOPE" = project ] && echo ".codex/skills"     || echo "$HOME/.codex/skills" ;;
    claude)    [ "$SCOPE" = project ] && echo ".claude/skills"    || echo "$HOME/.claude/skills" ;;
  esac
}

# 没指定工具就自动识别：装过哪个就装到哪个
if [ ${#TARGETS[@]} -eq 0 ]; then
  for t in workbuddy codebuddy codex claude; do
    [ -d "$HOME/.$t" ] && TARGETS+=("$t")
  done
  if [ ${#TARGETS[@]} -eq 0 ]; then
    echo "❌ 没检测到任何支持的工具（找不到 ~/.workbuddy、~/.codebuddy、~/.codex、~/.claude）"
    echo "   可以显式指定，例如： bash install.sh workbuddy"
    exit 1
  fi
  echo "🔍 检测到: ${TARGETS[*]}"
fi

for t in "${TARGETS[@]}"; do
  DEST="$(skills_dir "$t")"
  mkdir -p "$DEST"
  n=0
  for s in "$SRC"/*/; do
    name="$(basename "$s")"
    rm -rf "${DEST:?}/$name"
    cp -R "$s" "$DEST/$name"
    n=$((n + 1))
  done
  echo "✅ $t: 装了 $n 个 skill → $DEST"
done

cat <<'EOF'

装完了。在工具里说「写文章」即可触发。

⚠️  装完第一件事：改成你自己的号
    规则里的人设、读者定位、字数区间来自一个具体的号，
    不改的话写出来的稿子会带上别人的味道。要改的两个文件：
      write-article/rules/introduction.md   我是谁、写给谁、号的承诺
      write-article/rules/persona.md        口吻、A–E 类黑名单、红线
    直接跟 AI 说「打开写作规则的 introduction.md，帮我改成我的号」即可。
EOF
