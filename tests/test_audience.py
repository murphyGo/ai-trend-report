"""Audience enum 및 Article.audience 필드 테스트 (Phase 7.1)"""

import pytest

from src.models import Article, Audience, Category, Source


class TestAudienceEnum:
    """Audience enum 기본"""

    def test_members(self):
        assert {a.name for a in Audience} == {"GENERAL", "DEVELOPER", "ML_EXPERT"}

    def test_values(self):
        assert Audience.GENERAL.value == "일반인"
        assert Audience.DEVELOPER.value == "개발자"
        assert Audience.ML_EXPERT.value == "ML 전문가"


class TestAudienceFromString:
    """관대한 파싱"""

    @pytest.mark.parametrize("value,expected", [
        # enum name (대소문자 무관)
        ("GENERAL", Audience.GENERAL),
        ("general", Audience.GENERAL),
        ("DEVELOPER", Audience.DEVELOPER),
        ("developer", Audience.DEVELOPER),
        ("ML_EXPERT", Audience.ML_EXPERT),
        ("ml_expert", Audience.ML_EXPERT),
        # 한국어 value
        ("일반인", Audience.GENERAL),
        ("개발자", Audience.DEVELOPER),
        ("ML 전문가", Audience.ML_EXPERT),
        # 짧은 한국어
        ("일반", Audience.GENERAL),
        ("개발", Audience.DEVELOPER),
        ("전문가", Audience.ML_EXPERT),
        # 영어 약칭
        ("dev", Audience.DEVELOPER),
        ("mlexpert", Audience.ML_EXPERT),
        ("ml-expert", Audience.ML_EXPERT),
        ("expert", Audience.ML_EXPERT),
        ("ml", Audience.ML_EXPERT),
    ])
    def test_parses_known_aliases(self, value, expected):
        assert Audience.from_string(value) == expected

    @pytest.mark.parametrize("value", ["", "unknown", "foobar", None])
    def test_unknown_returns_none(self, value):
        # falsy 입력은 안전하게 None 반환 (guard clause)
        assert Audience.from_string(value) is None

    def test_ignores_surrounding_whitespace(self):
        assert Audience.from_string("  general  ") == Audience.GENERAL
        assert Audience.from_string("\t개발자\n") == Audience.DEVELOPER


class TestArticleAudience:
    """Article.audience 필드 동작"""

    def test_default_is_empty_list(self):
        article = Article(
            title="t", url="https://x.com/1", source=Source.ARXIV,
        )
        assert article.audience == []

    def test_accepts_audience_enums(self):
        article = Article(
            title="t", url="https://x.com/1", source=Source.ARXIV,
            audience=[Audience.ML_EXPERT, Audience.DEVELOPER],
        )
        assert article.audience == [Audience.ML_EXPERT, Audience.DEVELOPER]

    def test_normalizes_string_list_to_enums(self):
        """JSON에서 역직렬화될 때 문자열 리스트가 들어와도 Enum으로 정규화"""
        article = Article(
            title="t", url="https://x.com/1", source=Source.OPENAI_BLOG,
            audience=["GENERAL", "개발자"],
        )
        assert article.audience == [Audience.GENERAL, Audience.DEVELOPER]

    def test_drops_invalid_strings_silently(self):
        """알 수 없는 값은 조용히 제거 (나머지는 유지)"""
        article = Article(
            title="t", url="https://x.com/1", source=Source.ARXIV,
            audience=["GENERAL", "garbage", "DEVELOPER"],
        )
        assert article.audience == [Audience.GENERAL, Audience.DEVELOPER]

    def test_dedupes_preserving_order(self):
        article = Article(
            title="t", url="https://x.com/1", source=Source.ARXIV,
            audience=[Audience.GENERAL, Audience.DEVELOPER, Audience.GENERAL],
        )
        assert article.audience == [Audience.GENERAL, Audience.DEVELOPER]


