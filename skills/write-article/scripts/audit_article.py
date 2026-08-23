import sys
import re
import os

def audit_article(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 错误: 文件不存在 -> {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    report = []
    has_error = False

    # 1. 标题数量检查
    # 匹配 "### 01", "### 02" 或 "1. **" 这种标题格式
    # 车道A/B通常会有10个备选标题，这里主要检查备选标题区
    titles = re.findall(r'^\d+\.\s+\*\*', content, re.MULTILINE)
    # 或者检查 "### 01" 这种正文小标题
    sections = re.findall(r'^###\s+\d+', content, re.MULTILINE)

    # 优化字数统计：
    # 1. 找到起点 "## 正文成稿"
    # 2. 找到终点 (第一出现的附录：置顶评论/金句/数据来源)
    if "## 正文成稿" in content:
        temp = content.split("## 正文成稿")[1]
        # 寻找最近的结束标记
        end_markers = ["## 置顶评论", "## 可转发金句", "## 数据来源清单", "## 数据来源"]
        min_index = len(temp)
        for marker in end_markers:
            idx = temp.find(marker)
            if idx != -1 and idx < min_index:
                min_index = idx
        main_body = temp[:min_index]
    else:
        main_body = content

    # 移除Markdown语法
    text_only = re.sub(r'!\[.*?\]\(.*?\)', '', main_body) # 移除图片
    text_only = re.sub(r'（\[来源[^\]]*\]\([^\)]*\)）', '', text_only) # 移除来源标注整块（含括号）
    text_only = re.sub(r'\([来源][^\)]*\]\([^\)]*\)\)', '', text_only) # 移除英文括号版来源标注
    text_only = re.sub(r'\[.*?\]\(.*?\)', '', text_only) # 移除其他链接（含链接文字）
    text_only = re.sub(r'#+', '', text_only) # 移除标题符
    text_only = re.sub(r'\*\*|__', '', text_only) # 移除加粗
    text_only = re.sub(r'>\s+', '', text_only) # 移除引用符
    text_only = re.sub(r'\s+', '', text_only) # 移除空白

    char_count = len(text_only)

    # 3. 结构检查
    # 数据来源不再要求文末单独列清单：正文引用处必须直接带 URL（见 write_article.md Step 5）
    required_sections = [
        ("写在最后", r'##\s+写在最后'),
        ("金句", r'##\s+可转发金句|##\s+金句'),
        ("第一人称", r'我'),
    ]

    print(f"\n🔍 正在质检: {os.path.basename(file_path)}")
    print("=" * 40)

    # --- 报告输出 ---

    # 字数检查：低于 1000 仍视为内容不足；车道A建议 1000-2500，车道B建议 2500-3000，车道C建议 2000-2800。
    # 超过 3000 只提示，不失败——本号允许长文，不为脚本字数压缩表达。
    # 注意：脚本只卡「>=1000」这条底线，各车道的建议区间不做强制。
    # 车道C 稿件写完必须人工确认落在 2000-2800（实测校准区间），脚本报「合格」不代表符合车道C。
    if char_count >= 1000:
        if char_count <= 3000:
            print(f"✅ 字数合格: {char_count} (车道A 1000-2500 / 车道B 2500-3000 / 车道C 2000-2800)")
        else:
            print(f"⚠️ 字数较长: {char_count} (超过 3000，确认没有注水即可，不作为失败)")
    else:
        has_error = True
        diff = 1000 - char_count
        print(f"❌ 字数不足: {char_count} (目标: >=1000, 偏差: {diff})")

    # 结构检查
    print("-" * 20)
    for name, pattern in required_sections:
        if re.search(pattern, content):
            print(f"✅ 包含模块: {name}")
        else:
            has_error = True
            print(f"❌ 缺失模块: {name}")

    # 第一人称频率 (只要出现'我'就算)
    i_count = len(re.findall(r'我', content))
    if i_count >= 3:
        print(f"✅ 第一人称浓度: {i_count} 次")
    else:
        has_error = True
        print(f"❌ 第一人称过少: {i_count} 次 (需要 >= 3)")

    # 禁用词检查
    banned_words = ["综上所述", "本质上", "在当今时代", "总而言之"]
    found_banned = [w for w in banned_words if w in content]
    if found_banned:
        has_error = True
        print(f"❌ 发现禁用词: {found_banned}")
    else:
        pass # print("✅ 无禁用词")

    print("=" * 40)

    if has_error:
        print("🚫 质检未通过，请修复后再发布。")
        sys.exit(1)
    else:
        print("🎉 质检通过！可以发布。")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 skills/write-article/scripts/audit_article.py output/<article-slug>/<article-slug>.md")
        sys.exit(1)
    audit_article(sys.argv[1])
