#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拉取公众号「已发布」的全部图文文章，存到本地 published/ 目录。

用法：
  1. 在项目根目录 .env 里填 WECHAT_APPID / WECHAT_APPSECRET
  2. 公众号后台「设置与开发 → 基本配置 → IP 白名单」加入本机出口 IP
  3. python3 fetch_published.py

产出结构（存到「反思」目录）：
  ../反思/published/
  ├── INDEX.md                      # 全部文章索引（日期/标题/阅读地址）
  └── <YYYYMMDD>-<标题>/
      ├── article.md                # 正文（纯文本 + 图片引用）
      ├── article.html              # 原始 HTML（备查，转换有损时看这个）
      └── images/                   # 正文图片
"""

import json
import os
import re
import sys
import time
import html as html_mod
import urllib.request
import urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(ROOT), "反思", "published")
API = "https://api.weixin.qq.com/cgi-bin"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def load_env():
    env = {}
    path = os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        sys.exit("未找到 .env 文件，请先在项目根目录创建并填入 WECHAT_APPID / WECHAT_APPSECRET")
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def http_json(url, payload=None):
    data = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_token(appid, secret):
    r = http_json(f"{API}/token?grant_type=client_credential&appid={appid}&secret={secret}")
    if "access_token" not in r:
        code = r.get("errcode")
        if code == 40164:
            ip = re.search(r"invalid ip ([\d.]+)", r.get("errmsg", ""))
            sys.exit(f"当前出口 IP 不在白名单里{'（' + ip.group(1) + '）' if ip else ''}，"
                     f"请到公众号后台「基本配置 → IP 白名单」添加后重试。\n原始返回：{r}")
        sys.exit(f"获取 access_token 失败：{r}")
    return r["access_token"]


def safe_name(title, limit=40):
    name = re.sub(r'[\\/:*?"<>|\s]+', "-", title).strip("-")
    return name[:limit] or "untitled"


def img_ext(url):
    m = re.search(r"wx_fmt=(\w+)", url)
    if m:
        return "." + m.group(1).replace("jpeg", "jpg")
    m = re.search(r"\.(jpg|jpeg|png|gif|webp)", url, re.I)
    return "." + (m.group(1).lower() if m else "jpg")


def download_image(url, dest):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
            f.write(resp.read())
        return True
    except Exception as e:
        print(f"    图片下载失败（跳过）: {e}")
        return False


def html_to_md(content, img_dir):
    """微信正文 HTML → 简易 markdown：保住段落、标题层级尽力、图片下载到本地。"""
    os.makedirs(img_dir, exist_ok=True)
    imgs = []

    def repl_img(m):
        tag = m.group(0)
        src = re.search(r'data-src="([^"]+)"', tag) or re.search(r'src="([^"]+)"', tag)
        if not src:
            return ""
        url = html_mod.unescape(src.group(1))
        fname = f"{len(imgs) + 1:02d}{img_ext(url)}"
        imgs.append((url, os.path.join(img_dir, fname)))
        return f"\n\n![](images/{fname})\n\n"

    text = re.sub(r"<img[^>]*>", repl_img, content)
    text = re.sub(r"<br\s*/?>", "\n", text)
    # 块级标签结束视为段落分隔
    text = re.sub(r"</(p|section|div|h[1-6]|li|blockquote|figure)>", "\n\n", text)
    text = re.sub(r"<h([1-6])[^>]*>", lambda m: "\n\n" + "#" * int(m.group(1)) + " ", text)
    text = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_mod.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    for url, dest in imgs:
        download_image(url, dest)
        time.sleep(0.2)
    return text


def main():
    env = load_env()
    appid, secret = env.get("WECHAT_APPID"), env.get("WECHAT_APPSECRET")
    if not appid or not secret:
        sys.exit(".env 里缺 WECHAT_APPID 或 WECHAT_APPSECRET")
    token = get_token(appid, secret)
    os.makedirs(OUT_DIR, exist_ok=True)

    offset, total, index_rows = 0, None, []
    while total is None or offset < total:
        r = http_json(f"{API}/freepublish/batchget?access_token={token}",
                      {"offset": offset, "count": 20, "no_content": 0})
        if "item" not in r:
            sys.exit(f"拉取发布列表失败：{r}")
        total = r["total_count"]
        for item in r["item"]:
            ts = item["content"].get("create_time") or item.get("update_time", 0)
            date = time.strftime("%Y%m%d", time.localtime(ts))
            for news in item["content"]["news_item"]:
                if news.get("is_deleted"):
                    continue
                title = news.get("title") or "无标题"
                folder = os.path.join(OUT_DIR, f"{date}-{safe_name(title)}")
                os.makedirs(folder, exist_ok=True)
                print(f"[{date}] {title}")
                with open(os.path.join(folder, "article.html"), "w", encoding="utf-8") as f:
                    f.write(news.get("content", ""))
                md = html_to_md(news.get("content", ""), os.path.join(folder, "images"))
                header = (f"# {title}\n\n"
                          f"- 发布日期：{time.strftime('%Y-%m-%d', time.localtime(ts))}\n"
                          f"- 摘要：{news.get('digest', '')}\n"
                          f"- 线上地址：{news.get('url', '')}\n\n---\n\n")
                with open(os.path.join(folder, "article.md"), "w", encoding="utf-8") as f:
                    f.write(header + md + "\n")
                index_rows.append((date, title, os.path.basename(folder), news.get("url", "")))
        offset += r["item_count"]
        if r["item_count"] == 0:
            break

    index_rows.sort(reverse=True)
    with open(os.path.join(OUT_DIR, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("# 已发布文章索引\n\n| 日期 | 标题 | 本地目录 |\n|---|---|---|\n")
        for date, title, folder, url in index_rows:
            t = f"[{title}]({url})" if url else title
            f.write(f"| {date[:4]}-{date[4:6]}-{date[6:]} | {t} | {folder} |\n")
    print(f"\n完成：共 {len(index_rows)} 篇，存放在 {OUT_DIR}/，索引见 published/INDEX.md")


if __name__ == "__main__":
    main()
