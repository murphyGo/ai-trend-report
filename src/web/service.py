"""웹 대시보드 서비스 레이어"""

import logging
import re
from pathlib import Path
from typing import Optional

from ..models import Report, Category
from ..data_io import load_report, DEFAULT_DATA_DIR


logger = logging.getLogger(__name__)

# Phase 9.3 (M2) — 리포트 인메모리 캐시. 로컬 대시보드는 단일 프로세스라
# 디스크 반복 읽기 대신 메모리에 캐시해 검색 O(N*M) 문제를 완화.
_report_cache: dict[str, Report] = {}


def _cached_load_report(filepath: Path) -> Report:
    """load_report의 캐싱 래퍼. 같은 파일은 한 번만 파싱."""
    key = str(filepath)
    if key not in _report_cache:
        _report_cache[key] = load_report(filepath)
    return _report_cache[key]


def list_reports(data_dir: Optional[Path] = None) -> list[dict]:
    """모든 리포트 파일 목록 반환

    Args:
        data_dir: 데이터 디렉토리 (기본: data/)

    Returns:
        리포트 메타데이터 목록 [{id, date, article_count, filepath}, ...]
    """
    data_dir = data_dir or DEFAULT_DATA_DIR
    if not data_dir.exists():
        return []

    reports = []
    for filepath in sorted(data_dir.glob("report_*.json"), reverse=True):
        try:
            report = _cached_load_report(filepath)
            # 파일명에서 날짜 추출 (report_YYYY-MM-DD.json)
            date_str = filepath.stem.replace("report_", "")
            reports.append({
                "id": report.id,
                "date": date_str,
                "created_at": report.created_at.isoformat(),
                "article_count": len(report.articles),
                "filepath": str(filepath),
            })
        except Exception as e:
            logger.warning(f"Failed to load report {filepath}: {e}")
            continue

    return reports


def get_report(report_id: str, data_dir: Optional[Path] = None) -> Optional[Report]:
    """ID로 리포트 조회

    Args:
        report_id: 리포트 ID
        data_dir: 데이터 디렉토리

    Returns:
        리포트 객체 또는 None
    """
    data_dir = data_dir or DEFAULT_DATA_DIR
    if not data_dir.exists():
        return None

    for filepath in data_dir.glob("report_*.json"):
        try:
            report = _cached_load_report(filepath)
            if report.id == report_id:
                return report
        except Exception as e:
            logger.warning(f"Failed to load report {filepath}: {e}")
            continue

    return None


def get_report_by_date(date_str: str, data_dir: Optional[Path] = None) -> Optional[Report]:
    """날짜로 리포트 조회

    Args:
        date_str: 날짜 문자열 (YYYY-MM-DD)
        data_dir: 데이터 디렉토리

    Returns:
        리포트 객체 또는 None
    """
    data_dir = data_dir or DEFAULT_DATA_DIR
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        return None

    filepath = (data_dir / f"report_{date_str}.json").resolve()
    if not str(filepath).startswith(str(data_dir.resolve())):
        return None

    if not filepath.exists():
        return None

    try:
        return _cached_load_report(filepath)
    except Exception as e:
        logger.warning(f"Failed to load report {filepath}: {e}")
        return None


def search_articles(
    query: str,
    category: Optional[str] = None,
    data_dir: Optional[Path] = None,
) -> list[dict]:
    """기사 검색

    Args:
        query: 검색어 (제목, 요약에서 검색)
        category: 카테고리 필터 (선택)
        data_dir: 데이터 디렉토리

    Returns:
        검색 결과 기사 목록
    """
    data_dir = data_dir or DEFAULT_DATA_DIR
    if not data_dir.exists():
        return []

    results = []
    query_lower = query.lower()

    # 카테고리 필터 파싱
    target_category = None
    if category:
        try:
            target_category = Category.from_string(category)
        except Exception:
            pass

    for filepath in sorted(data_dir.glob("report_*.json"), reverse=True):
        try:
            report = _cached_load_report(filepath)
            date_str = filepath.stem.replace("report_", "")

            for article in report.articles:
                # 카테고리 필터
                if target_category and article.category != target_category:
                    continue

                # 텍스트 검색
                title_match = query_lower in article.title.lower()
                summary_match = query_lower in (article.summary or "").lower()

                if title_match or summary_match:
                    results.append({
                        "id": article.id,
                        "title": article.title,
                        "url": article.url,
                        "source": article.source.value,
                        "summary": article.summary,
                        "category": article.category.value,
                        "report_date": date_str,
                        "report_id": report.id,
                    })

        except Exception as e:
            logger.warning(f"Failed to search in {filepath}: {e}")
            continue

    return results


def get_categories() -> list[dict]:
    """모든 카테고리 목록 반환

    Returns:
        카테고리 목록 [{name, value}, ...]
    """
    return [
        {"name": cat.name, "value": cat.value}
        for cat in Category
    ]


def get_report_stats(report: Report) -> dict:
    """리포트 통계 계산

    Args:
        report: 리포트 객체

    Returns:
        통계 정보 {total, by_category, by_source}
    """
    by_category = {}
    by_source = {}

    for article in report.articles:
        # 카테고리별 집계
        cat_value = article.category.value
        by_category[cat_value] = by_category.get(cat_value, 0) + 1

        # 소스별 집계
        source_value = article.source.value
        by_source[source_value] = by_source.get(source_value, 0) + 1

    return {
        "total": len(report.articles),
        "by_category": by_category,
        "by_source": by_source,
    }
