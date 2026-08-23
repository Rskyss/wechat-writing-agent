import re
import random
import string
import html
import json
import os

import account_profile

ACCOUNT = account_profile.load()

# --- Templates Config ---
# High quality WeChat templates extracted from user samples
TEMPLATES = {
    # 头部占位图 (Head Image)：图床地址在 account_profile.json 的 head_image_url，未配置则不输出
    'image': ('''<section style="margin-bottom: 16px;">
  <img data-src="{url}" class="rich_pages wxw-img" style="border-radius: 9px;background-color: transparent;border-width: 1px;border-style: solid;border-color: rgb(243, 244, 239);width: 100%;" src="{url}">
</section>'''.format(url=html.escape(ACCOUNT['head_image_url'], quote=True))
        if ACCOUNT.get('head_image_url') else ''),

    # 本地预览图片 (Markdown image)
    'local_image': '''<section style="margin: 24px 0;">
  <img alt="{alt}" src="{src}" data-src="{src}" style="border-radius: 9px;background-color: transparent;border-width: 1px;border-style: solid;border-color: rgb(243, 244, 239);width: 100%;display: block;">
</section>''',

    # 正文段落 (Paragraph) - 字体16px, 深灰 rgb(54,54,54), 间距16px
    'paragraph': '''<section style="font-size: 16px;margin-bottom: 16px;color: rgb(54, 54, 54);margin-top: 16px;letter-spacing: 1px;">
    <span leaf=""><span textstyle="" style="color: rgb(54, 54, 54);">{content}</span></span>
</section>''',

    # 金色二级标题 (H2) - 对应 # 和 ## 和 ### 以及 01 序列
    'h2': '''<section style="margin-top: 32px;margin-bottom: 16px;" data-mpa-uuid="c81b3d64cac52fccb64286175b64edae" data-mpa-apply-md="t">
    <section mpa-from-tpl="t">
        <section>
            <section style="margin-top: 16px;margin-bottom: 16px;">
                <span style="font-size: 18px;"><span leaf=""><span textstyle="" style="color: rgb(177, 125, 62);font-weight: bold;">{content}</span></span></span>
            </section>
        </section>
    </section>
</section>''',

    # 列表项 (List Item) - 带•的段落
    'list_item': '''<section style="margin-bottom: 8px;font-size: 16px;color: rgb(54, 54, 54);letter-spacing: 1px;">
    <span leaf=""><span textstyle="" style="color: rgb(54, 54, 54);">• {content}</span></span>
</section>''',

    # 引用 (Blockquote)
    'blockquote': '''<section style="margin-bottom: 16px; padding: 16px; background-color: rgb(247, 247, 247); border-radius: 6px;">
    <span style="font-size: 14px; color: rgb(88, 88, 88); letter-spacing: 1px;">{content}</span>
</section>''',

    # 代码块 (Code) - Mac 窗口样式、等宽字体、保留缩进
    'code': '''<section style="margin: 24px 0; background-color: rgb(40, 44, 52); border-radius: 12px; overflow: hidden; border: 1px solid rgb(220, 222, 226); box-shadow: 0 6px 18px rgba(31, 35, 41, 0.10);">
    <section style="padding: 10px 14px; background-color: rgb(242, 243, 245); border-bottom: 1px solid rgb(216, 218, 222); font-size: 0; line-height: 1;">
        <span style="display: inline-block; width: 10px; height: 10px; margin-right: 7px; border-radius: 50%; background-color: rgb(255, 95, 87);"></span>
        <span style="display: inline-block; width: 10px; height: 10px; margin-right: 7px; border-radius: 50%; background-color: rgb(255, 189, 46);"></span>
        <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: rgb(40, 200, 64);"></span>
    </section>
    <section style="padding: 18px 20px; overflow-x: auto; -webkit-overflow-scrolling: touch;">
        <span style="display: block; font-size: 13px; line-height: 1.8; color: rgb(205, 211, 222); font-family: 'SF Mono', SFMono-Regular, Menlo, Consolas, Monaco, 'Courier New', monospace; letter-spacing: 0; white-space: pre-wrap; word-break: break-word;">{content}</span>
    </section>
</section>''',

    # 分割线 (HR) - 仅留白，无横线
    'hr': '''<section style="height: 1px; margin: 40px 0; border: none;"></section>''',

    # 内联加粗 (Bold)
    'bold_span': '<span textstyle="" style="color: rgb(0, 0, 0);font-weight: bold;">{content}</span>',

    # 底部名片 (Profile)：从 account_profile.json 读取，未配置则不插名片
    'profile': ACCOUNT['profile_card_html']
}

