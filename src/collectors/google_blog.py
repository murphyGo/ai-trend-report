"""Google AI 블로그 수집기"""

import re
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from .base import BaseCollector
from ..models import Article, Source


logger = logging.getLogger(__name__)


class GoogleBlogCollector(BaseCollector):
    """Google AI 관련 블로그 수집기"""

    source = Source.GOOGLE_BLOG
    base_url = "https://blog.google"

    # 수집할 블로그 카테고리 URL
    category_urls = [
        "/innovation-and-ai/models-and-research/google-deepmind/",
        "/innovation-and-ai/models-and-research/google-research/",
        "/innovation-and-ai/models-and-research/google-labs/",
        "/innovation-and-ai/models-and-research/gemini-models/",
    ]

    def fetch_articles(self) -> list[Article]:
        """블로그 카테고리 페이지에서 기사 목록 수집"""
        articles = []

        for category_path in self.category_urls:
            url = urljoin(self.base_url, category_path)
            category_articles = self._fetch_category_articles(url)
            articles.extend(category_articles)

        # 중복 제거 (URL 기준)
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)

        return unique_articles

    def _fetch_category_articles(self, url: str) -> list[Article]:
        """카테고리 페이지에서 기사 추출"""
        soup = self._fetch_html(url)
        if not soup:
            return []

        articles = []

        # Google 블로그 카드 요소 찾기
        # 여러 가능한 선택자 시도
        article_cards = soup.select("article") or soup.select(".article-card") or soup.select("[data-article]")

        for card in article_cards[:10]:  # 최근 10개만
            try:
                # 제목과 링크 추출
                title_elem = card.select_one("h2, h3, .title, [class*='title']")
                link_elem = card.select_one("a[href]")

                if not title_elem or not link_elem:
                    # 대체 방법: 카드 자체가 링크인 경우
                    link_elem = card if card.name == "a" else card.find_parent("a")
                    if not link_elem:
                        continue

                title = title_elem.get_text(strip=True) if title_elem else ""
                href = link_elem.get("href", "")

                if not title or not href:
                    continue

                # 상대 URL을 절대 URL로 변환
                article_url = urljoin(self.base_url, href)

                # 날짜 추출 시도
                date_elem = card.select_one("time, .date, [class*='date']")
                published_at = None
                if date_elem:
                    date_str = date_elem.get("datetime") or date_elem.get_text(strip=True)
                    published_at = self._parse_date(date_str)

                articles.append(Article(
                    title=title,
                    url=article_url,
                    source=self.source,
                    published_at=published_at,
                ))

            except Exception as e:
                logger.warning(f"Failed to parse article card: {e}")
                continue

        return articles

    def parse_article_content(self, url: str) -> str:
        """기사 상세 페이지에서 본문 추출"""
        soup = self._fetch_html(url)
        if not soup:
            return ""

        # 본문 컨테이너 찾기
        content_selectors = [
            "article .article-content",
            "article .content",
            ".post-content",
            ".article-body",
            "article",
        ]

        content_elem = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                break

        if not content_elem:
            return ""

        # 불필요한 요소 제거
        for elem in content_elem.select("script, style, nav, header, footer, .share, .related"):
            elem.decompose()

        # 텍스트 추출
        paragraphs = content_elem.find_all("p")
        text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]

        return "\n\n".join(text_parts)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열 파싱"""
        if not date_str:
            return None

        # ISO 형식
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        # 일반적인 날짜 형식들
        formats = [
            "%B %d, %Y",  # January 15, 2024
            "%b %d, %Y",  # Jan 15, 2024
            "%Y-%m-%d",   # 2024-01-15
            "%d %B %Y",   # 15 January 2024
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
