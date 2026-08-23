// Global variable to store current article info
let currentArticle = null;

async function loadArticles() {
    try {
        // 本地预览以磁盘内容为准，避免浏览器缓存旧标题和旧排序。
        const response = await fetch('data/articles.json?t=' + new Date().getTime());
        const data = await response.json();
        renderList(data.articles);
    } catch (err) {
        console.error("加载数据失败:", err);
    }
}

function renderList(articles) {
    const list = document.getElementById('history-list');
    list.innerHTML = '';

    articles.forEach((art, index) => {
        const li = document.createElement('li');
        li.className = 'history-item';
        li.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: baseline;">
                <div class="date">${art.date}</div>
                <button class="delete-btn" style="background: none; border: none; cursor: pointer; font-size: 14px; padding: 0 5px; color: #ff4d4f;" title="删除文章" onclick="deleteArticle(event, '${art.id}')">🗑️</button>
            </div>
            <div class="title">${art.title}</div>
        `;
        li.onclick = () => showArticle(art, li);
        list.appendChild(li);

        // Auto-select the first one
        if (index === 0) {
            showArticle(art, li);
        }
    });
}

function showArticle(art, element) {
    // Save current article info
    currentArticle = art;

    // UI Update for list
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');

    // UI Update for article
    document.getElementById('view-title').innerText = art.title;
    document.getElementById('view-author').innerText = art.author || '';
    document.getElementById('view-date').innerText = art.date;
    document.getElementById('view-word-count').innerText = art.word_count || 0;

    // We fetch the actual HTML content from the file path provided in JSON
    fetchArticleContent(art.path);
}

async function fetchArticleContent(path) {
    try {
        // Adjust path: articles.json will have paths relative to project root or data folder
        const response = await fetch(path + '?t=' + new Date().getTime());
        const text = await response.text();
        const body = document.getElementById('view-body');

        // 1. Create a dummy element to parse HTML thoroughly
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');

        // 2. Identify and Extract Content
        const allSections = Array.from(doc.body.children);

        let extraction = {
            titles: [],
            ending: [],
            comments: [],
            quotes: []
        };

        // Check for special title container (New V2 format)
        const titleContainer = doc.querySelector('.js-title-options');
        if (titleContainer) {
            try {
                const jsonTitles = JSON.parse(titleContainer.innerText);
                if (Array.isArray(jsonTitles)) {
                    extraction.titles = jsonTitles.map(title =>
                        String(title).replace(/^\*\*(.*)\*\*$/, '$1').trim()
                    );
                }
                titleContainer.remove(); // Remove from DOM to clean up
            } catch (e) {
                console.error("Failed to parse hidden titles", e);
            }
        }

        const getText = (el) => (el.innerText || el.textContent || '').trim();
        const hasMainMarker = allSections.some(el => getText(el).includes('正文成稿'));

        // States: 'pre' (before main content), 'main' (content), 'ending' (filters), 'comments' (pinned), 'quotes' (gold)
        // Older generated files include a "正文成稿" marker. Final WeChat HTML does not,
        // so treating everything before that marker as title candidates would delete the article.
        let currentExtractMode = hasMainMarker ? 'pre' : 'main';
        let hasStartedContent = hasMainMarker;

        for (let i = 0; i < allSections.length; i++) {
            const el = allSections[i];
            // allSections is captured before the hidden metadata node is removed.
            // Skip that stale entry so its raw JSON is not rendered as a title.
            if (el === titleContainer) continue;
            const text = getText(el);

            // Detect Phase Switches based on headers
            if (text.includes('正文成稿')) {
                currentExtractMode = 'main';
                el.remove(); continue;
            }
            if (text.includes('文末筛选器')) {
                currentExtractMode = 'ending';
                el.remove(); continue;
            }
            if (text.includes('置顶评论')) {
                currentExtractMode = 'comments';
                el.remove(); continue;
            }
            if (text.includes('可转发金句')) {
                currentExtractMode = 'quotes';
                el.remove(); continue;
            }

            // Perform extraction/removal based on mode
            if (currentExtractMode === 'pre') {
                // Check if it's a title candidate
                const isHeader = text.includes('备选');
                if (!isHeader && text.length > 2) {
                    let cleanTitle = text.replace(/^[•\-\d\.]+\s*/, '').trim();
                    if (cleanTitle) extraction.titles.push(cleanTitle);
                }
                // Remove everything before main content from view
                el.remove();

            } else if (currentExtractMode === 'main') {
                if (!hasStartedContent && text.length === 0) {
                    el.remove();
                    continue;
                }
                hasStartedContent = true;

            } else {
                // Post-content sections: Ending, Comments, Quotes
                // Extract to bucket
                if (text.length > 0 && !text.includes('---')) {
                    if (currentExtractMode === 'ending') extraction.ending.push(text);
                    if (currentExtractMode === 'comments') extraction.comments.push(text);
                    if (currentExtractMode === 'quotes') extraction.quotes.push(text);
                }
                // Remove from phone view
                el.remove();
            }
        }

        // Render Sidebar Content for all tabs
        renderSidebarContent(extraction);

        body.innerHTML = doc.body.innerHTML;

        // Calculate actual word count (Matched with WeChat logic: only count non-space/non-newline characters)
        const textContent = body.innerText || "";
        const actualWordCount = textContent.replace(/\s/g, '').length;
        document.getElementById('view-word-count').innerText = actualWordCount;

    } catch (err) {
        document.getElementById('view-body').innerHTML = `<p style="color:red">加载文章正文失败: ${err.message}</p>`;
        console.error(err);
    }
}

function renderSidebarContent(data) {
    // 1. Titles
    const titleList = document.getElementById('title-list');
    if (titleList) {
        titleList.innerHTML = '';
        if (data.titles.length === 0) {
            titleList.innerHTML = '<div style="font-size:12px;color:#999;text-align:center;padding-top:20px;">暂无备选标题</div>';
        } else {
            data.titles.forEach(t => {
                const item = document.createElement('div');
                item.className = 'title-option-item';
                item.innerText = t;
                item.onclick = () => {
                    document.getElementById('view-title').innerText = t;
                    document.querySelectorAll('.title-option-item').forEach(el => el.style.borderColor = 'transparent');
                    item.style.borderColor = 'var(--primary-color)';
                };
                titleList.appendChild(item);
            });
        }
    }

    // Helper for other tabs
    const renderSimpleList = (items, containerId, emptyText) => {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = '';
        if (!items || items.length === 0) {
            container.innerHTML = `<div style="font-size:12px;color:#999;text-align:center;padding-top:20px;">${emptyText}</div>`;
            return;
        }
        items.forEach(text => {
            const cleanText = text.replace(/^[•\-\d\.]+\s*/, '').trim();
            if (!cleanText) return;

            const div = document.createElement('div');
            div.className = 'extracted-item';
            div.innerText = cleanText;
            container.appendChild(div);
        });
    };

    renderSimpleList(data.ending, 'tab-ending', '暂无结尾内容');
    renderSimpleList(data.comments, 'tab-comments', '暂无置顶评论');
    renderSimpleList(data.quotes, 'tab-quotes', '暂无金句');

    // Clear quality check result when switching articles
    document.getElementById('quality-result').innerHTML = '';
}

function switchTab(tabName) {
    // 1. Sidebar Tabs UI update
    document.querySelectorAll('.tab-item').forEach(el => {
        // Check if onclick contains the tabName
        const onclickAttr = el.getAttribute('onclick');
        if (onclickAttr && onclickAttr.includes(`'${tabName}'`)) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });

    // 2. Content Areas toggle
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    const targetContent = document.getElementById(`tab-${tabName}`);
    if (targetContent) targetContent.classList.add('active');
}

async function copyArticleHtml() {
    const body = document.getElementById('view-body');
    const btn = document.getElementById('copy-btn');
    const originalContent = btn.innerHTML;

    if (!body) return;

    const html = body.innerHTML;
    const text = body.innerText || body.textContent || '';

    const copyWithSelectionFallback = () => {
        const container = document.createElement('div');
        container.setAttribute('contenteditable', 'true');
        container.style.position = 'fixed';
        container.style.left = '-9999px';
        container.style.top = '0';
        container.style.width = '1px';
        container.style.height = '1px';
        container.style.overflow = 'hidden';
        container.innerHTML = html;
        document.body.appendChild(container);

        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(container);
        selection.removeAllRanges();
        selection.addRange(range);

        let copied = false;
        try {
            copied = document.execCommand('copy');
        } finally {
            selection.removeAllRanges();
            container.remove();
        }
        return copied;
    };

    const copyWithTextAreaFallback = () => {
        const textarea = document.createElement('textarea');
        textarea.value = html;
        textarea.setAttribute('readonly', '');
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        textarea.style.top = '0';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();

        let copied = false;
        try {
            copied = document.execCommand('copy');
        } finally {
            textarea.remove();
        }
        return copied;
    };

    const showManualCopyDialog = () => {
        const existing = document.getElementById('manual-copy-dialog');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.id = 'manual-copy-dialog';
        overlay.style.position = 'fixed';
        overlay.style.inset = '0';
        overlay.style.zIndex = '9999';
        overlay.style.background = 'rgba(15, 23, 42, 0.45)';
        overlay.style.display = 'flex';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';
        overlay.style.padding = '24px';

        const panel = document.createElement('div');
        panel.style.width = 'min(760px, 92vw)';
        panel.style.maxHeight = '82vh';
        panel.style.background = '#fff';
        panel.style.borderRadius = '12px';
        panel.style.boxShadow = '0 24px 80px rgba(15, 23, 42, 0.28)';
        panel.style.padding = '18px';
        panel.style.display = 'flex';
        panel.style.flexDirection = 'column';
        panel.style.gap = '12px';

        const title = document.createElement('div');
        title.style.fontSize = '18px';
        title.style.fontWeight = '700';
        title.textContent = '浏览器拒绝自动复制，请手动复制';

        const hint = document.createElement('div');
        hint.style.fontSize = '14px';
        hint.style.color = '#666';
        hint.textContent = '下面的 HTML 已经全选。按 Cmd+C 复制，然后粘贴到微信编辑器。';

        const textarea = document.createElement('textarea');
        textarea.value = html;
        textarea.style.width = '100%';
        textarea.style.height = '48vh';
        textarea.style.boxSizing = 'border-box';
        textarea.style.border = '1px solid #ddd';
        textarea.style.borderRadius = '8px';
        textarea.style.padding = '12px';
        textarea.style.fontFamily = 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace';
        textarea.style.fontSize = '12px';
        textarea.style.lineHeight = '1.5';

        const actions = document.createElement('div');
        actions.style.display = 'flex';
        actions.style.justifyContent = 'flex-end';
        actions.style.gap = '10px';

        const closeBtn = document.createElement('button');
        closeBtn.textContent = '关闭';
        closeBtn.style.border = '0';
        closeBtn.style.borderRadius = '8px';
        closeBtn.style.padding = '10px 16px';
        closeBtn.style.cursor = 'pointer';
        closeBtn.onclick = () => overlay.remove();

        actions.appendChild(closeBtn);
        panel.appendChild(title);
        panel.appendChild(hint);
        panel.appendChild(textarea);
        panel.appendChild(actions);
        overlay.appendChild(panel);
        document.body.appendChild(overlay);

        textarea.focus();
        textarea.select();
    };

    try {
        if (navigator.clipboard && window.ClipboardItem) {
            await navigator.clipboard.write([
                new ClipboardItem({
                    'text/html': new Blob([html], { type: 'text/html' }),
                    'text/plain': new Blob([html], { type: 'text/plain' })
                })
            ]);
        } else if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(html);
        } else if (!copyWithSelectionFallback() && !copyWithTextAreaFallback()) {
            throw new Error('Clipboard API unavailable and fallback copy failed');
        }

        // UI Feedback
        btn.innerHTML = '<span>✅</span> 复制成功！';
        btn.style.background = '#28a745';

        setTimeout(() => {
            btn.innerHTML = originalContent;
            btn.style.background = '';
        }, 2000);
    } catch (err) {
        try {
            if (!copyWithSelectionFallback() && !copyWithTextAreaFallback()) {
                throw err;
            }

            btn.innerHTML = '<span>✅</span> 复制成功！';
            btn.style.background = '#28a745';

            setTimeout(() => {
                btn.innerHTML = originalContent;
                btn.style.background = '';
            }, 2000);
        } catch (fallbackErr) {
        console.error('复制失败:', err);
        console.error('备用复制失败:', fallbackErr);
        showManualCopyDialog();
        btn.innerHTML = '<span>⚠️</span> 手动复制';
        setTimeout(() => {
            btn.innerHTML = originalContent;
        }, 2000);
        }
    }
}

async function runQualityCheck() {
    if (!currentArticle) {
        alert('请先选择一篇文章');
        return;
    }

    const btn = document.getElementById('run-quality-check-btn');
    const resultDiv = document.getElementById('quality-result');
    const originalBtnContent = btn.innerHTML;

    // Show loading state
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> 检查中...';
    resultDiv.innerHTML = `
        <div class="quality-loading">
            <div class="quality-loading-spinner"></div>
            <p style="margin-top:15px;">正在分析文章质量...</p>
        </div>
    `;

    try {
        // Get markdown file path from HTML path
        // Example: ../articles/2026-01-28/moltbot_product_manager_laneA.html
        // Convert to: output/moltbot_product_manager_architecture_laneA.md
        const htmlPath = currentArticle.path;
        const mdFileName = htmlPath.split('/').pop().replace('.html', '.md');
        const mdPath = `output/${mdFileName}`;

        // Call quality check API
        const response = await fetch('http://localhost:8001/quality-check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ md_file: mdPath })
        });

        if (!response.ok) {
            throw new Error(`API调用失败: ${response.status}`);
        }

        const result = await response.json();

        if (result.success) {
            displayQualityResult(result.data);
        } else {
            throw new Error(result.error || '未知错误');
        }

    } catch (err) {
        console.error('质量检查失败:', err);
        resultDiv.innerHTML = `
            <div class="quality-error">
                <strong>❌ 检查失败</strong><br><br>
                <p>${err.message}</p>
                <br>
                <p style="font-size:12px;">请确保:</p>
                <ul style="font-size:12px;margin-top:5px;padding-left:20px;">
                    <li>后端服务已启动 (python3 preview_app/api_server.py)</li>
                    <li>文章文件存在于 output/ 目录</li>
                </ul>
            </div>
        `;
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalBtnContent;
    }
}

function displayQualityResult(data) {
    const resultDiv = document.getElementById('quality-result');

    // Extract data
    const score = data.综合评分;
    const titleAnalysis = data.标题分析;
    const seoAnalysis = data.SEO分析;
    const structureAnalysis = data.结构分析;

    // Rating text and color
    let ratingText = '';
    let ratingEmoji = '';
    let scoreColor = '';
    if (score >= 90) {
        ratingText = '优秀';
        ratingEmoji = '✨';
        scoreColor = '#10b981'; // green
    } else if (score >= 80) {
        ratingText = '良好';
        ratingEmoji = '👍';
        scoreColor = '#3b82f6'; // blue
    } else if (score >= 70) {
        ratingText = '及格';
        ratingEmoji = '✓';
        scoreColor = '#f59e0b'; // orange
    } else {
        ratingText = '需优化';
        ratingEmoji = '⚠️';
        scoreColor = '#ef4444'; // red
    }

    // Build HTML with new design
    let html = `
        <!-- Score Card -->
        <div class="quality-score-card">
            <div class="quality-score-big" style="color: ${scoreColor};">
                ${score}<span class="quality-score-small">/100</span>
            </div>
            <div class="quality-rating-badge" style="background: ${scoreColor};">
                ${ratingEmoji} ${ratingText}
            </div>
        </div>

        <!-- Metrics Grid -->
        <div class="quality-metrics-grid">
            <div class="quality-metric-card">
                <div class="metric-icon">📌</div>
                <div class="metric-label">标题平均分</div>
                <div class="metric-value">${Math.round(titleAnalysis.分析.平均分)}<span class="metric-unit">/100</span></div>
            </div>
            <div class="quality-metric-card">
                <div class="metric-icon">🔍</div>
                <div class="metric-label">SEO评分</div>
                <div class="metric-value">${seoAnalysis.总分}<span class="metric-unit">/100</span></div>
            </div>
            <div class="quality-metric-card">
                <div class="metric-icon">📐</div>
                <div class="metric-label">结构评分</div>
                <div class="metric-value">${structureAnalysis.评分}<span class="metric-unit">/100</span></div>
            </div>
        </div>

        <!-- Top Titles Section -->
        <div class="quality-section-card">
            <div class="quality-card-header">
                <span class="quality-card-icon">🏆</span>
                <span class="quality-card-title">推荐标题 Top 3</span>
            </div>
            <div class="quality-titles-list">
    `;

    // Add top 3 titles with better design
    titleAnalysis.推荐Top3.forEach((title, index) => {
        const rankClass = index === 0 ? 'rank-gold' : index === 1 ? 'rank-silver' : 'rank-bronze';
        html += `
            <div class="quality-title-card ${rankClass}" onclick="selectQualityTitle('${title.标题.replace(/'/g, "\\'")}')">
                <div class="title-rank">${index + 1}</div>
                <div class="title-content">
                    <div class="title-text">${title.标题}</div>
                    <div class="title-meta-row">
                        <span class="title-badge title-badge-score">${title.评分}分</span>
                        <span class="title-badge title-badge-type">${title.类型}</span>
                        <span class="title-badge title-badge-length">${title.字数}字</span>
                    </div>
                </div>
                <div class="title-arrow">→</div>
            </div>
        `;
    });

    html += `
            </div>
        </div>

        <!-- SEO Details -->
        <div class="quality-section-card">
            <div class="quality-card-header">
                <span class="quality-card-icon">🔍</span>
                <span class="quality-card-title">SEO分析详情</span>
                <span class="quality-score-badge">${seoAnalysis.总分}/100</span>
            </div>
            <div class="quality-detail-list">
                <div class="quality-detail-item">
                    <span class="detail-label">主关键词</span>
                    <span class="detail-value">${seoAnalysis.关键词分析.主关键词}</span>
                </div>
                <div class="quality-detail-item">
                    <span class="detail-label">关键词密度</span>
                    <span class="detail-value">${seoAnalysis.关键词分析.密度}</span>
                </div>
                <div class="quality-detail-item">
                    <span class="detail-label">小标题数量</span>
                    <span class="detail-value">${seoAnalysis.内容结构.小标题数量}个</span>
                </div>
                <div class="quality-detail-item">
                    <span class="detail-label">平均句长</span>
                    <span class="detail-value">${seoAnalysis.内容结构.平均句长}字</span>
                </div>
            </div>
        </div>

        <!-- Structure Details -->
        <div class="quality-section-card">
            <div class="quality-card-header">
                <span class="quality-card-icon">📐</span>
                <span class="quality-card-title">结构分析详情</span>
                <span class="quality-score-badge">${structureAnalysis.评分}/100</span>
            </div>
            <div class="quality-detail-list">
                <div class="quality-detail-item">
                    <span class="detail-label">总段落数</span>
                    <span class="detail-value">${structureAnalysis.段落分析.总段落数}段</span>
                </div>
                <div class="quality-detail-item">
                    <span class="detail-label">平均段落长度</span>
                    <span class="detail-value">${structureAnalysis.段落分析.平均长度}字</span>
                </div>
                <div class="quality-detail-item">
                    <span class="detail-label">"的"字占比</span>
                    <span class="detail-value">${structureAnalysis.语言分析.的字占比}</span>
                </div>
            </div>
        </div>
    `;

    // Suggestions with new design
    if (seoAnalysis.建议 && seoAnalysis.建议.length > 0) {
        html += `
            <div class="quality-suggestions-card">
                <div class="suggestions-header">
                    <span class="suggestions-icon">💡</span>
                    <span class="suggestions-title">优化建议</span>
                </div>
                <ul class="suggestions-list">
        `;
        seoAnalysis.建议.forEach(suggestion => {
            html += `<li class="suggestion-item">${suggestion}</li>`;
        });
        html += `</ul></div>`;
    }

    resultDiv.innerHTML = html;
}

function selectQualityTitle(title) {
    // Update the main title
    document.getElementById('view-title').innerText = title;

    // Visual feedback
    alert(`已选择标题:\n${title}`);
}

async function deleteArticle(event, id) {
    event.stopPropagation(); // 阻止点击事件冒泡到列表项上
    if (!confirm('确定要删除这篇文章吗？操作不可恢复。')) {
        return;
    }

    try {
        const response = await fetch('http://localhost:8001/delete-article', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id: id })
        });

        const result = await response.json();
        if (result.success) {
            // 删除成功，重新加载列表
            loadArticles();
            if (currentArticle && currentArticle.id === id) {
                document.getElementById('view-body').innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">文章已删除，请选择其他文章。</div>';
                document.getElementById('view-title').innerText = '未选择文章';
            }
        } else {
            alert('删除失败: ' + result.error);
        }
    } catch (err) {
        alert('后端服务未启动或连接出错: ' + err.message);
    }
}

window.onload = loadArticles;
