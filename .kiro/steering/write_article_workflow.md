# 写作规则入口（Kiro 指路牌）

> 这个文件本身不存规则。本项目所有写作规则只有一份正本，统一放在项目根目录的中立大脑文件夹 `agent/`（不属于任何工具，各工具门口只放指路牌指向它）。
> Kiro 在做任何中文写作 / 改写 / 润色 / 标题 / 公众号文章任务前，必须先读取并严格遵循下面这些正本文件。

## 动笔前必读（按顺序）

1. `agent/rules/introduction.md` —— 我是谁、写给谁、号的承诺。
2. `agent/rules/persona.md` —— 写作「底味」：口头禅、词汇黑名单（唯一来源）、正反案例、自检问题。
3. `agent/skills/house-style/SKILL.md` —— 文章结构、改写规则、阅读动线。

## 完整文章工作流

触发 `/write`、`/article`、「写文章」、「写公众号」、「找选题」时，严格按这份执行，逐个 CheckPoint 停下等用户选择：

- `agent/workflows/write_article.md`

## 配套技能（按需读取）

- 标题 / 文案：`agent/skills/copywriting/SKILL.md`
- 去 AI 味：`agent/skills/humanizer-zh/SKILL.md`
- 车道规则：`agent/lanes/车道A.md`（爆文流）、`agent/lanes/车道B.md`（干货流）、`agent/lanes/车道C.md`（观察思考流，解读型主力）

## 为什么这么设计

每个 IDE 只认自己门口的文件，但规则只该有一份。所以正本集中放在 `agent/`，各工具门口（Codex 的 `AGENTS.md`、Kiro 的本文件）只放一张指路牌，把 AI 领到同一份正本。

改规则只改 `agent/` 一处，所有工具同时生效，不用再到处抄、也不会改漏。
