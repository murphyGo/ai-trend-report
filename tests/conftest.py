"""pytest 공통 fixtures"""

import pytest
from datetime import datetime

from src.models import Article, Report, Category, Source
from src.config import Config, AnthropicConfig, SlackConfig, CollectorsConfig, LoggingConfig


@pytest.fixture
def sample_article() -> Article:
    """샘플 기사 fixture"""
    return Article(
        id="test-article-001",
        title="테스트 기사 제목",
        url="https://example.com/article/1",
        source=Source.ARXIV,
        content="이것은 테스트 기사의 내용입니다.",
        published_at=datetime(2024, 4, 5, 12, 0, 0),
        summary="테스트 기사의 요약입니다.",
        category=Category.LLM,
    )


@pytest.fixture
def sample_article_dict() -> dict:
    """샘플 기사 딕셔너리 fixture"""
    return {
        "id": "test-article-001",
        "title": "테스트 기사 제목",
        "url": "https://example.com/article/1",
        "source": "arxiv",
        "content": "이것은 테스트 기사의 내용입니다.",
        "published_at": "2024-04-05T12:00:00",
        "summary": "테스트 기사의 요약입니다.",
        "category": "LLM (대규모 언어 모델)",
    }


@pytest.fixture
def sample_report(sample_article) -> Report:
    """샘플 리포트 fixture"""
    articles = [
        sample_article,
        Article(
            id="test-article-002",
            title="두 번째 테스트 기사",
            url="https://example.com/article/2",
            source=Source.GOOGLE_BLOG,
            content="두 번째 기사�� 내용",
            summary="두 번째 기사 요약",
            category=Category.VISION,
        ),
    ]
    return Report(
        id="test-report-001",
        articles=articles,
        created_at=datetime(2024, 4, 5, 9, 0, 0),
    )


@pytest.fixture
def mock_config() -> Config:
    """모킹용 설정 fixture"""
    config = Config()
    config.anthropic = AnthropicConfig(
        api_key="test-api-key",
        model="claude-sonnet-4-20250514",
    )
    config.slack = SlackConfig(
        webhook_url="https://hooks.slack.com/services/test/webhook",
    )
    config.logging = LoggingConfig(
        level="INFO",
        log_file=None,
    )
    return config


@pytest.fixture
def arxiv_rss_response() -> str:
    """arXiv RSS 응답 샘플"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:dc="http://purl.org/dc/elements/1.1/"
         xmlns="http://purl.org/rss/1.0/">
  <channel>
    <title>cs.AI updates on arXiv.org</title>
  </channel>
  <item>
    <title>Test Paper Title (cs.AI)</title>
    <link>http://arxiv.org/abs/2404.00001</link>
    <dc:creator>Author Name</dc:creator>
    <description>This is the abstract of the test paper.</description>
  </item>
</rdf:RDF>"""


@pytest.fixture
def google_blog_html() -> str:
    """Google 블로그 HTML 응답 샘플"""
    return """<!DOCTYPE html>
<html>
<head><title>Google AI Blog</title></head>
<body>
<article>
    <a href="/technology/ai/test-article">
        <h3>Test Google AI Article</h3>
    </a>
    <time datetime="2024-04-05">April 5, 2024</time>
</article>
</body>
</html>"""


@pytest.fixture
def anthropic_news_html() -> str:
    """Anthropic 뉴스 HTML 응답 샘플"""
    return """<!DOCTYPE html>
<html>
<head><title>Anthropic News</title></head>
<body>
<a href="/news/test-article">
    <h2>Test Anthropic News Article</h2>
</a>
<time datetime="2024-04-05">April 5, 2024</time>
</body>
</html>"""
