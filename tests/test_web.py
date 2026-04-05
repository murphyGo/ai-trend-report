"""웹 대시보드 테스트"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from src.web.app import app
from src.web import service
from src.models import Article, Report, Category, Source
from src.data_io import save_report


@pytest.fixture
def client():
    """TestClient fixture"""
    return TestClient(app)


@pytest.fixture
def sample_report():
    """샘플 리포트 fixture"""
    articles = [
        Article(
            id="article-1",
            title="LLM Research Article",
            url="https://example.com/llm",
            source=Source.ARXIV,
            summary="This is a summary about LLM.",
            category=Category.LLM,
        ),
        Article(
            id="article-2",
            title="Vision AI Article",
            url="https://example.com/vision",
            source=Source.GOOGLE_BLOG,
            summary="This is a summary about vision AI.",
            category=Category.VISION,
        ),
    ]
    return Report(
        id="report-123",
        articles=articles,
        created_at=datetime(2026, 4, 5, 10, 0, 0),
    )


class TestIndexPage:
    """메인 페이지 테스트"""

    def test_index_page_loads(self, client):
        """메인 페이지 로드"""
        response = client.get("/")
        assert response.status_code == 200
        assert "AI Report Dashboard" in response.text

    def test_index_page_shows_no_reports(self, client, tmp_path, monkeypatch):
        """리포트 없을 때"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)

        with patch.object(service, "list_reports", return_value=[]):
            response = client.get("/")
            assert response.status_code == 200
            assert "No reports available" in response.text

    def test_index_page_with_reports(self, client, tmp_path, monkeypatch, sample_report):
        """리포트 있을 때"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)
        save_report(sample_report, tmp_path)

        response = client.get("/")
        assert response.status_code == 200
        # 리포트가 표시되는지 확인
        assert "2 articles" in response.text
        assert "report-123" in response.text

    def test_search_articles(self, client, tmp_path, monkeypatch, sample_report):
        """기사 검색"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)
        save_report(sample_report, tmp_path)

        response = client.get("/?q=LLM")
        assert response.status_code == 200
        assert "LLM Research Article" in response.text

    def test_search_no_results(self, client, tmp_path, monkeypatch, sample_report):
        """검색 결과 없음"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)
        save_report(sample_report, tmp_path)

        response = client.get("/?q=nonexistent")
        assert response.status_code == 200
        assert "No articles found" in response.text


class TestReportDetailPage:
    """리포트 상세 페이지 테스트"""

    def test_report_detail_loads(self, client, tmp_path, monkeypatch, sample_report):
        """리포트 상세 페이지 로드"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)
        save_report(sample_report, tmp_path)

        response = client.get(f"/reports/{sample_report.id}")
        assert response.status_code == 200
        assert "2026-04-05" in response.text
        assert "LLM Research Article" in response.text

    def test_report_not_found(self, client, tmp_path, monkeypatch):
        """존재하지 않는 리포트"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)

        response = client.get("/reports/nonexistent-id")
        assert response.status_code == 404


class TestAPIReports:
    """REST API 리포트 테스트"""

    def test_api_list_reports(self, client, tmp_path, monkeypatch, sample_report):
        """API 리포트 목록"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)
        save_report(sample_report, tmp_path)

        response = client.get("/api/reports")
        assert response.status_code == 200

        data = response.json()
        assert "count" in data
        assert "reports" in data
        assert data["count"] >= 1

    def test_api_report_detail(self, client, tmp_path, monkeypatch, sample_report):
        """API 리포트 상세"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)
        save_report(sample_report, tmp_path)

        response = client.get(f"/api/reports/{sample_report.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == sample_report.id
        assert "stats" in data
        assert "articles" in data
        assert len(data["articles"]) == 2

    def test_api_report_not_found(self, client, tmp_path, monkeypatch):
        """API 존재하지 않는 리포트"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)

        response = client.get("/api/reports/nonexistent-id")
        assert response.status_code == 404


class TestAPISearch:
    """REST API 검색 테스트"""

    def test_api_search(self, client, tmp_path, monkeypatch, sample_report):
        """API 검색"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)
        save_report(sample_report, tmp_path)

        response = client.get("/api/search?q=LLM")
        assert response.status_code == 200

        data = response.json()
        assert data["query"] == "LLM"
        assert data["count"] >= 1
        assert "LLM Research Article" in data["results"][0]["title"]

    def test_api_search_with_category(self, client, tmp_path, monkeypatch, sample_report):
        """API 카테고리 필터 검색"""
        monkeypatch.setattr(service, "DEFAULT_DATA_DIR", tmp_path)
        save_report(sample_report, tmp_path)

        response = client.get("/api/search?q=Article&category=LLM")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] >= 1
        # LLM 카테고리만 포함
        for result in data["results"]:
            assert "LLM" in result["category"]

    def test_api_search_requires_query(self, client):
        """API 검색어 필수"""
        response = client.get("/api/search")
        assert response.status_code == 422  # Validation error


class TestAPICategories:
    """REST API 카테고리 테스트"""

    def test_api_categories(self, client):
        """API 카테고리 목록"""
        response = client.get("/api/categories")
        assert response.status_code == 200

        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 12  # 12개 카테고리

        # 필수 카테고리 확인
        category_names = [c["name"] for c in data["categories"]]
        assert "LLM" in category_names
        assert "VISION" in category_names
        assert "OTHER" in category_names


class TestHealthCheck:
    """헬스 체크 테스트"""

    def test_health_check(self, client):
        """헬스 체크"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestService:
    """서비스 레이어 테스트"""

    def test_list_reports_empty(self, tmp_path):
        """빈 디렉토리"""
        reports = service.list_reports(tmp_path)
        assert reports == []

    def test_list_reports(self, tmp_path, sample_report):
        """리포트 목록"""
        save_report(sample_report, tmp_path)

        reports = service.list_reports(tmp_path)
        assert len(reports) == 1
        assert reports[0]["id"] == sample_report.id
        assert reports[0]["article_count"] == 2

    def test_get_report(self, tmp_path, sample_report):
        """리포트 조회"""
        save_report(sample_report, tmp_path)

        report = service.get_report(sample_report.id, tmp_path)
        assert report is not None
        assert report.id == sample_report.id

    def test_get_report_not_found(self, tmp_path):
        """존재하지 않는 리포트"""
        report = service.get_report("nonexistent", tmp_path)
        assert report is None

    def test_search_articles(self, tmp_path, sample_report):
        """기사 검색"""
        save_report(sample_report, tmp_path)

        results = service.search_articles("LLM", data_dir=tmp_path)
        assert len(results) >= 1
        assert results[0]["title"] == "LLM Research Article"

    def test_search_articles_with_category(self, tmp_path, sample_report):
        """카테고리 필터 검색"""
        save_report(sample_report, tmp_path)

        results = service.search_articles("Article", category="LLM", data_dir=tmp_path)
        assert len(results) == 1
        assert "LLM" in results[0]["category"]

    def test_get_categories(self):
        """카테고리 목록"""
        categories = service.get_categories()
        assert len(categories) == 12

    def test_get_report_stats(self, sample_report):
        """리포트 통계"""
        stats = service.get_report_stats(sample_report)

        assert stats["total"] == 2
        assert "LLM" in str(stats["by_category"])
        assert "arxiv" in stats["by_source"]
