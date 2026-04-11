"""audience-filter.js 회귀 방지 테스트 (Phase 7.6)

JS 파일을 실행하지 않고 파일 내용을 검사해 특정 핵심 규칙이 유지되는지
확인한다. jsdom 의존성 없이 실행 가능.

회귀 방지 대상:
- Phase 7.6에서 발견된 버그: `[data-audience]` 셀렉터가 필터 칩 자체(.audience-chip)도
  매치하여, 사용자가 한 레벨을 선택한 순간 다른 칩들이 숨겨져 레벨 전환 불가.
  반드시 `:not(.audience-chip)` exclusion이 들어가야 한다.
"""

from pathlib import Path

import pytest


JS_FILE = Path(__file__).parent.parent / "src" / "static" / "js" / "audience-filter.js"
TEMPLATE_FILE = (
    Path(__file__).parent.parent
    / "src" / "static" / "templates" / "audience_filter.html"
)


@pytest.fixture(scope="module")
def js_source() -> str:
    assert JS_FILE.exists(), f"audience-filter.js not found at {JS_FILE}"
    return JS_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def template_source() -> str:
    assert TEMPLATE_FILE.exists()
    return TEMPLATE_FILE.read_text(encoding="utf-8")


class TestFilterExcludesChips:
    """Phase 7.6 — 필터가 칩 자체를 숨기지 않도록 selector에 exclusion이 있어야 함"""

    def test_card_selector_excludes_chips(self, js_source: str):
        """filter 대상 selector는 반드시 .audience-chip을 제외해야 함"""
        assert ":not(.audience-chip)" in js_source, (
            "audience-filter.js must exclude .audience-chip from its filter selector. "
            "Without this, clicking a level hides the other chips and locks the user "
            "into the first selection (Phase 7.6 regression)."
        )

    def test_no_naked_data_audience_selector_in_apply_filter(self, js_source: str):
        """applyFilter가 맨몸의 `[data-audience]`로 카드를 쿼리하면 안 됨.

        chips도 data-audience를 갖기 때문에 exclusion 없이 쿼리하면 칩이 숨겨진다.
        """
        # applyFilter 함수 블록만 추출
        start = js_source.find("function applyFilter")
        assert start >= 0, "applyFilter function not found"
        # 다음 최상위 function 시작까지 대략 추출 (간단 휴리스틱)
        end = js_source.find("\n    function ", start + 20)
        if end < 0:
            end = len(js_source)
        body = js_source[start:end]

        # 카드 쿼리 selector가 naked `[data-audience]`여선 안 됨
        # (querySelectorAll('[data-audience]') without :not(...))
        import re
        naked_pattern = re.compile(r"querySelectorAll\(\s*['\"]\[data-audience\]['\"]\s*\)")
        matches = naked_pattern.findall(body)
        assert not matches, (
            f"Found naked [data-audience] selector in applyFilter: {matches}. "
            "This matches the chips themselves and causes Phase 7.6 regression."
        )


class TestChipsCarryDataAudience:
    """필터 칩이 data-audience를 갖는 사실을 문서/주석으로 명시"""

    def test_template_documents_chip_attribute_trap(self, template_source: str):
        """audience_filter.html 주석에 exclusion 요구사항이 명시돼야 함"""
        assert "audience-chip" in template_source
        # 주석에서 exclusion 필요성 또는 회귀 테스트 언급
        assert "7.6" in template_source or "not(.audience-chip)" in template_source or \
               "exclusion" in template_source.lower() or "회귀" in template_source

    def test_js_source_comments_explain_trap(self, js_source: str):
        """JS 소스 상단 주석에 트랩/hotfix 언급이 있어야 함"""
        # 파일 앞 30줄 안에 7.6 or hotfix or not(.audience-chip) 언급
        header = "\n".join(js_source.splitlines()[:30])
        assert ("7.6" in header or "hotfix" in header.lower() or
                "not(.audience-chip)" in header)


class TestFilterChipsAllPresent:
    """필터 바 파셜이 4개 칩을 모두 정의하는지"""

    @pytest.mark.parametrize("audience", ["ALL", "GENERAL", "DEVELOPER", "ML_EXPERT"])
    def test_each_level_has_a_chip(self, template_source: str, audience: str):
        assert f'data-audience="{audience}"' in template_source, (
            f"Filter template missing chip for audience={audience}"
        )

    def test_chip_count_is_four(self, template_source: str):
        import re
        count = len(re.findall(r'class="audience-chip"', template_source))
        assert count == 4, f"Expected 4 audience chips, found {count}"
