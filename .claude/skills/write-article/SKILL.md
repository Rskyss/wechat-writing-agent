---
name: write-article
description: Use when the user asks to write, draft, review, polish, or publish a WeChat Official Account article for 本号 — including /write, /article, 写文章, 写公众号, 找选题, 选题, 起标题, 改稿, 审稿, 发布前质检. Triggers the full 6-checkpoint article production workflow.
---

# Write Article（Claude Code 入口）

这是一张指路牌，不存规则。本项目所有写作规则只有一份正本，统一放在项目根目录的中立大脑文件夹 `agent/`（它不属于任何工具，各工具门口——`.claude`/`.kiro`/`.agent`/`AGENTS.md`——只放一张指向它的指路牌）。
触发本 skill 后，按以下顺序读取并严格遵循正本，禁止凭记忆执行：

## 动笔前必读（按顺序）

1. `agent/rules/introduction.md` — 我是谁、写给谁、号的承诺
2. `agent/rules/persona.md` — 写作底味：词汇黑名单（A-E类，唯一来源）、语义层人味-反预测原则
3. `agent/skills/house-style/SKILL.md` — 文章结构、改写规则、阅读动线

## 完整流程（选题 → 成稿 → 发布）

严格按 `agent/workflows/write_article.md` 逐步执行：

- 6 个强制 CheckPoint 不能跳过，每个检查点停下等用户选择
- 搜索优先用 `mcp__tavily__tavily_search`；深度挖角度/主编审稿用 `mcp__sequential-thinking__sequentialthinking`
- Step 5 写正文前先做"私货盘点"（按 persona.md 语义层分级，素材没有私货严禁编造）
- Step 5.5 强制运行统一质检，退出码 1 就逐项修复重跑直到通过：

  ```bash
  python3 check_article.py output/<article-slug>/<article-slug>.md
  ```

## 配套技能（按需读取）

- 标题/文案：`agent/skills/copywriting/SKILL.md`
- 去 AI 味：`agent/skills/humanizer-zh/SKILL.md`
- 车道规则：`agent/lanes/车道A.md`（爆文流）、`agent/lanes/车道B.md`（干货流）、`agent/lanes/车道C.md`（观察思考流，解读型主力）
- 完整 skill 说明（含改稿模式/输出契约/字数策略）：`agent/skills/write-article/SKILL.md`

## 为什么这么薄

每个 AI 工具只认自己门口的文件，但规则只该有一份。改规则只改 `agent/` 正本，本文件不需要跟着改。
