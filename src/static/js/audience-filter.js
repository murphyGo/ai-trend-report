// Audience filter — Phase 7.3 (+ 7.6 hotfix)
//
// 독자 레벨 필터 바 (audience_filter.html)의 칩 클릭에 반응해 전역적으로 기사 표시를
// 필터링. 선택 값은 localStorage에 저장되어 페이지 이동 시에도 유지된다.
//
// 규칙:
// - `.article-card[data-audience]` 등 필터링 대상 카드에 data-audience 속성 부착
//   (콤마 구분 enum name 문자열, 예: "GENERAL,DEVELOPER")
// - 선택 값이 'ALL'이거나 카드의 audience 중 하나에 포함되면 표시
// - 기사 리스트가 비게 되면 empty state 삽입, 카테고리 섹션이 비게 되면 섹션 자체 숨김
//
// ⚠️ Phase 7.6 hotfix:
//   필터 칩(.audience-chip)도 클릭 라우팅용으로 data-audience 속성을 갖는다.
//   순진하게 `[data-audience]`로 쿼리하면 칩 자신이 필터링에 걸려 다른 레벨
//   선택 후 나머지 칩이 사라지는 버그가 발생한다. 반드시 `:not(.audience-chip)`
//   로 칩을 제외해야 한다. (`tests/test_audience_filter_js.py`가 회귀 방지)
//
// Graceful degradation: JS가 로드되지 않거나 실패해도 모든 기사가 그대로 노출됨.

(function () {
    'use strict';

    var STORAGE_KEY = 'aiReportAudience';
    var DEFAULT = 'ALL';
    var VALID = ['ALL', 'GENERAL', 'DEVELOPER', 'ML_EXPERT'];

    // 필터 대상 카드를 쿼리할 때 쓰는 selector. 칩 자신을 제외해야 한다. (Phase 7.6)
    var CARD_SELECTOR = '[data-audience]:not(.audience-chip)';

    function getSaved() {
        try {
            var v = localStorage.getItem(STORAGE_KEY);
            return VALID.indexOf(v) >= 0 ? v : DEFAULT;
        } catch (e) {
            return DEFAULT;
        }
    }

    function setSaved(value) {
        try {
            localStorage.setItem(STORAGE_KEY, value);
        } catch (e) {
            // localStorage 거부 (private mode 등) — 세션 내에서만 적용
        }
    }

    function matchesAudience(card, audience) {
        if (audience === 'ALL') return true;
        var raw = card.getAttribute('data-audience') || '';
        if (!raw) return true; // audience 정보 없으면 항상 표시 (fallback)
        return raw.split(',').indexOf(audience) >= 0;
    }

    function ensureEmptyState(container, message) {
        var existing = container.querySelector(':scope > .audience-empty-state');
        if (existing) return existing;
        var node = document.createElement('div');
        node.className = 'audience-empty-state';
        node.innerHTML = '<p>' + message + '</p>';
        container.appendChild(node);
        return node;
    }

    function applyFilter(audience) {
        // Phase 7.6: 칩 제외 selector 사용 — 일반 article-card만 필터링
        var cards = document.querySelectorAll(CARD_SELECTOR);
        cards.forEach(function (card) {
            card.hidden = !matchesAudience(card, audience);
        });

        // 필터 칩 active 토글 (칩은 항상 보이게 유지)
        var chips = document.querySelectorAll('.audience-chip');
        chips.forEach(function (chip) {
            chip.hidden = false; // 이전 상태에서 잘못 숨겨졌다면 복원
            var isActive = chip.getAttribute('data-audience') === audience;
            chip.classList.toggle('active', isActive);
            chip.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });

        // 카테고리 섹션 (report.html, category.html 등)에서 섹션 내 모든 카드가 숨겨지면
        // 섹션 자체를 숨김. 칩은 .category-section 내부에 없으므로 exclusion 영향 없음.
        document.querySelectorAll('.category-section').forEach(function (section) {
            var visible = section.querySelector(CARD_SELECTOR + ':not([hidden])');
            section.hidden = !visible;
        });

        // .article-list 안의 empty state 처리
        document.querySelectorAll('.article-list').forEach(function (list) {
            var visible = list.querySelector(':scope > .article-card:not([hidden])');
            var emptyNode = list.querySelector(':scope > .audience-empty-state');
            if (!visible && audience !== 'ALL') {
                ensureEmptyState(list, '현재 선택한 레벨에 맞는 기사가 없어요.').hidden = false;
            } else if (emptyNode) {
                emptyNode.hidden = true;
            }
        });
    }

    function init() {
        var saved = getSaved();
        applyFilter(saved);

        document.querySelectorAll('.audience-chip').forEach(function (chip) {
            chip.addEventListener('click', function (e) {
                var value = e.currentTarget.getAttribute('data-audience') || DEFAULT;
                if (VALID.indexOf(value) < 0) return;
                setSaved(value);
                applyFilter(value);
            });
        });
    }

    // Phase 8.6 — Public API. 동적으로 카드를 추가하는 다른 스크립트(search.js 등)가
    // 렌더 후 현재 필터를 재적용할 수 있도록 전역에 노출.
    //
    // 사용 예:
    //   listEl.innerHTML = renderedCards;
    //   window.AudienceFilter.applyCurrent();
    window.AudienceFilter = {
        apply: function (value) {
            if (VALID.indexOf(value) < 0) value = DEFAULT;
            setSaved(value);
            applyFilter(value);
        },
        applyCurrent: function () {
            applyFilter(getSaved());
        },
        getCurrent: getSaved,
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
