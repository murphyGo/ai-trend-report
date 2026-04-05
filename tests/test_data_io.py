"""데이터 I/O 테스트"""

import pytest
import json
from datetime import datetime
from pathlib import Path

from src.data_io import (
    save_articles,
    load_articles,
    save_report,
    load_report,
    get_today_filename,
    get_latest_file,
)
from src.models import Article, Report, Source, Category


class TestGetTodayFilename:
    """get_today_filename 테스트"""

    def test_default_prefix(self):
        """기본 prefix 'articles'"""
        filename = get_today_filename()
        today = datetime.now().strftime("%Y-%m-%d")
        assert filename == f"articles_{today}.json"

    def test_custom_prefix(self):
        """커스텀 prefix"""
        filename = get_today_filename("report")
        today = datetime.now().strftime("%Y-%m-%d")
        assert filename == f"report_{today}.json"


class TestSaveLoadArticles:
    """기사 저장/로드 테스트"""

    def test_save_articles(self, tmp_path, sample_article):
        """기사 저장"""
        articles = [sample_article]
        filepath = save_articles(articles, tmp_path, "test_articles.json")

        assert filepath.exists()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["count"] == 1
        assert len(data["articles"]) == 1
        assert "collected_at" in data

    def test_save_articles_creates_directory(self, tmp_path, sample_article):
        """디렉토리 자동 생성"""
        output_dir = tmp_path / "subdir" / "nested"
        filepath = save_articles([sample_article], output_dir, "test.json")

        assert output_dir.exists()
        assert filepath.exists()

    def test_save_articles_empty_list(self, tmp_path):
        """빈 기사 목록 저장"""
        filepath = save_articles([], tmp_path, "empty.json")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["count"] == 0
        assert data["articles"] == []

    def test_load_articles(self, tmp_path, sample_article):
        """기사 로드"""
        filepath = save_articles([sample_article], tmp_path, "test.json")
        loaded = load_articles(filepath)

        assert len(loaded) == 1
        assert loaded[0].title == sample_article.title
        assert loaded[0].source == sample_article.source

    def test_save_load_roundtrip(self, tmp_path, sample_article):
        """저장/로드 왕복"""
        articles = [sample_article]
        filepath = save_articles(articles, tmp_path, "roundtrip.json")
        loaded = load_articles(filepath)

        assert len(loaded) == len(articles)
        assert loaded[0].id == sample_article.id
        assert loaded[0].title == sample_article.title
        assert loaded[0].category == sample_article.category

    def test_save_articles_unicode(self, tmp_path):
        """유니코드 내용 저장"""
        article = Article(
            title="한글 제목 테스트",
            url="https://example.com",
            source=Source.ARXIV,
            content="한글 내용: 가나다라마바사",
            summary="한글 요약",
        )
        filepath = save_articles([article], tmp_path, "unicode.json")
        loaded = load_articles(filepath)

        assert loaded[0].title == "한글 제목 테스트"
        assert "가나다라마바사" in loaded[0].content


class TestSaveLoadReport:
    """리포트 저장/로드 테스트"""

    def test_save_report(self, tmp_path, sample_report):
        """리포트 저장"""
        filepath = save_report(sample_report, tmp_path, "test_report.json")

        assert filepath.exists()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["id"] == sample_report.id
        assert len(data["articles"]) == 2

    def test_load_report(self, tmp_path, sample_report):
        """리포트 로드"""
        filepath = save_report(sample_report, tmp_path, "test_report.json")
        loaded = load_report(filepath)

        assert loaded.id == sample_report.id
        assert len(loaded.articles) == len(sample_report.articles)

    def test_save_load_report_roundtrip(self, tmp_path, sample_report):
        """리포트 저장/로드 왕복"""
        filepath = save_report(sample_report, tmp_path, "roundtrip.json")
        loaded = load_report(filepath)

        assert loaded.id == sample_report.id
        assert loaded.created_at == sample_report.created_at
        assert len(loaded.articles) == len(sample_report.articles)
        assert loaded.articles[0].title == sample_report.articles[0].title

    def test_save_report_empty(self, tmp_path):
        """빈 리포트 저장"""
        report = Report(articles=[])
        filepath = save_report(report, tmp_path, "empty_report.json")
        loaded = load_report(filepath)

        assert len(loaded.articles) == 0


class TestGetLatestFile:
    """get_latest_file 테스트"""

    def test_get_latest_file_exists(self, tmp_path):
        """파일이 있을 때"""
        (tmp_path / "articles_2024-01-01.json").write_text("{}")
        (tmp_path / "articles_2024-01-02.json").write_text("{}")
        (tmp_path / "articles_2024-01-03.json").write_text("{}")

        latest = get_latest_file(tmp_path, "articles")
        assert latest is not None
        assert "2024-01-03" in latest.name

    def test_get_latest_file_empty_dir(self, tmp_path):
        """디렉토리가 비어있을 때"""
        latest = get_latest_file(tmp_path, "articles")
        assert latest is None

    def test_get_latest_file_no_match(self, tmp_path):
        """매칭되는 파일 없을 때"""
        (tmp_path / "other_file.json").write_text("{}")

        latest = get_latest_file(tmp_path, "articles")
        assert latest is None

    def test_get_latest_file_nonexistent_dir(self, tmp_path):
        """디렉토리가 없을 때"""
        nonexistent = tmp_path / "nonexistent"
        latest = get_latest_file(nonexistent, "articles")
        assert latest is None

    def test_get_latest_file_report_prefix(self, tmp_path):
        """report prefix로 검색"""
        (tmp_path / "report_2024-01-01.json").write_text("{}")
        (tmp_path / "articles_2024-01-01.json").write_text("{}")

        latest = get_latest_file(tmp_path, "report")
        assert latest is not None
        assert "report_" in latest.name
