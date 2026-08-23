# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这是什么项目

公众号文章生产流水线。**不是传统代码项目**——主要"产出"是 `output/<article-slug>/` 下的中文文章，Python 脚本是辅助工具，不是核心交付物。

用户身份：在 AI 领域创业的产品经理。沟通时用产品语言、避免技术黑话；输出文档/代码注释时使用中文。

## 架构：一个中立大脑 + 每个工具一张门牌（重要：不要误判为冗余）

写作规则只有一份正本，全部放在项目根目录的中立大脑文件夹 **`agent/`**（不带点、不属于任何工具）。各 AI 工具只认自己门口的特殊文件，所以每个工具门口放**一张指向 `agent/` 的薄门牌**，本身不存规则：

| 文件/目录 | 角色 |
|---|---|
| **`agent/`** (rules/workflows/skills/lanes) | **中立大脑 = 唯一正本**（身份/性格/书写方法/车道/技能全在这） |
| `AGENTS.md` | Codex 的门牌 → 指向 `agent/` |
| `.agent/` | Antigravity 的门牌（`.agent/rules/_brain-pointer.md`，always_on）→ 指向 `agent/` |
| `.kiro/` (hooks/settings/steering) | Kiro 的门牌 + 工具配置（steering 指向 `agent/`；hooks/settings 是 Kiro 自己的配置。`.kiro/skills` 已删，不再存副本） |
| `.claude/` | Claude Code 的门牌（`.claude/skills/write-article/`）→ 指向 `agent/` |

**改写作规则只改 `agent/` 一处，所有工具同时生效。** 门牌只在工具"读不到 agent/ 就瞎了"时才需要动。

> 说明：所有 skill 只在 `agent/skills/` 存唯一一份。`.kiro/` 只保留 Kiro 自己的工具配置（hooks/settings）和门牌（steering）。Python 脚本（check_article.py 等）是「手」不是「脑」，留在项目根目录，不进 `agent/`。

## 写作工作流（强制 SOP）

触发词：`/write`、`/article`、"写文章"、"写公众号"。一旦触发，**严格按 `agent/workflows/write_article.md` 执行**，6 个强制 CheckPoint 不能跳过：

1. **Step 1**：双轨搜索（公域 + 私域 Moltbot/DeepSeek/Agent），输出 10 个热点 → 等用户选 1 个
2. **Step 2**：调 `sequentialthinking` 深度挖掘 → 输出 10 个角度（含🔥传播/🛠️实用/🧠深度评分）→ 等用户选 1 个
3. **Step 3**：车道建议（A 爆文流 / B 干货流）→ 等用户选
4. **Step 4**：根据 `agent/lanes/车道A.md` 或 `agent/lanes/车道B.md` 生成 10 个标题 → 等用户选
5. **Step 4.5**：根据内容类型自动决定模块数（3/4-5/6），不询问用户
6. **Step 5**：写正文，**必须先加载 `agent/rules/persona.md` 的人设/口吻规则**（"本号底味"），同时实时应用 `humanizer-zh` skill 去 AI 味
7. **Step 5.5**：自动跑统一质检 `check_article.py`；技术/科普类文章额外做**技术准确性审查**（AI 切「抬杠的领域专家」视角，专防过度简化的技术类比，见 `agent/workflows/write_article.md` Step 5.5）
8. **Step 6**：转 HTML + 同步预览

搜索工具优先级：`mcp__tavily__tavily_search` > 普通 web search。深度思考/主编审稿用 `mcp__sequential_thinking__sequentialthinking`。

## 核心命令

### 文章质检（Step 5.5 强制执行，统一入口）
```bash
python3 check_article.py output/<article-slug>/<article-slug>.md
# 一条命令跑完 4 组检查：结构字数 → AI味(含E类对比句式) → persona黑名单(动态读取) → 平台合规/引用溯源
# 退出码 1 = 有必须修复项，逐项修复后重跑直到通过；⚠️警告项不阻塞但要向用户报告
```
（`audit_article.py` / `detect_ai_tone.py` 仍可单独调用调试，但正式流程只认 `check_article.py`。）

