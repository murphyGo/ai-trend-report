"""알림 전송기 추상 베이스 — Phase 9.1

Slack / Discord / Email notifier가 공유하는 인터페이스와 공통 헬퍼.
메시지 빌드 로직은 채널마다 완전히 다르므로 추상 메서드로 남기고,
quiet-day 판별 같은 공통 판단만 여기에 둔다.

향후 새 알림 채널(Teams, Telegram 등) 추가 시 이 베이스를 상속.
"""

from abc import ABC, abstractmethod
import logging

from .models import Report
from .constants import QUIET_DAY_THRESHOLD


logger = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """알림 전송기 추상 베이스"""

    @abstractmethod
    def send_report(self, report: Report) -> bool:
        """리포트를 알림 채널로 전송.

        구현체는 quiet-day 배너, 빈 리포트 처리를 포함해야 하며,
        성공 시 True, 실패 시 False를 반환한다.
        """
        ...

    def send_error_notification(self, error_message: str) -> bool:
        """에러 알림 전송 (선택).

        기본 구현은 미지원 경고 로그. 필요한 채널만 override.
        Discord는 현재 이 메서드를 override하지 않으므로 no-op.
        """
        logger.warning(
            f"{self.__class__.__name__} does not support error notifications"
        )
        return False

    @staticmethod
    def is_quiet_day(report: Report) -> bool:
        """리포트 기사 수가 임계값 미만인지 판별.

        Returns:
            True면 알림에 "조용한 날" 배너를 포함해야 함.
        """
        return len(report.articles) < QUIET_DAY_THRESHOLD
