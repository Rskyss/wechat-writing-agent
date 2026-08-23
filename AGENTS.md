# Codex 项目说明

这个仓库里放的是公众号写作流程，以及从 Antigravity（`.agent`）和 Kiro（`.kiro`）迁移过来的本地 Agent 技能。
Codex 在这个项目里工作时，必须把这些文件当成项目级规则和可执行技能来使用。

## 禁止 6A / Superpowers

- 本项目是公众号写作仓库，**禁止使用 6A 和任何 Superpowers 开发流程/技能**。
- 不得在写作、审稿、改稿、出图、排版或发布任务中调用 `superpowers:brainstorming`、`superpowers:writing-plans`、`superpowers:executing-plans`、`superpowers:using-git-worktrees` 或其他 `superpowers:*` 技能。
- 不得因写作任务创建 `docs/superpowers/` 下的设计文档、实施计划或开发规格，不得为此创建开发分支或 worktree。
- 正式长文及其调研、图片、prompt 和临时笔记只能放在 `output/<article-slug>/` 对应目录；微信图片消息形态的“图文”统一放在 `img_outputs/<post-slug>/`，两者不得混用。

## 规则来源

- 在处理中文文章写作、改写、润色、标题、文案任务前，必须先读取：
  - `agent/rules/introduction.md`
  - `agent/rules/persona.md`
- 公众号文章工作流必须遵循：
  - `agent/workflows/write_article.md`
- 微信图片消息形态的图文工作流必须遵循：
  - `agent/workflows/image_post.md`
  - `agent/workflows/image_post_styles.md`
- 写作规则只有一份正本，全部放在 `agent/`（人设、风格、车道、工作流、写作类技能）。`.kiro/steering/write_article_workflow.md` 只是一张「指路牌」，把 Kiro 领回 `.agent` 读同一份正本，不再保存副本。改写作规则只改 `agent/`，Codex / Kiro 同时生效。

## 本地技能

即使下面这些目录没有出现在 Codex 的全局技能列表里，也要把它们当成当前项目的本地 Codex 技能：

- `agent/skills/*`（全部写作与工具技能的唯一正本；`.kiro/skills` 已废弃删除，不再存在）

当用户请求命中某个本地技能时：

1. 打开对应技能目录里的 `SKILL.md`。
2. 按照其中的触发条件、工作流和输出要求执行。
3. 所有相对路径里的 `references/`、`prompts/`、`scripts/`、依赖文件和素材，都要从该技能目录开始解析。
4. 所有技能（`humanizer-zh`、`copywriting`、`house-style`、`twitter-capture` 等）都只在 `agent/skills/` 保留唯一一份正本，不要在别处存副本。

## 脚本执行

- 技能脚本可以通过 shell 执行。优先使用每个 `SKILL.md` 里写好的命令示例，并把 `${SKILL_DIR}` 替换成真实技能目录。
- 对带脚本的技能，优先使用技能文档里已经写好的命令格式。

- 运行需要浏览器自动化、网络访问、剪贴板访问、外部平台发布或登录状态的脚本前，要说明会访问什么；如果沙箱要求授权，就先请求用户批准。
- 除非用户明确要求迁移，否则不要重写或移动技能脚本。

## 图文工作流优先规则

当用户说“图文”“图文文章”“图片消息”“滑图”“卡片图文”“信息图卡组”或类似表达时：

1. 默认理解为微信图片消息，不进入普通长文工作流。
2. 必须先读取 `agent/workflows/image_post.md` 和 `agent/workflows/image_post_styles.md`。
3. 图文规则优先于 `agent/workflows/write_article.md` 和普通长文配图规则。
4. 所有文件只能放在 `img_outputs/<post-slug>/`，标准结构为：
   - `copy.md`
   - `sources.md`
   - `style-spec.md`
   - `prompts/`
   - `images/`
   - `research/`
5. 默认先创建文案和 Prompt，不生成图片；用户明确说“出图”后才使用 Codex 内置出图能力。
6. 未经用户指定，图片消息默认采用适合手机滑读的 `2:3` 竖版、`1080 × 1620 px`。
7. 严禁把图文文件创建到 `output/`。
8. 只有用户明确说“长文配图”“公众号文章配图”时，才按长文规则放入 `output/<article-slug>/`。

## 出图默认规则

