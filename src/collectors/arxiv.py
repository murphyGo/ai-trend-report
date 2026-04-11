"""arXiv 논문 수집기"""

import re
import logging
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Optional
import xml.etree.ElementTree as ET

from .base import BaseCollector
from ..models import Article, Source


logger = logging.getLogger(__name__)


def _parse_arxiv_date(value: Optional[str]) -> Optional[datetime]:
    """arXiv RSS의 pubDate / dc:date 문자열을 datetime으로 변환.

    지원 형식:
    - RFC 822: 'Thu, 10 Apr 2026 00:00:00 +0000' (pubDate)
    - ISO 8601: '2026-04-10T00:00:00Z' 또는 '2026-04-10' (dc:date)
    """
    if not value:
        return None
    value = value.strip()

    # 1. RFC 822 (pubDate) — email.utils
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        pass

    # 2. ISO 8601 (dc:date)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass

    return None


class ArxivCollector(BaseCollector):
    """arXiv 논문 수집기"""

    source = Source.ARXIV
    base_url = "https://arxiv.org"
    rss_url = "https://rss.arxiv.org/rss"

    def __init__(
        self,
        categories: Optional[list[str]] = None,
        max_per_category: int = 20,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.categories = categories or ["cs.AI", "cs.LG", "cs.CL"]
        self.max_per_category = max_per_category

    def fetch_articles(self) -> list[Article]:
        """RSS 피드에서 최신 논문 수집"""
        articles = []

        for category in self.categories:
            rss_feed = self._fetch_rss(category)
            if rss_feed:
                articles.extend(rss_feed)

        # 중복 제거 (URL 기준)
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)

        return unique_articles

    def _fetch_rss(self, category: str) -> list[Article]:
        """특정 카테고리의 RSS 피드 파싱 (max_per_category 상한 적용)"""
        url = f"{self.rss_url}/{category}"
        xml_content = self._fetch_text(url)

        if not xml_content:
            return []

        articles = []
        try:
            root = ET.fromstring(xml_content)

            # RSS 네임스페이스 처리
            ns = {
                "dc": "http://purl.org/dc/elements/1.1/",
                "arxiv": "http://arxiv.org/schemas/atom",
            }

            # 카테고리당 상한 적용 (arXiv RSS는 최신순이라 앞에서부터 자름)
            for item in root.findall(".//item")[: self.max_per_category]:
                title_elem = item.find("title")
                link_elem = item.find("link")
                description_elem = item.find("description")

                if title_elem is None or link_elem is None:
                    continue

                title = title_elem.text or ""
                # arXiv 제목에서 카테고리 태그 제거
                title = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()

                link = link_elem.text or ""
                # abs URL을 표준화
                if "/abs/" in link:
                    arxiv_id = link.split("/abs/")[-1]
                    link = f"https://arxiv.org/abs/{arxiv_id}"

                description = ""
                if description_elem is not None and description_elem.text:
                    # HTML 태그 제거
                    description = re.sub(r"<[^>]+>", "", description_elem.text)
                    description = description.strip()

                # 발행 일시 추출 — Phase 8.1 (DEBT-003 해소)
                # 1) pubDate (RFC 822) 우선, 2) dc:date (ISO 8601) fallback
                pub_elem = item.find("pubDate")
                published_at = _parse_arxiv_date(
                    pub_elem.text if pub_elem is not None else None
                )
                if published_at is None:
                    dc_elem = item.find("dc:date", ns)
                    if dc_elem is not None:
                        published_at = _parse_arxiv_date(dc_elem.text)

                articles.append(Article(
                    title=title,
                    url=link,
                    source=self.source,
                    content=description,  # RSS의 description을 초기 content로 사용
                    published_at=published_at,
                ))

        except ET.ParseError as e:
            logger.error(f"Failed to parse RSS for {category}: {e}")

        return articles

    def parse_article_content(self, url: str) -> str:
        """논문 상세 페이지에서 abstract 추출"""
        soup = self._fetch_html(url)
        if not soup:
            return ""

        # Abstract 추출
        abstract_block = soup.find("blockquote", class_="abstract")
        if abstract_block:
            # "Abstract:" 레이블 제거
            abstract_text = abstract_block.get_text()
            abstract_text = re.sub(r"^Abstract:\s*", "", abstract_text, flags=re.IGNORECASE)
            return abstract_text.strip()

        return ""
