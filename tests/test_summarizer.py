"""요약기 테스트"""

import pytest
from unittest.mock import Mock, MagicMock

import anthropic

from src.summarizer import Summarizer, SUMMARIZE_PROMPT
from src.models import Article, Category, Source
from src.config import Config, AnthropicConfig


@pytest.fixture
def mock_anthropic_client(mocker):
    """Anthropic 클라이언트 모킹"""
    mock_client = MagicMock()
    mocker.patch("src.summarizer.anthropic.Anthropic", return_value=mock_client)
    return mock_client


@pytest.fixture
def summarizer(mock_config):
    """Summarizer 인스턴스"""
    return Summarizer(mock_config)


@pytest.fixture
def article_for_summary():
    """요약용 기사"""
    return Article(
        title="New AI Model Released",
        url="https://example.com/ai-model",
        source=Source.ARXIV,
        content="This is a detailed article about a new AI model. " * 50,
    )


class TestSummarizer:
    """Summarizer 테스트"""

    def test_summarizer_init(self, mock_config, mock_anthropic_client):
        """초기화 테스트"""
        summarizer = Summarizer(mock_config)
        assert summarizer.model == mock_config.anthropic.model

    def test_summarize_success(self, mock_config, mock_anthropic_client, article_for_summary):
        """요약 성공"""
        # API 응답 모킹
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"summary": "테스트 요약입니다.", "category": "LLM (대규모 언어 모델)"}')]
        mock_anthropic_client.messages.create.return_value = mock_response

        summarizer = Summarizer(mock_config)
        result = summarizer.summarize(article_for_summary)

        assert result.summary == "테스트 요약입니다."
        assert result.category == Category.LLM

    def test_summarize_empty_content(self, mock_config, mock_anthropic_client):
        """빈 내용 처리"""
        article = Article(
            title="Empty Article",
            url="https://example.com",
            source=Source.ARXIV,
            content="",
        )

        summarizer = Summarizer(mock_config)
        result = summarizer.summarize(article)

        # API 호출 안 함
        mock_anthropic_client.messages.create.assert_not_called()
        assert result.summary == ""

    def test_summarize_api_error(self, mock_config, mock_anthropic_client, article_for_summary):
        """API 에러 처리"""
        mock_anthropic_client.messages.create.side_effect = anthropic.APIError(
            message="API Error",
            request=MagicMock(),
            body=None,
        )

        summarizer = Summarizer(mock_config)
        result = summarizer.summarize(article_for_summary)

        # 에러 시 원본 반환
        assert result.title == article_for_summary.title
        assert result.summary == ""

    def test_summarize_batch(self, mock_config, mock_anthropic_client):
        """배치 요약"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"summary": "요약", "category": "기타"}')]
        mock_anthropic_client.messages.create.return_value = mock_response

        articles = [
            Article(title="Article 1", url="https://example.com/1", source=Source.ARXIV, content="Content 1"),
            Article(title="Article 2", url="https://example.com/2", source=Source.ARXIV, content="Content 2"),
        ]

        summarizer = Summarizer(mock_config)
        results = summarizer.summarize_batch(articles)

        assert len(results) == 2
        assert mock_anthropic_client.messages.create.call_count == 2


class TestParseResponse:
    """응답 파싱 테스트"""

    def test_parse_json_direct(self, mock_config, mock_anthropic_client):
        """직접 JSON 파싱"""
        summarizer = Summarizer(mock_config)

        response = '{"summary": "테스트", "category": "LLM"}'
        result = summarizer._parse_response(response)

        assert result["summary"] == "테스트"
        assert result["category"] == "LLM"

    def test_parse_json_code_block(self, mock_config, mock_anthropic_client):
        """```json 블록 파싱"""
        summarizer = Summarizer(mock_config)

        response = """Here is the summary:
```json
{"summary": "코드 블록 요약", "category": "AI 에이전트 & 자동화"}
```
"""
        result = summarizer._parse_response(response)

        assert result["summary"] == "코드 블록 요약"
        assert result["category"] == "AI 에이전트 & 자동화"

    def test_parse_json_plain_code_block(self, mock_config, mock_anthropic_client):
        """``` 블록 파싱 (json 없이)"""
        summarizer = Summarizer(mock_config)

        response = """Summary:
```
{"summary": "일반 블록", "category": "기타"}
```
"""
        result = summarizer._parse_response(response)

        assert result["summary"] == "일반 블록"

    def test_parse_invalid_json_fallback(self, mock_config, mock_anthropic_client):
        """잘못된 JSON 폴백"""
        summarizer = Summarizer(mock_config)

        response = "This is just plain text without JSON."
        result = summarizer._parse_response(response)

        # 폴백: 텍스트 자체를 요약으로
        assert "plain text" in result["summary"]
        assert result["category"] == "기타"

    def test_parse_long_fallback_truncated(self, mock_config, mock_anthropic_client):
        """긴 폴백 텍스트 자르기"""
        summarizer = Summarizer(mock_config)

        response = "A" * 1000  # 1000자
        result = summarizer._parse_response(response)

        assert len(result["summary"]) <= 503  # 500 + "..."


class TestSummarizePrompt:
    """프롬프트 테스트"""

    def test_prompt_contains_categories(self):
        """프롬프트에 카테고리 포함"""
        for category in Category:
            assert category.value in SUMMARIZE_PROMPT or "{categories}" in SUMMARIZE_PROMPT

    def test_prompt_has_placeholders(self):
        """프롬프트에 필요한 플레이스홀더"""
        assert "{title}" in SUMMARIZE_PROMPT
        assert "{content}" in SUMMARIZE_PROMPT
        assert "{categories}" in SUMMARIZE_PROMPT