- 当用户说“出图”“生成图片”“生成海报”“配图”“封面图”或类似表达时，默认使用 **Codex 内置出图能力**。
- 不要默认调用 Google/Gemini/DashScope 等外部图片 API。
- 只有当用户明确要求使用某个外部 provider、某个本地技能脚本，或 Codex 内置出图无法满足任务时，才说明原因并征求用户确认。
- 正式长文配图放入 `output/<article-slug>/images/`，对应 Prompt 放入 `output/<article-slug>/prompts/`；图文图片放入 `img_outputs/<post-slug>/images/`，对应 Prompt 放入 `img_outputs/<post-slug>/prompts/`。
- 长文中的文字较多配图可优先使用 `16:9`；图文图片默认使用 `2:3` 竖版、`1080 × 1620 px`。两种形态都要清晰中文标题、大字号、留白充足，不要为了塞正文生成密密麻麻的说明图。

## 文章工作流默认规则

当用户输入 `/write`、`/article`、`写文章`、`写公众号`，或者要求寻找选题时：

1. 必须按 `agent/workflows/write_article.md` 一步一步执行。
2. 遇到每个强制检查点时，必须停下来等待用户选择。
3. 需要当前网络资料时，优先使用 `mcp__tavily__tavily_search`；如果返回套餐额度耗尽、限流或认证错误，必须保持相同参数，依次自动改用 `mcp__tavily_backup__tavily_search`、`mcp__tavily_3__tavily_search`、`mcp__tavily_4__tavily_search`、`mcp__tavily_5__tavily_search`、`mcp__tavily_6__tavily_search`。六个入口全部不可用时再使用普通网页搜索。
4. 工作流要求深度思考或主编审稿时，使用 `mcp__sequential_thinking__sequentialthinking`。
5. 生成标题时，加载 `agent/skills/copywriting/SKILL.md` 里的 `copywriting` 技能。
6. 写作和润色时，加载 `agent/skills/humanizer-zh/SKILL.md` 里的 `humanizer-zh` 技能。
7. 每次生成文章时，必须先在 `output/` 下创建一个文章专属文件夹：`output/<article-slug>/`。
   - 正文保存为：`output/<article-slug>/<article-slug>.md`
   - 图片保存到：`output/<article-slug>/images/`
   - 图片生成 prompt 保存到：`output/<article-slug>/prompts/`
   - 调研资料、链接、截图说明、临时笔记保存到：`output/<article-slug>/sources.md` 或 `output/<article-slug>/notes/`
   - 不要再把新文章的 `.md`、图片、prompt 直接散放到 `output/` 根目录。
8. 草稿完成后，运行统一质量检查（一条命令，退出码 1 时逐项修复后重跑）：

   ```bash
   python3 check_article.py output/<article-slug>/<article-slug>.md
   ```

## 发布工作流

当用户要求转换或发布一篇已经完成的文章时：

1. 如果存在对应本地技能（发布类技能需自行安装，见 README「可选：第三方发布技能」），优先使用。
2. 对内置的微信公众号预览流程，运行：

   ```bash
   python3 convert_to_wechat.py output/<article-slug>/<article-slug>.md preview_app/articles/<article-slug>.html
   python3 sync_articles.py
   ```

3. 转换完成后，报告本地预览路径或预览 URL。

## GitHub 同步记忆

当用户说“同步到 GitHub”“同步到 github”“更新到仓库”或类似表达时，默认执行以下流程：

1. 默认远程仓库为你自己 fork/clone 的地址，默认分支为 `main`。
2. 先运行 `git status --short`、`git remote -v`、`git diff --stat`，确认变更范围。
3. 同步前检查并排除以下内容：
   - `.env`、`.env.*`、`account_profile.json`
   - `node_modules/`
   - `output/`
   - `preview_app/articles/`
   - `preview_app/data/articles.json`
   - `illustrations/`
   - `cover-image/`
   - `x-to-markdown/`
   - `*.docx`
   - `reddit_mock.html`
   - `__pycache__/`、`*.pyc`、`*.log`、`.DS_Store`
4. 如果有实质性变更，更新或补充 `更新记录.md`，用中文写清楚本次同步包含哪些内容。
5. 提交前运行基础校验：
   - `python3 -m py_compile audit_article.py convert_to_wechat.py preview_app/api_server.py`
   - 如变更涉及预览数据或转换流程，优先再运行对应脚本做一次最小验证。
6. 使用清晰中文 commit message，例如：
   - `chore: 同步公众号写作工作流与本地技能`
   - `docs: 更新项目规则与同步记录`
7. 推送到 `origin main`。如果远端有新提交，先 `git fetch origin` 并审查差异，不要盲目覆盖。
