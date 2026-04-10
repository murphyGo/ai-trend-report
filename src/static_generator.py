"""정적 사이트 생성 모듈

GitHub Pages 배포를 위한 정적 HTML 파일 생성
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from .models import Report, Category, Source
from .data_io import load_report, list_report_files


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

    def generate(self) -> None:
        """전체 정적 사이트 생성"""
        # 출력 디렉토리 준비
        self._prepare_output_dir()

        # 리포트 로드
        reports = self._load_all_reports()

        if not reports:
            print("No reports found")
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

        print(f"Static site generated: {self.output_dir}")

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
                print(f"Failed to load {filepath}: {e}")

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

        # 카테고리 인덱스 페이지 (모든 카테고리 그리드, 기사가 있는 것만)
        index_template = self.env.get_template("categories_index.html")
        category_counts = [
            (cat, len(category_articles.get(cat, []))) for cat in Category
        ]
        # 기사 수 많은 순으로 정렬 (0개는 뒤로)
        category_counts.sort(key=lambda x: (-x[1], x[0].name))

        html = index_template.render(
            category_counts=category_counts,
            total_articles=sum(c for _, c in category_counts),
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

        # 인덱스 페이지 (모든 소스, 기사 수 많은 순)
        index_template = self.env.get_template("sources_index.html")
        source_counts = [
            (src, len(source_articles.get(src, []))) for src in Source
        ]
        source_counts.sort(key=lambda x: (-x[1], x[0].name))

        html = index_template.render(
            source_counts=source_counts,
            total_articles=sum(c for _, c in source_counts),
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
        """검색 인덱스 JSON 생성"""
        index = []
        for report in reports:
            date_str = report.created_at.strftime("%Y-%m-%d")
            for article in report.articles:
                index.append({
                    "id": article.id,
                    "title": article.title,
                    "summary": article.summary or "",
                    "category": article.category.value if article.category else "OTHER",
                    "source": article.source.value if article.source else "",
                    "url": article.url,
                    "date": date_str,
                    "report_url": f"{self.base_url}/reports/{date_str}.html",
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
