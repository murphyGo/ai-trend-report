"""OpenAI 블로그 수집기"""

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from .base import BaseCollector
from ..models import Article, Source


logger = logging.getLogger(__name__)


class OpenAIBlogCollector(BaseCollector):
    """OpenAI 블로그/뉴스 수집기"""

    source = Source.OPENAI_BLOG
    base_url = "https://openai.com"
    news_url = "https://openai.com/news/"

    def fetch_articles(self) -> list[Article]:
        """뉴스 페이지에서 기사 목록 수집"""
        soup = self._fetch_html(self.news_url)
        if not soup:
            return []

        articles = []

        # OpenAI 뉴스 페이지에서 기사 링크 찾기
        # 여러 선택자 시도
        article_cards = (
            soup.select("a[href*='/index/']") or
            soup.select("a[href*='/news/']") or
            soup.select("article a[href]") or
            soup.select("[class*='card'] a[href]")
        )

        for card in article_cards[:15]:  # 최근 15개
            try:
                href = card.get("href", "")
                if not href:
                    continue

                # 뉴스/연구 관련 링크만 필터링
                if not any(path in href for path in ["/index/", "/news/", "/research/"]):
                    continue

                # 제목 추출
                title_elem = card.select_one("h2, h3, h4, .title, [class*='title'], span")
                if not title_elem:
                    # 카드 자체의 텍스트 사용
                    title = card.get_text(strip=True)
                else:
                    title = title_elem.get_text(strip=True)

                if not title or len(title) < 5:
                    continue

                # URL 정규화
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
                logger.warning(f"Failed to parse OpenAI article card: {e}")
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
            "[class*='content']",
            "[class*='post']",
            ".prose",
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
        for elem in content_elem.select("script, style, nav, header, footer, .share, .related, .sidebar, [class*='nav']"):
            elem.decompose()

        # 텍스트 추출
        paragraphs = content_elem.find_all("p")
        text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]

        # 최대 길이 제한
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
