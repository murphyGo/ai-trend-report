"""Phase 9.1 — BaseNotifier 및 공통 상수 테스트"""

import pytest

from src.models import Article, Report, Source, Category
from src.constants import QUIET_DAY_THRESHOLD, CATEGORY_ORDER
from src.notifier_base import BaseNotifier
from src.slack_notifier import SlackNotifier
from src.discord_notifier import DiscordNotifier
from src.email_notifier import EmailNotifier


class TestConstants:
    """공통 상수가 single source of truth인지 검증"""

    def test_quiet_day_threshold_is_int(self):
        assert isinstance(QUIET_DAY_THRESHOLD, int)
        assert QUIET_DAY_THRESHOLD > 0

    def test_category_order_has_all_categories(self):
        assert set(CATEGORY_ORDER) == set(Category)

    def test_category_order_length(self):
        assert len(CATEGORY_ORDER) == len(Category)

    def test_category_order_no_duplicates(self):
        assert len(CATEGORY_ORDER) == len(set(CATEGORY_ORDER))


class TestBaseNotifier:
    """추상 베이스 클래스"""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseNotifier()

    def test_is_quiet_day_true_when_below_threshold(self):
        report = Report(articles=[])
        assert BaseNotifier.is_quiet_day(report) is True

    def test_is_quiet_day_true_at_boundary(self):
        articles = [
            Article(title=f"t{i}", url=f"https://x.com/{i}", source=Source.ARXIV)
            for i in range(QUIET_DAY_THRESHOLD - 1)
        ]
        report = Report(articles=articles)
        assert BaseNotifier.is_quiet_day(report) is True

    def test_is_quiet_day_false_at_threshold(self):
        articles = [
            Article(title=f"t{i}", url=f"https://x.com/{i}", source=Source.ARXIV)
            for i in range(QUIET_DAY_THRESHOLD)
        ]
        report = Report(articles=articles)
        assert BaseNotifier.is_quiet_day(report) is False

    def test_default_send_error_returns_false(self):
        """send_error_notification의 기본 구현은 False 반환 (미지원 경고)"""

        class ConcreteNotifier(BaseNotifier):
            def send_report(self, report):
                return True

        notifier = ConcreteNotifier()
        assert notifier.send_error_notification("test") is False


class TestInheritance:
    """3개 notifier가 모두 BaseNotifier를 상속하는지 확인"""

    def test_slack_inherits(self):
        assert issubclass(SlackNotifier, BaseNotifier)

    def test_discord_inherits(self):
        assert issubclass(DiscordNotifier, BaseNotifier)

    def test_email_inherits(self):
        assert issubclass(EmailNotifier, BaseNotifier)


class TestNoLocalThresholdConstants:
    """notifier 파일에 QUIET_DAY_THRESHOLD가 로컬 정의되지 않았는지 확인 (M6 회귀)"""

    @pytest.mark.parametrize("module_path", [
        "src/slack_notifier.py",
        "src/discord_notifier.py",
        "src/email_notifier.py",
    ])
    def test_no_local_threshold_definition(self, module_path):
        """각 notifier 파일에 QUIET_DAY_THRESHOLD = (할당)이 없어야 함"""
        from pathlib import Path
        content = Path(module_path).read_text()
        # "QUIET_DAY_THRESHOLD = 3" 같은 할당문이 없어야 함
        # import는 OK: "from .constants import QUIET_DAY_THRESHOLD"
        lines = content.split("\n")
        for line in lines:
            stripped = line.strip()
            # 할당문 체크 (import가 아닌)
            if (
                stripped.startswith("QUIET_DAY_THRESHOLD")
                and "=" in stripped
                and "import" not in stripped
            ):
                pytest.fail(
                    f"{module_path} still has local QUIET_DAY_THRESHOLD assignment: {stripped}"
                )
