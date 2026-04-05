"""정적 사이트 생성 모듈

GitHub Pages 배포를 위한 정적 HTML 파일 생성
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from .models import Report, Category
from .data_io import load_report, list_report_files


# 기본 경로
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = STATIC_DIR / "templates"


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

    def __init__(self, data_dir: Path, output_dir: Path):
        """
        Args:
            data_dir: 리포트 JSON 파일이 있는 디렉토리
            output_dir: 정적 사이트 출력 디렉토리
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)

        # Jinja2 환경 설정
        self.env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )

        # 커스텀 필터 등록
        self.env.filters["category_color"] = get_category_color
        self.env.filters["category_label"] = get_category_label

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
        self._generate_search_page(reports)

        # 데이터 파일 생성
        self._generate_reports_json(reports)
        self._generate_search_index(reports)

        print(f"Static site generated: {self.output_dir}")

    def _prepare_output_dir(self) -> None:
        """출력 디렉토리 준비"""
        # 기존 파일 삭제 (reports/, data/ 만)
        for subdir in ["reports", "data", "css", "js"]:
            subpath = self.output_dir / subdir
            if subpath.exists():
                shutil.rmtree(subpath)

        # 디렉토리 생성
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)
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
        """메인 페이지 생성"""
        template = self.env.get_template("index.html")

        latest_report = reports[0] if reports else None

        # 카테고리별 그룹핑
        articles_by_category = {}
        if latest_report:
            for article in latest_report.articles:
                cat = article.category or Category.OTHER
                if cat not in articles_by_category:
                    articles_by_category[cat] = []
                articles_by_category[cat].append(article)

        html = template.render(
            latest_report=latest_report,
            articles_by_category=articles_by_category,
            reports=reports[:10],  # 최근 10개
            total_reports=len(reports),
            generated_at=datetime.now().isoformat(),
            Category=Category,
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
            )

            # 날짜 기반 파일명
            date_str = report.created_at.strftime("%Y-%m-%d")
            (self.output_dir / "reports" / f"{date_str}.html").write_text(
                html, encoding="utf-8"
            )

    def _generate_search_page(self, reports: list[Report]) -> None:
        """검색 페이지 생성"""
        template = self.env.get_template("search.html")

        html = template.render(
            categories=list(Category),
            Category=Category,
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
                "url": f"/reports/{date_str}.html",
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
                    "report_url": f"/reports/{date_str}.html",
                })

        (self.output_dir / "data" / "search-index.json").write_text(
            json.dumps(index, ensure_ascii=False),
            encoding="utf-8"
        )


def generate_static_site(
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> None:
    """정적 사이트 생성 헬퍼 함수"""
    if data_dir is None:
        data_dir = Path("data")
    if output_dir is None:
        output_dir = Path("_site")

    generator = StaticSiteGenerator(data_dir, output_dir)
    generator.generate()


if __name__ == "__main__":
    generate_static_site()
