# 公众号写作 Agent · 一个中立大脑 + 每个 AI 工具一张门牌

把「怎么写公众号文章」这件事，写成一套 AI 工具能直接读懂并执行的规则系统。

不是 prompt 合集，是一条**带强制检查点的流水线**：选题 → 角度 → 车道 → 标题 → 正文 → 质检 → 转微信 HTML。规则只有一份正本，Claude Code / Codex / Kiro / Antigravity 四套工具同时生效。

> 这套系统跑了半年多、上百篇稿子，里面的规则大多是**踩坑之后反推出来的**（比如 AI 写"惊讶"时必用"后背发凉"、参考范文时会不自觉复制人家的比喻、AI 整理二手资料时会给错误镀金）。规则本身比框架值钱。

---

## 它解决什么问题

用 AI 写长文，最常见的三个坑：

1. **AI 味洗不掉**——"综上所述""本质上""不是 A，而是 B"，读者一眼看出是机器写的。
2. **每次都要重新交代要求**——上次说过的规矩，这次又得说一遍。
3. **越改越像别人**——让 AI 参考一篇爆款，它会不自觉把人家的框架、比喻、金句一起搬过来。

这套系统的对策分别是：一份持续增补的**词汇黑名单 + 句式黑名单**（并且有脚本自动检测）、一份**所有工具共读的规则正本**、一条**原创性红线 + 逐段比对自查**。

---

## 安装

**这就是 5 个标准 `SKILL.md` 技能**（write-article、house-style、humanizer-zh、copywriting、twitter-capture），装到哪个工具都是同一套东西。各家只是取用方式不同。

### 通用：一条命令装到任意工具

```bash
git clone https://github.com/Rskyss/wechat-writing-agent.git && cd wechat-writing-agent
bash install.sh                    # 自动识别你装了哪些工具，全装上
```

也可以指定：`bash install.sh workbuddy` / `codebuddy` / `codex` / `claude`，
加 `--project` 则装到当前项目而非用户全局。

技能落到各自的目录：`~/.workbuddy/skills/`、`~/.codebuddy/skills/`、`~/.codex/skills/`、`~/.claude/skills/`。

### Claude Code / Codex：也可以走插件市场

这两家支持从 GitHub 直接拉，不用先 clone：

```
# Claude Code
/plugin marketplace add Rskyss/wechat-writing-agent
/plugin install wechat-writing@wechat-writing-agent
```

```bash
# Codex
codex plugin marketplace add Rskyss/wechat-writing-agent
codex plugin add wechat-writing@wechat-writing-agent
```

### WorkBuddy：也可以直接把仓库地址丢给它

在对话里贴上本仓库地址，让它帮你装，它会自己把技能放进 `~/.workbuddy/skills/`。

---

**装完第一件事**：规则里的人设、读者定位、字数区间来自一个具体的号，直接用会让你的稿子带上别人的味道。要改的两个文件：

- `write-article/rules/introduction.md` — 我是谁、写给谁、号的承诺
- `write-article/rules/persona.md` — 口吻、A–E 类黑名单、红线

直接跟 AI 说「打开写作规则的 introduction.md，帮我改成我的号」即可。

### 另一条路：clone 整个仓库当项目脚手架

想要本地预览应用、想改脚本、或者用 Kiro / Antigravity 的，走这条：

```bash
git clone https://github.com/Rskyss/wechat-writing-agent.git writing && cd writing
cp account_profile.example.json account_profile.json   # 填自己的号名和名片（可选）
./1.sh                                                  # 启动本地预览（端口 8000）
```

四套工具的门牌都已配好，打开目录说「写文章」即可。

---

## 架构：规则正本 = 插件本体 + 多张门牌

每个 AI 工具只认自己门口的特殊文件（Claude Code 认 `CLAUDE.md`，Codex 认 `AGENTS.md`…）。如果每个工具各存一份规则，改一次要改四处，很快就会不一致。

所以：规则**只有一份正本**放在 `skills/write-article/`，每个工具门口放**一张指向它的薄门牌**，本身不存规则。

正本之所以放在 `skills/` 而不是一个中立的 `agent/` 文件夹，是因为 Claude Code 安装插件时**只复制插件目录本身**——规则放在目录外，装到别人机器上就只剩一张空纸条。放进去之后，规则、车道、质检脚本随插件一起走。

| 文件/目录 | 角色 |
|---|---|
| **`skills/`** | **唯一正本**：身份 / 性格 / 写作方法 / 车道 / 脚本，同时是插件本体 |
| `.claude-plugin/` | 插件与市场清单（让别人能装） |
| `CLAUDE.md` | Claude Code 在本仓库内的门牌 |
| `AGENTS.md` | Codex 的门牌 |
| `.kiro/steering/` + `.kiro/hooks/` | Kiro 的门牌 |
| `.agent/rules/_brain-pointer.md` | Antigravity 的门牌（always_on） |

**改规则只改 `skills/` 一处，四套工具同时生效。**

