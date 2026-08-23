#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一质检入口 - 一条命令跑完文章发布前的全部自检
用法: python3 skills/write-article/scripts/check_article.py output/<article-slug>/<article-slug>.md

检查项:
  1. audit_article.py     结构/字数/第一人称
  2. detect_ai_tone.py    AI 味六维检测 + E类对比句式
  3. persona.md 黑名单    A/B/C/D 类禁用词（动态读取 persona.md，改黑名单不用改脚本）
  4. 平台合规             诱导关注/导流话术、敏感表述（微信推荐流红线）
  5. 引用与标点           正文数据溯源、英文直引号、中文弯引号不超过 4 对

退出码: 0 = 全部通过，1 = 存在必须修复项
"""

import os
import re
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 规则正本与本脚本同在 skill 目录内：scripts/ 的上一级就是 skill 根
SKILL_DIR = os.path.dirname(BASE_DIR)
PERSONA_PATH = os.path.join(SKILL_DIR, "rules", "persona.md")

# persona.md 里标注"尽量少用/有条件使用"的词，只警告不判死
SOFT_WORDS = {"生态", "矩阵", "赛道", "颠覆性", "革命性", "划时代", "使用", "利用"}

# 平台合规硬红线：命中即不通过（微信"诱导关注/不正当引流"处罚为删文到封号）
COMPLIANCE_HARD = [
    (r"魔法上网", "敏感表述，改为“国际网络环境”"),
    (r"关注(公众号)?(之后|后|才)(可|能|才能|即可|方可|解锁)", "诱导关注话术"),
    (r"关注解锁", "诱导关注话术"),
    (r"仅粉丝可见", "诱导关注话术"),
    (r"回复.{0,8}(才能|才可|解锁)", "不正当引流话术：内容必须正文自足"),
    (r"不关注就", "诱导关注话术"),
]

# 合规警告：允许出现但要人工确认场景合理（推荐流下被举报风险高）
COMPLIANCE_WARN = [
    (r"加我微信", "私域导流，确认是用户素材明确要求"),
    (r"扫(描|码).{0,6}二维码|二维码", "扫码导流，确认场景必要"),
    (r"进群", "社群导流，确认是用户素材明确要求"),
]


def load_persona_blacklist():
    """从 persona.md 的「词汇黑名单」区解析 A/B/C/D 类禁用词。

    返回 dict: {"A": [...], "B": [...], "C": [...], "D": [...]}
    E 类句式由 detect_ai_tone.py 负责，这里跳过。
    """
    if not os.path.exists(PERSONA_PATH):
        return {}

    with open(PERSONA_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"## 二、词汇黑名单(.*?)\n## 三、", content, re.DOTALL)
    if not match:
        return {}
    section = match.group(1)

    blacklist = {}
    current = None
    for line in section.splitlines():
        header = re.match(r"###\s+🚫\s+([A-E])类", line)
        if header:
            current = header.group(1)
            continue
        if current is None or current == "E":
            continue
        row = re.match(r"\|\s*([^|]+?)\s*\|", line)
        if not row:
            continue
        first_cell = row.group(1).strip()
        if first_cell in ("禁用词", "禁用句式") or set(first_cell) <= {"-", " "}:
            continue
        for token in first_cell.split("/"):
            token = token.strip()
            # 跳过占位模板（首先……其次……、进行XX操作等），由 detect_ai_tone 或人工把关
            if not token or len(token) < 2 or "…" in token or "XX" in token:
                continue
            blacklist.setdefault(current, []).append(token)
    return blacklist


def scan_blacklist(text):
    """扫描 A/B/C/D 类禁用词。返回 (hard_hits, soft_hits)。"""
    blacklist = load_persona_blacklist()
    hard_hits, soft_hits = [], []
    for category, words in blacklist.items():
        for word in words:
            count = text.count(word)
            if count == 0:
                continue
            item = f"[{category}类] {word} × {count}"
            if word in SOFT_WORDS or category == "C":
                soft_hits.append(item)
            else:
                hard_hits.append(item)
    return hard_hits, soft_hits


def scan_compliance(text):
    """平台合规扫描。返回 (hard_hits, warn_hits)。"""
    hard_hits, warn_hits = [], []
    for pattern, reason in COMPLIANCE_HARD:
        found = re.findall(pattern, text)
        if found:
            hard_hits.append(f"{reason}（命中 {len(found)} 处，模式: {pattern}）")
    for pattern, reason in COMPLIANCE_WARN:
        found = re.findall(pattern, text)
        if found:
            warn_hits.append(f"{reason}（命中 {len(found)} 处）")
    return hard_hits, warn_hits


def check_citation(text):
    """正文有数据表述但全文没有任何 http 链接时提醒。"""
    body_match = re.search(r"## 正文成稿\n(.*?)(\n## 写在最后|$)", text, re.DOTALL)
    body = body_match.group(1) if body_match else text
    has_data = bool(re.search(r"\d+(\.\d+)?\s*%|数据显示|报告(称|说|提到|指出)|调查", body))
    has_link = bool(re.search(r"https?://", body))
    issues = []
    if has_data and not has_link:
        issues.append("正文出现了数据/报告表述，但引用处没有任何 URL（规则：引用处必须直接带真实链接）")
    # 裸域名当来源 = 等同编造引用（车道C 第11条）。真实来源链接一定带路径。
    # 只判「看起来是来源标注」的链接（锚文字含日期/报告/机构等），
    # 产品入口、工具官网这类裸域名是正常用法，不算。
    pairs = re.findall(r"\[([^\]]*)\]\((https?://[^/)\s]+/?)\)", body)
    src_like = re.compile(r"\d{4}\s*年|\d+\s*月\s*\d+\s*日|报告|来源|据[^\u4e00-\u9fa5]{0,4}称|研究|调查|统计|白皮书|论文|Report|20\d\d")
    bare = [u for a, u in pairs if src_like.search(a)]
    if bare:
        issues.append(
            "引用链接只有域名没有具体文章路径，等同编造引用，必须换成能打开的原文地址"
            f"（{'、'.join(sorted(set(bare)))}）；手上没有具体链接就写清「报告名+发布方+日期」并注明依据的是哪处转述"
        )
    return issues


def check_punctuation(text):
    """检查全部读者可见正文（从「正文成稿」到文末）。

    代码块内不计；英文直引号禁用；中文弯引号最多 4 对且必须成对。
    """
    body_match = re.search(r"## 正文成稿\n(.*)$", text, re.DOTALL)
    body = body_match.group(1) if body_match else text
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)   # 去掉围栏代码块
    body = re.sub(r"`[^`\n]*`", "", body)                     # 去掉行内代码
    issues = []
    straight_count = body.count('"')
    if straight_count:
        issues.append(
            f'正文有 {straight_count} 个英文直引号 "，中文正文必须用中文弯引号 “”'
            '（转微信后直引号显示为竖直的一撇，很扎眼）'
        )

    open_count = body.count("“")
    close_count = body.count("”")
    if open_count != close_count:
        issues.append(
            f"正文中文弯引号没有成对：左引号 {open_count} 个，右引号 {close_count} 个"
        )
    elif open_count > 4:
        issues.append(f"正文有 {open_count} 对中文弯引号，硬规则要求不得超过 4 对")
    return issues


def run_script(script, filepath):
    """运行子脚本，透传输出，返回是否通过。"""
    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, script), filepath],
        capture_output=True, text=True,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.returncode == 0


def main():
    if len(sys.argv) != 2:
        print("用法: python3 skills/write-article/scripts/check_article.py output/<article-slug>/<article-slug>.md")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    failed = []

    print("\n" + "=" * 50)
    print("📋 统一质检 [1/4] 结构与字数 (audit_article.py)")
    print("=" * 50)
    if not run_script("audit_article.py", filepath):
        failed.append("结构/字数")

    print("\n" + "=" * 50)
    print("📋 统一质检 [2/4] AI 味检测 (detect_ai_tone.py)")
    print("=" * 50)
    if not run_script("detect_ai_tone.py", filepath):
        failed.append("AI 味")

    print("\n" + "=" * 50)
    print("📋 统一质检 [3/4] persona.md 词汇黑名单（全文扫描）")
    print("=" * 50)
    hard_hits, soft_hits = scan_blacklist(text)
    if hard_hits:
        failed.append("词汇黑名单")
        for h in hard_hits:
            print(f"❌ 禁用词: {h}")
    for s in soft_hits:
        print(f"⚠️ 慎用词（确认是否自嘲/引用场景）: {s}")
    if not hard_hits and not soft_hits:
        print("✅ 未命中黑名单")
    elif not hard_hits:
        print("✅ 无硬性禁用词（以上警告请人工确认）")

    print("\n" + "=" * 50)
    print("📋 统一质检 [4/4] 平台合规与引用溯源")
    print("=" * 50)
    comp_hard, comp_warn = scan_compliance(text)
    citation_warns = check_citation(text)
    punct_hits = check_punctuation(text)
    if comp_hard:
        failed.append("平台合规")
        for h in comp_hard:
            print(f"❌ 合规红线: {h}")
    if punct_hits:
        failed.append("中文标点")
        for h in punct_hits:
            print(f"❌ 标点规范: {h}")
    for w in comp_warn:
        print(f"⚠️ 导流提醒: {w}")
    for w in citation_warns:
        print(f"⚠️ 引用提醒: {w}")
    if not comp_hard and not comp_warn and not citation_warns and not punct_hits:
        print("✅ 合规检查通过，引用与标点检查通过")

    print("\n" + "=" * 50)
    if failed:
        print(f"🚫 质检未通过，需修复: {', '.join(failed)}")
        print("=" * 50)
        sys.exit(1)
    print("🎉 全部质检通过！可以进入转换发布流程。")
    print("=" * 50)
    sys.exit(0)


if __name__ == "__main__":
    main()
