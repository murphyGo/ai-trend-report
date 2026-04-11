"""이메일 알림 테스트"""

import pytest
import smtplib
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.email_notifier import EmailNotifier
from src.models import Article, Report, Category, Source
from src.config import Config, EmailConfig


class TestEmailNotifier:
    """EmailNotifier 테스트"""

    @pytest.fixture
    def email_config(self):
        """이메일 설정 fixture"""
        config = Config()
        config.email = EmailConfig(
            enabled=True,
            smtp_host="smtp.test.com",
            smtp_port=587,
            use_tls=True,
            username="test@test.com",
            password="testpassword",
            sender="sender@test.com",
            recipients=["recipient1@test.com", "recipient2@test.com"],
        )
        return config

    @pytest.fixture
    def notifier(self, email_config):
        """EmailNotifier 인스턴스"""
        return EmailNotifier(email_config)

    @patch('smtplib.SMTP')
    def test_send_report_success(self, mock_smtp, notifier, sample_report):
        """리포트 전송 성공"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = notifier.send_report(sample_report)

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@test.com", "testpassword")
        mock_server.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    def test_send_report_empty_quiet_day(self, mock_smtp, notifier):
        """빈 리포트 처리 — Phase 8.5에서 quiet-day 배너 포함해 전송하도록 변경"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        empty_report = Report(articles=[])
        result = notifier.send_report(empty_report)

        # 빈 리포트도 quiet-day 배너와 함께 성공 전송
        assert result is True
        mock_smtp.assert_called_once()
        mock_server.send_message.assert_called_once()

    @patch('smtplib.SMTP')
    def test_send_report_smtp_error(self, mock_smtp, notifier, sample_report):
        """SMTP 에러 처리"""
        mock_smtp.return_value.__enter__.side_effect = smtplib.SMTPException("SMTP Error")

        result = notifier.send_report(sample_report)

        assert result is False

    @patch('smtplib.SMTP')
    def test_send_report_no_recipients(self, mock_smtp, email_config, sample_report):
        """수신자 없음"""
        email_config.email.recipients = []
        notifier = EmailNotifier(email_config)

        result = notifier.send_report(sample_report)

        assert result is False
        mock_smtp.assert_not_called()

    @patch('smtplib.SMTP')
    def test_send_report_custom_recipients(self, mock_smtp, email_config, sample_report):
        """커스텀 수신자 지정 — Phase 8.6: Bcc로 전송되어 To에는 sender, Bcc에 수신자"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        custom_recipients = ["custom@test.com"]
        notifier = EmailNotifier(email_config, recipients=custom_recipients)

        result = notifier.send_report(sample_report)

        assert result is True
        # Phase 8.6 — 수신자는 프라이버시 위해 Bcc로 숨김
        sent_message = mock_server.send_message.call_args[0][0]
        assert sent_message['To'] == "sender@test.com"  # self-addressed
        assert sent_message['Bcc'] == "custom@test.com"
        # envelope recipients가 실제 수신자를 포함해야 함 (send_message의 to_addrs kwarg)
        kwargs = mock_server.send_message.call_args[1]
        assert kwargs.get("to_addrs") == custom_recipients

    @patch('smtplib.SMTP')
    def test_send_error_notification(self, mock_smtp, notifier):
        """에러 알림 전송"""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = notifier.send_error_notification("Test error message")

        assert result is True
        mock_server.send_message.assert_called_once()

        # 전송된 메시지 내용 확인
        sent_message = mock_server.send_message.call_args[0][0]
        assert "[AI Report] 오류 발생" in sent_message['Subject']


class TestBuildHtmlMessage:
    """HTML 메시지 빌드 테스트"""

    @pytest.fixture
    def notifier(self):
        config = Config()
        config.email = EmailConfig(
            sender="test@test.com",
            recipients=["recipient@test.com"],
        )
        return EmailNotifier(config)

    def test_build_html_message_header(self, notifier, sample_report):
        """헤더 포함 확인"""
        html = notifier._build_html_message(sample_report)

        assert "AI 데일리 리포트" in html
        assert "<!DOCTYPE html>" in html

    def test_build_html_message_categories(self, notifier, sample_report):
        """카테고리별 섹션"""
        html = notifier._build_html_message(sample_report)

        # sample_report에는 LLM과 VISION 카테고리 기사가 있음
        assert "category-title" in html

    def test_build_html_message_article_format(self, notifier):
        """기사 포맷 확인"""
        article = Article(
            title="Test Article Title",
            url="https://example.com/test",
            source=Source.ARXIV,
            summary="This is a test summary.",
            category=Category.LLM,
        )
        report = Report(articles=[article])

        html = notifier._build_html_message(report)

        # 기사 제목과 링크 포함
        assert "Test Article Title" in html
        assert "example.com/test" in html
        assert "test summary" in html

    def test_build_html_message_footer(self, notifier, sample_report):
        """푸터 확인"""
        html = notifier._build_html_message(sample_report)

        assert "AI Report Automation Service" in html
        assert f"{len(sample_report.articles)}개의 기사" in html


class TestFormatArticleHtml:
    """기사 HTML 포맷팅 테스트"""

    @pytest.fixture
    def notifier(self):
        config = Config()
        config.email = EmailConfig(
            sender="test@test.com",
            recipients=["recipient@test.com"],
        )
        return EmailNotifier(config)

    def test_format_article_basic(self, notifier):
        """기본 기사 포맷"""
        article = Article(
            title="Test Title",
            url="https://example.com",
            source=Source.ARXIV,
            summary="Test summary",
            category=Category.LLM,
        )

        formatted = notifier._format_article_html(article)

        assert "Test Title" in formatted
        assert "example.com" in formatted
        assert "Test summary" in formatted
        assert "source-arxiv" in formatted

    def test_format_article_long_summary_truncated(self, notifier):
        """긴 요약 자르기"""
        article = Article(
            title="Test",
            url="https://example.com",
            source=Source.ARXIV,
            summary="A" * 600,  # 600자 요약
            category=Category.LLM,
        )

        formatted = notifier._format_article_html(article)

        # 500자로 잘리고 ... 추가
        assert "A" * 500 in formatted
        assert "..." in formatted

    def test_format_article_empty_summary(self, notifier):
        """빈 요약"""
        article = Article(
            title="Test",
            url="https://example.com",
            source=Source.ARXIV,
            summary="",
            category=Category.LLM,
        )

        formatted = notifier._format_article_html(article)

        assert "Test" in formatted
        assert "(요약 없음)" in formatted

    def test_format_article_source_badges(self, notifier):
        """소스별 배지 스타일"""
        sources = [
            (Source.ARXIV, "source-arxiv", "arXiv"),
            (Source.GOOGLE_BLOG, "source-google", "Google"),
            (Source.ANTHROPIC_BLOG, "source-anthropic", "Anthropic"),
            (Source.OPENAI_BLOG, "source-openai", "OpenAI"),
            (Source.HUGGINGFACE_BLOG, "source-huggingface", "HuggingFace"),
            (Source.KOREAN_NEWS, "source-korean", "한국 뉴스"),
        ]

        for source, class_name, display_name in sources:
            article = Article(
                title="Test",
                url="https://example.com",
                source=source,
                category=Category.LLM,
            )
            formatted = notifier._format_article_html(article)
            assert class_name in formatted
            assert display_name in formatted


class TestBuildSubject:
    """이메일 제목 테스트"""

    @pytest.fixture
    def notifier(self):
        config = Config()
        config.email = EmailConfig(
            sender="test@test.com",
            recipients=["recipient@test.com"],
        )
        return EmailNotifier(config)

    def test_build_subject_quiet_day(self, notifier, sample_report):
        """기사 수 < 3인 경우 quiet-day prefix (sample_report는 2개)"""
        subject = notifier._build_subject(sample_report)

        # Phase 8.5: 2개 기사 → quiet-day prefix
        assert "조용한 날" in subject
        assert "AI 데일리 리포트" in subject
        assert f"{len(sample_report.articles)}개 기사" in subject

    def test_build_subject_normal(self, notifier):
        """기사 수 >= 3인 경우 일반 prefix"""
        from src.models import Article, Report, Source, Category
        articles = [
            Article(title=f"t{i}", url=f"https://x.com/{i}", source=Source.ARXIV)
            for i in range(5)
        ]
        report = Report(articles=articles)
        subject = notifier._build_subject(report)

        assert "[AI Report]" in subject
        assert "조용한 날" not in subject
        assert "5개 기사" in subject


class TestEmailConfig:
    """EmailConfig 테스트"""

    def test_email_config_defaults(self):
        """기본값 테스트"""
        config = EmailConfig()

        assert config.enabled is False
        assert config.smtp_host == "smtp.gmail.com"
        assert config.smtp_port == 587
        assert config.use_tls is True
        assert config.username == ""
        assert config.password == ""
        assert config.sender == ""
        assert config.recipients == []  # 기본값은 빈 리스트 (환경 변수에서 로드)

    def test_email_config_custom_values(self):
        """커스텀 값 테스트"""
        config = EmailConfig(
            enabled=True,
            smtp_host="smtp.custom.com",
            smtp_port=465,
            use_tls=False,
            username="user@custom.com",
            password="secret",
            sender="sender@custom.com",
            recipients=["a@test.com", "b@test.com"],
        )

        assert config.enabled is True
        assert config.smtp_host == "smtp.custom.com"
        assert config.smtp_port == 465
        assert config.use_tls is False
        assert config.username == "user@custom.com"
        assert config.password == "secret"
        assert config.sender == "sender@custom.com"
        assert config.recipients == ["a@test.com", "b@test.com"]


class TestConfigEmailLoading:
    """Config의 이메일 설정 로딩 테스트"""

    def test_config_email_from_yaml(self, tmp_path, monkeypatch):
        """YAML에서 이메일 설정 로드"""
        # 환경 변수 클리어 (YAML 값 테스트를 위해)
        # setenv("")로 빈 문자열 설정 - load_dotenv 이후에도 적용됨
        monkeypatch.setenv("EMAIL_RECIPIENTS", "")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
email:
  enabled: true
  smtp_host: smtp.custom.com
  smtp_port: 465
  sender: custom@example.com
  recipients:
    - user1@example.com
    - user2@example.com
""")

        config = Config.load(config_file)

        assert config.email.enabled is True
        assert config.email.smtp_host == "smtp.custom.com"
        assert config.email.smtp_port == 465
        assert config.email.sender == "custom@example.com"
        assert config.email.recipients == ["user1@example.com", "user2@example.com"]

    def test_config_email_env_override(self, tmp_path, monkeypatch):
        """환경 변수가 YAML보다 우선"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
email:
  username: yaml_user
  password: yaml_pass
""")

        monkeypatch.setenv("EMAIL_USERNAME", "env_user")
        monkeypatch.setenv("EMAIL_PASSWORD", "env_pass")

        config = Config.load(config_file)

        # 환경 변수 값이 우선
        assert config.email.username == "env_user"
        assert config.email.password == "env_pass"

    def test_config_email_resolve_env(self, tmp_path, monkeypatch):
        """${ENV_VAR} 형식 치환"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
email:
  username: ${MY_EMAIL_USER}
  password: ${MY_EMAIL_PASS}
""")

        monkeypatch.setenv("MY_EMAIL_USER", "resolved_user")
        monkeypatch.setenv("MY_EMAIL_PASS", "resolved_pass")

        config = Config.load(config_file)

        assert config.email.username == "resolved_user"
        assert config.email.password == "resolved_pass"

    def test_config_email_recipients_from_env(self, tmp_path, monkeypatch):
        """EMAIL_RECIPIENTS 환경 변수에서 수신자 로드"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")  # 빈 설정 파일

        monkeypatch.setenv("EMAIL_RECIPIENTS", "user1@test.com, user2@test.com, user3@test.com")

        config = Config.load(config_file)

        assert len(config.email.recipients) == 3
        assert "user1@test.com" in config.email.recipients
        assert "user2@test.com" in config.email.recipients
        assert "user3@test.com" in config.email.recipients
