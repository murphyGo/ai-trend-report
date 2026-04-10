// AI Report Search functionality using Fuse.js

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
// Empty string falls back to root-relative paths (works on localhost).
const SITE_BASE_URL = window.SITE_BASE_URL || '';

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
        document.getElementById('results-info').textContent = 'Failed to load search data';
    }
}

// Perform search
function performSearch() {
    const query = document.getElementById('search-input').value.trim();
    const categoryFilter = document.getElementById('category-filter').value;

    let results = [];

    if (query) {
        // Use Fuse.js for fuzzy search
        const fuseResults = fuse.search(query);
        results = fuseResults.map(r => r.item);
    } else {
        // No query, show all (or filtered)
        results = [...searchIndex];
    }

    // Apply category filter
    if (categoryFilter) {
        results = results.filter(item => item.category === categoryFilter);
    }

    // Sort by date (newest first)
    results.sort((a, b) => b.date.localeCompare(a.date));

    // Limit results
    const maxResults = 100;
    const limitedResults = results.slice(0, maxResults);

    // Display results
    displayResults(limitedResults, results.length);
}

// Display results
function displayResults(results, totalCount) {
    const infoEl = document.getElementById('results-info');
    const listEl = document.getElementById('results-list');

    if (results.length === 0) {
        infoEl.textContent = 'No results found';
        listEl.innerHTML = '';
        return;
    }

    infoEl.textContent = `Found ${totalCount} articles${totalCount > 100 ? ' (showing first 100)' : ''}`;

    listEl.innerHTML = results.map(article => `
        <article class="article-card">
            <h4>
                <a href="${article.url}" target="_blank" rel="noopener">
                    ${escapeHtml(article.title)}
                </a>
            </h4>
            <div class="article-meta">
                <span class="category-badge" style="background: ${categoryColors[article.category] || '#9E9E9E'}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">
                    ${categoryLabels[article.category] || article.category}
                </span>
                <span class="source">${article.source}</span>
                <span class="date">${article.date}</span>
                <a href="${article.report_url}" class="report-link">View Report</a>
            </div>
            ${article.summary ? `<p class="summary">${escapeHtml(article.summary)}</p>` : ''}
        </article>
    `).join('');
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadSearchIndex();

    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const categoryFilter = document.getElementById('category-filter');

    // Search on button click
    searchBtn.addEventListener('click', performSearch);

    // Search on Enter key
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Filter on category change
    categoryFilter.addEventListener('change', performSearch);

    // Debounced search on input
    let debounceTimer;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(performSearch, 300);
    });
});
