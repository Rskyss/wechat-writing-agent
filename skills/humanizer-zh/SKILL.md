---
name: humanizer-zh
description: Remove AI-generated tone and rewrite text to sound like a real native Chinese internet user.
---

# Humanizer-Zh Skill

> **路径说明**：下文的 `${CLAUDE_SKILL_DIR}` 指本 skill 所在目录。若你的工具不展开这个变量（Claude Code、CodeBuddy/WorkBuddy 会展开），按**相对本文件所在目录**解析即可，效果相同。

This skill transforms "AI-written text" into "Human-written text".

## Detection Indicators (What to remove)

具体禁用词（过渡词、抽象名词、商业黑话、AI 情绪表演词）以 persona.md 的「词汇黑名单」为准，本文件不重复列。本文件只盯这两类**靠词表查不出来**的 AI 味：

- **Balanced Structure**: 段落长度过于工整、几乎一样长。
- **Neutral Tone**: 没有情绪、没有立场、四平八稳。

## Rewrite Rules (How to fix)

### 1. Break the Structure (打破结构)
- Mix very short sentences (2-5 words) with longer explanations.
- Use one-sentence paragraphs for emphasis.

### 2. Street-Corner Test (街角语体同频)
- **核心逻辑**：如果全篇要走口语化路线，那么**专业原理解释部分也必须同步“下凡”**。
- **禁止词汇割裂**：严禁一边用“逻辑剥丝抽茧”般的高端学术腔，一边突然生硬插入“卧槽”、“流哈喇子”、“吓出一身冷汗”。
- **做法**：用向大爷解释的方式重写原理解释段落（例如：“它利用自动化插件进行毫秒级抓取” 改为 “这玩意就像个不知疲倦的贩子，死盯着两边市场倒买倒卖”）。
- **口语填充自然化**：可以加“说实话”、“我看了一下”，但只能加在语境匹配的句子前。

### 3. Physical Grounding (物理接地)
- Instead of "I felt anxious", say "I stared at the screen, palms sweating".
- Instead of "It is fast", say "I blinked, and it was done".

### 4. Peer Voice（平等交流）
- "你"不需要频繁出现。口语感来自真实动作、具体判断和自然句子，不靠不断点读者的名字。
- 遵守 `persona.md` 的「和读者并肩，不当读者的爹」：不替读者预设想法，不用命令式建议。
- 优先写"我是怎么做的"、"这个场景可以怎么测"、"我的判断是"，给依据和选项，把决定权留给读者。

## Output Check
Before outputting, read the text aloud (internally). If it sounds like a broadcast news anchor, REWRITE IT. It should sound like a friend talking over hotpot.

---

## 六不原则 (Six "Don'ts" - Anti-AI Rules)

写作过程中，必须严格遵守以下禁止项：

### ❌ 不用教学式序号
- **禁止**: "第一步...第二步...第三步..."
- **替代**: "先...然后...最后..." 或 "我是这么做的：..."

### ❌ 不用对称排比
- **禁止**: 连续 3 个以上的"不仅...而且..."、"既...又..."
- **替代**: 打乱节奏，用不同句式

### ❌ 不用完美收尾
- **禁止**: 每段都以反问句或总结句结尾
- **替代**: 至少 2 个段落"不完整"（突然结束、跑题、留白）

### ❌ 不用通用外链
- **禁止**: 只给分类页 URL（如 `https://techcrunch.com/category/ai/`）
- **替代**: 具体文章链接 或 "建议搜索：XX 关键词"

### ❌ 不用术语堆砌
- **禁止**: 商业黑话密度 > 1 个/千字（完整清单见 persona.md 的「词汇黑名单」）
- **替代**: 用大白话（"碾压"、"帮忙"、"核心道理"）

### ❌ 不用情绪词代替具体描写
- **禁止**: "我很焦虑"、"我很兴奋"
- **替代**: "我盯着屏幕，手心全是汗" / "我把那条消息的时间戳翻出来看了三遍"

---

## 强制检查清单 (Mandatory Checklist)

**在文章生成完成后，必须逐条确认以下 7 项。任何一项不通过 → 立即重写对应段落。**

### ✅ Checklist（每项必须打勾）

- [ ] **结构检查**: 是否有至少 **2 个段落"不完整"**（如突然结束、跑题后拉回、只有例子没总结）？
- [ ] **情绪检查**: 是否有至少 **3 处情绪外露**（无语、惊讶、自嘲、吐槽）？
- [ ] **物理细节**: 是否有至少 **1 处"物理接地"描写**（而非"我很焦虑"这种抽象词）？
- [ ] **链接检查**: 所有外链是否指向**具体文章**（而非分类页）？如果找不到具体文章，是否改用"建议搜索：XX"？
- [ ] **工具推荐**: 是否避免了**"第一步/第二步"式的教学结构**？改用"我是这么做的"或"试试这个方法"？
- [ ] **网络梗密度**: 全文网络梗 **≤ 3 个**（过多会显得"刻意模仿"）？
- [ ] **段落长度**: 是否至少有 **2 个相邻段落的句子数差值 ≥ 3**（避免过于工整）？

**如果任何一项不通过 → 不要输出，返回修改。**

---

## 使用建议

1. **写作时实时应用**: 每写完 2 个模块，暂停，应用本 Skill 检查这 2 个模块。
2. **生成后全文检查**: 跑 `python3 ${CLAUDE_SKILL_DIR}/../write-article/scripts/detect_ai_tone.py <文章.md>` 自动检测 AI 味。
3. **优先修复**: 如果检测不通过，优先修复"结构工整度"和"外链真实性"（这两项最容易被 AI 检测器识别）。
