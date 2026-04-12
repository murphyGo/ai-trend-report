"""Hugging Face Daily Papers 수집기

HuggingFace는 공식 RSS를 제공하지 않으므로 Takara.ai의 비공식 RSS 피드를 사용합니다.
https://papers.takara.ai/api/feed

트렌딩 논문 큐레이션이라 arXiv raw 피드보다 품질이 높음.
fallback으로 huggingface.co/papers HTML 스크래핑을 시도합니다.

Phase 9.4 (DEBT-004): Takara 피드가 반환���는 `tldr.takara.ai/p/{id}` URL을
`huggingface.co/papers/{id}`로 변환해 사용자가 HF 페이지로 직접 이동하도록 함.
"""

import logging
import re
from urllib.parse import urljoin

from .rss_base import RSSCollector
from ..models import Article, Source


logger = logging.getLogger(__name__)

# Takara TLDR URL 패턴: https://tldr.takara.ai/p/{arxiv_id}
_TAKARA_PATTERN = re.compile(r"^https?://tldr\.takara\.ai/p/(.+)$")


def _normalize_hf_url(url: str) -> str:
    """Takara TLDR URL을 HuggingFace Papers URL로 변환 (DEBT-004).

    `https://tldr.takara.ai/p/2604.08263` → `https://huggingface.co/papers/2604.08263`
    이미 HF/arxiv URL이면 그대로 반환.
    """
    match = _TAKARA_PATTERN.match(url)
    if match:
        paper_id = match.group(1)
        return f"https://huggingface.co/papers/{paper_id}"
    return url


class HFPapersCollector(RSSCollector):
    """Hugging Face Daily Papers (비공식 RSS)"""

    source = Source.HF_PAPERS
    base_url = "https://huggingface.co"
    feed_url = "https://papers.takara.ai/api/feed"
    max_items = 15

    def fetch_articles(self) -> list[Article]:
        """RSS 우선 시도, 실패 시 HTML fallback. Takara URL은 HF URL로 변환."""
        articles = super().fetch_articles()
        if articles:
            for article in articles:
                article.url = _normalize_hf_url(article.url)
            return articles

        logger.info(
            f"[{self.source.value}] RSS feed empty, falling back to HTML scraping"
        )
        return self._fetch_html_fallback()

    def _fetch_html_fallback(self) -> list[Article]:
        """huggingface.co/papers 페이지에서 직접 파싱"""
        soup = self._fetch_html(f"{self.base_url}/papers")
        if not soup:
            return []

        articles: list[Article] = []
        seen_urls: set[str] = set()

        # HF papers 페이지는 /papers/{paper_id} 링크로 구성
        paper_links = soup.select("a[href^='/papers/']")
        for link in paper_links[: self.max_items]:
            try:
                href = link.get("href", "")
                if not href or href == "/papers" or href == "/papers/":
                    continue

                paper_url = urljoin(self.base_url, href)
                if paper_url in seen_urls:
                    continue
                seen_urls.add(paper_url)

                # 제목 추출: 링크 자체 또는 내부 h3
                title_elem = link.select_one("h3, h2, h4") or link
                title = title_elem.get_text(strip=True)

                if not title or len(title) < 5:
                    continue

                articles.append(Article(
                    title=title,
                    url=paper_url,
                    source=self.source,
                ))
            except Exception as e:
                logger.warning(f"Failed to parse HF papers link: {e}")
                continue

        return articles