class TestArticleAudienceSerialization:
    """to_dict / from_dict 라운드트립"""

    def test_to_dict_uses_enum_names(self):
        article = Article(
            title="t", url="https://x.com/1", source=Source.ARXIV,
            audience=[Audience.ML_EXPERT, Audience.DEVELOPER],
        )
        assert article.to_dict()["audience"] == ["ML_EXPERT", "DEVELOPER"]

    def test_roundtrip_preserves_audience(self):
        original = Article(
            title="t", url="https://x.com/1", source=Source.OPENAI_BLOG,
            category=Category.LLM,
            audience=[Audience.GENERAL, Audience.DEVELOPER],
        )
        restored = Article.from_dict(original.to_dict())
        assert restored.audience == original.audience

    def test_legacy_dict_without_audience_field(self):
        """Phase 7 이전 JSON에는 audience 필드가 없음 — 빈 리스트로 복원"""
        legacy_dict = {
            "id": "abc",
            "title": "Legacy article",
            "url": "https://x.com/1",
            "source": "arxiv",
            "category": "LLM (대규모 언어 모델)",
        }
        article = Article.from_dict(legacy_dict)
        assert article.audience == []

    def test_legacy_dict_with_null_audience(self):
        """audience가 null인 경우도 안전하게 빈 리스트로 처리"""
        legacy_dict = {
            "id": "abc",
            "title": "Legacy",
            "url": "https://x.com/1",
            "source": "arxiv",
            "audience": None,
        }
        article = Article.from_dict(legacy_dict)
        assert article.audience == []


class TestStaticGeneratorAudienceHelpers:
    """static_generator의 audience 헬퍼 — source fallback 동작"""

    def test_get_article_audience_uses_claude_tags_when_set(self):
        from src.static_generator import get_article_audience
        article = Article(
            title="t", url="https://x.com/1", source=Source.ARXIV,
            audience=[Audience.GENERAL],
        )
        # Claude가 명시적으로 GENERAL만 태그했으면 source 기본값(ML_EXPERT)을 무시
        assert get_article_audience(article) == [Audience.GENERAL]

    def test_get_article_audience_falls_back_to_source(self):
        from src.static_generator import get_article_audience
        article = Article(
            title="t", url="https://x.com/1", source=Source.ARXIV,
        )
        # 빈 audience → ARXIV의 기본 매핑 (ML_EXPERT)
        assert get_article_audience(article) == [Audience.ML_EXPERT]

    def test_get_article_audience_techcrunch_is_general(self):
        from src.static_generator import get_article_audience
        article = Article(
            title="t", url="https://x.com/1", source=Source.TECHCRUNCH_AI,
        )
        assert get_article_audience(article) == [Audience.GENERAL]

    def test_get_audience_data_attr_format(self):
        from src.static_generator import get_audience_data_attr
        article = Article(
            title="t", url="https://x.com/1", source=Source.ARXIV,
            audience=[Audience.GENERAL, Audience.DEVELOPER],
        )
        assert get_audience_data_attr(article) == "GENERAL,DEVELOPER"

    def test_get_audience_data_attr_fallback(self):
        from src.static_generator import get_audience_data_attr
        article = Article(
            title="t", url="https://x.com/1", source=Source.NVIDIA_BLOG,
        )
        # NVIDIA는 DEVELOPER + ML_EXPERT 기본 매핑
        assert get_audience_data_attr(article) == "DEVELOPER,ML_EXPERT"

    def test_count_audience_aggregates_multi_tag(self):
        from src.static_generator import count_audience
        articles = [
            Article(title="1", url="https://x.com/1", source=Source.ARXIV,
                    audience=[Audience.ML_EXPERT]),
            Article(title="2", url="https://x.com/2", source=Source.OPENAI_BLOG,
                    audience=[Audience.GENERAL, Audience.DEVELOPER]),
            Article(title="3", url="https://x.com/3", source=Source.MARKTECHPOST,
                    audience=[Audience.DEVELOPER, Audience.ML_EXPERT]),
        ]
        counts = count_audience(articles)
        assert counts == {"GENERAL": 1, "DEVELOPER": 2, "ML_EXPERT": 2}

    def test_count_audience_uses_fallback_for_untagged(self):
        from src.static_generator import count_audience
        # 태그 없는 arxiv 기사는 fallback으로 ML_EXPERT 카운트에 포함
        articles = [
            Article(title="1", url="https://x.com/1", source=Source.ARXIV),
            Article(title="2", url="https://x.com/2", source=Source.ARXIV),
        ]
        counts = count_audience(articles)
        assert counts["ML_EXPERT"] == 2
        assert counts["GENERAL"] == 0
