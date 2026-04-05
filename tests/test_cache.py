"""기사 캐시 테스트"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from src.cache import ArticleCache
from src.models import Article, Source


class TestArticleCache:
    """ArticleCache 테스트"""

    def test_cache_init_empty(self, tmp_path):
        """빈 캐시 초기화"""
        cache = ArticleCache(cache_dir=tmp_path)
        assert len(cache) == 0

    def test_cache_mark_seen(self, tmp_path):
        """URL 캐시 추가"""
        cache = ArticleCache(cache_dir=tmp_path)

        url = "https://example.com/article1"
        assert not cache.is_seen(url)

        cache.mark_seen(url)
        assert cache.is_seen(url)
        assert url in cache

    def test_cache_mark_seen_batch(self, tmp_path):
        """여러 URL 일괄 추가"""
        cache = ArticleCache(cache_dir=tmp_path)

        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3",
        ]

        cache.mark_seen_batch(urls)

        for url in urls:
            assert cache.is_seen(url)

        assert len(cache) == 3

    def test_cache_save_load(self, tmp_path):
        """캐시 저장 및 로드"""
        # 캐시 생성 및 데이터 추가
        cache1 = ArticleCache(cache_dir=tmp_path)
        cache1.mark_seen("https://example.com/1")
        cache1.mark_seen("https://example.com/2")
        cache1.save()

        # 새 캐시 인스턴스로 로드
        cache2 = ArticleCache(cache_dir=tmp_path)
        assert len(cache2) == 2
        assert cache2.is_seen("https://example.com/1")
        assert cache2.is_seen("https://example.com/2")

    def test_cache_filter_new(self, tmp_path, sample_article):
        """새 기사 필터링"""
        cache = ArticleCache(cache_dir=tmp_path)

        # 기존 기사 캐시에 추가
        cache.mark_seen(sample_article.url)

        # 새 기사 생성
        new_article = Article(
            title="New Article",
            url="https://example.com/new",
            source=Source.ARXIV,
        )

        articles = [sample_article, new_article]
        filtered = cache.filter_new(articles)

        assert len(filtered) == 1
        assert filtered[0].url == "https://example.com/new"

    def test_cache_add_articles(self, tmp_path):
        """기사 목록 URL 캐시 추가"""
        cache = ArticleCache(cache_dir=tmp_path)

        articles = [
            Article(title="A1", url="https://a.com/1", source=Source.ARXIV),
            Article(title="A2", url="https://a.com/2", source=Source.ARXIV),
        ]

        cache.add_articles(articles)

        assert cache.is_seen("https://a.com/1")
        assert cache.is_seen("https://a.com/2")
        assert len(cache) == 2

    def test_cache_clear(self, tmp_path):
        """캐시 초기화"""
        cache = ArticleCache(cache_dir=tmp_path)
        cache.mark_seen("https://example.com/1")
        cache.mark_seen("https://example.com/2")

        assert len(cache) == 2

        cache.clear()

        assert len(cache) == 0
        assert not cache.is_seen("https://example.com/1")


class TestCacheExpiration:
    """캐시 만료 테스트"""

    def test_cache_expiration(self, tmp_path):
        """만료된 캐시 항목 제거"""
        cache_file = tmp_path / ".article_cache.json"

        # 오래된 데이터로 캐시 파일 생성
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        new_date = datetime.now().isoformat()

        data = {
            "last_updated": new_date,
            "max_age_days": 7,
            "count": 2,
            "urls": {
                "https://old.com/expired": old_date,  # 10일 전 - 만료
                "https://new.com/fresh": new_date,     # 방금 - 유효
            }
        }

        with open(cache_file, "w") as f:
            json.dump(data, f)

        # 캐시 로드 (만료 항목 자동 정리)
        cache = ArticleCache(cache_dir=tmp_path, max_age_days=7)

        assert len(cache) == 1
        assert not cache.is_seen("https://old.com/expired")
        assert cache.is_seen("https://new.com/fresh")

    def test_cache_max_age_zero_no_expiration(self, tmp_path):
        """max_age_days=0이면 만료 안 함"""
        cache_file = tmp_path / ".article_cache.json"

        old_date = (datetime.now() - timedelta(days=100)).isoformat()

        data = {
            "last_updated": datetime.now().isoformat(),
            "urls": {
                "https://very-old.com": old_date,
            }
        }

        with open(cache_file, "w") as f:
            json.dump(data, f)

        cache = ArticleCache(cache_dir=tmp_path, max_age_days=0)

        # max_age_days=0이면 만료 처리 안 함
        assert cache.is_seen("https://very-old.com")


class TestCacheFileFormats:
    """캐시 파일 형식 테스트"""

    def test_legacy_list_format(self, tmp_path):
        """이전 형식 (리스트) 호환성"""
        cache_file = tmp_path / ".article_cache.json"

        # 이전 형식: urls가 리스트
        data = {
            "last_updated": datetime.now().isoformat(),
            "urls": [
                "https://example.com/1",
                "https://example.com/2",
            ]
        }

        with open(cache_file, "w") as f:
            json.dump(data, f)

        cache = ArticleCache(cache_dir=tmp_path)

        assert len(cache) == 2
        assert cache.is_seen("https://example.com/1")
        assert cache.is_seen("https://example.com/2")

    def test_corrupted_cache_file(self, tmp_path):
        """손상된 캐시 파일 처리"""
        cache_file = tmp_path / ".article_cache.json"

        with open(cache_file, "w") as f:
            f.write("invalid json {{{")

        # 손상된 파일은 무시하고 빈 캐시로 시작
        cache = ArticleCache(cache_dir=tmp_path)
        assert len(cache) == 0

    def test_missing_cache_file(self, tmp_path):
        """캐시 파일 없음"""
        cache = ArticleCache(cache_dir=tmp_path)
        assert len(cache) == 0


class TestCacheIntegration:
    """캐시 통합 테스트"""

    def test_full_workflow(self, tmp_path):
        """전체 워크플로우"""
        # 1. 첫 실행: 모든 기사 수집
        cache = ArticleCache(cache_dir=tmp_path)

        articles = [
            Article(title="Article 1", url="https://a.com/1", source=Source.ARXIV),
            Article(title="Article 2", url="https://a.com/2", source=Source.ARXIV),
        ]

        # 새 기사 필터링 (모두 새 기사)
        new_articles = cache.filter_new(articles)
        assert len(new_articles) == 2

        # 캐시에 추가
        cache.add_articles(new_articles)
        cache.save()

        # 2. 두 번째 실행: 기존 기사 스킵
        cache2 = ArticleCache(cache_dir=tmp_path)

        # 같은 기사 + 새 기사 1개
        articles2 = [
            Article(title="Article 1", url="https://a.com/1", source=Source.ARXIV),
            Article(title="Article 2", url="https://a.com/2", source=Source.ARXIV),
            Article(title="Article 3", url="https://a.com/3", source=Source.ARXIV),
        ]

        new_articles2 = cache2.filter_new(articles2)
        assert len(new_articles2) == 1
        assert new_articles2[0].url == "https://a.com/3"
