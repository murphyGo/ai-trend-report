"""기사 URL 캐시 - 중복 수집 방지"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import Article


logger = logging.getLogger(__name__)

DEFAULT_CACHE_DIR = Path(__file__).parent.parent / "data"
DEFAULT_CACHE_FILE = ".article_cache.json"
DEFAULT_MAX_AGE_DAYS = 7


class ArticleCache:
    """URL 기반 기사 캐시

    이미 수집된 기사의 URL을 추적하여 중복 수집을 방지합니다.
    캐시는 일정 기간(기본 7일) 후 자동으로 만료됩니다.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        cache_file: str = DEFAULT_CACHE_FILE,
        max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    ):
        """캐시 초기화

        Args:
            cache_dir: 캐시 디렉토리 (기본: data/)
            cache_file: 캐시 파일명 (기본: .article_cache.json)
            max_age_days: 캐시 유효 기간 일수 (기본: 7일)
        """
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_file = self.cache_dir / cache_file
        self.max_age_days = max_age_days
        self._seen_urls: dict[str, str] = {}  # url -> timestamp
        self._load_cache()

    def _load_cache(self) -> None:
        """캐시 파일 로드"""
        if not self.cache_file.exists():
            logger.debug(f"Cache file not found: {self.cache_file}")
            return

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # URL별 타임스탬프 로드
            urls_with_time = data.get("urls", {})
            if isinstance(urls_with_time, list):
                # 하위 호환성: 이전 형식 (리스트)
                now_str = datetime.now().isoformat()
                self._seen_urls = {url: now_str for url in urls_with_time}
            else:
                self._seen_urls = urls_with_time

            # 만료된 항목 정리
            self._cleanup_expired()

            logger.info(f"Loaded {len(self._seen_urls)} URLs from cache")

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load cache: {e}")
            self._seen_urls = {}

    def _cleanup_expired(self) -> None:
        """만료된 캐시 항목 제거"""
        if self.max_age_days <= 0:
            return

        cutoff = datetime.now() - timedelta(days=self.max_age_days)
        cutoff_str = cutoff.isoformat()

        expired = [
            url for url, timestamp in self._seen_urls.items()
            if timestamp < cutoff_str
        ]

        for url in expired:
            del self._seen_urls[url]

        if expired:
            logger.debug(f"Removed {len(expired)} expired cache entries")

    def save(self) -> None:
        """캐시 파일 저장"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "last_updated": datetime.now().isoformat(),
            "max_age_days": self.max_age_days,
            "count": len(self._seen_urls),
            "urls": self._seen_urls,
        }

        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved {len(self._seen_urls)} URLs to cache")
        except IOError as e:
            logger.error(f"Failed to save cache: {e}")

    def is_seen(self, url: str) -> bool:
        """URL이 이미 캐시에 있는지 확인

        Args:
            url: 확인할 URL

        Returns:
            캐시에 있으면 True
        """
        return url in self._seen_urls

    def mark_seen(self, url: str) -> None:
        """URL을 캐시에 추가

        Args:
            url: 추가할 URL
        """
        self._seen_urls[url] = datetime.now().isoformat()

    def mark_seen_batch(self, urls: list[str]) -> None:
        """여러 URL을 일괄 캐시에 추가

        Args:
            urls: 추가할 URL 목록
        """
        now_str = datetime.now().isoformat()
        for url in urls:
            self._seen_urls[url] = now_str

    def filter_new(self, articles: list[Article]) -> list[Article]:
        """새 기사만 필터링 (캐시에 없는 것)

        Args:
            articles: 필터링할 기사 목록

        Returns:
            캐시에 없는 새 기사 목록
        """
        new_articles = [a for a in articles if not self.is_seen(a.url)]
        skipped = len(articles) - len(new_articles)

        if skipped > 0:
            logger.info(f"Skipped {skipped} cached articles, {len(new_articles)} new")

        return new_articles

    def add_articles(self, articles: list[Article]) -> None:
        """기사 목록의 URL을 캐시에 추가

        Args:
            articles: 추가할 기사 목록
        """
        self.mark_seen_batch([a.url for a in articles])

    def clear(self) -> None:
        """캐시 초기화"""
        self._seen_urls = {}
        logger.info("Cache cleared")

    def __len__(self) -> int:
        """캐시된 URL 수"""
        return len(self._seen_urls)

    def __contains__(self, url: str) -> bool:
        """URL 캐시 여부 확인 (in 연산자 지원)"""
        return self.is_seen(url)