def parse_inline_elements(text):
    """处理行内样式：加粗、转义"""
    # 移除不需要的符号
    text = text.replace('--', '')

    # 0. Markdown 外链 [人名](url) -> 只保留人名（微信正文不支持外链；
    #    若原样保留方括号语法，编辑器里清理时极易把引用主体一起删掉）
    text = re.sub(r'\[([^\]]+)\]\((?:https?|mailto)[^)]*\)', r'\1', text)

    # 1. 替换加粗 **text** -> bold_span
    def replace_bold(match):
        return TEMPLATES['bold_span'].format(content=match.group(1))

    # 2. 简单的 HTML 转义 (防止内容中的 < > 破坏结构)
    # text = html.escape(text, quote=False) # 暂不完全转义，以免破坏 bold 标签，我们手动处理特殊字符
    # 实际上由于 bold_span 是替换进去的，我们应该先处理 bold

    text = re.sub(r'\*\*(.*?)\*\*', replace_bold, text)
    return text

def convert_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    html_parts = []
    input_dir = os.path.dirname(os.path.abspath(input_path))
    output_dir = os.path.dirname(os.path.abspath(output_path))

    # 只有文章目录里存在真实封面时才展示。旧版固定塞入远程占位图，
    # 本地预览常显示为失效的大图，也会让无封面的文章无端多出一屏。
    cover_path = next(
        (
            os.path.join(input_dir, "images", f"cover.{ext}")
            for ext in ("png", "jpg", "jpeg", "webp")
            if os.path.isfile(os.path.join(input_dir, "images", f"cover.{ext}"))
        ),
        None,
    )
    if cover_path:
        cover_src = os.path.relpath(cover_path, output_dir)
        html_parts.append(
            TEMPLATES['local_image'].format(
                alt="文章封面",
                src=html.escape(cover_src, quote=True),
            )
        )

    # State Machine flags
    in_code_block = False
    in_titles_section = False
    current_titles = []
    code_block_content = []
    paragraph_buffer = []

    def flush_paragraph():
        if paragraph_buffer:
            content = '<br>'.join(paragraph_buffer)
            html_parts.append(TEMPLATES['paragraph'].format(content=content))
            paragraph_buffer.clear()

    for line in lines:
        stripped_line = line.strip()

        # --- Pre-processing for Code Blocks ---
        if stripped_line.startswith('```'):
            flush_paragraph()
            if in_code_block:
                full_content = '<br>'.join(code_block_content)
                html_parts.append(TEMPLATES['code'].format(content=full_content))
                code_block_content = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            # 用 line.rstrip('\n') 而非 stripped_line，保留行首缩进（提示词/代码的层级对齐）
            code_block_content.append(html.escape(line.rstrip('\n')))
            continue

        # Empty lines act as separators, but we want each non-empty line to be its own block
        if not stripped_line:
             continue

        # 1. Handle HR

        if stripped_line == '---':
            flush_paragraph()
            html_parts.append(TEMPLATES['hr'])
            continue

        # 2. Handle Markdown Images: ![alt](path)
        image_match = re.match(r'^!\[(.*?)\]\((.*?)\)$', stripped_line)
        if image_match:
            flush_paragraph()
            alt_text = html.escape(image_match.group(1), quote=True)
            image_src = image_match.group(2).strip()
            if os.path.isabs(image_src) and os.path.isfile(image_src):
                image_src = os.path.relpath(image_src, output_dir)
            elif not re.match(r'^(https?://|/)', image_src):
                absolute_src = os.path.abspath(os.path.join(input_dir, image_src))
                image_src = os.path.relpath(absolute_src, output_dir)
            image_src = html.escape(image_src, quote=True)
            html_parts.append(TEMPLATES['local_image'].format(alt=alt_text, src=image_src))
            continue

        # 3. Handle Lists (*, -, •)
        if re.match(r'^[\*\-•]\s+', stripped_line) or re.match(r'^\d+\.\s+', stripped_line):
            if in_titles_section:
                title_text = re.sub(r'^[\*\-\d\.]+\s+', '', stripped_line)
                current_titles.append(title_text)
                continue

            flush_paragraph()
            content = re.sub(r'^[\*\-\d\.]+\s+', '', stripped_line)
            content = parse_inline_elements(content)
            html_parts.append(TEMPLATES['list_item'].format(content=content))
            continue

        # 2. Handle Headers (#, ##, ###) OR Numbered Titles (01, 02...)
        # Allow titles to be wrapped in bold **
        clean_line = stripped_line.strip('*').strip()
        numbered_title_match = re.match(r'^(\d{2})[\s\.、]+(.+)$', clean_line)

        if stripped_line.startswith('#') or numbered_title_match:
            flush_paragraph()
            if numbered_title_match:
                content = clean_line
            else:
                content = stripped_line.lstrip('#').strip()

            raw_content = content
            content = re.sub(r'^(标题[：:]?|标题[A-Z][：:]?)', '', content).strip()

            is_titles_header = (
                "标题10个" in raw_content
                or "标题备选" in raw_content
                or raw_content.startswith("备选")
                or content.startswith("备选")
            )

            # 离开标题备选区时，先把收集到的标题写入隐藏容器
            if in_titles_section and not is_titles_header:
                titles_json = json.dumps(current_titles, ensure_ascii=False)
                html_parts.append(f'<div class="js-title-options" style="display:none">{titles_json}</div>')
                in_titles_section = False

            if is_titles_header:
                in_titles_section = True
                current_titles = []
                continue

            content = parse_inline_elements(content)
            html_parts.append(TEMPLATES['h2'].format(content=content))
            continue

        # If we encounter content but were in titles section, finalize it
        if in_titles_section:
            titles_json = json.dumps(current_titles, ensure_ascii=False)
            html_parts.append(f'<div class="js-title-options" style="display:none">{titles_json}</div>')
            in_titles_section = False

        # 4. Handle Image Suggestions
        if stripped_line.startswith('> [图片建议]'):
            flush_paragraph()
            content = stripped_line.replace('> ', '', 1)
            img_box = f'''<section style="margin: 24px 0; padding: 16px; border: 1px dashed rgb(177, 125, 62); background-color: rgb(253, 246, 236); border-radius: 6px; text-align: center;">
                <span style="font-size: 14px; color: rgb(138, 97, 48); font-weight: bold;">📷 {content}</span>
            </section>'''
            html_parts.append(img_box)
            continue

        # 5. Handle Blockquotes (>)
        if stripped_line.startswith('> '):
            flush_paragraph()
            content = stripped_line.replace('> ', '', 1)
            content = parse_inline_elements(content)
            html_parts.append(TEMPLATES['blockquote'].format(content=content))
            continue

        # 6. Normal Paragraph - Immediate Flush (Single line per block style)
        content = parse_inline_elements(stripped_line)
        # Directly output to HTML parts to achieve "breathing" layout
        html_parts.append(TEMPLATES['paragraph'].format(content=content))

    # Final flush
    flush_paragraph()

    # Add Footer Profile
    html_parts.append(TEMPLATES['profile'])

    full_html = '\n'.join(html_parts)

    # 输出目录可能还不存在（preview_app/articles/ 不进 Git，新克隆时是空的）
    out_dir = os.path.dirname(os.path.abspath(output_path))
    os.makedirs(out_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    print(f"Successfully converted {input_path} to {output_path}")

    # 同步本地预览列表：只在用户当前目录就是仓库脚手架时才做
    #（cwd 有 sync_articles.py = 脚手架模式）。装成插件时 cwd 是用户自己的
    # 项目，没有这个脚本，直接跳过——转换本身已经完成，不该报警告。
    import subprocess
    sync_script = os.path.join(os.getcwd(), 'sync_articles.py')
    if os.path.exists(sync_script):
        try:
            subprocess.run(['python3', sync_script], check=True, cwd=os.getcwd())
        except Exception as e:
            print(f"Warning: Failed to auto-sync articles: {e}")

def update_article_list(html_path):
    """Automatically update the preview app's history list"""
    import json
    import os
    from datetime import datetime

    json_path = 'preview_app/data/articles.json'
    # Fallback to local path if running from inside writing dir
    if not os.path.exists(json_path):
        json_path = os.path.join(os.path.dirname(__file__), 'preview_app/data/articles.json')

    if not os.path.exists(json_path):
         return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {"articles": []}

    # Use simplified relative path for the web app
    rel_path = os.path.relpath(html_path, os.path.dirname(os.path.dirname(json_path)))

    # Extract title from corresponding .md file intelligently
    md_path = html_path.replace('.html', '.md')
    title = extract_title_from_md(md_path)
    if not title:
        # Fallback to filename if extraction fails
        title = os.path.basename(html_path).replace('.html', '')

    # Check if already exists
    if any(a['path'] == rel_path for a in data['articles']):
        return

    new_entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "title": title,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "author": ACCOUNT['author'],
        "path": rel_path
    }

    # Insert at beginning
    data['articles'].insert(0, new_entry)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Updated history: {json_path}")

