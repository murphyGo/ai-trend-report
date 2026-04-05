"""통합 테스트"""

import pytest
import responses
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.models import Article, Report, Category, Source
from src.config import Config
from src.data_io import save_articles, load_articles, save_report, load_report


class TestDataPipeline:
    """데이터 파이프라인 통합 테스트"""

    def test_article_save_load_roundtrip(self, tmp_path):
        """기사 저장 → 로드 전체 흐름"""
        # 기사 생성
        articles = [
            Article(
                title="Integration Test Article 1",
                url="https://example.com/1",
                source=Source.ARXIV,
                content="Test content 1",
                summary="Test summary 1",
                category=Category.LLM,
            ),
            Article(
                title="Integration Test Article 2",
                url="https://example.com/2",
                source=Source.GOOGLE_BLOG,
                content="Test content 2",
                summary="Test summary 2",
                category=Category.VISION,
            ),
        ]

        # 저장
        filepath = save_articles(articles, tmp_path, "integration_test.json")

        # 로드
        loaded = load_articles(filepath)

        # 검증
        assert len(loaded) == 2
        assert loaded[0].title == articles[0].title
        assert loaded[0].source == articles[0].source
        assert loaded[1].category == articles[1].category

    def test_report_save_load_roundtrip(self, tmp_path, sample_report):
        """리포트 저장 → 로드 전체 흐름"""
        # 저장
        filepath = save_report(sample_report, tmp_path, "report_test.json")

        # 로드
        loaded = load_report(filepath)

        # 검증
        assert loaded.id == sample_report.id
        assert len(loaded.articles) == len(sample_report.articles)
        assert loaded.articles[0].title == sample_report.articles[0].title


class TestCollectorPipeline:
    """수집기 파이프라인 통합 테스트"""

    @responses.activate
    def test_arxiv_to_article_conversion(self):
        """arXiv RSS → Article 변환"""
        from src.collectors import ArxivCollector

        rss_response = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>cs.AI updates</title>
    <item>
      <title>Test Paper (cs.AI)</title>
      <link>http://arxiv.org/abs/2404.00001</link>
      <description>Test abstract</description>
    </item>
  </channel>
</rss>"""

        responses.add(
            responses.GET,
            "https://rss.arxiv.org/rss/cs.AI",
            body=rss_response,
            status=200,
        )

        collector = ArxivCollector(categories=["cs.AI"])
        articles = collector.fetch_articles()

        assert len(articles) == 1
        assert articles[0].source == Source.ARXIV
        assert "(cs.AI)" not in articles[0].title  # 태그 제거됨


class TestCategoryClassification:
    """카테고리 분류 통합 테스트"""

    def test_category_from_string_integration(self):
        """다양한 입력에서 카테고리 분류"""
        test_cases = [
            ("LLM (대규모 언어 모델)", Category.LLM),
            ("AI 에이전트 & 자동화", Category.AGENT),
            ("컴퓨터 비전 & 멀티모달", Category.VISION),
            ("비디오 생성", Category.VIDEO),
            ("로보틱스 & 3D", Category.ROBOTICS),
            ("AI 안전성 & 윤리", Category.SAFETY),
            ("강화학습", Category.RL),
            ("ML 인프라 & 최적화", Category.INFRA),
            ("의료 & 생명과학", Category.MEDICAL),
            ("금융 & 트레이딩", Category.FINANCE),
            ("산업 동향 & 한국 소식", Category.INDUSTRY),
            ("기타", Category.OTHER),
            ("Unknown Category", Category.OTHER),
        ]

        for input_str, expected in test_cases:
            result = Category.from_string(input_str)
            assert result == expected, f"Failed for input: {input_str}"

    def test_article_category_assignment(self):
        """기사에 카테고리 할당"""
        article = Article(
            title="Test",
            url="https://example.com",
            source=Source.ARXIV,
            category="LLM",  # 문자열로 전달 # type: ignore
        )

        assert article.category == Category.LLM


class TestReportGrouping:
    """리포트 그룹화 통합 테스트"""

    def test_articles_by_category_grouping(self):
        """카테고리별 기사 그룹화"""
        articles = [
            Article(title="LLM Article 1", url="https://1.com", source=Source.ARXIV, category=Category.LLM),
            Article(title="Vision Article", url="https://2.com", source=Source.ARXIV, category=Category.VISION),
            Article(title="LLM Article 2", url="https://3.com", source=Source.ARXIV, category=Category.LLM),
            Article(title="Safety Article", url="https://4.com", source=Source.ARXIV, category=Category.SAFETY),
        ]

        report = Report(articles=articles)
        by_category = report.articles_by_category()

        assert len(by_category[Category.LLM]) == 2
        assert len(by_category[Category.VISION]) == 1
        assert len(by_category[Category.SAFETY]) == 1
        assert Category.AGENT not in by_category


class TestEndToEnd:
    """End-to-End 테스트"""

    @responses.activate
    def test_collect_and_save(self, tmp_path):
        """수집 → 저장 흐름"""
        from src.collectors import ArxivCollector

        rss_response = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>cs.AI updates</title>
    <item>
      <title>E2E Test Paper</title>
      <link>http://arxiv.org/abs/2404.99999</link>
      <description>E2E test abstract</description>
    </item>
  </channel>
</rss>"""

        responses.add(
            responses.GET,
            "https://rss.arxiv.org/rss/cs.AI",
            body=rss_response,
            status=200,
        )

        # 수집
        collector = ArxivCollector(categories=["cs.AI"])
        articles = collector.fetch_articles()

        # 저장
        filepath = save_articles(articles, tmp_path, "e2e_test.json")

        # 로드 및 검증
        loaded = load_articles(filepath)
        assert len(loaded) == 1
        assert "E2E Test" in loaded[0].title

    def test_full_report_workflow(self, tmp_path, sample_article):
        """전체 리포트 워크플로우"""
        # 1. 기사 목록 생성
        articles = [sample_article]

        # 2. 기사 저장
        articles_path = save_articles(articles, tmp_path, "articles.json")

        # 3. 기사 로드
        loaded_articles = load_articles(articles_path)

        # 4. 리포트 생성
        report = Report(articles=loaded_articles)

        # 5. 리포트 저장
        report_path = save_report(report, tmp_path, "report.json")

        # 6. 리포트 로드
        loaded_report = load_report(report_path)

        # 7. 검증
        assert len(loaded_report.articles) == 1
        assert loaded_report.articles[0].title == sample_article.title
        by_category = loaded_report.articles_by_category()
        assert Category.LLM in by_category
