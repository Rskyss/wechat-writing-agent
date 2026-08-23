---
name: write-article
description: Use when the user asks to write, plan, draft, review, polish, or publish a WeChat Official Account (公众号) article — including /write, /article, 写文章, 写公众号, 找选题, 选题, 起标题, 改稿, 审稿, 发布前质检. Runs a 6-checkpoint production workflow with vocabulary blacklists and an automated AI-tone quality gate.
---

# 公众号写作 Skill

> **路径说明**：下文的 `${CLAUDE_SKILL_DIR}` 指本 skill 所在目录。若你的工具不展开这个变量（Claude Code、CodeBuddy/WorkBuddy 会展开），按**相对本文件所在目录**解析即可，效果相同。

一条带强制检查点的中文长文流水线：选题 → 角度 → 车道 → 标题 → 正文 → 质检 → 转微信 HTML。

规则正本全部在本 skill 目录内，禁止凭记忆执行——每次都读文件。

> **首次使用必读**：`${CLAUDE_SKILL_DIR}/rules/introduction.md` 和 `rules/persona.md` 里的人设、读者定位、字数区间来自一个具体的号。**如果用户没改过这两个文件，先提醒他改**，否则写出来的稿子会带上别人的味道。

## 动笔前必读（按顺序，不许跳）

1. [身份定位](${CLAUDE_SKILL_DIR}/rules/introduction.md) — 我是谁、写给谁、号的承诺
2. [写作底味](${CLAUDE_SKILL_DIR}/rules/persona.md) — 词汇黑名单（A–E 类，唯一正本）、语义层反预测原则、原创性红线
3. [结构层](${CLAUDE_SKILL_DIR}/../house-style/SKILL.md) — 文章结构、改写规则、阅读动线

## 完整流程（选题 → 成稿 → 发布）

严格按 [写作 SOP](${CLAUDE_SKILL_DIR}/workflows/write_article.md) 逐步执行。

**6 个强制 CheckPoint，每个都停下等用户选择，禁止一口气写完**：

| Step | 动作 | 停下等什么 |
|---|---|---|
| 1 | 双轨搜索热点 | 10 个选题 → 等用户选 1 个 |
| 2 | 深度挖掘角度（用 sequentialthinking） | 10 个角度带评分 → 等用户选 1 个 |
| 3 | 车道建议 | A/B/C → 等用户选 |
| 4 | 按车道起标题 | 10 个标题 → 等用户选 |
| 4.5 | 定模块数（3 / 4-5 / 6） | 不问用户，按内容类型自动决定 |
| 5 | 写正文 | 先做「私货盘点」，素材没私货严禁编造 |
| 5.5 | 强制质检 | 见下方，不通过不许进 Step 6 |
| 6 | 转 HTML | 交付可粘贴的微信 HTML |

**车道规则**（Step 3 选定后读对应那份）：

- [车道A 爆文流](${CLAUDE_SKILL_DIR}/lanes/车道A.md) — 热点 + 情绪钩子，1000–2500 字
- [车道B 干货流](${CLAUDE_SKILL_DIR}/lanes/车道B.md) — 方法论 + 可操作步骤，2500–3000 字
- [车道C 观察思考流](${CLAUDE_SKILL_DIR}/lanes/车道C.md) — 交付判据和思考，**不教人做事**，2000–2800 字

**搜索与思考工具**：调研优先 `mcp__tavily__tavily_search`，无则普通 web search；深挖角度和主编审稿用 `mcp__sequential-thinking__sequentialthinking`。

## Step 5.5 强制质检

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/check_article.py <文章.md>
```

一条命令跑完四组检查。**退出码 1 = 有必须修复项，逐项改完重跑，直到通过才能进 Step 6**；⚠️ 警告项不阻塞，但要向用户报告。

四组分别是：结构字数 → AI 味（A–E 类）→ persona 黑名单（动态读 persona.md）→ 平台合规与引用溯源。

技术/科普类文章额外做**技术准确性审查**：切「抬杠的领域专家」视角，专防过度简化的技术类比（详见 SOP 的 Step 5.5）。

参考过范文的稿子，成稿必须**逐段比对自查**——范文只能提供事实素材和选题方向，它的开篇框架、比喻、金句、论证顺序一律不许搬，**神似也算洗稿**。

## Step 6 转微信 HTML

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/convert_to_wechat.py <文章.md> <输出.html>
```

号名和公众号名片从用户项目根目录的 `account_profile.json` 读取；没有这个文件就用中性占位符，不影响转换。

## 改稿模式（用户已有草稿）

用户直接给稿子让你审/改/润色时，走轻流程，不要跑完整 6 步：

1. 保住用户的核心论点和语气，你是改稿不是重写。
2. 应用 [结构层](${CLAUDE_SKILL_DIR}/../house-style/SKILL.md) 和 [去 AI 味](${CLAUDE_SKILL_DIR}/../humanizer-zh/SKILL.md)。
3. 改完照样跑上面的质检命令。

## 输出契约

成稿的 Markdown 必须含这四个二级标题（质检脚本靠它们识别正文边界）：

```
## 标题备选     （10 个候选）
## 正文成稿
## 写在最后
## 可转发金句
```

文末**不要**单列「数据来源清单」——所有数字、引用、案例在正文提及处直接附真实 URL，这是真实性的唯一标准。调研链接统一存到同目录 `sources.md`。文章基于观点而非外部事实时，在 `sources.md` 里说明，**不许编造引用**。

建议的文章目录结构（保持整洁，别把文件散放）：

```
<article-slug>/
├── <article-slug>.md
├── sources.md
├── images/
├── prompts/
└── notes/        （可选）
```

## 字数策略

**不要为了凑字数目标压缩表达。** 1000 字是完整文章的下限；各车道的区间是建议不是硬限；文章长但立得住，就让它长。其余规则照常生效：结构、风格、黑名单、AI 味检测、引用诚实、发布格式。

## 配套 skill

- 起标题/文案 → [copywriting](${CLAUDE_SKILL_DIR}/../copywriting/SKILL.md)
- 去 AI 味 → [humanizer-zh](${CLAUDE_SKILL_DIR}/../humanizer-zh/SKILL.md)
- 抓推文截图 → [twitter-capture](${CLAUDE_SKILL_DIR}/../twitter-capture/SKILL.md)
- 图文（微信图片消息）→ [image_post](${CLAUDE_SKILL_DIR}/workflows/image_post.md) + [版式](${CLAUDE_SKILL_DIR}/workflows/image_post_styles.md)
- 行业分析框架 → [references/](${CLAUDE_SKILL_DIR}/references/) 下的商业分析、故事叙事、36kr_pro_mode
