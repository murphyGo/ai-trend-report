"""RSS/Atom 피드 기반 수집기 공통 베이스

feedparser를 사용하여 표준 RSS 2.0 / Atom 피드를 파싱합니다.
각 피드 소스는 이 클래스를 상속받아 feed_url과 source만 지정하면 됩니다.
"""

import logging
import re
from datetime import datetime
from time import mktime
from typing import Optional

import feedparser

from .base import BaseCollector
from ..models import Article, Source


logger = logging.getLogger(__name__)


class RSSCollector(BaseCollector):
    """RSS/Atom 피드 수집기 공통 베이스

    서브클래스에서 다음을 지정:
        source: Source enum
        base_url: 사이트 홈 URL
        feed_url: RSS/Atom 피드 URL
        max_items: 수집할 최대 아이템 수 (기본 15)

    대부분의 RSS 피드는 entry 내에 요약/본문을 포함하므로,
    parse_article_content()는 기본적으로 빈 문자열을 반환합니다.
    (fetch_articles 단계에서 entry content를 Article.content로 이미 채움)
    전체 본문이 필요한 경우 서브클래스에서 override할 수 있습니다.
    """

    feed_url: str = ""
    max_items: int = 15
    # 일부 사이트(예: MarkTechPost/Cloudflare)는 일반 브라우저 UA를 차단함.
    # None이 아니면 fetch 시 이 UA로 일시 교체.
    feed_user_agent: Optional[str] = None

    def fetch_articles(self) -> list[Article]:
        """RSS/Atom 피드에서 기사 목록 수집"""
        if not self.feed_url:
            logger.error(f"[{self.source.value}] feed_url is not set")
            return []

        # 사이트별 UA 오버라이드 (필요 시)
        original_ua = None
        if self.feed_user_agent:
            original_ua = self.session.headers.get("User-Agent")
            self.session.headers["User-Agent"] = self.feed_user_agent

        try:
            xml_content = self._fetch_text(self.feed_url)
        finally:
            if original_ua is not None:
                self.session.headers["User-Agent"] = original_ua
        if not xml_content:
            logger.warning(f"[{self.source.value}] Failed to fetch feed from {self.feed_url}")
            return []

        try:
            feed = feedparser.parse(xml_content)
        except Exception as e:
            logger.error(f"[{self.source.value}] Failed to parse feed: {e}")
            return []

        if feed.bozo and not feed.entries:
            logger.warning(
                f"[{self.source.value}] Feed parse warning: {feed.bozo_exception}"
            )
            return []

        articles: list[Article] = []
        seen_urls: set[str] = set()

        for entry in feed.entries[: self.max_items]:
            try:
                title = self._clean_text(getattr(entry, "title", ""))
                url = getattr(entry, "link", "")

                if not title or not url:
                    continue
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                published_at = self._extract_date(entry)
                content = self._extract_content(entry)

                articles.append(Article(
                    title=title,
                    url=url,
                    source=self.source,
                    content=content,
                    published_at=published_at,
                ))
            except Exception as e:
                logger.warning(f"[{self.source.value}] Failed to parse entry: {e}")
                continue

        return articles

    def parse_article_content(self, url: str) -> str:
        """기본 구현: RSS entry에 이미 content가 있으므로 빈 문자열 반환

        서브클래스에서 전체 본문이 필요한 경우 override할 수 있습니다.
        BaseCollector.collect()는 Article.content가 비어있을 때만 이 메서드를 호출하므로,
        fetch_articles에서 content를 채우면 이 메서드는 호출되지 않습니다.
        """
        return ""

    @staticmethod
    def _clean_text(text: str) -> str:
        """HTML 태그 제거 및 공백 정리"""
        if not text:
            return ""
        # HTML 태그 제거
        text = re.sub(r"<[^>]+>", "", text)
        # 연속된 공백 정리
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _extract_date(entry) -> Optional[datetime]:
        """feedparser entry에서 발행 일시 추출"""
        # feedparser가 파싱해둔 struct_time 우선 사용
        for attr in ("published_parsed", "updated_parsed", "created_parsed"):
            parsed = getattr(entry, attr, None)
            if parsed:
                try:
                    return datetime.fromtimestamp(mktime(parsed))
                except (TypeError, ValueError, OverflowError):
                    continue

        # fallback: ISO 문자열
        for attr in ("published", "updated", "created"):
            raw = getattr(entry, attr, None)
            if raw:
                try:
                    return datetime.fromisoformat(raw.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    continue

        return None

    def _extract_content(self, entry) -> str:
        """feedparser entry에서 본문 텍스트 추출

        우선순위: content[0].value > summary > description
        """
        # Atom content
        content_list = getattr(entry, "content", None)
        if content_list:
            try:
                value = content_list[0].get("value", "") if isinstance(content_list[0], dict) else getattr(content_list[0], "value", "")
                if value:
                    return self._clean_text(value)[: self._max_content_length()]
            except (IndexError, AttributeError):
                pass

        # RSS summary / description
        for attr in ("summary", "description"):
            raw = getattr(entry, attr, None)
            if raw:
                return self._clean_text(raw)[: self._max_content_length()]

        return ""

    @staticmethod
    def _max_content_length() -> int:
        """토큰 절약용 본문 길이 제한"""
        return 10000
