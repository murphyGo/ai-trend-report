"""기사 수집기 모듈"""

from .base import BaseCollector
from .rss_base import RSSCollector

# 기존 수집기
from .arxiv import ArxivCollector
from .google_blog import GoogleBlogCollector
from .anthropic_blog import AnthropicBlogCollector
from .openai_blog import OpenAIBlogCollector
from .huggingface_blog import HuggingFaceBlogCollector
from .korean_news import KoreanNewsCollector

# Tier 1: 공식 RSS 소스
from .rss_tier1 import (
    MicrosoftResearchCollector,
    NvidiaDeveloperBlogCollector,
    MarkTechPostCollector,
    BAIRBlogCollector,
    StanfordAILabCollector,
    TechCrunchAICollector,
    VentureBeatAICollector,
)

# Tier 2: HF Papers + HTML 스크래핑 소스
from .hf_papers import HFPapersCollector
from .meta_ai_blog import MetaAIBlogCollector
from .mit_tech_review import MITTechReviewCollector

# Tier 3: 한국 소스
from .korean_rss import NaverD2Collector, KakaoTechCollector
from .lg_ai_research import LGAIResearchCollector

__all__ = [
    "BaseCollector",
    "RSSCollector",
    # 기존
    "ArxivCollector",
    "GoogleBlogCollector",
    "AnthropicBlogCollector",
    "OpenAIBlogCollector",
    "HuggingFaceBlogCollector",
    "KoreanNewsCollector",
    # Tier 1
    "MicrosoftResearchCollector",
    "NvidiaDeveloperBlogCollector",
    "MarkTechPostCollector",
    "BAIRBlogCollector",
    "StanfordAILabCollector",
    "TechCrunchAICollector",
    "VentureBeatAICollector",
    # Tier 2
    "HFPapersCollector",
    "MetaAIBlogCollector",
    "MITTechReviewCollector",
    # Tier 3
    "NaverD2Collector",
    "KakaoTechCollector",
    "LGAIResearchCollector",
]
