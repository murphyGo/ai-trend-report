"""MIT Technology Review 수집기 (RSS 기반)

전체 사이트 RSS 피드를 받아 AI 관련 카테고리/키워드 항목만 필터링.
WordPress 기반이라 RSS 2.0 표준을 따릅니다.
"""

import logging

import feedparser

from .rss_base import RSSCollector
from ..models import Article, Source


logger = logging.getLogger(__name__)


# AI 관련 카테고리 또는 제목 키워드 (대소문자 무시)
AI_KEYWORDS = (
    "ai",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "llm",
    "chatgpt",
    "openai",
    "anthropic",
    "claude",
    "gemini",
    "robot",
    "neural",
    "generative",
    "computing",
    "algorithm",
)


class MITTechReviewCollector(RSSCollector):
    """MIT Technology Review (AI 키워드 필터링)"""

    source = Source.MIT_TECH_REVIEW
    base_url = "https://www.technologyreview.com"
    feed_url = "https://www.technologyreview.com/feed/"
    max_items = 30  # 필터링 전에 더 많이 수집

    def fetch_articles(self) -> list[Article]:
        """전체 피드 수집 후 AI 관련 항목만 필터링"""
        if not self.feed_url:
            return []

        xml_content = self._fetch_text(self.feed_url)
        if not xml_content:
            logger.warning(f"[{self.source.value}] Failed to fetch feed")
            return []

        try:
            feed = feedparser.parse(xml_content)
        except Exception as e:
            logger.error(f"[{self.source.value}] Failed to parse feed: {e}")
            return []

        articles: list[Article] = []
        seen_urls: set[str] = set()

        for entry in feed.entries[: self.max_items]:
            try:
                title = self._clean_text(getattr(entry, "title", ""))
                url = getattr(entry, "link", "")

                if not title or not url or url in seen_urls:
                    continue

                # AI 관련성 체크: 제목 또는 카테고리에 키워드 포함
                if not self._is_ai_related(entry, title):
                    continue

                seen_urls.add(url)
                articles.append(Article(
                    title=title,
                    url=url,
                    source=self.source,
                    content=self._extract_content(entry),
                    published_at=self._extract_date(entry),
                ))

                if len(articles) >= 15:
                    break
            except Exception as e:
                logger.warning(f"[{self.source.value}] Failed to parse entry: {e}")
                continue

        return articles

    @staticmethod
    def _is_ai_related(entry, title: str) -> bool:
        """카테고리 태그 또는 제목에 AI 관련 키워드가 있는지 확인"""
        haystack = title.lower()

        # 카테고리 태그도 검사
        tags = getattr(entry, "tags", None) or []
        for tag in tags:
            term = tag.get("term", "") if isinstance(tag, dict) else getattr(tag, "term", "")
            haystack += " " + term.lower()

        # 단어 경계 매칭 (예: "ai"가 "fair" 안에서 매칭되지 않도록)
        return any(
            f" {kw} " in f" {haystack} " or haystack.startswith(f"{kw} ") or haystack.endswith(f" {kw}") or kw in haystack.split()
            for kw in AI_KEYWORDS
        )