def extract_title_from_md(md_path):
    """从md文件中智能提取标题"""
    import os
    if not os.path.exists(md_path):
        return None

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 策略1: 优先从"## 正文成稿"后找第一个有效段落(通常是文章开头,最能代表主题)
        in_body_section = False
        for line in lines:
            stripped = line.strip()

            # 检测"## 正文成稿"
            if "正文成稿" in stripped or "正文" in stripped:
                in_body_section = True
                continue

            # 在正文区域内,找第一个非空非标题段落
            if in_body_section:
                if stripped and not stripped.startswith('#') and not stripped.startswith('```'):
                    # 取前50字符作为标题预览
                    return stripped[:50] if len(stripped) > 50 else stripped

        # 策略2: 如果正文区找不到,从"## 标题备选"提取第一个标题
        in_titles_section = False
        for line in lines:
            stripped = line.strip()

            # 检测"## 标题备选"
            if "标题备选" in stripped or "标题10个" in stripped:
                in_titles_section = True
                continue

            # 在标题备选区域内,找第一个编号列表项
            if in_titles_section:
                # 匹配 "1. xxxxx" 或 "• xxxxx" 或 "- xxxxx"
                match = re.match(r'^[\d]+[\.\s]+(.+)$', stripped)  # 数字编号
                if not match:
                    match = re.match(r'^[\*\-•]\s+(.+)$', stripped)  # 符号编号

                if match:
                    title = match.group(1).strip()
                    return title

                # 如果遇到空行或下一个##,说明标题区结束
                if not stripped or stripped.startswith('##'):
                    break

        # 策略3: 如果都找不到,取第一个非空段落
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('```'):
                return stripped[:50]  # 取前50字符

        return None
    except:
        return None

if __name__ == '__main__':
    # Default behavior for manual runs
    import sys
    if len(sys.argv) > 2:
        convert_file(sys.argv[1], sys.argv[2])
    else:
        # Fallback for testing
        print("Usage: python3 skills/write-article/scripts/convert_to_wechat.py <input.md> <output.html>")
