"""정적 사이트 생성 모듈

GitHub Pages 배포를 위한 정적 HTML 파일 생성
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from .models import Report, Article, Category, Source, Audience
from .data_io import load_report, list_report_files


logger = logging.getLogger(__name__)


# 기본 경로
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = STATIC_DIR / "templates"


# 소스 티어 분류 (색상 그룹핑용)
SOURCE_TIER_MAP: dict[Source, str] = {
    # Frontier Labs
    Source.ANTHROPIC_BLOG: "Frontier Lab",
    Source.OPENAI_BLOG: "Frontier Lab",
    Source.GOOGLE_BLOG: "Frontier Lab",
    Source.HUGGINGFACE_BLOG: "Frontier Lab",
    # Research (논문 + 기업/학계 리서치)
    Source.ARXIV: "Research",
    Source.HF_PAPERS: "Research",
    Source.MICROSOFT_RESEARCH: "Research",
    Source.NVIDIA_BLOG: "Research",
    Source.BAIR_BLOG: "Research",
    Source.STANFORD_AI: "Research",
    # Media
    Source.MARKTECHPOST: "Media",
    Source.TECHCRUNCH_AI: "Media",
    Source.VENTUREBEAT_AI: "Media",
    Source.MIT_TECH_REVIEW: "Media",
    # Korean
    Source.KOREAN_NEWS: "Korean",
    Source.NAVER_D2: "Korean",
    Source.KAKAO_TECH: "Korean",
    # Inactive (코드 존재, 사이트 정책으로 미사용)
    Source.META_AI_BLOG: "Inactive",
    Source.LG_AI_RESEARCH: "Inactive",
}

# 티어 → 색상 (모두 흰 글씨 대비 충분)
TIER_COLORS: dict[str, str] = {
    "Frontier Lab": "#2563eb",  # blue
    "Research": "#7c3aed",      # purple
    "Media": "#ea580c",         # orange
    "Korean": "#db2777",        # pink
    "Inactive": "#64748b",      # muted grey
}

# 소스 display label (Source enum의 raw value 대신 사용자용 이름)
SOURCE_LABELS: dict[Source, str] = {
    Source.ARXIV: "arXiv",
    Source.GOOGLE_BLOG: "Google AI",
    Source.ANTHROPIC_BLOG: "Anthropic",
    Source.OPENAI_BLOG: "OpenAI",
    Source.HUGGINGFACE_BLOG: "Hugging Face",
    Source.KOREAN_NEWS: "AI타임스",
    Source.MICROSOFT_RESEARCH: "Microsoft Research",
    Source.NVIDIA_BLOG: "NVIDIA Developer",
    Source.MARKTECHPOST: "MarkTechPost",
    Source.BAIR_BLOG: "BAIR (Berkeley)",
    Source.STANFORD_AI: "Stanford AI Lab",
    Source.TECHCRUNCH_AI: "TechCrunch AI",
    Source.VENTUREBEAT_AI: "VentureBeat AI",
    Source.HF_PAPERS: "HF Daily Papers",
    Source.META_AI_BLOG: "Meta AI",
    Source.MIT_TECH_REVIEW: "MIT Tech Review",
    Source.NAVER_D2: "Naver D2",
    Source.KAKAO_TECH: "Kakao Tech",
    Source.LG_AI_RESEARCH: "LG AI Research",
}


def get_source_label(source: Source) -> str:
    """소스 display 이름"""
    if not source:
        return "Unknown"
    return SOURCE_LABELS.get(source, source.value)


def get_source_tier(source: Source) -> str:
    """소스 티어 이름"""
    if not source:
        return ""
    return SOURCE_TIER_MAP.get(source, "Other")


def get_source_color(source: Source) -> str:
    """소스 색상 (티어 기반)"""
    tier = get_source_tier(source)
    return TIER_COLORS.get(tier, "#64748b")


# =============================================================================
# Audience (독자 레벨) — FR-036~040
# =============================================================================

# 소스 기반 기본 audience 매핑. Claude가 article.audience를 설정하지 않은 경우
# (레거시 리포트 등) 폴백으로 사용. 각 소스를 읽을 만한 독자층 1~3 레벨.
SOURCE_AUDIENCE: dict[Source, list[Audience]] = {
    # 연구/논문
    Source.ARXIV:              [Audience.ML_EXPERT],
    Source.HF_PAPERS:          [Audience.ML_EXPERT, Audience.DEVELOPER],
    # Frontier Lab
    Source.ANTHROPIC_BLOG:     [Audience.GENERAL, Audience.DEVELOPER],
    Source.OPENAI_BLOG:        [Audience.GENERAL, Audience.DEVELOPER],
    Source.GOOGLE_BLOG:        [Audience.GENERAL, Audience.DEVELOPER],
    Source.HUGGINGFACE_BLOG:   [Audience.DEVELOPER, Audience.ML_EXPERT],
    # 기업/학계 리서치
    Source.MICROSOFT_RESEARCH: [Audience.ML_EXPERT, Audience.DEVELOPER],
    Source.NVIDIA_BLOG:        [Audience.DEVELOPER, Audience.ML_EXPERT],
    Source.BAIR_BLOG:          [Audience.ML_EXPERT],
    Source.STANFORD_AI:        [Audience.ML_EXPERT],
    # 미디어/큐레이션
    Source.MARKTECHPOST:       [Audience.DEVELOPER, Audience.ML_EXPERT],
    Source.TECHCRUNCH_AI:      [Audience.GENERAL],
    Source.VENTUREBEAT_AI:     [Audience.GENERAL, Audience.DEVELOPER],
    Source.MIT_TECH_REVIEW:    [Audience.GENERAL],
    # 한국
    Source.KOREAN_NEWS:        [Audience.GENERAL],
    Source.NAVER_D2:           [Audience.DEVELOPER],
    Source.KAKAO_TECH:         [Audience.DEVELOPER],
    # 비활성이지만 매핑은 유지
    Source.META_AI_BLOG:       [Audience.GENERAL, Audience.DEVELOPER],
    Source.LG_AI_RESEARCH:     [Audience.DEVELOPER, Audience.ML_EXPERT],
}

# audience 칩 라벨 (짧은 한국어 form)
AUDIENCE_LABELS: dict[Audience, str] = {
    Audience.GENERAL: "일반인",
    Audience.DEVELOPER: "개발자",
    Audience.ML_EXPERT: "ML 전문가",
}

# 카드 미니 배지용 초단축 form
AUDIENCE_SHORT: dict[Audience, str] = {
    Audience.GENERAL: "일반",
    Audience.DEVELOPER: "개발",
    Audience.ML_EXPERT: "ML",
}


def get_article_audience(article: Article) -> list[Audience]:
    """기사의 effective audience 반환.

    우선순위:
    1. `article.audience`가 비어있지 않으면 그대로 사용 (Claude가 태깅함)
    2. article.source가 있으면 `SOURCE_AUDIENCE` 매핑 fallback
    3. 그 외엔 전 레벨(전체 표시)

    빈 리스트를 반환하지 않도록 보장 — 필터링 시 "어느 레벨에도 속하지 않음" 상태를
    피하기 위해.
    """
    if article.audience:
        return list(article.audience)
    if article.source and article.source in SOURCE_AUDIENCE:
        return list(SOURCE_AUDIENCE[article.source])
    return list(Audience)


def get_audience_data_attr(article: Article) -> str:
    """HTML `data-audience` 속성용 콤마 구분 enum name 문자열.

    예: "GENERAL,DEVELOPER"
    """
    return ",".join(a.name for a in get_article_audience(article))


def get_audience_labels(article: Article) -> list[str]:
    """표시용 한국어 라벨 리스트."""
    return [AUDIENCE_LABELS[a] for a in get_article_audience(article)]


def count_audience(articles: list[Article]) -> dict[str, int]:
    """기사 리스트의 audience 분포를 집계.

    반환 형식: {"GENERAL": 5, "DEVELOPER": 8, "ML_EXPERT": 12}
    템플릿에서 `counts.GENERAL` 같은 형태로 사용하기 위해 enum name을 key로 사용.
    Multi-tag이므로 합계가 len(articles)를 넘을 수 있음.
    """
    counts: dict[str, int] = {a.name: 0 for a in Audience}
    for article in articles:
        for aud in get_article_audience(article):
            counts[aud.name] += 1
    return counts


def get_category_color(category: Category) -> str:
    """카테고리별 색상 반환"""
    colors = {
        Category.LLM: "#4CAF50",
        Category.AGENT: "#2196F3",
        Category.VISION: "#9C27B0",
        Category.VIDEO: "#E91E63",
        Category.ROBOTICS: "#FF5722",
        Category.SAFETY: "#F44336",
        Category.RL: "#00BCD4",
        Category.INFRA: "#607D8B",
        Category.MEDICAL: "#8BC34A",
        Category.FINANCE: "#FFC107",
        Category.INDUSTRY: "#795548",
        Category.OTHER: "#9E9E9E",
    }
    return colors.get(category, "#9E9E9E")


def get_category_label(category: Category) -> str:
    """카테고리 한글 라벨"""
    labels = {
        Category.LLM: "LLM",
        Category.AGENT: "AI 에이전트",
        Category.VISION: "컴퓨터 비전",
        Category.VIDEO: "비디오 생성",
        Category.ROBOTICS: "로보틱스",
        Category.SAFETY: "AI 안전성",
        Category.RL: "강화학습",
        Category.INFRA: "ML 인프라",
        Category.MEDICAL: "의료/생명과학",
        Category.FINANCE: "금융",
        Category.INDUSTRY: "산업 동향",
        Category.OTHER: "기타",
    }
    return labels.get(category, "기타")


def _safe_url_filter(url: str) -> str:
    """http/https만 허용, 그 외(javascript:, data: 등)는 '#' 반환."""
    if not url or not isinstance(url, str):
        return "#"
    stripped = url.strip().lower()
    if stripped.startswith("http://") or stripped.startswith("https://"):
        return url
    return "#"


class StaticSiteGenerator:
    """정적 사이트 생성기"""

    def __init__(self, data_dir: Path, output_dir: Path, base_url: Optional[str] = None):
        """
        Args:
            data_dir: 리포트 JSON 파일이 있는 디렉토리
            output_dir: 정적 사이트 출력 디렉토리
            base_url: 사이트 URL prefix (예: "/ai-trend-report").
                      None이면 SITE_BASE_URL 환경변수 사용, 없으면 빈 문자열.
                      GitHub Pages 프로젝트 사이트처럼 서브패스에 배포 시 필요.
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)

        # base_url 결정: 인자 > 환경변수 > 빈 문자열
        if base_url is None:
            base_url = os.getenv("SITE_BASE_URL", "")
        # 일관성을 위해 트레일링 슬래시 제거 (템플릿에서 {{ base_url }}/... 로 사용)
        self.base_url = base_url.rstrip("/")

        # Jinja2 환경 설정
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )

        # 커스텀 필터 등록
        self.env.filters["category_color"] = get_category_color
        self.env.filters["category_label"] = get_category_label
        self.env.filters["source_label"] = get_source_label
        self.env.filters["source_color"] = get_source_color
        self.env.filters["source_tier"] = get_source_tier
        self.env.filters["audience_data"] = get_audience_data_attr
        self.env.filters["audience_labels"] = get_audience_labels
        self.env.filters["safe_url"] = _safe_url_filter

    def generate(self) -> None:
        """전체 정적 사이트 생성"""
        # 출력 디렉토리 준비
        self._prepare_output_dir()

        # 리포트 로드
        reports = self._load_all_reports()

        if not reports:
            logger.warning("No reports found in %s", self.data_dir)
            return

        # 정적 파일 복사
        self._copy_static_files()

        # 페이지 생성
        self._generate_index(reports)
        self._generate_report_pages(reports)
        self._generate_category_pages(reports)
        self._generate_source_pages(reports)
        self._generate_search_page(reports)

        # 데이터 파일 생성
        self._generate_reports_json(reports)
        self._generate_search_index(reports)

        logger.info("Static site generated: %s", self.output_dir)

    def _prepare_output_dir(self) -> None:
        """출력 디렉토리 준비"""
        # 기존 파일 삭제
        for subdir in ["reports", "categories", "sources", "data", "css", "js"]:
            subpath = self.output_dir / subdir
            if subpath.exists():
                shutil.rmtree(subpath)

        # 디렉토리 생성
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "categories").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "sources").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "data").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "css").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "js").mkdir(parents=True, exist_ok=True)

    def _load_all_reports(self) -> list[Report]:
        """모든 리포트 로드 (최신순 정렬)"""
        reports = []
        for filepath in list_report_files(self.data_dir):
            try:
                report = load_report(filepath)
                if report:
                    reports.append(report)
            except Exception as e:
                logger.warning("Failed to load %s: %s", filepath, e)

        # 최신순 정렬
        reports.sort(key=lambda r: r.created_at, reverse=True)
        return reports

    def _copy_static_files(self) -> None:
        """CSS, JS 파일 복사"""
        # CSS
        css_src = STATIC_DIR / "css"
        if css_src.exists():
            for f in css_src.glob("*.css"):
                shutil.copy(f, self.output_dir / "css" / f.name)

        # JS
        js_src = STATIC_DIR / "js"
        if js_src.exists():
            for f in js_src.glob("*.js"):
                shutil.copy(f, self.output_dir / "js" / f.name)

    def _generate_index(self, reports: list[Report]) -> None:
        """메인 페이지 생성 (대시보드 스타일)

        홈은 기사 목록 대신 "탐색 허브" 역할:
        - 히어로 + 오늘의 리포트로 가는 CTA 버튼
        - 통계 카드 4개 (Articles / Categories / Sources / Total Reports)
        - 오늘의 카테고리 미리보기 그리드 (상위 8개)
        - 오늘의 소스 미리보기 그리드 (상위 8개)
        - 최근 리포트 아카이브

        실제 기사 목록은 /reports/{date}.html 에서만 렌더링.
        """
        template = self.env.get_template("index.html")

        latest_report = reports[0] if reports else None

        # 최신 리포트 기준 카테고리/소스 카운트 집계
        today_category_counts: dict[Category, int] = {}
        today_source_counts: dict[Source, int] = {}
        latest_date = ""

        if latest_report:
            latest_date = latest_report.created_at.strftime("%Y-%m-%d")
            for article in latest_report.articles:
                cat = article.category or Category.OTHER
                today_category_counts[cat] = today_category_counts.get(cat, 0) + 1
                if article.source:
                    today_source_counts[article.source] = (
                        today_source_counts.get(article.source, 0) + 1
                    )

        # 카운트 내림차순 정렬 후 상위 8개 (이름으로 tie-breaking)
        top_categories = sorted(
            today_category_counts.items(),
            key=lambda x: (-x[1], x[0].name),
        )[:8]
        top_sources = sorted(
            today_source_counts.items(),
            key=lambda x: (-x[1], x[0].name),
        )[:8]

        html = template.render(
            latest_report=latest_report,
            latest_date=latest_date,
            total_articles=len(latest_report.articles) if latest_report else 0,
            total_categories=len(today_category_counts),
            total_sources=len(today_source_counts),
            total_reports=len(reports),
            top_categories=top_categories,
            top_sources=top_sources,
            reports=reports[:10],
            generated_at=datetime.now().isoformat(),
            Category=Category,
            Source=Source,
            base_url=self.base_url,
        )

        (self.output_dir / "index.html").write_text(html, encoding="utf-8")

    def _generate_report_pages(self, reports: list[Report]) -> None:
        """개별 리포트 페이지 생성"""
        template = self.env.get_template("report.html")

        for i, report in enumerate(reports):
            # 카테고리별 그룹핑
            articles_by_category = {}
            for article in report.articles:
                cat = article.category or Category.OTHER
                if cat not in articles_by_category:
                    articles_by_category[cat] = []
                articles_by_category[cat].append(article)

            # 이전/다음 리포트
            prev_report = reports[i + 1] if i + 1 < len(reports) else None
            next_report = reports[i - 1] if i > 0 else None

            html = template.render(
                report=report,
                articles_by_category=articles_by_category,
                prev_report=prev_report,
                next_report=next_report,
                Category=Category,
                base_url=self.base_url,
            )

            # 날짜 기반 파일명
            date_str = report.created_at.strftime("%Y-%m-%d")
            (self.output_dir / "reports" / f"{date_str}.html").write_text(
                html, encoding="utf-8"
            )

    def _generate_category_pages(self, reports: list[Report]) -> None:
        """카테고리별 페이지 생성

        모든 리포트의 기사를 카테고리별로 집계해서:
        1. 카테고리 인덱스 페이지 (categories/index.html) - 12개 카테고리 그리드
        2. 개별 카테고리 페이지 (categories/{NAME}.html) - 해당 카테고리의 전 기사
        """
        # 카테고리별 기사 집계 (reports가 이미 최신순 정렬이라 자연스럽게 최신순)
        category_articles: dict[Category, list[tuple]] = {}
        for report in reports:
            date_str = report.created_at.strftime("%Y-%m-%d")
            for article in report.articles:
                cat = article.category or Category.OTHER
                if cat not in category_articles:
                    category_articles[cat] = []
                category_articles[cat].append((article, date_str))

        # 개별 카테고리 페이지
        category_template = self.env.get_template("category.html")
        for category in Category:
            articles = category_articles.get(category, [])
            html = category_template.render(
                category=category,
                articles=articles,  # list of (article, date_str) tuples
                article_count=len(articles),
                base_url=self.base_url,
                Category=Category,
            )
            (self.output_dir / "categories" / f"{category.name}.html").write_text(
                html, encoding="utf-8"
            )

        # 카테고리 인덱스 페이지 — 카드당 audience 미니 통계 포함 (Phase 7.4)
        index_template = self.env.get_template("categories_index.html")
        category_entries = []
        for cat in Category:
            entries = category_articles.get(cat, [])
            aud_counts = count_audience([art for art, _ in entries])
            category_entries.append({
                "category": cat,
                "count": len(entries),
                "audience_counts": aud_counts,
            })
        # 기사 수 많은 순으로 정렬 (0개는 뒤로)
        category_entries.sort(key=lambda e: (-e["count"], e["category"].name))

        html = index_template.render(
            category_entries=category_entries,
            total_articles=sum(e["count"] for e in category_entries),
            base_url=self.base_url,
            Category=Category,
        )
        (self.output_dir / "categories" / "index.html").write_text(
            html, encoding="utf-8"
        )

    def _generate_source_pages(self, reports: list[Report]) -> None:
        """소스별 페이지 생성

        모든 리포트의 기사를 Source별로 집계해:
        1. 소스 인덱스 (sources/index.html) - 소스 카드 그리드
        2. 개별 소스 페이지 (sources/{NAME}.html) - 해당 소스의 전 기사
        """
        # 소스별 기사 집계 (reports가 이미 최신순이므로 자연 최신순)
        source_articles: dict[Source, list[tuple]] = {}
        for report in reports:
            date_str = report.created_at.strftime("%Y-%m-%d")
            for article in report.articles:
                src = article.source
                if src is None:
                    continue
                if src not in source_articles:
                    source_articles[src] = []
                source_articles[src].append((article, date_str))

        # 개별 소스 페이지
        source_template = self.env.get_template("source.html")
        for source in Source:
            articles = source_articles.get(source, [])
            html = source_template.render(
                source=source,
                articles=articles,
                article_count=len(articles),
                base_url=self.base_url,
                Source=Source,
            )
            (self.output_dir / "sources" / f"{source.name}.html").write_text(
                html, encoding="utf-8"
            )

        # 소스 인덱스 페이지 — 카드당 audience 미니 통계 포함 (Phase 7.4)
        index_template = self.env.get_template("sources_index.html")
        source_entries = []
        for src in Source:
            entries = source_articles.get(src, [])
            aud_counts = count_audience([art for art, _ in entries])
            source_entries.append({
                "source": src,
                "count": len(entries),
                "audience_counts": aud_counts,
            })
        source_entries.sort(key=lambda e: (-e["count"], e["source"].name))

        html = index_template.render(
            source_entries=source_entries,
            total_articles=sum(e["count"] for e in source_entries),
            base_url=self.base_url,
            Source=Source,
        )
        (self.output_dir / "sources" / "index.html").write_text(
            html, encoding="utf-8"
        )

    def _generate_search_page(self, reports: list[Report]) -> None:
        """검색 페이지 생성"""
        template = self.env.get_template("search.html")

        html = template.render(
            categories=list(Category),
            Category=Category,
            base_url=self.base_url,
        )

        (self.output_dir / "search.html").write_text(html, encoding="utf-8")

    def _generate_reports_json(self, reports: list[Report]) -> None:
        """리포트 목록 JSON 생성"""
        data = []
        for report in reports:
            date_str = report.created_at.strftime("%Y-%m-%d")
            data.append({
                "id": report.id,
                "date": date_str,
                "article_count": len(report.articles),
                "url": f"{self.base_url}/reports/{date_str}.html",
            })

        (self.output_dir / "data" / "reports.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _generate_search_index(self, reports: list[Report]) -> None:
        """검색 인덱스 JSON 생성

        Phase 8.6: 각 엔트리에 `audience` 필드 추가 — 클라이언트 audience 필터가
        동적으로 렌더된 검색 결과 카드에도 적용될 수 있도록 `data-audience`로
        노출하기 위함.
        """
        index = []
        for report in reports:
            date_str = report.created_at.strftime("%Y-%m-%d")
            for article in report.articles:
                audience_list = [a.name for a in get_article_audience(article)]
                index.append({
                    "id": article.id,
                    "title": article.title,
                    "summary": article.summary or "",
                    "category": article.category.name if article.category else "OTHER",
                    "category_label": article.category.value if article.category else "",
                    "source": article.source.name if article.source else "",
                    "source_label": get_source_label(article.source) if article.source else "",
                    "url": article.url,
                    "date": date_str,
                    "report_url": f"{self.base_url}/reports/{date_str}.html",
                    "audience": audience_list,
                })

        (self.output_dir / "data" / "search-index.json").write_text(
            json.dumps(index, ensure_ascii=False),
            encoding="utf-8"
        )


def generate_static_site(
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    base_url: Optional[str] = None,
) -> None:
    """정적 사이트 생성 헬퍼 함수"""
    if data_dir is None:
        data_dir = Path("data")
    if output_dir is None:
        output_dir = Path("_site")

    generator = StaticSiteGenerator(data_dir, output_dir, base_url=base_url)
    generator.generate()


if __name__ == "__main__":
    generate_static_site()
