#!/usr/bin/env python3
"""
简单的API服务器,用于前端调用质量检查工具
"""

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ModuleNotFoundError:
    Flask = None
    request = None
    jsonify = None
    CORS = None
import json
import re
import sys
from collections import Counter
from pathlib import Path

app = Flask(__name__) if Flask is not None else None
if app is not None:
    CORS(app)  # 允许跨域请求

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

EMOTION_WORDS = (
    "别",
    "慌",
    "真相",
    "为什么",
    "背后",
    "风险",
    "焦虑",
    "警惕",
    "崩",
    "翻车",
)

STOP_WORDS = {
    "我们", "你们", "他们", "自己", "这个", "那个", "因为", "所以", "然后",
    "如果", "但是", "不是", "就是", "一个", "可以", "已经", "还是", "没有",
    "这些", "那些", "以及", "进行", "对于",
}


def extract_title_candidates(content: str) -> list[str]:
    lines = content.splitlines()
    titles = []
    in_title_section = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("##") and ("标题备选" in stripped or "标题10个" in stripped):
            in_title_section = True
            continue

        if in_title_section and stripped.startswith("##"):
            break

        if in_title_section:
            match = re.match(r"^[\-\*\•]?\s*(\d+[\.\、])?\s*(.+)$", stripped)
            if not match:
                continue
            title = re.sub(r"^\*\*(.+)\*\*$", r"\1", match.group(2)).strip()
            if title:
                titles.append(title)

    if titles:
        return titles

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            return [stripped[2:].strip()]
    return []


def extract_main_body(content: str) -> str:
    if "## 正文成稿" not in content:
        return content
    temp = content.split("## 正文成稿", 1)[1]
    end_markers = ("## 写在最后", "## 置顶评论", "## 可转发金句", "## 数据来源清单", "## 数据来源")
    end_index = len(temp)
    for marker in end_markers:
        idx = temp.find(marker)
        if idx != -1 and idx < end_index:
            end_index = idx
    return temp[:end_index]


