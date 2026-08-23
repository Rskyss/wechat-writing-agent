import sys
import os
import re
import json
import html as html_mod

import account_profile

ACCOUNT = account_profile.load()

def convert(md_file):
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract titles
    titles_match = re.search(r'## 标题备选\n(.*?)\n## 正文成稿', content, re.S)
    titles = []
    if titles_match:
        for line in titles_match.group(1).split('\n'):
            line = line.strip()
            if not line: continue
            # Remove numbering and bold markers
            title = re.sub(r'^\d+\.\s*', '', line).strip('*').strip()
            if title: titles.append(title)

    # Extract main body
    body_match = re.search(r'## 正文成稿\n(.*?)$', content, re.S)
    if not body_match:
        print("未找到正文成稿部分")
        return

    body = body_match.group(1)

    html_parts = []

    # Header image（地址在 account_profile.json 的 head_image_url，未配置则跳过）
    if ACCOUNT.get('head_image_url'):
        head_url = html_mod.escape(ACCOUNT['head_image_url'], quote=True)
        html_parts.append(f'<section style="margin-bottom: 16px;">\n  <img data-src="{head_url}" class="rich_pages wxw-img" style="border-radius: 9px;background-color: transparent;border-width: 1px;border-style: solid;border-color: rgb(243, 244, 239);width: 100%;" src="{head_url}">\n</section>')

    # Hidden titles
    html_parts.append(f'<div class="js-title-options" style="display:none">{json.dumps(titles, ensure_ascii=False)}</div>')

    sections = [s.strip() for s in body.split('\n\n') if s.strip()]
    for section in sections:
        # Headers
        if section.startswith('# '):
            text = section[2:].strip()
            html_parts.append(f'<section style="margin-top: 32px;margin-bottom: 16px;"><section><section style="margin-top: 16px;margin-bottom: 16px;"><span style="font-size: 17px;"><span style="color: rgb(177, 125, 62);font-weight: bold;">{text}</span></span></section></section></section>')
        elif section.startswith('## '):
            text = section[3:].strip()
            html_parts.append(f'<section style="margin-top: 32px;margin-bottom: 16px;"><section><section style="margin-top: 16px;margin-bottom: 16px;"><span style="font-size: 17px;"><span style="color: rgb(177, 125, 62);font-weight: bold;">{text}</span></span></section></section></section>')
        elif section.startswith('### '):
            text = section[4:].strip()
            html_parts.append(f'<section style="margin-top: 32px;margin-bottom: 16px;"><section><section style="margin-top: 16px;margin-bottom: 16px;"><span style="font-size: 17px;"><span style="color: rgb(177, 125, 62);font-weight: bold;">{text}</span></span></section></section></section>')

        # Quote/Image Suggestion
        elif section.startswith('> '):
            text = section[2:].strip()
            if '图片建议' in text:
                 html_parts.append(f'<section style="margin: 24px 0; padding: 16px; border: 1px dashed rgb(177, 125, 62); background-color: rgb(253, 246, 236); border-radius: 6px; text-align: center;"><span style="font-size: 14px; color: rgb(138, 97, 48); font-weight: bold;">📷 {text}</span></section>')
            elif '素材传送门' in text:
                 html_parts.append(f'<section style="margin-bottom: 16px; padding: 16px; background-color: rgb(247, 247, 247); border-radius: 6px;"><span style="font-size: 14px; color: rgb(88, 88, 88); letter-spacing: 1px;"><span style="color: rgb(0, 0, 0);font-weight: bold;">🔗 素材传送门</span>: {text.split("素材传送门:")[1].strip() if "素材传送门:" in text else text}</span></section>')
            else:
                 html_parts.append(f'<section style="font-size: 15px;margin-bottom: 16px;color: rgb(51, 51, 51);margin-top: 16px;letter-spacing: 1px;border-left: 3px solid #ccc;padding-left: 10px;">{text}</section>')

        # Lists
        elif section.startswith('1. ') or section.startswith('• ') or re.match(r'^\d+\.', section):
             lines = section.split('\n')
             for line in lines:
                 line_text = re.sub(r'^[\d\.\•\-\s]+', '', line).strip()
                 html_parts.append(f'<section style="margin-bottom: 8px;font-size: 15px;color: rgb(51, 51, 51);letter-spacing: 1px;"><span style="color: rgb(29, 29, 37);">• {line_text}</span></section>')

        # Paragraphs
        else:
            # Inline code
            section = re.sub(r'`(.*?)`', r'<code style="background:#f0f0f0;padding:2px 4px;border-radius:3px;">\1</code>', section)
            # Bold
            section = re.sub(r'\*\*(.*?)\*\*', r'<span style="font-weight: bold;">\1</span>', section)
            # Links
            section = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" style="color:#b17d3e;text-decoration:none;">\1</a>', section)

            html_parts.append(f'<section style="font-size: 15px;margin-bottom: 16px;color: rgb(51, 51, 51);margin-top: 16px;letter-spacing: 1px;"><span style="color: rgb(29, 29, 37);">{section}</span></section>')

    # Footer 名片（内容在 account_profile.json 的 profile_card_html，未配置则跳过）
    if ACCOUNT.get('profile_card_html'):
        html_parts.append(ACCOUNT['profile_card_html'])

    final_html = "\n".join(html_parts)

    filename = os.path.basename(md_file).replace('.md', '.html')
    output_path = os.path.join(os.path.dirname(md_file), '..', 'preview_app', 'articles', filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"转换成功: {output_path}")

    json_path = os.path.join(os.path.dirname(md_file), '..', 'preview_app', 'data', 'articles.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    path_in_json = f"articles/{filename}"
    exists = False
    for art in data['articles']:
        if art['path'] == path_in_json:
            art['title'] = titles[0] if titles else "未标题文章"
            art['date'] = "2026-02-23"
            exists = True
            break

    if not exists:
        new_id = str(int(os.path.getmtime(md_file)))
        for a in data['articles']:
             if a['id'] == new_id:
                  new_id = str(int(new_id) + 1)
        new_art = {
            "id": new_id,
            "title": titles[0] if titles else "未标题文章",
            "date": "2026-02-23",
            "author": ACCOUNT['author'],
            "path": path_in_json
        }
        data['articles'].insert(0, new_art)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("已更新 articles.json")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 convert_md_to_html.py <md_file>")
    else:
        convert(sys.argv[1])
