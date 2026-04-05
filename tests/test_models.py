"""데이터 모델 테스트"""

import pytest
from datetime import datetime

from src.models import Article, Report, Category, Source


class TestCategory:
    """Category enum 테스트"""

    def test_category_from_string_exact_match(self):
        """정확한 카테고리 매칭"""
        assert Category.from_string("LLM (대규모 언어 모델)") == Category.LLM
        assert Category.from_string("AI 에이전트 & 자동화") == Category.AGENT
        assert Category.from_string("컴퓨터 비전 & 멀티모달") == Category.VISION

    def test_category_from_string_partial_match(self):
        """부분 매칭 (값에 포함)"""
        assert Category.from_string("이 기사는 LLM에 관한 것입니다") == Category.LLM
        assert Category.from_string("비디오 생성 기술") == Category.VIDEO

    def test_category_from_string_name_match(self):
        """enum 이름으로 매칭"""
        assert Category.from_string("llm") == Category.LLM
        assert Category.from_string("AGENT") == Category.AGENT
        assert Category.from_string("vision") == Category.VISION

    def test_category_from_string_case_insensitive(self):
        """대소문자 무시"""
        assert Category.from_string("LLM") == Category.LLM
        assert Category.from_string("llm") == Category.LLM

    def test_category_from_string_unknown_returns_other(self):
        """알 수 없는 문자열은 OTHER 반환"""
        assert Category.from_string("unknown category") == Category.OTHER
        assert Category.from_string("") == Category.OTHER
        assert Category.from_string("xyz") == Category.OTHER


class TestSource:
    """Source enum 테스트"""

    def test_source_values(self):
        """Source enum 값 확인"""
        assert Source.ARXIV.value == "arxiv"
        assert Source.GOOGLE_BLOG.value == "google"
        assert Source.ANTHROPIC_BLOG.value == "anthropic"


class TestArticle:
    """Article 데이터클래스 테스트"""

    def test_article_creation(self, sample_article):
        """기본 Article 생성"""
        assert sample_article.title == "테스트 기사 제목"
        assert sample_article.source == Source.ARXIV
        assert sample_article.category == Category.LLM

    def test_article_default_values(self):
        """기본값 확인"""
        article = Article(
            title="Test",
            url="https://example.com",
            source=Source.ARXIV,
        )
        assert article.content == ""
        assert article.summary == ""
        assert article.published_at is None
        assert article.category == Category.OTHER
        assert article.id  # UUID 자동 생성

    def test_article_post_init_string_source(self):
        """문자열 source 자동 변환"""
        article = Article(
            title="Test",
            url="https://example.com",
            source="arxiv",  # type: ignore
        )
        assert article.source == Source.ARXIV

    def test_article_post_init_string_category(self):
        """문자열 category 자동 변환"""
        article = Article(
            title="Test",
            url="https://example.com",
            source=Source.ARXIV,
            category="LLM",  # type: ignore
        )
        assert article.category == Category.LLM

    def test_article_to_dict(self, sample_article):
        """to_dict 직렬화"""
        data = sample_article.to_dict()
        assert data["id"] == "test-article-001"
        assert data["title"] == "테스트 기사 제목"
        assert data["source"] == "arxiv"
        assert data["category"] == "LLM (대규모 언어 모델)"
        assert data["published_at"] == "2024-04-05T12:00:00"

    def test_article_to_dict_none_published_at(self):
        """published_at이 None일 때 직렬화"""
        article = Article(
            title="Test",
            url="https://example.com",
            source=Source.ARXIV,
        )
        data = article.to_dict()
        assert data["published_at"] is None

    def test_article_from_dict(self, sample_article_dict):
        """from_dict 역직렬화"""
        article = Article.from_dict(sample_article_dict)
        assert article.id == "test-article-001"
        assert article.title == "테스트 기사 제목"
        assert article.source == Source.ARXIV
        assert article.category == Category.LLM
        assert article.published_at == datetime(2024, 4, 5, 12, 0, 0)

    def test_article_from_dict_minimal(self):
        """최소 필드로 역직렬화"""
        data = {
            "title": "Minimal",
            "url": "https://example.com",
            "source": "arxiv",
        }
        article = Article.from_dict(data)
        assert article.title == "Minimal"
        assert article.content == ""
        assert article.summary == ""
        assert article.category == Category.OTHER

    def test_article_roundtrip(self, sample_article):
        """to_dict → from_dict 왕복"""
        data = sample_article.to_dict()
        restored = Article.from_dict(data)
        assert restored.id == sample_article.id
        assert restored.title == sample_article.title
        assert restored.source == sample_article.source
        assert restored.category == sample_article.category


class TestReport:
    """Report 데이터클래스 테스트"""

    def test_report_creation(self, sample_report):
        """기본 Report 생성"""
        assert sample_report.id == "test-report-001"
        assert len(sample_report.articles) == 2

    def test_report_default_values(self):
        """기본값 확인"""
        report = Report()
        assert report.articles == []
        assert report.id  # UUID 자동 생성
        assert report.created_at  # 현재 시간 자동 설정

    def test_report_articles_by_category(self, sample_report):
        """카테고리별 그룹화"""
        by_category = sample_report.articles_by_category()
        assert Category.LLM in by_category
        assert Category.VISION in by_category
        assert len(by_category[Category.LLM]) == 1
        assert len(by_category[Category.VISION]) == 1

    def test_report_articles_by_category_empty(self):
        """빈 리포트 그룹화"""
        report = Report()
        by_category = report.articles_by_category()
        assert by_category == {}

    def test_report_to_dict(self, sample_report):
        """to_dict 직렬화"""
        data = sample_report.to_dict()
        assert data["id"] == "test-report-001"
        assert data["created_at"] == "2024-04-05T09:00:00"
        assert len(data["articles"]) == 2

    def test_report_from_dict(self, sample_report):
        """from_dict 역직렬화"""
        data = sample_report.to_dict()
        restored = Report.from_dict(data)
        assert restored.id == sample_report.id
        assert len(restored.articles) == 2
        assert restored.articles[0].title == "테스트 기사 제목"

    def test_report_roundtrip(self, sample_report):
        """to_dict → from_dict 왕복"""
        data = sample_report.to_dict()
        restored = Report.from_dict(data)
        assert restored.id == sample_report.id
        assert restored.created_at == sample_report.created_at
        assert len(restored.articles) == len(sample_report.articles)
