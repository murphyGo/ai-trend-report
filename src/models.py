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
    OPENAI_BLOG = "openai"
    HUGGINGFACE_BLOG = "huggingface"
    KOREAN_NEWS = "korean"
    # Tier 1: 공식 RSS 소스
    MICROSOFT_RESEARCH = "microsoft_research"
    NVIDIA_BLOG = "nvidia"
    MARKTECHPOST = "marktechpost"
    BAIR_BLOG = "bair"
    STANFORD_AI = "stanford_ai"
    TECHCRUNCH_AI = "techcrunch"
    VENTUREBEAT_AI = "venturebeat"
    # Tier 2: 비공식 RSS / HTML 스크래핑
    HF_PAPERS = "hf_papers"
    META_AI_BLOG = "meta_ai"
    MIT_TECH_REVIEW = "mit_tech_review"
    # Tier 3: 한국 소스
    NAVER_D2 = "naver_d2"
    KAKAO_TECH = "kakao_tech"
    LG_AI_RESEARCH = "lg_ai_research"


class Audience(Enum):
    """독자 레벨 (FR-036)

    기사가 어떤 독자층에게 유용한지 표현. Multi-tag 허용 — 하나의 기사가
    여러 레벨에 속할 수 있음 (예: "OpenAI GPT-5 발표"는 일반인/개발자/ML 전문가
    모두에게 관련됨).

    UI의 필터 칩은 이 enum의 `name`을 사용하고 (`GENERAL`, `DEVELOPER`,
    `ML_EXPERT`), 사용자 노출용 라벨은 `value` 또는 별도 label 맵 사용.
    """
    GENERAL = "일반인"
    DEVELOPER = "개발자"
    ML_EXPERT = "ML 전문가"

    @classmethod
    def from_string(cls, value: str) -> Optional["Audience"]:
        """관대한 파싱 — enum name, value, 한영 약칭 모두 허용.

        None을 반환하는 경우 호출자가 기본값을 결정.
        """
        if not value:
            return None
        v = value.strip().lower().replace(" ", "").replace("-", "_")
        aliases = {
            "general": cls.GENERAL,
            "일반인": cls.GENERAL,
            "일반": cls.GENERAL,
            "developer": cls.DEVELOPER,
            "dev": cls.DEVELOPER,
            "개발자": cls.DEVELOPER,
            "개발": cls.DEVELOPER,
            "ml_expert": cls.ML_EXPERT,
            "mlexpert": cls.ML_EXPERT,
            "expert": cls.ML_EXPERT,
            "ml전문가": cls.ML_EXPERT,
            "ml": cls.ML_EXPERT,
            "전문가": cls.ML_EXPERT,
        }
        return aliases.get(v)


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
    audience: list[Audience] = field(default_factory=list)  # FR-036: 독자 레벨 (multi-tag)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        if isinstance(self.source, str):
            self.source = Source(self.source)
        if isinstance(self.category, str):
            self.category = Category.from_string(self.category)
        # audience가 문자열 리스트로 들어올 수 있음 (JSON 역직렬화 직후)
        normalized: list[Audience] = []
        for item in self.audience:
            if isinstance(item, Audience):
                normalized.append(item)
            elif isinstance(item, str):
                parsed = Audience.from_string(item)
                if parsed is not None:
                    normalized.append(parsed)
        # 중복 제거하되 순서 유지
        seen: set[Audience] = set()
        self.audience = [a for a in normalized if not (a in seen or seen.add(a))]

    def to_dict(self) -> dict:
        """JSON 직렬화용 딕셔너리 변환"""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source.value,
            "content": self.content,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "summary": self.summary,
            "category": self.category.value,
            "audience": [a.name for a in self.audience],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Article":
        """딕셔너리에서 Article 복원"""
        published_at = None
        if data.get("published_at"):
            published_at = datetime.fromisoformat(data["published_at"])

        # audience 필드는 Phase 7 이전 리포트에는 없음 — 빈 리스트로 복원되어
        # 이후 static_generator의 fallback (source 기반)이 적용됨.
        raw_audience = data.get("audience", []) or []

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data["title"],
            url=data["url"],
            source=Source(data["source"]),
            content=data.get("content", ""),
            published_at=published_at,
            summary=data.get("summary", ""),
            category=Category.from_string(data.get("category", "기타")),
            audience=list(raw_audience),
        )


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

    def to_dict(self) -> dict:
        """JSON 직렬화용 딕셔너리 변환"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "articles": [article.to_dict() for article in self.articles],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Report":
        """딕셔너리에서 Report 복원"""
        articles = [Article.from_dict(a) for a in data.get("articles", [])]
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            created_at=created_at,
            articles=articles,
        )