def strip_markdown(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#>*`_~\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def classify_title(title: str) -> str:
    if any(word in title for word in ("真相", "内幕", "背后", "为什么")):
        return "信息差型"
    if any(word in title for word in ("我", "实测", "复盘", "亲测")):
        return "实测型"
    if any(word in title for word in ("别", "慌", "警惕", "风险", "崩")):
        return "焦虑型"
    return "中性"


def score_title(title: str) -> int:
    score = 60
    length = len(title)

    if 12 <= length <= 20:
        score += 15
    elif 8 <= length <= 24:
        score += 8
    else:
        score -= 6

    if re.search(r"\d", title):
        score += 5
    if re.search(r"[？?！!]", title):
        score += 5

    score += min(10, sum(1 for word in EMOTION_WORDS if word in title) * 2)
    return max(0, min(100, int(score)))


def analyse_titles(titles: list[str]) -> dict:
    scored = []
    for title in titles:
        scored.append(
            {
                "标题": title,
                "评分": score_title(title),
                "类型": classify_title(title),
                "字数": len(title),
            }
        )
    scored.sort(key=lambda x: x["评分"], reverse=True)
    avg = sum(item["评分"] for item in scored) / len(scored) if scored else 0
    return {"推荐Top3": scored[:3], "分析": {"平均分": round(avg, 2)}}


def pick_main_keyword(text: str) -> tuple[str, int]:
    pure = "".join(re.findall(r"[\u4e00-\u9fff]+", text))
    tokens = []
    for size in (4, 3, 2):
        for i in range(0, max(0, len(pure) - size + 1)):
            token = pure[i : i + size]
            if token in STOP_WORDS:
                continue
            if len(set(token)) == 1:
                continue
            tokens.append(token)
    if not tokens:
        return "未识别", 0
    word, hits = Counter(tokens).most_common(1)[0]
    return word, hits


def analyse_seo(main_body: str) -> dict:
    text = strip_markdown(main_body)
    char_count = len(text.replace(" ", ""))
    keyword, hits = pick_main_keyword(text)
    density = (hits * len(keyword) / char_count * 100) if char_count and keyword != "未识别" else 0.0

    heading_count = len(re.findall(r"^(###\s+|\*\*\d{2}\s+)", main_body, re.MULTILINE))
    sentences = [s.strip() for s in re.split(r"[。！？!?]", text) if s.strip()]
    avg_sentence_len = round(sum(len(s) for s in sentences) / len(sentences)) if sentences else 0

    score = 0
    score += 40 if 1.5 <= density <= 3.5 else (30 if 1.0 <= density <= 4.5 else 20)
    score += 30 if heading_count >= 3 else (24 if heading_count == 2 else (16 if heading_count == 1 else 8))
    score += 30 if 15 <= avg_sentence_len <= 25 else (22 if 10 <= avg_sentence_len <= 30 else 14)

    suggestions = []
    if density < 1.5:
        suggestions.append("关键词密度偏低，建议在标题和小标题适度重复核心关键词。")
    elif density > 3.5:
        suggestions.append("关键词密度偏高，建议减少重复表达，避免关键词堆砌。")
    if heading_count < 3:
        suggestions.append("小标题偏少，建议每 200-300 字补一个小标题提升可读性。")
    if avg_sentence_len > 30:
        suggestions.append("句子平均长度偏高，建议拆分长句。")
    elif avg_sentence_len < 10:
        suggestions.append("句子偏短且碎，建议适当合并语义相关短句。")

    return {
        "总分": int(max(0, min(100, score))),
        "关键词分析": {"主关键词": keyword, "密度": f"{density:.2f}%"},
        "内容结构": {"小标题数量": heading_count, "平均句长": avg_sentence_len},
        "建议": suggestions,
    }


def analyse_structure(main_body: str) -> dict:
    text = strip_markdown(main_body)
    paragraphs = [p.strip() for p in main_body.split("\n\n") if p.strip()]
    cleaned = [strip_markdown(p) for p in paragraphs if not p.startswith("#") and strip_markdown(p)]

    para_count = len(cleaned)
    avg_para_len = round(sum(len(p) for p in cleaned) / para_count) if para_count else 0
    max_para_len = max((len(p) for p in cleaned), default=0)

    char_count = len(text.replace(" ", ""))
    de_ratio = (text.count("的") / char_count * 100) if char_count else 0.0

    score = 100
    if para_count < 5:
        score -= 8
    if avg_para_len > 220:
        score -= 10
    if max_para_len > 300:
        score -= 10
    if de_ratio > 3.5:
        score -= 15
    elif de_ratio > 3.0:
        score -= 8

    return {
        "评分": int(max(0, min(100, score))),
        "段落分析": {"总段落数": para_count, "平均长度": avg_para_len},
        "语言分析": {"的字占比": f"{de_ratio:.2f}%"},
    }


def build_quality_report(md_path: Path) -> dict:
    content = md_path.read_text(encoding="utf-8")
    titles = extract_title_candidates(content)
    main_body = extract_main_body(content)

    title_analysis = analyse_titles(titles)
    seo = analyse_seo(main_body)
    structure = analyse_structure(main_body)
    overall = round(title_analysis["分析"]["平均分"] * 0.4 + seo["总分"] * 0.3 + structure["评分"] * 0.3)

    return {
        "文件": md_path.name,
        "综合评分": int(overall),
        "标题分析": title_analysis,
        "SEO分析": seo,
        "结构分析": structure,
    }


def run_cli_check(md_file: str) -> int:
    md_path = (PROJECT_ROOT / md_file).resolve() if not Path(md_file).is_absolute() else Path(md_file)
    if not md_path.exists():
        print(f"❌ 文件不存在: {md_file}")
        return 1

    report_data = build_quality_report(md_path)
    report_file = md_path.parent / f"{md_path.stem}_质量报告.json"
    report_file.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 60)
    print("  公众号文章质量检查报告")
    print("=" * 60)
    print(f"📄 文件: {md_path.name}")
    print(f"⭐ 综合评分: {report_data['综合评分']}/100")
    print(f"🔍 SEO评分: {report_data['SEO分析']['总分']}/100")
    print(f"📐 结构评分: {report_data['结构分析']['评分']}/100")
    print()
    print("📌 推荐标题 Top 3:")
    top3 = report_data["标题分析"]["推荐Top3"]
    if top3:
        for idx, item in enumerate(top3, start=1):
            print(f"   {idx}. {item['标题']}")
            print(f"      评分: {item['评分']}/100 | 类型: {item['类型']}")
    else:
        print("   （未识别到标题备选）")
    print()
    print(f"💾 完整报告已保存至: {report_file}")
    return 0


