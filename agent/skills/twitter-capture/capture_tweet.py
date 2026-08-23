#!/usr/bin/env python3
"""
X(Twitter) 推文真实截图工具
用法:
  python3 agent/skills/twitter-capture/capture_tweet.py <推文URL或ID> <输出.png> [--embed] [--pad N] [--search "关键词" --profile <目录>]

红线(最高优先级): 只允许两种像素级后处理——裁边(裁掉边缘的 UI 杂条,如访客页 Read replies 条)
和四周留白。**严禁删改页面内容(藏图/压行/补假 UI)后冒充截图,严禁伪造任何互动数据。**

模式一(默认): 访客详情页直截 —— 首选,无需登录
  访问 x.com/i/status/<ID>,截 article 元素。原生界面+完整热度数据
  (浏览量/评论/转发/赞/收藏行访客都能看到)。长推正文会全文展开,图会长——接受它,
  或改用模式三拿原生截断卡。

模式二(--embed): 公开嵌入页 —— 兜底
  访客详情页哪天被 X 关掉时用。无热度行,只做样式扒壳(去边框/Follow,不动内容)。

模式三(--search): 登录态搜索卡片 —— 需要"原生截断+Show more"的短版时用
  搜索结果里的长推卡片是 X 自己截断的(真实的 Show more+热度行,零编辑)。
  需要登录态: --profile 指向已登录的 Chrome user-data-dir(如项目 .x-browser-profile,
  用户在其中登录一次;注意退出浏览器要正常关闭,pkill 强杀会丢登录态)。
  用法: capture_tweet.py <推文ID> <输出.png> --search 'from:用户名 "精确短语"' --profile .x-browser-profile

依赖: pip install playwright pillow numpy && python3 -m playwright install chromium
"""
import re
import sys

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")

EMBED_STRIP_CSS = """
article, article > div { border: none !important; box-shadow: none !important; border-radius: 0 !important; }
html, body, #app, article { background: #ffffff !important; }
"""

EMBED_HIDE_JS = """
() => {
  document.querySelectorAll('a,span,div[role="button"]').forEach(el => {
    const t = (el.textContent || '').trim();
    if (t === 'Follow' || t === '关注') { (el.closest('a') || el).style.display = 'none'; }
  });
  document.querySelectorAll('a[role="link"],div[role="button"]').forEach(el => {
    if (/Read .*repl/i.test(el.textContent || '')) (el.closest('div[style]') || el).style.display = 'none';
  });
  document.querySelectorAll('div').forEach(el => {
    const t = el.textContent || '';
    if (el.children.length && /Copy link to post/.test(t) && /Reply/.test(t)
        && el.querySelectorAll('a,div[role="button"]').length <= 8 && !el.querySelector('article')) {
      el.style.display = 'none';
    }
  });
  document.querySelectorAll('[aria-label*="Learn more"]').forEach(el => el.style.display='none');
}
"""


def crop_reply_bar(path):
    """裁边: 访客页底部 'Read N replies' 灰色圆角条(边缘 UI 杂条,允许裁)"""
    from PIL import Image
    import numpy as np
    im = Image.open(path).convert("RGB")
    a = np.array(im)
    H, W = a.shape[:2]
    mid = a[:, W // 4:W * 3 // 4, :]
    gray = ((np.abs(mid[:, :, 0].astype(int) - 239) < 10)
            & (np.abs(mid[:, :, 1].astype(int) - 243) < 10)
            & (np.abs(mid[:, :, 2].astype(int) - 244) < 10))
    frac = gray.mean(axis=1)
    rows = [i for i in range(H - 1, max(0, H - 400), -1) if frac[i] > 0.8]
    if rows:
        im.crop((0, 0, W, min(rows) - 12)).save(path)


def add_padding(path, pad):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    c = Image.new("RGB", (im.width + pad * 2, im.height + pad * 2), (255, 255, 255))
    c.paste(im, (pad, pad))
    c.save(path)


def capture(tweet, out_path, embed=False, pad=32, search=None, profile=None):
    m = re.search(r"(\d{15,20})", tweet)
    if not m and not search:
        sys.exit("无法从参数解析推文ID")
    tid = m.group(1) if m else None
    with sync_playwright() as p:
        if search:
            if not profile:
                sys.exit("--search 需要 --profile 指向已登录的浏览器配置目录")
            ctx = p.chromium.launch_persistent_context(
                profile, channel="chrome", headless=False,
                viewport={"width": 640, "height": 2200}, device_scale_factor=2,
                locale="en-US", args=["--window-position=2000,2000"])
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            from urllib.parse import quote
            page.goto(f"https://x.com/search?q={quote(search)}&f=top",
                      wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector('article[data-testid="tweet"]', timeout=30000)
            page.wait_for_timeout(3000)
            el = page.query_selector('article[data-testid="tweet"]')
            el.screenshot(path=out_path)
            ctx.close()
        else:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={"width": 640, "height": 2200},
                                device_scale_factor=2, locale="en-US", user_agent=UA)
            page = ctx.new_page()
            if embed:
                page.goto(f"https://platform.twitter.com/embed/Tweet.html?id={tid}&theme=light&lang=en&dnt=true",
                          wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(2500)
                page.add_style_tag(content=EMBED_STRIP_CSS)
                page.evaluate(EMBED_HIDE_JS)
                page.wait_for_timeout(400)
            else:
                page.goto(f"https://x.com/i/status/{tid}", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(6000)
            el = page.query_selector("article") or page.query_selector("body")
            el.screenshot(path=out_path)
            b.close()
            if not embed:
                crop_reply_bar(out_path)
    if pad > 0:
        add_padding(out_path, pad)
    print("saved:", out_path)


if __name__ == "__main__":
    argv = sys.argv[1:]
    args, kv = [], {}
    i = 0
    while i < len(argv):
        if argv[i] in ("--search", "--profile", "--pad"):
            kv[argv[i][2:]] = argv[i + 1]; i += 2
        elif argv[i].startswith("--"):
            kv[argv[i][2:]] = True; i += 1
        else:
            args.append(argv[i]); i += 1
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    capture(args[0], args[1],
            embed=bool(kv.get("embed")),
            pad=int(kv.get("pad", 32)),
            search=kv.get("search"),
            profile=kv.get("profile"))
