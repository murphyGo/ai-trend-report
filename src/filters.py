"""기사 필터 — Phase 8

수집 직후 Claude 랭킹 전에 적용되는 순수 함수형 필터들:

1. `filter_by_recency` — 최근 N일 이내 발행된 기사만 통과
2. `filter_already_seen` — 최근 리포트에서 이미 본 URL 제거

두 필터 모두 부작용 없는 순수 함수라 테스트가 쉽고 `run_collect_only`의
파이프라인 조립에서 독립적으로 호출된다.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from .models import Article


logger = logging.getLogger(__name__)


def _ensure_aware(dt: datetime) -> datetime:
    """naive datetime을 UTC aware로 승격.

    arXiv `pubDate`는 타임존 정보 포함(RFC 822), `dc:date`는 간혹 naive.
    비교 시점에 한쪽으로 통일해야 하므로 naive는 UTC로 간주한다.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def filter_by_recency(
    articles: list[Article],
    days: int,
    *,
    now: Optional[datetime] = None,
) -> tuple[list[Article], int, int]:
    """지난 `days`일 이내에 발행된 기사만 유지.

    `published_at`이 `None`인 기사는 **유지(keep)** 한다 — 보수적 fallback.
    일부 수집기(레거시 HTML 스크래퍼 등)가 아직 날짜를 안 채울 수 있으므로
    무조건 드롭하면 Frontier Lab 블로그 등 중요한 소스가 소실된다.

    Args:
        articles: 원본 기사 목록
        days: 허용 기간(일). 0 이하면 필터 비활성화 (모든 기사 반환).
        now: 테스트용 고정 현재 시점. 미지정 시 `datetime.now(UTC)`.

    Returns:
        `(kept, filtered_out, unknown_kept)` 튜플.
        - kept: 필터 통과한 기사
        - filtered_out: 오래돼서 제거된 기사 수
        - unknown_kept: `published_at=None`이라 보수적으로 유지된 수
    """
    if days <= 0 or not articles:
        return list(articles), 0, 0

    if now is None:
        now = datetime.now(timezone.utc)
    else:
        now = _ensure_aware(now)

    cutoff = now - timedelta(days=days)

    kept: list[Article] = []
    filtered_out = 0
    unknown_kept = 0

    for article in articles:
        if article.published_at is None:
            kept.append(article)
            unknown_kept += 1
            continue

        pub = _ensure_aware(article.published_at)
        if pub >= cutoff:
            kept.append(article)
        else:
            filtered_out += 1

    return kept, filtered_out, unknown_kept


def filter_already_seen(
    articles: list[Article],
    seen_urls: set[str],
) -> tuple[list[Article], int]:
    """최근 리포트에 이미 등장한 URL 제거.

    Args:
        articles: 원본 기사 목록
        seen_urls: 차단할 URL 집합 (예: `load_recent_report_urls`의 반환값)

    Returns:
        `(kept, removed)` 튜플.
    """
    if not seen_urls or not articles:
        return list(articles), 0

    kept: list[Article] = []
    removed = 0
    for article in articles:
        if article.url in seen_urls:
            removed += 1
        else:
            kept.append(article)

    return kept, removed
