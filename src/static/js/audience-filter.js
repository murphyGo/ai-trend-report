// Audience filter — Phase 7.3
//
// 독자 레벨 필터 바 (audience_filter.html)의 칩 클릭에 반응해 전역적으로 기사 표시를
// 필터링. 선택 값은 localStorage에 저장되어 페이지 이동 시에도 유지된다.
//
// 규칙:
// - `[data-audience]` 속성이 있는 요소가 필터 대상 (article-card 등).
// - data-audience는 콤마 구분 enum name 문자열 (예: "GENERAL,DEVELOPER").
// - 선택 값이 'ALL'이거나 카드의 audience 중 하나에 포함되면 표시.
// - 기사 리스트 안이 완전히 비게 되면 "조건에 맞는 기사가 없어요" empty state 표시.
// - 카테고리별 섹션 전체가 비게 되면 섹션 자체를 숨김.
//
// JS가 로드되지 않거나 실패해도 모든 기사가 그대로 노출됨 (graceful degradation).

(function () {
    'use strict';

    var STORAGE_KEY = 'aiReportAudience';
    var DEFAULT = 'ALL';
    var VALID = ['ALL', 'GENERAL', 'DEVELOPER', 'ML_EXPERT'];

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
        var cards = document.querySelectorAll('[data-audience]');
        cards.forEach(function (card) {
            card.hidden = !matchesAudience(card, audience);
        });

        // 필터 칩 active 토글
        var chips = document.querySelectorAll('.audience-chip');
        chips.forEach(function (chip) {
            var isActive = chip.getAttribute('data-audience') === audience;
            chip.classList.toggle('active', isActive);
            chip.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });

        // 카테고리 섹션 (report.html, category.html 등)에서 섹션 내 모든 카드가 숨겨지면
        // 섹션 자체를 숨김.
        document.querySelectorAll('.category-section').forEach(function (section) {
            var visible = section.querySelector('[data-audience]:not([hidden])');
            section.hidden = !visible;
        });

        // .article-list 안의 empty state 처리
        document.querySelectorAll('.article-list').forEach(function (list) {
            var visible = list.querySelector(':scope > [data-audience]:not([hidden]), :scope > .article-card:not([hidden])');
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

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
