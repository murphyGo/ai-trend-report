"""기사 수집기 기본 클래스"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

import requests
from bs4 import BeautifulSoup

from ..models import Article, Source


logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """기사 수집기 추상 클래스"""

    source: Source
    base_url: str

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })

    @abstractmethod
    def fetch_articles(self) -> list[Article]:
        """기사 목록 수집"""
        pass

    @abstractmethod
    def parse_article_content(self, url: str) -> str:
        """개별 기사 본문 파싱"""
        pass

    def _fetch_html(self, url: str) -> Optional[BeautifulSoup]:
        """URL에서 HTML 가져오기"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def _fetch_text(self, url: str) -> Optional[str]:
        """URL에서 텍스트 가져오기"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def collect(self) -> list[Article]:
        """기사 수집 및 본문 파싱"""
        articles = self.fetch_articles()
        logger.info(f"[{self.source.value}] Found {len(articles)} articles")

        for article in articles:
            if not article.content:
                try:
                    article.content = self.parse_article_content(article.url)
                except Exception as e:
                    logger.warning(f"Failed to parse content for {article.url}: {e}")

        return articles
