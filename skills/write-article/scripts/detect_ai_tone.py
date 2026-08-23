#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 味检测脚本 - 检测文章中的 AI 生成特征
用法: python3 skills/write-article/scripts/detect_ai_tone.py output/<article-slug>/<article-slug>.md
"""

import re
import sys
from collections import Counter

def load_article(filepath):
    """读取文章内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取正文部分（从"## 正文成稿"到"## 写在最后"）
    match = re.search(r'## 正文成稿\n(.*?)\n## 写在最后', content, re.DOTALL)
    if match:
        return match.group(1)
    else:
        print("⚠️  未找到正文成稿部分，检测全文")
        return content

def calculate_paragraph_variance(text):
    """计算段落长度方差"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and not p.startswith('#')]
    if len(paragraphs) < 3:
        return 100  # 段落太少，不扣分

    lengths = [len(p) for p in paragraphs]
    avg = sum(lengths) / len(lengths)
    variance = sum((x - avg) ** 2 for x in lengths) / len(lengths)
    variance_ratio = (variance ** 0.5) / avg if avg > 0 else 1

    return variance_ratio

def detect_sequential_markers(text):
    """检测序列化痕迹"""
    patterns = [
        # 只抓「用序数组织结构」的枚举用法：第一，/第一点/第一步/第一部分
        # 不抓固定词组：第一反应（车道C 第3条强制动作）、第一时间、第一次、第一大股东
        r'第[一二三四五六七八九十]+(?=[，,、：:]|点[，,、：:\s]|步|部分)',
        r'首先|其次|再次|最后',
        r'步骤\s*[1-9]',
        # 排除小数（1.13 亿）与版本号：只抓行首/句首的裸序号
        r'(?<![0-9.])[1-9]\.(?![0-9])',
    ]
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text))
    return count

def detect_jargon_density(text):
    """检测术语密度"""
    jargons = [
        '降维打击', '赋能', '底层逻辑', '闭环', '抓手',
        '生态', '赛道', '范式', '颗粒度', '链路',
        '高维降噪', '数字化转型', '沉浸式体验'
    ]
    count = sum(text.count(j) for j in jargons)
    density = count / (len(text) / 1000) if len(text) > 0 else 0
    return density

def detect_fake_links(text):
    """检测虚假外链（通用分类页）"""
    fake_patterns = [
        r'https://[^/]+/category/',
        r'https://[^/]+/tag/',
        r'https://techcrunch\.com/\s*\)',
        r'https://www\.wired\.com/\s*\)',
    ]
    count = 0
    for pattern in fake_patterns:
        count += len(re.findall(pattern, text))
    return count

def detect_abstract_vs_physical(text):
    """检测抽象情绪词 vs 物理描写比例"""
    abstract_words = ['焦虑', '兴奋', '紧张', '愤怒', '恐惧', '开心', '难过']
    physical_phrases = [
        '手心出汗', '愣了', '盯着', '深呼吸', '皱眉', '眨眼',
        '脚趾', '心跳', '瞪大眼睛', '咬牙'
    ]

    abstract_count = sum(text.count(w) for w in abstract_words)
    physical_count = sum(text.count(p) for p in physical_phrases)

    total = abstract_count + physical_count
    if total == 0:
        return 0  # 都没有，不扣分

    abstract_ratio = abstract_count / total
    return abstract_ratio

def detect_contrast_pattern(text):
    """检测 AI 对比句式（persona.md E类：不是A，而是B）"""
    patterns = [
        r'不是[^。！？\n]{1,30}[，,]\s*而是',
        r'不是[^。！？\n，,]{1,15}而是',
        r'与其说[^。！？\n]{1,30}不如说',
        r'重要的不是[^。！？\n]{1,30}[，,]\s*而是',
        # 去掉"而"的隐形变体，同属 E 类：不是A，是B / 不在A，在B
        r'不是[^。！？\n，,]{1,20}[，,]\s*(?:就)?是[^。！？\n]',
        r'不在[^。！？\n，,]{1,15}[，,]\s*(?:而)?在[^。！？\n]',
    ]
    matched = set()
    for pattern in patterns:
        for m in re.finditer(pattern, text):
            matched.add(m.start())
    return len(matched)

def detect_rule_of_three(text):
    """检测三连排比（rule of three）：AI 高频修辞指纹。
    顿号版："X、Y、Z" —— 注意带"和/与"收尾的（如"评论、私信、搜索词和成交记录"）
    是正常事实列举，不算。
    逗号版："你看得见，你可以骂，你可以退订。" —— 2026-07-31 补：原来只查顿号，
    逗号排比整个漏网。要求以句号/分号收尾且每节 ≤8 字，避免误伤正常长句里的连续分句。"""
    matched = set()
    # 顿号版：本身就是列举结构，不需要额外校验
    for m in re.finditer(r'[^，。；\n、]{2,8}、[^，。；\n、]{2,8}、[^，。；\n、]{2,8}[，。；]', text):
        matched.add(m.start())
    # 逗号版：必须再过一道"结构重复"校验。中文复句天然是"A，B，C。"，
    # 只数逗号会把"这个支点如果没有，后面看到再多案例，也很容易被带偏"这类
    # 正常复句全判成排比（实测误报率超过一半）。真排比靠的是节与节的句式重复。
    for m in re.finditer(r'[^，。；\n、]{2,8}，[^，。；\n、]{2,8}，[^，。；\n、]{2,8}[。；]', text):
        if _has_parallel_structure(m.group()):
            matched.add(m.start())
    return len(matched)

def _has_parallel_structure(seg):
    """三节里至少两节开头相同 = 结构重复 = 真排比。
    命中："你看得见，你可以骂，你可以退订"（三节同以"你"起）
    放过："这个支点如果没有，后面看到再多案例，也很容易被带偏"（各节开头都不同）"""
    parts = [p for p in re.split(r'[，、]', seg.rstrip('。；')) if p]
    if len(parts) < 3:
        return False
    # ① 节首重复："你看得见，你可以骂，你可以退订"
    for n in (1, 2):
        heads = [p[:n] for p in parts if len(p) >= n]
        if heads and Counter(heads).most_common(1)[0][1] >= 2:
            return True
    # ② 节内共同词：重复的词不一定在句首——"但它不是彩票，不是捷径，也不是万能答案"
    #    的"不是"、"踩过多少坑，有多少资源，有多少经验"的"多少"
    seen = Counter()
    for p in parts:
        seen.update({p[i:i+2] for i in range(len(p) - 1)})  # 每节内去重再计
    return any(v >= 2 for v in seen.values())

def detect_staccato_triple(text):
    """检测三连短句连击（persona F 类）：连续 3 个及以上短句用句号砸下来，
    如"你实际多付了 60%。你察觉不到。因为你从来不知道基准是多少。"
    与 detect_rule_of_three 的区别：那个查顿号并列，这个查句号连击，两者互不覆盖。
    2026-07-31 外部模型指认后新增——脚本当时对这种节奏报 0 分，完全没抓到。"""
    hits = 0
    for para in text.split('\n'):
        # 按句末标点切句，只留有实质内容的
        sents = [s.strip() for s in re.split(r'[。！？]', para) if s.strip()]
        run = 0
        for s in sents:
            # 短句阈值 15 字：12 字实测太严——"因为你从来不知道基准是多少"(13字)
            # 正是重锤的第三下，卡在 12 会直接漏掉整串。再长就属于正常叙述了
            if len(s) <= 15:
                run += 1
                if run == 3:
                    hits += 1
                elif run > 3:
                    pass  # 同一串只记一次
            else:
                run = 0
    return hits

def detect_hedge_stance(text):
    """检测自我限权表态密度（persona F 类）：分寸要留，被砍的是表态的壳。
    外部模型指认：这类对冲的出现时机（恰在读者要反驳的前一秒）是 AI 最稳定的行为特征。"""
    patterns = [
        r'说句公道话', r'平心而论', r'客观地说', r'公允地说',
        r'(我|这里)?也?得承认(另一面|一点|另一层)?', r'我知道有人会说', r'可能有人会说',
        r'我不是说[^，。]{1,12}(干了|做了|在)', r'这里必须说清楚', r'话说回来',
    ]
    return sum(len(re.findall(p, text)) for p in patterns)

def detect_dash_density(text):
    """检测破折号（——）密度：AI 爱用破折号制造强调感"""
    count = text.count('——')
    density = count / (len(text) / 1000) if len(text) > 0 else 0
    return count, density

def detect_vague_attribution(text):
    """检测模糊归因：没名没姓的"专家表示/业内人士认为"（违反透明式写作）"""
    pattern = r'(有?专家|业内人士|分析人士|观察人士|不少网友|有网友|业内普遍|有研究)(认为|表示|指出|担心|称)'
    return len(re.findall(pattern, text))

def detect_connector_density(text):
    """检测标准连接词密度：然而/因此/此外 过密是 AI 特征"""
    connectors = ['然而', '因此', '此外', '与此同时', '总的来说', '事实上', '换言之', '综合来看']
    count = sum(text.count(c) for c in connectors)
    density = count / (len(text) / 1000) if len(text) > 0 else 0
    return count, density

def check_semantic_humanity(text):
    """语义层提醒（不计分）：私货细节密度 + 可被反驳观点。
    2026 检测已进入语义层，真正防降权的是模型编不出来的私货。"""
    warnings = []
    # 私货细节：具体日期/次数/金额/时长等不可预测信息
    detail_pattern = r'\d+\s*(月|日|号|次|遍|周|天|小时|分钟|块|元|刀|美元|万|个月|年)|[0-9]{1,2}[:：][0-9]{2}'
    detail_count = len(re.findall(detail_pattern, text))
    if detail_count < 3:
        warnings.append(f"私货细节偏少（仅 {detail_count} 处具体时间/次数/金额）：实测型文章必须补真实细节；资讯解读型可用独立判断替代（不阻塞），但严禁编造亲历来凑")
    # 可被反驳的观点：立场鲜明的第一人称判断
    opinion_pattern = (r'我(认为|倾向|更倾向|不看好|看好|赌|猜|判断|不同意|反对|担心|建议|的选择)'
                       r'|我的(判断|看法|结论|立场|选择)(是|很明确|不同)?')
    if not re.search(opinion_pattern, text):
        warnings.append("全文没有可被反驳的第一人称观点（我认为/我不看好/我赌…）：删掉金句后这篇还剩什么？")
    return warnings

def detect_meme_density(text):
    """检测网络梗密度"""
    memes = [
        '脚趾能在地里扣出三室一厅',
        '魔法打败魔法',
        '破防',
        '真香',
        '绝绝子',
        'yyds',
        '无语了',
        '离谱'
    ]
    count = sum(text.count(m) for m in memes)
    density = count / (len(text) / 1000) if len(text) > 0 else 0
    return density

def run_detection(filepath):
    """执行完整检测"""
    print(f"\n🤖 正在检测: {filepath}")
    print("=" * 50)

    text = load_article(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        full_text = f.read()  # E类对比句式扫全文（含标题备选和金句）
    total_score = 0
    details = []

    # 检测 1: 结构工整度
    variance = calculate_paragraph_variance(text)
    if variance < 0.2:
        score = 10
        status = "❌"
        details.append(f"结构工整度: {status} {score}/10 (段落长度方差 {variance:.2%}，过于均匀)")
        total_score += score
    else:
        status = "✅"
        details.append(f"结构工整度: {status} 0/10")

    # 检测 2: 序列化痕迹
    seq_count = detect_sequential_markers(text)
    if seq_count >= 3:
        score = 10
        status = "❌"
        details.append(f"序列化痕迹: {status} {score}/10 (发现 {seq_count} 处序号/步骤)")
        total_score += score
    elif seq_count >= 1:
        score = 5
        status = "⚠️"
        details.append(f"序列化痕迹: {status} {score}/10 (发现 {seq_count} 处序号/步骤)")
        total_score += score
    else:
        status = "✅"
        details.append(f"序列化痕迹: {status} 0/10")

    # 检测 3: 术语密度
    jargon_density = detect_jargon_density(text)
    if jargon_density > 2:
        score = 10
        status = "❌"
        details.append(f"术语密度: {status} {score}/10 (密度 {jargon_density:.1f} 个/千字)")
        total_score += score
    elif jargon_density > 1:
        score = 5
        status = "⚠️"
        details.append(f"术语密度: {status} {score}/10 (密度 {jargon_density:.1f} 个/千字)")
        total_score += score
    else:
        status = "✅"
        details.append(f"术语密度: {status} 0/10")

    # 检测 4: 外链真实性
    fake_links = detect_fake_links(text)
    if fake_links >= 2:
        score = 10
        status = "❌"
        details.append(f"外链真实性: {status} {score}/10 (发现 {fake_links} 个通用分类页链接)")
        total_score += score
    elif fake_links >= 1:
        score = 5
        status = "⚠️"
        details.append(f"外链真实性: {status} {score}/10 (发现 {fake_links} 个通用分类页链接)")
        total_score += score
    else:
        status = "✅"
        details.append(f"外链真实性: {status} 0/10")

    # 检测 5: 情绪词 vs 物理描写
    abstract_ratio = detect_abstract_vs_physical(text)
    if abstract_ratio > 0.6:
        score = 10
        status = "❌"
        details.append(f"情绪表达: {status} {score}/10 (抽象词占比 {abstract_ratio:.0%}，缺少物理描写)")
        total_score += score
    elif abstract_ratio > 0.4:
        score = 5
        status = "⚠️"
        details.append(f"情绪表达: {status} {score}/10 (抽象词占比 {abstract_ratio:.0%})")
        total_score += score
    else:
        status = "✅"
        details.append(f"情绪表达: {status} 0/10")

    # 检测 6: 网络梗密度
    meme_density = detect_meme_density(text)
    if meme_density > 3:
        score = 10
        status = "❌"
        details.append(f"网络梗密度: {status} {score}/10 (密度 {meme_density:.1f} 个/千字，过于刻意)")
        total_score += score
    elif meme_density > 2:
        score = 5
        status = "⚠️"
        details.append(f"网络梗密度: {status} {score}/10 (密度 {meme_density:.1f} 个/千字)")
        total_score += score
    else:
        status = "✅"
        details.append(f"网络梗密度: {status} 0/10")

    # 检测 7: 三连排比（rule of three）
    # 阈值 2026-07-31 校准：新增逗号版排比后计数普遍翻倍，沿用旧阈值(5/3)会误卡
    # 一半以上历史文章。全量扫 44 篇重定为 8/5，只抓真正密集的（实测 18/14/12 处那几篇）
    triple_count = detect_rule_of_three(text)
    if triple_count >= 8:
        score = 10
        details.append(f"三连排比: ❌ {score}/10 (发现 {triple_count} 处三连排比，密度过高，AI高频指纹)")
        total_score += score
    elif triple_count >= 5:
        score = 5
        details.append(f"三连排比: ⚠️ {score}/10 (发现 {triple_count} 处，注意打散节奏)")
        total_score += score
    else:
        details.append(f"三连排比: ✅ 0/10")

    # 检测 7.5: 三连短句连击（persona F 类，上限 1 处）
    staccato_count = detect_staccato_triple(text)
    if staccato_count >= 3:
        score = 10
        details.append(f"三连短句连击: ❌ {score}/10 (发现 {staccato_count} 处短句三连砸，上限 1 处，工整过头)")
        total_score += score
    elif staccato_count == 2:
        score = 5
        details.append(f"三连短句连击: ⚠️ {score}/10 (2 处，留一处最有力的，其余并进上下文)")
        total_score += score
    else:
        details.append(f"三连短句连击: ✅ 0/10")

    # 检测 7.6: 自我限权表态密度（persona F 类，上限 2 处）
    hedge_count = detect_hedge_stance(text)
    if hedge_count >= 4:
        score = 10
        details.append(f"自我限权表态: ❌ {score}/10 ({hedge_count} 处\"说句公道话/我得承认\"式对冲，上限 2 处——分寸留着，砍掉表态的壳)")
        total_score += score
    elif hedge_count == 3:
        score = 5
        details.append(f"自我限权表态: ⚠️ {score}/10 (3 处，超出的改成直接摆反面事实，不做自我标注)")
        total_score += score
    else:
        details.append(f"自我限权表态: ✅ 0/10")

    # 检测 8: 破折号密度
    dash_count, dash_density = detect_dash_density(text)
    if dash_density > 2:
        score = 10
        details.append(f"破折号密度: ❌ {score}/10 ({dash_count} 处——，密度 {dash_density:.1f}/千字)")
        total_score += score
    elif dash_density > 1:
        score = 5
        details.append(f"破折号密度: ⚠️ {score}/10 ({dash_count} 处——，密度 {dash_density:.1f}/千字)")
        total_score += score
    else:
        details.append(f"破折号密度: ✅ 0/10")

    # 检测 9: 模糊归因
    vague_count = detect_vague_attribution(text)
    if vague_count >= 2:
        score = 10
        details.append(f"模糊归因: ❌ {score}/10 ({vague_count} 处\"专家表示\"式无名引用，必须具体到谁/何时)")
        total_score += score
    elif vague_count == 1:
        score = 5
        details.append(f"模糊归因: ⚠️ {score}/10 (1 处无名引用，改成具体的人和出处)")
        total_score += score
    else:
        details.append(f"模糊归因: ✅ 0/10")

    # 检测 10: 连接词密度
    conn_count, conn_density = detect_connector_density(text)
    if conn_density > 3:
        score = 10
        details.append(f"连接词密度: ❌ {score}/10 ({conn_count} 处然而/因此/此外，密度 {conn_density:.1f}/千字)")
        total_score += score
    elif conn_density > 2:
        score = 5
        details.append(f"连接词密度: ⚠️ {score}/10 ({conn_count} 处，密度 {conn_density:.1f}/千字)")
        total_score += score
    else:
        details.append(f"连接词密度: ✅ 0/10")

    # 检测 11: AI 对比句式（不是A，而是B）—— persona.md E类，严格禁止
    contrast_count = detect_contrast_pattern(full_text)
    if contrast_count >= 2:
        score = 10
        status = "❌"
        details.append(f"AI对比句式: {status} {score}/10 (发现 {contrast_count} 处\"不是A，而是B\"，E类严格禁止)")
        total_score += score
    elif contrast_count == 1:
        score = 5
        status = "⚠️"
        details.append(f"AI对比句式: {status} {score}/10 (发现 1 处\"不是A，而是B\"，E类严格禁止)")
        total_score += score
    else:
        status = "✅"
        details.append(f"AI对比句式: {status} 0/10")

    # 输出结果
    for detail in details:
        print(detail)

    # 语义层提醒（不计分，但 2026 检测趋势下这才是护城河）
    semantic_warnings = check_semantic_humanity(text)
    if semantic_warnings:
        print("-" * 50)
        for w in semantic_warnings:
            print(f"🧬 语义层提醒: {w}")

    print("-" * 50)
    if contrast_count >= 1:
        print(f"❌ 检测未通过！AI 味总分: {total_score}/130（E类对比句式零容忍，必须全部改写）")
        print("\n💡 修改建议:")
        print("  - 改写所有\"不是A，而是B\"：直接说B，或拆成两句（见 persona.md E类替换示范）")
        return False
    if total_score <= 30:
        print(f"✅ 检测通过！AI 味总分: {total_score}/130")
        return True
    else:
        print(f"❌ 检测未通过！AI 味总分: {total_score}/130")
        print("\n💡 修改建议:")
        if variance < 0.2:
            print("  - 调整段落长度，让某些段落故意短一些或长一些")
        if seq_count >= 3:
            print("  - 删除'第一/第二'等序号，改用'先说/再说'或直接删除")
        if jargon_density > 2:
            print("  - 减少术语使用，改用日常口语")
        if fake_links >= 2:
            print("  - 替换通用外链为具体文章 URL 或改为'建议搜索：XX'")
        if abstract_ratio > 0.6:
            print("  - 增加物理细节描写，减少抽象情绪词")
        if meme_density > 3:
            print("  - 减少网络梗数量，保持自然")
        if triple_count >= 3:
            print("  - 打散\"X、Y、Z\"三连并列：改成两项，或拆成独立句子")
        if dash_density > 1:
            print("  - 减少破折号（——），改用句号或逗号")
        if vague_count >= 1:
            print("  - \"专家表示/业内人士\"改成具体的人名/帖子/出处（透明式写作）")
        if conn_density > 2:
            print("  - 删掉部分然而/因此/此外，用口语过渡或直接删")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python3 skills/write-article/scripts/detect_ai_tone.py output/<article-slug>/<article-slug>.md")
        sys.exit(1)

    filepath = sys.argv[1]
    passed = run_detection(filepath)
    sys.exit(0 if passed else 1)
