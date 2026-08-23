import json
import os
import shutil
from datetime import datetime
import re
import html

import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
# account_profile.py 随写作 skill 一起放在 skills/write-article/scripts/
sys.path.insert(0, os.path.join(ROOT, 'skills', 'write-article', 'scripts'))
import account_profile

ACCOUNT = account_profile.load()

def sync_all():
    preview_articles_dir = os.path.join(ROOT, 'preview_app', 'articles')
    json_path = os.path.join(ROOT, 'preview_app', 'data', 'articles.json')
    
    # Ensure preview articles directory exists
    if not os.path.exists(preview_articles_dir):
        os.makedirs(preview_articles_dir)
        print(f"Created preview articles dir: {preview_articles_dir}")

    if not os.path.exists(preview_articles_dir):
        print(f"Preview articles dir {preview_articles_dir} does not exist")
        html_files = []
    else:
        # Scan all .html files directly from preview_app/articles
        html_files = [f for f in os.listdir(preview_articles_dir) if f.endswith('.html')]
        # Sort by modification time (most recent first)
        html_files.sort(key=lambda x: os.path.getmtime(os.path.join(preview_articles_dir, x)), reverse=True)
    
    data = {"articles": []}
    
    ignored_titles = ["备选", "正文成稿", "文末筛选器", "置顶评论", "可转发金句"]

    for filename in html_files:
        file_path = os.path.join(preview_articles_dir, filename)

        # Default title is filename without extension
        title = filename.replace('.html', '').replace('_', ' ')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 优先读取转换器写入的标题备选；带 ✅ 的一项是已选标题。
                title_options_match = re.search(
                    r'<div class="js-title-options"[^>]*>(.*?)</div>',
                    content,
                    re.DOTALL
                )
                selected_title_found = False
                if title_options_match:
                    try:
                        title_options = json.loads(html.unescape(title_options_match.group(1)))
                        selected = next((item for item in title_options if "✅" in item), None)
                        if selected:
                            title = re.sub(r'\s*✅\s*$', '', selected).strip()
                            title = re.sub(r'^\*\*(.*?)\*\*$', r'\1', title).strip()
                            selected_title_found = True
                    except (json.JSONDecodeError, TypeError):
                        pass

                # Find all occurrences of golden title style or h2
                candidates = re.findall(r'<span textstyle="" style="color: rgb\(177, 125, 62\);font-weight: bold;">(.*?)</span>', content)
                
                if not selected_title_found:
                    for c in candidates:
                        t = c.strip()
                        if any(t.startswith(prefix) for prefix in ignored_titles):
                            continue
                        if t.isdigit() or (len(t) < 3 and t.isdigit() is False):
                            continue

                        title = t
                        break
                
        except Exception as e:
            print(f"Error parsing {filename}: {e}")
        
        # Path relative to index.html in preview_app
        rel_path = f"articles/{filename}"
        
        entry = {
            "id": str(int(os.path.getmtime(file_path))),
            "title": title,
            "date": datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d"),
            "author": ACCOUNT['author'],
            "path": rel_path
        }
        data["articles"].append(entry)

    # data/ 不进 Git，新克隆的仓库首次运行时需要自己建出来
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Synced {len(data['articles'])} articles to {json_path}")

if __name__ == '__main__':
    sync_all()
