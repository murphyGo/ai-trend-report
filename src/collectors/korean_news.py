"""한국 AI 뉴스 수집기"""

import re
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

from .base import BaseCollector
from ..models import Article, Source


logger = logging.getLogger(__name__)


class KoreanNewsCollector(BaseCollector):
    """한국 AI 뉴스 수집기 (AI타임스)"""

    source = Source.KOREAN_NEWS
    base_url = "https://www.aitimes.kr"
    news_url = "https://www.aitimes.kr/news/articleList.html?sc_section_code=S1N1"

    def fetch_articles(self) -> list[Article]:
        """뉴스 페이지에서 기사 목록 수집"""
        soup = self._fetch_html(self.news_url)
        if not soup:
            return []

        articles = []

        # AI타임스 기사 목록 찾기
        article_cards = (
            soup.select(".list-block") or
            soup.select("article") or
            soup.select(".news-list li") or
            soup.select("ul.type2 li") or
            soup.select("[class*='article']")
        )

        for card in article_cards[:15]:  # 최근 15개
            try:
                # 링크 요소 찾기
                link_elem = card.select_one("a[href*='articleView']")
                if not link_elem:
                    link_elem = card.select_one("a[href]")

                if not link_elem:
                    continue

                href = link_elem.get("href", "")
                if not href or "articleView" not in href:
                    continue

                # 제목 추출
                title_elem = card.select_one("h2, h3, h4, .titles, .title, [class*='title']")
                if not title_elem:
                    title_elem = link_elem

                title = title_elem.get_text(strip=True)

                if not title or len(title) < 5:
                    continue

                # URL 정규화
                article_url = urljoin(self.base_url, href)

                # 날짜 추출 시도
                date_elem = card.select_one(".byline, .date, [class*='date'], time, em")
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
                logger.warning(f"Failed to parse Korean news article card: {e}")
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
            "#article-view-content-div",
            ".article-body",
            ".article-content",
            "article",
            "[itemprop='articleBody']",
        ]

        content_elem = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                break

        if not content_elem:
            return ""

        # 불필요한 요소 제거
        for elem in content_elem.select("script, style, nav, header, footer, .ad, .related, .reporter"):
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
        """날짜 문자열 파싱 (한국어 형식 포함)"""
        if not date_str:
            return None

        # 날짜 문자열 정리
        date_str = date_str.strip()

        # 기자명 등 제거하고 날짜 부분만 추출
        # 예: "홍길동 기자 | 2024.04.05" -> "2024.04.05"
        date_match = re.search(r'(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})', date_str)
        if date_match:
            date_str = date_match.group(1)

        # ISO 형식
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        # 한국어/일반 날짜 형식들
        formats = [
            "%Y.%m.%d",       # 2024.04.05
            "%Y-%m-%d",       # 2024-04-05
            "%Y/%m/%d",       # 2024/04/05
            "%Y년 %m월 %d일",  # 2024년 04월 05일
            "%m월 %d일",       # 04월 05일 (연도 없음)
            "%Y.%m.%d %H:%M", # 2024.04.05 09:30
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
