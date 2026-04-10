"""LG AI Research Blog 수집기 (HTML 스크래핑)

EXAONE 시리즈 등 LG AI연구원의 주요 AI 연구 성과를 커버합니다.
공식 RSS 피드가 확인되지 않아 HTML 스크래핑으로 구현.
"""

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from .base import BaseCollector
from ..models import Article, Source


logger = logging.getLogger(__name__)


class LGAIResearchCollector(BaseCollector):
    """LG AI Research Blog"""

    source = Source.LG_AI_RESEARCH
    base_url = "https://www.lgresearch.ai"
    blog_url = "https://www.lgresearch.ai/blog"

    def fetch_articles(self) -> list[Article]:
        soup = self._fetch_html(self.blog_url)
        if not soup:
            return []

        articles: list[Article] = []
        seen_urls: set[str] = set()

        # LG AI Research 블로그 카드 찾기
        article_cards = (
            soup.select("a[href*='/blog/']") or
            soup.select("article a[href]") or
            soup.select("[class*='card'] a[href]")
        )

        for card in article_cards[:15]:
            try:
                href = card.get("href", "")
                if not href or "/blog/" not in href:
                    continue

                # 메인 블로그 페이지 자체 제외
                if href.rstrip("/") in ("/blog", "/blog/"):
                    continue

                article_url = urljoin(self.base_url, href)
                if article_url in seen_urls:
                    continue
                seen_urls.add(article_url)

                # 제목 추출
                title_elem = card.select_one("h1, h2, h3, h4, [class*='title'], [class*='tit']")
                title = (title_elem.get_text(strip=True) if title_elem
                         else card.get_text(strip=True))

                if not title or len(title) < 3:
                    continue

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
                logger.warning(f"Failed to parse LG AI Research card: {e}")
                continue

        return articles

    def parse_article_content(self, url: str) -> str:
        soup = self._fetch_html(url)
        if not soup:
            return ""

        content_selectors = [
            "article",
            ".post-content",
            "[class*='content']",
            "[class*='article']",
            "main",
        ]

        content_elem = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                break

        if not content_elem:
            return ""

        for elem in content_elem.select("script, style, nav, header, footer, .share, .related, .sidebar"):
            elem.decompose()

        paragraphs = content_elem.find_all("p")
        text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]

        full_text = "\n\n".join(text_parts)
        if len(full_text) > 10000:
            full_text = full_text[:10000] + "..."

        return full_text

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None

        date_str = date_str.strip()

        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        formats = [
            "%Y.%m.%d",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y년 %m월 %d일",
            "%B %d, %Y",
            "%b %d, %Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
