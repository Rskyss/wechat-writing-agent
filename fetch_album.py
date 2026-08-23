#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过公众号「合集」公开页面，把合集内全部文章（线上正式版）下载到本地。
不需要任何 API 权限，适用于个人未认证号。

用法：
  python3 fetch_album.py "<合集链接>"
  # 合集链接形如 https://mp.weixin.qq.com/mp/appmsgalbum?__biz=xxx&action=getalbum&album_id=xxx

产出（复用 fetch_published.py 的目录结构）：
  ../反思/published/<YYYYMMDD>-<标题>/{article.md, article.html, images/}
  ../反思/published/INDEX.md
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

from fetch_published import OUT_DIR, UA, html_to_md, safe_name

MOBILE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
             "AppleWebKit/605.1.15 MicroMessenger/8.0.40")


def http_get(url, ua=MOBILE_UA):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def list_album(album_url):
    """翻页拉取合集内全部文章的 标题/时间/永久链接。"""
    q = urllib.parse.parse_qs(urllib.parse.urlparse(album_url).query)
    biz, album_id = q["__biz"][0], q["album_id"][0]
    articles, begin_msgid, begin_itemidx = [], "", ""
    while True:
        url = (f"https://mp.weixin.qq.com/mp/appmsgalbum?action=getalbum"
               f"&__biz={urllib.parse.quote(biz)}&album_id={album_id}&count=20&f=json"
               f"&begin_msgid={begin_msgid}&begin_itemidx={begin_itemidx}")
        r = json.loads(http_get(url))
        resp = r.get("getalbum_resp", {})
        batch = resp.get("article_list", [])
        if isinstance(batch, dict):  # 只剩一篇时微信会返回对象而不是数组
            batch = [batch]
        if not batch:
            break
        articles.extend(batch)
        if str(resp.get("continue_flag", "0")) != "1":
            break
        begin_msgid, begin_itemidx = batch[-1]["msgid"], batch[-1]["itemidx"]
        time.sleep(1)
    return articles


def fetch_article(url):
    """抓单篇文章页，返回 (标题, 发布时间戳, 正文HTML)。"""
    page = http_get(url)
    if "环境异常" in page or "verify" in page[:2000].lower():
        return None, None, None
    m = re.search(r'<meta property="og:title" content="([^"]*)"', page)
    title = m.group(1) if m else ""
    m = re.search(r"var ct\s*=\s*['\"](\d+)['\"]", page) or re.search(r'createTime\s*[:=]\s*[\'"](\d+)', page)
    ts = int(m.group(1)) if m else 0
    m = re.search(r'<div[^>]*id="js_content"[^>]*>(.*?)</div>\s*<script', page, re.S)
    if not m:
        m = re.search(r'<div[^>]*id="js_content"[^>]*>(.*)', page, re.S)
    content = m.group(1) if m else ""
    return title, ts, content


def main():
    if len(sys.argv) < 2:
        sys.exit("用法：python3 fetch_album.py \"<合集链接>\"")
    articles = list_album(sys.argv[1])
    print(f"合集内共 {len(articles)} 篇文章\n")
    os.makedirs(OUT_DIR, exist_ok=True)

    index_rows, failed = [], []
    for i, a in enumerate(articles, 1):
        url = a["url"].replace("http://", "https://")
        title = a.get("title", "")
        ts = int(a.get("create_time", 0))
        date = time.strftime("%Y%m%d", time.localtime(ts))
        print(f"[{i}/{len(articles)}] {date} {title}")
        try:
            page_title, page_ts, content = fetch_article(url)
        except Exception as e:
            print(f"    抓取失败：{e}")
            failed.append((date, title, url))
            continue
        if not content:
            print("    没拿到正文（可能触发了反爬校验），记入失败清单")
            failed.append((date, title, url))
            continue
        folder = os.path.join(OUT_DIR, f"{date}-{safe_name(title)}")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "article.html"), "w", encoding="utf-8") as f:
            f.write(content)
        md = html_to_md(content, os.path.join(folder, "images"))
        header = (f"# {title}\n\n"
                  f"- 发布日期：{time.strftime('%Y-%m-%d', time.localtime(ts))}\n"
                  f"- 线上地址：{url}\n\n---\n\n")
        with open(os.path.join(folder, "article.md"), "w", encoding="utf-8") as f:
            f.write(header + md + "\n")
        index_rows.append((date, title, os.path.basename(folder), url))
        time.sleep(2)  # 控制频率，避免触发反爬

    index_rows.sort(reverse=True)
    with open(os.path.join(OUT_DIR, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("# 已发布文章索引（来自合集抓取）\n\n| 日期 | 标题 | 本地目录 |\n|---|---|---|\n")
        for date, title, folder, url in index_rows:
            f.write(f"| {date[:4]}-{date[4:6]}-{date[6:]} | [{title}]({url}) | {folder} |\n")
        if failed:
            f.write("\n## 抓取失败（需重试或手动处理）\n\n")
            for date, title, url in failed:
                f.write(f"- {date} [{title}]({url})\n")
    print(f"\n完成：成功 {len(index_rows)} 篇，失败 {len(failed)} 篇，存放在 {OUT_DIR}/")


if __name__ == "__main__":
    main()
