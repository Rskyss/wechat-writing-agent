# 更新日志

## 1.1.0

**支持的工具从 1 个变成 4 个。**

### 新增

- **Codex 一键安装**：`codex plugin marketplace add Rskyss/wechat-writing-agent` → `codex plugin add wechat-writing@wechat-writing-agent`（新增 `.codex-plugin/plugin.json` 与 `.agents/plugins/marketplace.json`）
- **CodeBuddy / WorkBuddy 支持**：新增 `.codebuddy-plugin/` 清单
- **通用安装脚本 `install.sh`**：一条命令装到 workbuddy / codebuddy / codex / claude，不带参数自动识别本机已装的工具；`--project` 可装到当前项目而非用户全局

### 修复

- **配套 skill 装出去后规则读不到**：`house-style`、`humanizer-zh`、`copywriting` 里指向 `persona.md`、`introduction.md` 和质检脚本的路径原本是仓库根相对路径，装成插件后从用户自己的工作目录解析不到。已改为 `${CLAUDE_SKILL_DIR}` 形式，并在每个 SKILL.md 顶部注明：工具若不展开该变量，按相对本文件的目录解析即可
- **WorkBuddy 技能目录写错**：文档里误写成 `~/.codebuddy/skills/`，实际是 `~/.workbuddy/skills/`，两者不是同一位置

### 文档

- README 改为「这就是 5 个标准 SKILL.md」的框架，安装章节按工具重排，不再以插件市场为主线

---

## 1.0.0

首个可安装版本。

- 规则正本迁入 `skills/write-article/`（rules / workflows / lanes / references / scripts 自包含），SKILL.md 用 `${CLAUDE_SKILL_DIR}` 定位自身，装到哪都能找到规则和脚本
- `house-style`、`humanizer-zh`、`copywriting`、`twitter-capture` 提升为同级 skill
- 新增 `.claude-plugin/` 清单，支持 Claude Code 插件市场安装
- 6 个强制检查点的长文流水线、A–E 类 AI 味黑名单、三条车道（爆文流 / 干货流 / 观察思考流）
- 统一质检 `check_article.py`：结构字数 / AI 味 / 人设黑名单 / 引用溯源
- MIT LICENSE

### 已知的坑（1.1.0 已修）

- 配套 skill 的跨文件引用用的是仓库根相对路径，单独装出去会读不到规则
