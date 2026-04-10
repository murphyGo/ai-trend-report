"""Tier 1 RSS 수집기 - 공식 RSS 피드가 제공되는 소스들

각 소스는 RSSCollector를 상속받아 feed_url과 source만 지정합니다.
"""

from .rss_base import RSSCollector
from ..models import Source


class MicrosoftResearchCollector(RSSCollector):
    """Microsoft Research Blog

    Phi 시리즈, Copilot, 에이전트 리서치 등 MS의 AI 연구 결과를 커버.
    """
    source = Source.MICROSOFT_RESEARCH
    base_url = "https://www.microsoft.com/en-us/research/"
    feed_url = "https://www.microsoft.com/en-us/research/blog/feed/"


class NvidiaDeveloperBlogCollector(RSSCollector):
    """NVIDIA Developer Blog

    GPU/CUDA/ML 인프라 중심. ML_INFRA 카테고리 보강용.
    """
    source = Source.NVIDIA_BLOG
    base_url = "https://developer.nvidia.com/"
    feed_url = "https://developer.nvidia.com/blog/feed"


class MarkTechPostCollector(RSSCollector):
    """MarkTechPost

    신규 논문·모델·툴을 빠르게 정리하는 큐레이션 미디어.
    Cloudflare가 일반 브라우저 UA를 차단하므로 Feedly의 fetcher UA로 우회.
    """
    source = Source.MARKTECHPOST
    base_url = "https://www.marktechpost.com/"
    feed_url = "https://www.marktechpost.com/feed/"
    feed_user_agent = (
        "feedly/1.0 (+http://www.feedly.com/fetcher.html; like FeedFetcher-Google)"
    )


class BAIRBlogCollector(RSSCollector):
    """Berkeley AI Research (BAIR) Blog

    학계 리서치 관점의 장문 해설.
    """
    source = Source.BAIR_BLOG
    base_url = "https://bair.berkeley.edu/"
    feed_url = "https://bair.berkeley.edu/blog/feed.xml"


class StanfordAILabCollector(RSSCollector):
    """Stanford AI Lab (SAIL) Blog"""
    source = Source.STANFORD_AI
    base_url = "https://ai.stanford.edu/"
    feed_url = "https://ai.stanford.edu/blog/feed.xml"


class TechCrunchAICollector(RSSCollector):
    """TechCrunch - Artificial Intelligence category

    산업 동향, 투자, 제품 뉴스. INDUSTRY 카테고리 보강.
    """
    source = Source.TECHCRUNCH_AI
    base_url = "https://techcrunch.com/"
    feed_url = "https://techcrunch.com/category/artificial-intelligence/feed/"


class VentureBeatAICollector(RSSCollector):
    """VentureBeat - AI category

    엔터프라이즈 AI 동향.
    """
    source = Source.VENTUREBEAT_AI
    base_url = "https://venturebeat.com/"
    feed_url = "https://venturebeat.com/category/ai/feed/"