### 转换与预览（Step 6 发布流程）
```bash
python3 convert_to_wechat.py output/<article-slug>/<article-slug>.md preview_app/articles/<article-slug>.html
python3 sync_articles.py
./1.sh   # 启动 preview_app（端口 8000 + API 8001），首次会自动建 .venv 并装依赖
```

### 提交前轻量校验
```bash
python3 -m py_compile check_article.py audit_article.py detect_ai_tone.py convert_to_wechat.py preview_app/api_server.py
```

## 写作"底味"硬规则（Step 5 必读）

`agent/rules/persona.md` 是写作时的最高优先级约束，也是黑名单的**唯一正本**。下面只是几类高频词的**速查**（不是完整清单，增删词一律改 persona.md，别在这里加）：

- **A 类 AI 八股**：综上所述、首先/其次/最后、本质上、核心逻辑、深入探讨
- **B 类商业黑话**：赋能、抓手、闭环、底层逻辑、降维打击、生态/矩阵/赛道
- **C 类距离感**：小编、笔者、各位读者、利用、进行 XX 操作
- **D 类 AI 情绪表演**：愣了几秒、后背发凉、手心出汗、不禁感叹、细思极恐、令人震惊

D 类是隐性的"伪真人"陷阱——AI 写惊讶时最爱用，必须换成具体动作（"翻了翻时间戳"），不是身体感觉标签。

**原创性红线（严禁洗稿，最高优先级）**：用户给某篇文章让你"参考着写一篇"时，范文只能取**事实素材（自己回一手核）+ 选题方向**；它的开篇框架、比喻、金句、论证顺序一律不许搬，**神似也算洗稿**。AI 天生会收敛到"看到的最优模板"，参考范文时极易从"参考"滑成"复制"。参考过范文的稿，成稿必做逐段比对自查（见 `persona.md` 案例8、`write_article.md` Step 5.5 第4步）。

## output 目录规则（强制，完整版见 `agent/workflows/write_article.md` Step 5）

每篇新文章必须建专属目录，**严禁**把 .md / 图 / prompt 散放到 `output/` 根目录：

```
output/<article-slug>/
├── <article-slug>.md       # 正文
├── sources.md              # 调研链接、截图说明
├── images/                 # 封面、配图、截图
├── prompts/                # 图片生成 prompt（与 images 同名 .md）
└── notes/                  # 可选临时笔记
```

文章正文开头必须包含 `## 标题备选`（10 个候选）→ `## 正文成稿` → `## 写在最后` → `## 可转发金句`。`audit_article.py` 依赖这个结构识别正文边界做字数检查（≥1000 字，车道A建议 1000-2500 / 车道B建议 2500-3000 / 车道C建议 2000-2800）。不再要求文末"数据来源清单"，所有引用在正文提及处直接带真实 URL。

## 同步到 GitHub

触发词："同步到 GitHub"、"更新到仓库"。默认远程为你自己的仓库地址，分支 `main`。`AGENTS.md` 第 82-107 行有完整流程，关键点：

- `.gitignore` 已排除 `output/`、`illustrations/`、`cover-image/`、`preview_app/articles/`、`preview_app/data/articles.json`、`*.docx`、`reddit_mock.html`、`.env*` —— **文章正文和素材本地保留，不进 Git**
- 有实质性变更时更新 `更新记录.md`
- commit message 用清晰中文（如 `chore: 同步公众号写作工作流与本地技能`）
- 推送前先 `git fetch origin` 检查差异，不要盲目覆盖

## 编辑代码 / skill / 规则时的注意

- 修改 `agent/skills/<name>/` 时不用再同步别处——skill 只有 `agent/skills/` 一份正本了
- 修改写作规则（persona / workflow / humanizer）时同步检查 `agent/rules/`、`.kiro/steering/`、`AGENTS.md` 是否需要联动更新
- 改完任意写作流程或脚本，记得在 `更新记录.md` 加一条
