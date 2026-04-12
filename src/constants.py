"""프로젝트 공통 상수 — Phase 9.1

여러 모듈에서 중복 정의되던 상수를 single source of truth로 통합.
"""

from .models import Category

# Quiet-day 임계값 — 리포트 기사 수가 이보다 적으면 알림에 "조용한 날" 배너 표시.
# 이전: slack_notifier, discord_notifier, email_notifier에 각각 독립 정의됨.
QUIET_DAY_THRESHOLD: int = 3

# 카테고리 렌더링 순서 — Slack/Email 등 알림에서 카테고리 섹션을 이 순서로 표시.
# 이전: slack_notifier.py와 email_notifier.py에 각각 동일한 리스트로 중복.
CATEGORY_ORDER: list[Category] = [
    Category.LLM,
    Category.AGENT,
    Category.VISION,
    Category.VIDEO,
    Category.ROBOTICS,
    Category.SAFETY,
    Category.RL,
    Category.INFRA,
    Category.MEDICAL,
    Category.FINANCE,
    Category.INDUSTRY,
    Category.OTHER,
]
