---
name: twitter-capture
description: 抓取推特(X.com)推文的真实截图。首选「访客详情页直截」（无登录、原生界面+完整热度数据）；需要原生截断短版用「登录态搜索卡片」；「嵌入页」兜底。红线：只许裁边和留白，严禁删改页面内容后冒充截图。
---

# 推特(X)推文真实截图 Skill

**适用场景**：文章需要 X 推文/评论的真实截图时（②类来源截图），必须使用此技能。

## ⛔ 红线（最高优先级，2026-07 用户明确划定）

**"真实截图"= 页面渲染什么截什么。**只允许两种像素级后处理：
- **裁边**：裁掉边缘的 UI 杂条（访客页"Read N replies"条、登录页"Relevant/View quotes"行）
- **留白**：四周补 32px 白边（用户校准值；56 太多，贴边不行）

**严禁**：藏图/删引用卡/CSS 压行截断/自己补"Show more"或任何 UI 元素/伪造互动数据。哪怕内容一字未改，"编辑过的页面"也不是截图。想要短版 → 用方法二拿 X 原生的截断卡，不许自己造。

## 🥇 方法一：访客详情页直截（默认，无需登录）

`https://x.com/i/status/<推文ID>` 对未登录访客完整渲染，**带全套真实热度数据**（浏览量/评论/转发/赞/收藏）。别被 WebFetch 的 402 骗了——那是接口层拦截，真浏览器能进。

```bash
python3 skills/twitter-capture/capture_tweet.py <推文ID> output/<slug>/images/<文件名>.png
```

- 长推正文会全文展开，图会长——**接受它**，或改用方法二拿原生截断卡。
- 推文 ID 从 URL 的 `/status/` 后取；没有 URL 用 Tavily 搜 `site:x.com <关键词>` 找（引用转发/大V评论常被索引）。

## 🥈 方法二：登录态搜索卡片（要"原生截断+Show more"短版时用；**按需启用，优先 MCP 路线**）

> 2026-07 决策：登录态场景优先用 **Playwright MCP + Browser Bridge 扩展**（微软官方，直连用户日常已登录的 Chrome，无自动化指纹、无需维护登录目录），用户装扩展后 `claude mcp add playwright -- npx @playwright/mcp@latest` 即可。下面的手搓登录目录法仅作 MCP 不可用时的备选。
>
> **2026-07-17 实测通过**，MCP 路线 SOP：①首次连接会在用户 Chrome 弹授权页，让用户点任意标签的 Allow & select；②`browser_navigate` 到 `x.com/search?q=from%3A用户名 "精确短语"&f=live`；③`browser_snapshot` 找到含 Show more 的目标 article 的 ref；④`browser_take_screenshot` 传 `target=<ref>` + `scale=device` 截元素图；⑤用完把用户浏览器导航回 x.com/home。
> **已知坑：Cici/豆包翻译扩展会往页面注入第二个 `<body>`，导致 Playwright 所有操作报 "strict mode violation: locator('body') resolved to 2 elements"，MCP 侧无法绕过**——让用户在 `chrome://extensions` 暂时关掉该扩展再重试。

搜索结果里的长推卡片是 **X 自己截断的**：真实的 Show more、真实热度行、高度只有全文的 1/3——这才是合法的短版来源。

```bash
python3 skills/twitter-capture/capture_tweet.py <推文ID> <输出.png> \
  --search 'from:用户名 "推文里一段精确短语"' --profile .x-browser-profile
```

- **需要登录态**：项目 `.x-browser-profile/`（已 gitignore）里存着用户登录过的 Chrome 配置。失效时让用户重新登录一次：
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --user-data-dir=<项目>/.x-browser-profile https://x.com/login`
- 登录态运维教训（都踩过）：**pkill 强杀 Chrome 会丢没落盘的登录态**，要正常关窗口；**headless 模式会被 X 识别拒服务**，用 `headless=False` + 把窗口挪到屏幕外（`--window-position=2000,2000`）；Playwright 自带 Chromium 的登录按钮会被 X 废掉（疑似人机验证组件加载失败），**登录动作必须在真 Chrome 里做**。
- 线程详情页第一个 article 是**父推文**，不是焦点推——按关键词匹配目标卡片再截（活教材：截隐私跟帖结果截成了主推）。

## 🥉 方法三：嵌入页扒壳（兜底）

访客详情页哪天被 X 关掉时用：`--embed`。无热度行；只做样式扒壳（去边框/Follow 按钮，不动内容）。

## 通用 SOP

1. 截完**必须用 Read 工具亲眼看图**，核两件事：
   - **图文一致**：推文全文可能推翻你从摘要得到的定性（活教材：Dan Fitzpatrick 开头 BREAKING 报喜、后半段批判"免费不是慷慨"——只看摘要会把他写成庆祝派）。图里读者看得到的每句话，正文转述不能跟它打架。
   - **数字一致**：正文引用的浏览量/点赞必须和图内显示一致。
2. **一处一张推文图，严禁多条竖拼长图**（用户明确反馈）。
3. 截图存 `output/<slug>/images/`，`sources.md` 登记：文件名+内容说明+来源推文 URL。