def quality_check():
    """
    运行质量检查工具

    请求体:
    {
        "md_file": "output/文章.md"
    }

    返回:
    {
        "success": true,
        "data": { ... }  // 质量报告JSON
    }
    """
    try:
        data = request.get_json()
        md_file = data.get('md_file')

        if not md_file:
            return jsonify({
                'success': False,
                'error': '缺少md_file参数'
            }), 400

        # 构建完整路径
        md_path = PROJECT_ROOT / md_file

        if not md_path.exists():
            return jsonify({
                'success': False,
                'error': f'文件不存在: {md_file}'
            }), 404

        report_data = build_quality_report(md_path)
        report_file = md_path.parent / f"{md_path.stem}_质量报告.json"
        report_file.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding='utf-8')

        return jsonify({
            'success': True,
            'data': report_data
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def health():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': '质量检查API服务正常运行'
    })


def delete_article():
    """彻底删除文章接口"""
    try:
        data = request.get_json()
        article_id = data.get('id')
        if not article_id:
            return jsonify({'success': False, 'error': '缺少标题或ID参数'}), 400

        json_path = PROJECT_ROOT / 'preview_app' / 'data' / 'articles.json'
        if not json_path.exists():
            return jsonify({'success': False, 'error': '历史数据文件不存在'}), 404

        with open(json_path, 'r', encoding='utf-8') as f:
            articles_data = json.load(f)

        filtered = []
        target = None
        for a in articles_data.get('articles', []):
            if str(a.get('id')) == str(article_id):
                target = a
            else:
                filtered.append(a)

        if not target:
            return jsonify({'success': False, 'error': '找不到这篇文章'}), 404

        # 写入文件
        articles_data['articles'] = filtered
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=4)

        # 尝试删除 HTML 文件 和 MD 内容
        try:
            html_path = PROJECT_ROOT / 'preview_app' / target.get('path', '')
            if html_path.exists() and html_path.is_file():
                html_path.unlink()

            md_path = PROJECT_ROOT / 'output' / (html_path.stem + '.md')
            if md_path.exists() and md_path.is_file():
                md_path.unlink()
        except:
            pass # 出错不阻断流程

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if app is not None:
    app.add_url_rule('/quality-check', 'quality_check', quality_check, methods=['POST'])
    app.add_url_rule('/health', 'health', health, methods=['GET'])
    app.add_url_rule('/delete-article', 'delete_article', delete_article, methods=['POST'])


if __name__ == '__main__':
    if len(sys.argv) == 2:
        raise SystemExit(run_cli_check(sys.argv[1]))

    if app is None:
        print("❌ 启动 API 需要 Flask 依赖。请先安装: pip install -r preview_app/requirements.txt")
        raise SystemExit(1)

    print("🚀 启动质量检查API服务器...")
    print("📍 服务地址: http://localhost:8001")
    print("💡 健康检查: http://localhost:8001/health")
    print("⏹️  停止服务: Ctrl+C\n")

    app.run(host='0.0.0.0', port=8001, debug=True)
