"""Tier 3 한국 기술 블로그 RSS/Atom 수집기

- Naver D2: Atom 피드 (https://d2.naver.com/d2.atom)
- Kakao Tech: RSS 피드 (https://tech.kakao.com/feed/)

Naver D2와 Kakao Tech는 AI 전용은 아니지만 주요 AI 포스트를 포함하며
한국 산업 동향(INDUSTRY) 카테고리 강화용으로 사용.
"""

from .rss_base import RSSCollector
from ..models import Source


class NaverD2Collector(RSSCollector):
    """네이버 D2 기술 블로그 (Atom)"""
    source = Source.NAVER_D2
    base_url = "https://d2.naver.com/"
    feed_url = "https://d2.naver.com/d2.atom"


class KakaoTechCollector(RSSCollector):
    """카카오 기술 블로그"""
    source = Source.KAKAO_TECH
    base_url = "https://tech.kakao.com/"
    feed_url = "https://tech.kakao.com/feed/"
