// AI Report Search functionality using Fuse.js
//
// Phase 8.6 Hotfix:
//   - 모든 사용자 입력 필드를 innerHTML에 삽입하기 전에 escapeHtml 적용
//   - URL은 safeUrl()로 프로토콜(http/https)만 허용, javascript:/data: 등 차단
//   - 렌더된 카드에 data-audience 속성을 포함해 audience 필터와 통합
//   - window.AudienceFilter.applyCurrent() 호출로 현재 레벨 필터 재적용

let searchIndex = [];
let fuse = null;

const categoryLabels = {
    'LLM': 'LLM',
    'AGENT': 'AI 에이전트',
    'VISION': '컴퓨터 비전',
    'VIDEO': '비디오 생성',
    'ROBOTICS': '로보틱스',
    'SAFETY': 'AI 안전성',
    'RL': '강화학습',
    'INFRA': 'ML 인프라',
    'MEDICAL': '의료/생명과학',
    'FINANCE': '금융',
    'INDUSTRY': '산업 동향',
    'OTHER': '기타'
};

const categoryColors = {
    'LLM': '#4CAF50',
    'AGENT': '#2196F3',
    'VISION': '#9C27B0',
    'VIDEO': '#E91E63',
    'ROBOTICS': '#FF5722',
    'SAFETY': '#F44336',
    'RL': '#00BCD4',
    'INFRA': '#607D8B',
    'MEDICAL': '#8BC34A',
    'FINANCE': '#FFC107',
    'INDUSTRY': '#795548',
    'OTHER': '#9E9E9E'
};

// Base URL for fetching site-local resources (set in base.html).
const SITE_BASE_URL = window.SITE_BASE_URL || '';

// HTML escape to prevent XSS when inserting user-controlled text.
function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// Validate URL protocol. Returns '#' for anything other than http/https/relative.
// Blocks javascript:, data:, vbscript:, etc. (XSS vectors).
function safeUrl(url) {
    if (!url || typeof url !== 'string') return '#';
    try {
        // Relative URLs start with / and resolve against current origin — allow.
        if (url.startsWith('/')) return url;
        const parsed = new URL(url);
        if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
            return url;
        }
        return '#';
    } catch (e) {
        return '#';
    }
}

// Load search index
async function loadSearchIndex() {
    try {
        const response = await fetch(`${SITE_BASE_URL}/data/search-index.json`);
        searchIndex = await response.json();

        // Initialize Fuse.js
        fuse = new Fuse(searchIndex, {
            keys: [
                { name: 'title', weight: 0.4 },
                { name: 'summary', weight: 0.3 },
                { name: 'category', weight: 0.2 },
                { name: 'source', weight: 0.1 }
            ],
            threshold: 0.4,
            includeScore: true
        });

        console.log(`Loaded ${searchIndex.length} articles for search`);
    } catch (error) {
        console.error('Failed to load search index:', error);
        const info = document.getElementById('results-info');
        if (info) info.textContent = 'Failed to load search data';
    }
}

// Perform search
function performSearch() {
    const query = document.getElementById('search-input').value.trim();
    const categoryFilter = document.getElementById('category-filter').value;

    let results = [];

    if (query && fuse) {
        const fuseResults = fuse.search(query);
        results = fuseResults.map(r => r.item);
    } else {
        results = [...searchIndex];
    }

    if (categoryFilter) {
        results = results.filter(item => item.category === categoryFilter);
    }

    // Sort by date (newest first)
    results.sort((a, b) => (b.date || '').localeCompare(a.date || ''));

    const maxResults = 100;
    const limitedResults = results.slice(0, maxResults);

    displayResults(limitedResults, results.length);
}

// Render results
function displayResults(results, totalCount) {
    const infoEl = document.getElementById('results-info');
    const listEl = document.getElementById('results-list');

    if (results.length === 0) {
        infoEl.textContent = 'No results found';
        listEl.innerHTML = '';
        return;
    }

    infoEl.textContent = `Found ${totalCount} articles${totalCount > 100 ? ' (showing first 100)' : ''}`;

    listEl.innerHTML = results.map(article => {
        const catKey = article.category || 'OTHER';
        const catLabel = categoryLabels[catKey] || catKey;
        const catColor = categoryColors[catKey] || '#9E9E9E';
        const sourceLabel = article.source_label || article.source || '';
        const audienceAttr = Array.isArray(article.audience)
            ? article.audience.join(',')
            : '';

        return `
        <article class="article-card" data-audience="${escapeHtml(audienceAttr)}">
            <h4>
                <a href="${escapeHtml(safeUrl(article.url))}" target="_blank" rel="noopener">
                    ${escapeHtml(article.title)}
                </a>
            </h4>
            <div class="article-meta">
                <span class="category-badge" style="background: ${escapeHtml(catColor)}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">
                    ${escapeHtml(catLabel)}
                </span>
                <span class="source">${escapeHtml(sourceLabel)}</span>
                <span class="date">${escapeHtml(article.date)}</span>
                <a href="${escapeHtml(safeUrl(article.report_url))}" class="report-link">View Report</a>
            </div>
            ${article.summary ? `<p class="summary">${escapeHtml(article.summary)}</p>` : ''}
        </article>
        `;
    }).join('');

    // Phase 8.6 — 동적으로 렌더한 카드에 현재 audience 필터를 재적용.
    // audience-filter.js가 노출한 public API 사용.
    if (window.AudienceFilter && typeof window.AudienceFilter.applyCurrent === 'function') {
        window.AudienceFilter.applyCurrent();
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadSearchIndex();

    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const categoryFilter = document.getElementById('category-filter');

    if (searchBtn) searchBtn.addEventListener('click', performSearch);
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performSearch();
        });

        // Debounced search on input
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(performSearch, 300);
        });
    }
    if (categoryFilter) categoryFilter.addEventListener('change', performSearch);
});