如果你的工具不在表里（Cursor、Cline、Windsurf、Gemini CLI…），照着 `AGENTS.md` 的格式新建一张薄门牌即可，内容就一句话：规则在 `skills/write-article/`，先读 rules 下那两个文件。

---

## 写作流程（6 个强制检查点）

每个检查点都**停下来等你选**，不一口气写完——这是刻意的，AI 单跑到底的稿子基本不能用。

| Step | 做什么 | 产出 |
|---|---|---|
| 1 | 双轨搜索热点 | 10 个选题 → 你选 1 个 |
| 2 | 深度挖掘（调 sequentialthinking） | 10 个角度，带传播/实用/深度评分 → 你选 1 个 |
| 3 | 车道建议 | A 爆文流 / B 干货流 / C 观察思考流 → 你选 |
| 4 | 按车道规则起标题 | 10 个标题 → 你选 |
| 5 | 写正文 | 先加载人设规则，实时去 AI 味 |
| 5.5 | 自动质检 | 跑 `check_article.py`，技术类文章额外做准确性审查 |
| 6 | 转 HTML + 同步预览 | 微信可直接粘贴的 HTML |

**三条车道**是从实际发布数据反推出来的，不是拍脑袋分的：

- **车道A 爆文流**：热点 + 情绪钩子，1000–2500 字
- **车道B 干货流**：方法论 + 可操作步骤，2500–3000 字
- **车道C 观察思考流**：交付判据和思考，**不教人做事**，2000–2800 字

车道C 最容易被写歪——它和 B 的分界是"给读者一种看事情的角度"而非"一套操作步骤"，规则里为此单列了禁用句式清单（"具体能做的事""你可以这么做""三步走"…）。

---

## 质检：规则不靠自觉，靠脚本卡

```bash
python3 skills/write-article/scripts/check_article.py output/<article-slug>/<article-slug>.md
```

一条命令跑完四组检查，退出码 1 表示有必须修复项：

1. **结构字数**——车道区间、必需章节
2. **AI 味检测**——A 类八股 / B 类商业黑话 / C 类距离感 / D 类情绪表演 / E 类对比句式
3. **人设黑名单**——动态读取 `persona.md`，改规则不用改脚本
4. **平台合规与引用溯源**——含"拿域名首页冒充数据来源"检测

其中 **E 类**（"不是 A，而是 B"及其变体）和 **D 类**（"后背发凉""手心出汗"这类身体感觉标签）是 AI 最难自查的两类，必须靠脚本拦。

---

## 目录速览

```
skills/                        📦 正本 = 插件本体（装走的就是这个）
├── write-article/             主入口 skill
│   ├── SKILL.md                  流程总纲，用 ${CLAUDE_SKILL_DIR} 指路
│   ├── rules/
│   │   ├── introduction.md       我是谁、写给谁、号的承诺   ← 必改
│   │   └── persona.md            口吻、A–E 类黑名单、红线   ← 必改
│   ├── workflows/
│   │   ├── write_article.md      长文 SOP（6 个检查点）
│   │   └── image_post*.md        图文（微信图片消息）规则
│   ├── lanes/                    车道A / 车道B / 车道C
│   ├── references/               商业分析、故事叙事等分析框架
│   └── scripts/
│       ├── check_article.py      统一质检入口（正式流程只认这个）
│       ├── audit_article.py      结构字数检查
│       ├── detect_ai_tone.py     AI 味检测
│       ├── convert_to_wechat.py  Markdown → 微信 HTML
│       └── account_profile.py    读取你的号名/名片
├── house-style/               结构层：文章长什么样
├── humanizer-zh/              去 AI 味
├── copywriting/               标题与文案
└── twitter-capture/           抓推文截图

.claude-plugin/                插件与市场清单（让别人能装）
CLAUDE.md / AGENTS.md / .agent/ / .kiro/    各工具门牌，指向 skills/

以下只在 clone 整个仓库时才有（不随插件安装）：
preview_app/                   本地预览应用（./1.sh 启动）
sync_articles.py               同步文章到预览列表
fetch_published.py             抓取线上已发布文章做比对
tests/                         脚本回归测试
account_profile.json           你的号名/名片（本地私有，已 gitignore）
```

---

## 可选：第三方发布技能

本仓库**不包含**第三方技能（如宝玉的 baoyu-* 全家桶：出图、转 HTML、发布到微信/X 等）。原仓库用过它们，但那是别人的作品，不随本仓库分发。需要的话请从作者本人的渠道获取，放到 `skills/` 下即可被同样的门牌机制识别。

内置的 `convert_to_wechat.py` 已能覆盖「Markdown → 微信 HTML」这一步，不装第三方技能也能跑完整条流水线。

---

## 说明

- 规则文件里的示例人设、车道字数区间、黑名单词表，都来自一个具体的号。**直接拿去用会让你的稿子带上别人的味道**，请务必按自己的定位改写 `introduction.md` 和 `persona.md`。
- `output/`（文章成品）、`img_outputs/`（图文成品）、`account_profile.json`（账号资料）默认都不进 Git。
