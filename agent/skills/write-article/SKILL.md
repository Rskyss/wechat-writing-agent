---
name: write-article
description: Use when the user asks to write, plan, draft, review, polish, or publish a WeChat Official Account article for 本号, including /write, /article, 写文章, 写公众号, 找选题, 选题挖掘, 标题生成, 正文成稿, 发布前质检, or turning a draft into a project output article folder.
---

# Write Article Skill

This skill coordinates the 本号 WeChat article workflow. It wraps the project workflow file instead of duplicating it, so the source of truth stays in one place.

## Load First

Before any Chinese article writing, rewriting, title, copywriting, or polishing task, read:

- `agent/skills/house-style/SKILL.md`
- `agent/rules/introduction.md`
- `agent/rules/persona.md`

For full article production from topic discovery to publishing, read and follow:

- `agent/workflows/write_article.md`

If `.kiro/steering/*.md` conflicts with `.agent` rules, prefer `.agent`.

## Trigger Modes

### Full Workflow

Use the full 5-step workflow when the user asks:

- `/write`
- `/article`
- `写文章`
- `写公众号`
- `找选题`
- `选题`
- `帮我写一篇公众号`

In this mode:

1. Follow `agent/workflows/write_article.md` step by step.
2. Stop at every required checkpoint and wait for the user's choice.
3. Use `mcp__tavily__tavily_search` first for current research; fall back to normal web search only if needed.
4. Use `mcp__sequential_thinking__sequentialthinking` for deep angle mining and editor review.
5. Apply `agent/skills/house-style/SKILL.md` to all titles, drafts, rewrites, and review comments.

### Existing Draft Mode

Use a lighter flow when the user already provides a draft and asks to review, polish, organize, or save it.

In this mode:

1. Keep the user's core argument and voice.
2. Apply `agent/skills/house-style/SKILL.md` and `agent/skills/humanizer-zh/SKILL.md`.
3. If turning it into a project artifact, create:
   - `output/<article-slug>/`
   - `output/<article-slug>/<article-slug>.md`
   - `output/<article-slug>/sources.md`
   - `output/<article-slug>/images/`
   - `output/<article-slug>/prompts/`
   - optional `output/<article-slug>/notes/`
4. Do not scatter new article files directly under `output/`.
5. Run the unified quality check after creating the article file (exit code 1 means fix and re-run until it passes):
   ```bash
   python3 check_article.py output/<article-slug>/<article-slug>.md
   ```

## Required Companion Skills

- For 本号 voice and personal style, read `agent/skills/house-style/SKILL.md`.
- For headline generation, read `agent/skills/copywriting/SKILL.md`.
- For writing and polishing, read `agent/skills/humanizer-zh/SKILL.md`.
- For image generation requests such as `出图`, `生成海报`, `配图`, or `封面图`, use Codex built-in image generation by default. You may reuse prompt structure, visual style rules, and layout references from Baoyu skills such as `baoyu-cover-image`, `baoyu-infographic`, and `baoyu-slide-deck`, but only as prompt-design guidance. Do not default to Google/Gemini/DashScope image APIs or `baoyu-image-gen` providers unless the user explicitly asks for them or approves a fallback.
- For Markdown to WeChat preview or publishing, prefer:

## Output Contract

Every complete article markdown file should contain:

- `## 标题备选`
- `## 正文成稿`
- `## 写在最后`
- `## 可转发金句`

不再在文末单独列「数据来源清单」：所有数字/引用/案例必须在正文提及处直接附带真实 URL（这是真实性的唯一标准）。调研链接统一存到 `sources.md`。

If the article is based on opinion rather than external facts, state that in `sources.md` instead of inventing citations.

## Length Policy

Do not compress 本号 articles just to satisfy a 2500-character target.

- Keep the user's original argument, rhythm, and personal style.
- Treat 1000 characters as the minimum for a complete article.
- Treat 2500 characters as a soft suggestion only.
- If an article is long but coherent, keep it long.
- Other rules still apply: structure, style, banned words, AI-tone checks, source honesty, and publishing format.

## Publishing Preview

When the user asks to convert or preview a completed article, run:

```bash
python3 convert_to_wechat.py output/<article-slug>/<article-slug>.md preview_app/articles/<article-slug>.html
python3 sync_articles.py
```

Then report the generated preview path or local preview URL.
