"""JSON 파일 읽기/쓰기 유틸리티"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Article, Report

logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"


def get_today_filename(prefix: str = "articles") -> str:
    """오늘 날짜 기반 파일명 생성"""
    return f"{prefix}_{datetime.now().strftime('%Y-%m-%d')}.json"


def save_articles(
    articles: list[Article],
    output_dir: Optional[Path] = None,
    filename: Optional[str] = None,
) -> Path:
    """기사 목록을 JSON 파일로 저장

    Args:
        articles: 저장할 기사 목록
        output_dir: 출력 디렉토리 (기본: data/)
        filename: 파일명 (기본: articles_YYYY-MM-DD.json)

    Returns:
        저장된 파일 경로
    """
    output_dir = output_dir or DEFAULT_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = filename or get_today_filename("articles")
    filepath = output_dir / filename

    data = {
        "collected_at": datetime.now().isoformat(),
        "count": len(articles),
        "articles": [article.to_dict() for article in articles],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(articles)} articles to {filepath}")
    return filepath


def load_articles(filepath: Path) -> list[Article]:
    """JSON 파일에서 기사 목록 로드

    Args:
        filepath: JSON 파일 경로

    Returns:
        기사 목록
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = [Article.from_dict(a) for a in data.get("articles", [])]
    logger.info(f"Loaded {len(articles)} articles from {filepath}")
    return articles


def save_report(
    report: Report,
    output_dir: Optional[Path] = None,
    filename: Optional[str] = None,
) -> Path:
    """리포트를 JSON 파일로 저장

    Args:
        report: 저장할 리포트
        output_dir: 출력 디렉토리 (기본: data/)
        filename: 파일명 (기본: report_YYYY-MM-DD.json)

    Returns:
        저장된 파일 경로
    """
    output_dir = output_dir or DEFAULT_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = filename or get_today_filename("report")
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)

    logger.info(f"Saved report with {len(report.articles)} articles to {filepath}")
    return filepath


def load_report(filepath: Path) -> Report:
    """JSON 파일에서 리포트 로드

    Args:
        filepath: JSON 파일 경로

    Returns:
        리포트
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = Report.from_dict(data)
    logger.info(f"Loaded report with {len(report.articles)} articles from {filepath}")
    return report


def get_latest_file(
    data_dir: Optional[Path] = None,
    prefix: str = "articles",
) -> Optional[Path]:
    """가장 최근 데이터 파일 찾기

    Args:
        data_dir: 데이터 디렉토리
        prefix: 파일 접두사 (articles 또는 report)

    Returns:
        가장 최근 파일 경로 또는 None
    """
    data_dir = data_dir or DEFAULT_DATA_DIR
    if not data_dir.exists():
        return None

    files = sorted(data_dir.glob(f"{prefix}_*.json"), reverse=True)
    return files[0] if files else None


def list_report_files(data_dir: Optional[Path] = None) -> list[Path]:
    """모든 리포트 파일 목록 반환 (최신순)

    Args:
        data_dir: 데이터 디렉토리

    Returns:
        리포트 파일 경로 목록 (최신순 정렬)
    """
    data_dir = data_dir or DEFAULT_DATA_DIR
    if not data_dir.exists():
        return []

    return sorted(data_dir.glob("report_*.json"), reverse=True)
