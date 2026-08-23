#!/usr/bin/env python3
"""
便捷删除文章脚本
用法: python3 delete_article.py <文章名(不含扩展名)>
示例: python3 delete_article.py moltbook_ai_community_laneA
"""
import os
import sys
import subprocess

def delete_article(article_name):
    """删除指定文章的 md 和 html，并自动同步列表"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定义文件路径
    md_path = os.path.join(script_dir, 'output', f'{article_name}.md')
    html_path = os.path.join(script_dir, 'preview_app/articles', f'{article_name}.html')
    
    deleted = []
    
    # 删除 MD 文件
    if os.path.exists(md_path):
        os.remove(md_path)
        deleted.append(md_path)
        print(f"✅ 已删除: {md_path}")
    else:
        print(f"⚠️  未找到: {md_path}")
    
    # 删除 HTML 文件
    if os.path.exists(html_path):
        os.remove(html_path)
        deleted.append(html_path)
        print(f"✅ 已删除: {html_path}")
    else:
        print(f"⚠️  未找到: {html_path}")
    
    if not deleted:
        print(f"❌ 错误: 文章 '{article_name}' 不存在")
        return False
    
    # 自动同步文章列表
    print("\n🔄 正在同步文章列表...")
    sync_script = os.path.join(script_dir, 'sync_articles.py')
    try:
        subprocess.run(['python3', sync_script], check=True, cwd=script_dir)
        print("✅ 同步完成！")
        return True
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 delete_article.py <文章名>")
        print("示例: python3 delete_article.py moltbook_ai_community_laneA")
        sys.exit(1)
    
    article_name = sys.argv[1]
    delete_article(article_name)
