"""Anthropic (Claude) 블로그 수집기"""

import re
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from .base import BaseCollector
from ..models import Article, Source


logger = logging.getLogger(__name__)


class AnthropicBlogCollector(BaseCollector):
    """Anthropic 블로그 수집기"""

    source = Source.ANTHROPIC_BLOG
    base_url = "https://www.anthropic.com"
    blog_url = "https://www.anthropic.com/news"

    def fetch_articles(self) -> list[Article]:
        """블로그 메인 페이지에서 기사 목록 수집"""
        soup = self._fetch_html(self.blog_url)
        if not soup:
            return []

        articles = []

        # Anthropic 블로그 기사 카드 찾기
        article_cards = soup.select("article") or soup.select("[class*='post']") or soup.select("[class*='article']")

        # 대체: 링크 기반 탐색
        if not article_cards:
            article_cards = soup.select("a[href*='/news/']")

        for card in article_cards[:15]:  # 최근 15개
            try:
                # 링크 요소 찾기
                if card.name == "a":
                    link_elem = card
                else:
                    link_elem = card.select_one("a[href]")

                if not link_elem:
                    continue

                href = link_elem.get("href", "")
                if not href or not ("/news/" in href or "/research/" in href):
                    continue

                # 제목 추출
                title_elem = card.select_one("h2, h3, h4, .title, [class*='title']")
                if not title_elem:
                    title_elem = link_elem

                title = title_elem.get_text(strip=True)

                if not title:
                    continue

                # URL 정규화
                article_url = urljoin(self.base_url, href)

                # 날짜 추출
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
                logger.warning(f"Failed to parse Anthropic article card: {e}")
                continue

        # 중복 제거
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)

        return unique_articles

    def parse_article_content(self, url: str) -> str:
        """기사 상세 페이지에서 본문 추출"""
        soup = self._fetch_html(url)
        if not soup:
            return ""

        # 본문 컨테이너 찾기
        content_selectors = [
            "article",
            ".post-content",
            ".article-content",
            "[class*='content']",
            "main",
        ]

        content_elem = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                break

        if not content_elem:
            return ""

        # 불필요한 요소 제거
        for elem in content_elem.select("script, style, nav, header, footer, .share, .related, .sidebar"):
            elem.decompose()

        # 텍스트 추출
        paragraphs = content_elem.find_all("p")
        text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]

        # 최대 길이 제한 (토큰 절약)
        full_text = "\n\n".join(text_parts)
        if len(full_text) > 10000:
            full_text = full_text[:10000] + "..."

        return full_text

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
            "%b %Y",      # Jan 2024
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
