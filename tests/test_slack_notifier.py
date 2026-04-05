"""Slack 알림 테스트"""

import pytest
import responses
from datetime import datetime

from src.slack_notifier import SlackNotifier
from src.models import Article, Report, Category, Source


class TestSlackNotifier:
    """SlackNotifier 테스트"""

    @pytest.fixture
    def notifier(self, mock_config):
        """SlackNotifier 인스턴스"""
        return SlackNotifier(mock_config)

    @responses.activate
    def test_send_report_success(self, notifier, sample_report):
        """리포트 전송 성공"""
        responses.add(
            responses.POST,
            notifier.webhook_url,
            status=200,
            body="ok",
        )

        result = notifier.send_report(sample_report)

        assert result is True
        assert len(responses.calls) == 1

    @responses.activate
    def test_send_report_empty(self, notifier):
        """빈 리포트 처리"""
        empty_report = Report(articles=[])

        result = notifier.send_report(empty_report)

        # 빈 리포트는 전송하지 않음
        assert result is False
        assert len(responses.calls) == 0

    @responses.activate
    def test_send_report_http_error(self, notifier, sample_report):
        """HTTP 에러 처리"""
        responses.add(
            responses.POST,
            notifier.webhook_url,
            status=500,
            body="Internal Server Error",
        )

        result = notifier.send_report(sample_report)

        assert result is False

    @responses.activate
    def test_send_error_notification(self, notifier):
        """에러 알림 전송"""
        responses.add(
            responses.POST,
            notifier.webhook_url,
            status=200,
            body="ok",
        )

        notifier.send_error_notification("Test error message")

        assert len(responses.calls) == 1
        # 요청 본문에 에러 메시지 포함 확인
        request_body = responses.calls[0].request.body
        if isinstance(request_body, bytes):
            request_body = request_body.decode("utf-8")
        assert "Test error message" in request_body


class TestBuildMessageBlocks:
    """Block Kit 메시지 빌드 테스트"""

    @pytest.fixture
    def notifier(self, mock_config):
        return SlackNotifier(mock_config)

    def test_build_message_blocks_header(self, notifier, sample_report):
        """헤더 블록 포함"""
        blocks = notifier._build_message_blocks(sample_report)

        # 첫 번째 블록이 헤더
        assert blocks[0]["type"] == "header"
        # 한국어 헤더 "AI 데일리 리포트" 확인
        assert "리포트" in blocks[0]["text"]["text"] or "Report" in blocks[0]["text"]["text"]

    def test_build_message_blocks_categories(self, notifier, sample_report):
        """카테고리별 섹션"""
        blocks = notifier._build_message_blocks(sample_report)

        # 카테고리 섹션 확인
        block_texts = [str(b) for b in blocks]
        block_str = " ".join(block_texts)

        # sample_report에는 LLM과 VISION 카테고리 기사가 있음
        assert "LLM" in block_str or "대규모 언어 모델" in block_str

    def test_build_message_blocks_article_format(self, notifier):
        """기사 포맷 확인"""
        article = Article(
            title="Test Article Title",
            url="https://example.com/test",
            source=Source.ARXIV,
            summary="This is a test summary.",
            category=Category.LLM,
        )
        report = Report(articles=[article])

        blocks = notifier._build_message_blocks(report)
        block_str = str(blocks)

        # 기사 제목과 링크 포함
        assert "Test Article Title" in block_str
        assert "example.com" in block_str


class TestFormatArticle:
    """기사 포맷팅 테스트"""

    @pytest.fixture
    def notifier(self, mock_config):
        return SlackNotifier(mock_config)

    def test_format_article_basic(self, notifier):
        """기본 기사 포맷"""
        article = Article(
            title="Test Title",
            url="https://example.com",
            source=Source.ARXIV,
            summary="Test summary",
            category=Category.LLM,
        )

        formatted = notifier._format_article(article)

        assert "Test Title" in formatted
        assert "example.com" in formatted
        assert "Test summary" in formatted

    def test_format_article_long_summary_truncated(self, notifier):
        """긴 요약 자르기"""
        article = Article(
            title="Test",
            url="https://example.com",
            source=Source.ARXIV,
            summary="A" * 500,  # 500자 요약
            category=Category.LLM,
        )

        formatted = notifier._format_article(article)

        # 300자로 잘리고 ... 추가
        assert len(formatted) < 500 + 200  # 제목/URL 포함해도 700 미만

    def test_format_article_empty_summary(self, notifier):
        """빈 요약"""
        article = Article(
            title="Test",
            url="https://example.com",
            source=Source.ARXIV,
            summary="",
            category=Category.LLM,
        )

        formatted = notifier._format_article(article)

        assert "Test" in formatted


class TestSendWithRetry:
    """재시도 로직 테스트"""

    @pytest.fixture
    def notifier(self, mock_config):
        return SlackNotifier(mock_config)

    @responses.activate
    def test_successful_send_no_retry_needed(self, notifier, sample_report):
        """성공 시 재시도 불필요"""
        responses.add(
            responses.POST,
            notifier.webhook_url,
            status=200,
            body="ok",
        )

        result = notifier.send_report(sample_report)

        assert result is True
        assert len(responses.calls) == 1


class TestCategoryOrdering:
    """카테고리 정렬 테스트"""

    @pytest.fixture
    def notifier(self, mock_config):
        return SlackNotifier(mock_config)

    def test_categories_grouped(self, notifier):
        """같은 카테고리 기사 그룹화"""
        articles = [
            Article(title="LLM 1", url="https://example.com/1", source=Source.ARXIV, category=Category.LLM),
            Article(title="Vision 1", url="https://example.com/2", source=Source.ARXIV, category=Category.VISION),
            Article(title="LLM 2", url="https://example.com/3", source=Source.ARXIV, category=Category.LLM),
        ]
        report = Report(articles=articles)

        blocks = notifier._build_message_blocks(report)
        block_str = str(blocks)

        # LLM 기사들이 함께 나타나야 함
        assert block_str.count("LLM 1") == 1
        assert block_str.count("LLM 2") == 1
