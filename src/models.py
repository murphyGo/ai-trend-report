"""데이터 모델 정의"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class Category(Enum):
    """기사 카테고리"""
    LLM = "LLM (대규모 언어 모델)"
    AGENT = "AI 에이전트 & 자동화"
    VISION = "컴퓨터 비전 & 멀티모달"
    VIDEO = "비디오 생성"
    ROBOTICS = "로보틱스 & 3D"
    SAFETY = "AI 안전성 & 윤리"
    RL = "강화학습"
    INFRA = "ML 인프라 & 최적화"
    MEDICAL = "의료 & 생명과학"
    FINANCE = "금융 & 트레이딩"
    INDUSTRY = "산업 동향 & 한국 소식"
    OTHER = "기타"

    @classmethod
    def from_string(cls, value: str) -> "Category":
        """문자열에서 카테고리 찾기"""
        value_lower = value.lower()
        for category in cls:
            if category.value.lower() in value_lower or category.name.lower() in value_lower:
                return category
        return cls.OTHER


class Source(Enum):
    """기사 출처"""
    ARXIV = "arxiv"
    GOOGLE_BLOG = "google"
    ANTHROPIC_BLOG = "anthropic"


@dataclass
class Article:
    """기사 데이터 모델"""
    title: str
    url: str
    source: Source
    content: str = ""
    published_at: Optional[datetime] = None
    summary: str = ""
    category: Category = Category.OTHER
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        if isinstance(self.source, str):
            self.source = Source(self.source)
        if isinstance(self.category, str):
            self.category = Category.from_string(self.category)


@dataclass
class Report:
    """리포트 데이터 모델"""
    articles: list[Article] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def articles_by_category(self) -> dict[Category, list[Article]]:
        """카테고리별로 기사 그룹화"""
        result: dict[Category, list[Article]] = {}
        for article in self.articles:
            if article.category not in result:
                result[article.category] = []
            result[article.category].append(article)
        return result