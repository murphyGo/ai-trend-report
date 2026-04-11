"""Phase 8.6 Hotfix 회귀 방지 테스트

보안/신뢰성 이슈들에 대한 회귀 테스트:
- H1: search.js 의 escape/safeUrl 셀렉터 존재 여부 (정적 분석)
- H2: email_notifier의 html escape 적용 검증
- H3: email recipients가 Bcc로 전송됨
- H4: MIMEMultipart에 plain text 대안 포함
- H5: sender 빈 경우 username fallback
- H6: search.js에 audience 필드 접근 + AudienceFilter.applyCurrent 호출
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.models import Article, Report, Source, Category
from src.email_notifier import EmailNotifier, _esc, _is_safe_url
from src.config import Config, EmailConfig


# ---- Paths ----
SEARCH_JS = Path(__file__).parent.parent / "src" / "static" / "js" / "search.js"
AUDIENCE_JS = Path(__file__).parent.parent / "src" / "static" / "js" / "audience-filter.js"


# ---- H1 + H6: search.js 정적 분석 ----

class TestSearchJsSecurity:
    """H1: search.js XSS 방지 정적 가드"""

    @pytest.fixture(scope="class")
    def js_source(self) -> str:
        return SEARCH_JS.read_text(encoding="utf-8")

    def test_has_safe_url_helper(self, js_source):
        assert "function safeUrl(" in js_source

    def test_safe_url_rejects_non_http(self, js_source):
        # safeUrl이 http:/https:만 허용하고 나머지는 '#'로 대체
        assert "protocol === 'http:'" in js_source
        assert "protocol === 'https:'" in js_source
        assert "return '#'" in js_source

    def test_url_fields_escaped_and_safed(self, js_source):
        """article.url / report_url은 safeUrl + escapeHtml 모두 거쳐야 함"""
        # 렌더 부분에서 두 URL 필드가 safeUrl(...)로 감싸지는지
        assert "safeUrl(article.url)" in js_source
        assert "safeUrl(article.report_url)" in js_source
        # 그리고 escapeHtml 안에 들어가는지
        assert "escapeHtml(safeUrl(article.url))" in js_source

    def test_source_and_date_escaped(self, js_source):
        """article.source, article.date가 innerHTML 삽입 시 escapeHtml으로 감싸짐"""
        assert "escapeHtml(article.date)" in js_source
        # source_label 또는 source 둘 중 하나라도 escape되면 OK
        assert "escapeHtml(sourceLabel)" in js_source or "escapeHtml(article.source)" in js_source


class TestSearchJsAudienceIntegration:
    """H6: search.js가 audience 필터와 통합됨"""

    @pytest.fixture(scope="class")
    def js_source(self) -> str:
        return SEARCH_JS.read_text(encoding="utf-8")

    def test_data_audience_attr_on_cards(self, js_source):
        """렌더된 카드에 data-audience 속성이 포함됨"""
        assert 'data-audience="${escapeHtml(audienceAttr)}"' in js_source

    def test_applies_current_audience_after_render(self, js_source):
        """displayResults가 끝난 후 AudienceFilter.applyCurrent() 호출"""
        assert "window.AudienceFilter" in js_source
        assert "applyCurrent" in js_source

    def test_audience_filter_exposes_public_api(self):
        """audience-filter.js가 window.AudienceFilter API 객체를 노출"""
        js = AUDIENCE_JS.read_text(encoding="utf-8")
        assert "window.AudienceFilter" in js
        assert "applyCurrent" in js


# ---- H2 + H3 + H4 + H5: email_notifier ----

@pytest.fixture
def email_config_with_sender() -> Config:
    config = Config()
    config.email = EmailConfig(
        enabled=True,
        smtp_host="smtp.test.com",
        smtp_port=587,
        use_tls=True,
        username="user@test.com",
        password="pass",
        sender="sender@test.com",
        recipients=["a@test.com", "b@test.com"],
    )
    return config


@pytest.fixture
def email_config_no_sender() -> Config:
    config = Config()
    config.email = EmailConfig(
        enabled=True,
        smtp_host="smtp.test.com",
        smtp_port=587,
        use_tls=True,
        username="user@test.com",
        password="pass",
        sender="",  # H5: 빈 sender
        recipients=["a@test.com"],
    )
    return config


@pytest.fixture
def malicious_article() -> Article:
    """XSS 페이로드를 포함한 기사 (H2 테스트용)"""
    return Article(
        title='<script>alert("pwn")</script> 정상 제목',
        url="https://safe.com/article",
        source=Source.ARXIV,
        summary='요약 <img src=x onerror="alert(1)">',
        category=Category.LLM,
    )


@pytest.fixture
def sample_report_malicious(malicious_article) -> Report:
    return Report(articles=[malicious_article, malicious_article, malicious_article])


class TestEmailEscaping:
    """H2: HTML escape 적용"""

    def test_esc_helper_escapes_script_tags(self):
        assert "&lt;script&gt;" in _esc("<script>x</script>")

    def test_esc_helper_none_safe(self):
        assert _esc(None) == ""

    def test_esc_quotes_for_attributes(self):
        # quote=True로 " 와 ' 모두 escape
        assert "&quot;" in _esc('"')
        assert "&#x27;" in _esc("'")

    def test_is_safe_url(self):
        assert _is_safe_url("https://x.com/")
        assert _is_safe_url("http://x.com/")
        assert not _is_safe_url("javascript:alert(1)")
        assert not _is_safe_url("data:text/html,<script>")
        assert not _is_safe_url("")
        assert not _is_safe_url(None)

    def test_build_html_message_escapes_malicious_title(
        self, email_config_with_sender, sample_report_malicious
    ):
        notifier = EmailNotifier(email_config_with_sender)
        html_out = notifier._build_html_message(sample_report_malicious)

        # raw <script> 또는 <img onerror= 는 본문에 있어선 안 됨
        assert "<script>alert" not in html_out
        assert 'onerror="alert' not in html_out
        # escape된 형태는 OK
        assert "&lt;script&gt;" in html_out

    def test_error_notification_escapes_message(
        self, email_config_with_sender
    ):
        notifier = EmailNotifier(email_config_with_sender)
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            notifier.send_error_notification("<script>alert('e')</script>")
            sent = mock_server.send_message.call_args[0][0]
            # multipart/alternative → html 파트에서 확인
            html_part = None
            for part in sent.walk():
                if part.get_content_type() == "text/html":
                    html_part = part.get_payload(decode=True).decode()
                    break
            assert html_part is not None
            assert "<script>alert" not in html_part
            assert "&lt;script&gt;" in html_part


class TestEmailBccPrivacy:
    """H3: 수신자 주소가 Bcc로 숨겨짐"""

    def test_recipients_in_bcc_not_to(
        self, email_config_with_sender, sample_report_malicious
    ):
        notifier = EmailNotifier(email_config_with_sender)
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            notifier.send_report(sample_report_malicious)
            sent = mock_server.send_message.call_args[0][0]

            # To에는 sender, 수신자 주소 없음
            assert sent["To"] == "sender@test.com"
            assert "a@test.com" not in (sent["To"] or "")
            assert "b@test.com" not in (sent["To"] or "")

            # Bcc에 실제 수신자 포함
            assert "a@test.com" in sent["Bcc"]
            assert "b@test.com" in sent["Bcc"]

    def test_envelope_recipients_include_actual_recipients(
        self, email_config_with_sender, sample_report_malicious
    ):
        """SMTP envelope (to_addrs)에는 실제 수신자가 있어야 전송됨"""
        notifier = EmailNotifier(email_config_with_sender)
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            notifier.send_report(sample_report_malicious)
            kwargs = mock_server.send_message.call_args[1]
            assert kwargs["to_addrs"] == ["a@test.com", "b@test.com"]
            assert kwargs["from_addr"] == "sender@test.com"


class TestEmailPlainTextAlternative:
    """H4: multipart/alternative에 plain text 파트 포함"""

    def test_multipart_has_plain_and_html(
        self, email_config_with_sender, sample_report_malicious
    ):
        notifier = EmailNotifier(email_config_with_sender)
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            notifier.send_report(sample_report_malicious)
            sent = mock_server.send_message.call_args[0][0]

            content_types = [
                part.get_content_type()
                for part in sent.walk()
                if part.get_content_maintype() == "text"
            ]
            assert "text/plain" in content_types
            assert "text/html" in content_types

    def test_plain_text_contains_article_titles(self, email_config_with_sender):
        notifier = EmailNotifier(email_config_with_sender)
        report = Report(articles=[
            Article(title="Test Article Alpha", url="https://x.com/1",
                    source=Source.ARXIV, summary="요약 A", category=Category.LLM),
            Article(title="Test Article Beta", url="https://x.com/2",
                    source=Source.ARXIV, summary="요약 B", category=Category.LLM),
            Article(title="Test Article Gamma", url="https://x.com/3",
                    source=Source.ARXIV, summary="요약 C", category=Category.LLM),
        ])
        plain = notifier._build_plain_message(report)
        assert "Test Article Alpha" in plain
        assert "Test Article Beta" in plain
        assert "Test Article Gamma" in plain
        assert "요약 A" in plain

    def test_plain_text_shows_quiet_day_when_empty(self, email_config_with_sender):
        notifier = EmailNotifier(email_config_with_sender)
        plain = notifier._build_plain_message(Report(articles=[]))
        assert "조용한 날" in plain


class TestEmailSenderFallback:
    """H5: sender 빈 경우 username으로 fallback"""

    def test_from_uses_username_when_sender_empty(
        self, email_config_no_sender
    ):
        notifier = EmailNotifier(email_config_no_sender)
        assert notifier._effective_sender() == "user@test.com"

    def test_sent_message_from_header_uses_fallback(
        self, email_config_no_sender
    ):
        notifier = EmailNotifier(email_config_no_sender)
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            report = Report(articles=[
                Article(title="a", url="https://x.com/1",
                        source=Source.ARXIV, summary="s", category=Category.LLM)
                for _ in range(3)
            ])
            notifier.send_report(report)

            sent = mock_server.send_message.call_args[0][0]
            assert sent["From"] == "user@test.com"
            kwargs = mock_server.send_message.call_args[1]
            assert kwargs["from_addr"] == "user@test.com"

    def test_sender_preferred_when_both_set(self, email_config_with_sender):
        notifier = EmailNotifier(email_config_with_sender)
        assert notifier._effective_sender() == "sender@test.com"
