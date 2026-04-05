"""수집기 테스트"""

import pytest
import responses
from requests.exceptions import ConnectionError, Timeout

from src.collectors import ArxivCollector, GoogleBlogCollector, AnthropicBlogCollector
from src.collectors.base import BaseCollector
from src.models import Source


class TestBaseCollector:
    """BaseCollector 테스트"""

    def test_collector_user_agent(self):
        """User-Agent 헤더 설정 확인"""
        collector = ArxivCollector()
        assert "User-Agent" in collector.session.headers
        assert "Mozilla" in collector.session.headers["User-Agent"]

    @responses.activate
    def test_fetch_html_success(self):
        """HTML 가져오기 성공"""
        responses.add(
            responses.GET,
            "https://example.com/page",
            body="<html><body>Test</body></html>",
            status=200,
        )

        collector = ArxivCollector()
        soup = collector._fetch_html("https://example.com/page")

        assert soup is not None
        assert soup.find("body").text == "Test"

    @responses.activate
    def test_fetch_html_error(self):
        """HTML 가져오기 실패"""
        responses.add(
            responses.GET,
            "https://example.com/error",
            status=500,
        )

        collector = ArxivCollector()
        soup = collector._fetch_html("https://example.com/error")

        assert soup is None

    @responses.activate
    def test_fetch_text_success(self):
        """텍스트 가져오기 성공"""
        responses.add(
            responses.GET,
            "https://example.com/text",
            body="Plain text content",
            status=200,
        )

        collector = ArxivCollector()
        text = collector._fetch_text("https://example.com/text")

        assert text == "Plain text content"

    @responses.activate
    def test_fetch_text_error(self):
        """텍스트 가져오기 실패"""
        responses.add(
            responses.GET,
            "https://example.com/error",
            status=404,
        )

        collector = ArxivCollector()
        text = collector._fetch_text("https://example.com/error")

        assert text is None


class TestArxivCollector:
    """ArxivCollector 테스트"""

    @pytest.fixture
    def arxiv_rss(self):
        """arXiv RSS 샘플 응답 (RSS 2.0 형식)"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>cs.AI updates on arXiv.org</title>
    <item>
      <title>Test Paper: A Novel Approach (cs.AI)</title>
      <link>http://arxiv.org/abs/2404.00001</link>
      <description>This is the abstract of the test paper about AI.</description>
    </item>
    <item>
      <title>Another Paper on Machine Learning (cs.LG)</title>
      <link>http://arxiv.org/abs/2404.00002</link>
      <description>Abstract for the second paper.</description>
    </item>
  </channel>
</rss>"""

    @responses.activate
    def test_arxiv_collector_fetch_articles(self, arxiv_rss):
        """arXiv 기사 수집"""
        responses.add(
            responses.GET,
            "https://rss.arxiv.org/rss/cs.AI",
            body=arxiv_rss,
            status=200,
        )

        collector = ArxivCollector(categories=["cs.AI"])
        articles = collector.fetch_articles()

        assert len(articles) == 2
        assert articles[0].source == Source.ARXIV
        # 제목에서 (cs.AI) 태그가 제거되어야 함
        assert "(cs.AI)" not in articles[0].title
        assert "Test Paper" in articles[0].title

    @responses.activate
    def test_arxiv_collector_multiple_categories(self, arxiv_rss):
        """여러 카테고리 수집"""
        responses.add(
            responses.GET,
            "https://rss.arxiv.org/rss/cs.AI",
            body=arxiv_rss,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://rss.arxiv.org/rss/cs.LG",
            body=arxiv_rss,
            status=200,
        )

        collector = ArxivCollector(categories=["cs.AI", "cs.LG"])
        articles = collector.fetch_articles()

        # 중복 제거 후 기사 수 확인 (같은 RSS라서 2개)
        assert len(articles) == 2

    @responses.activate
    def test_arxiv_collector_http_error(self):
        """HTTP 에러 처리"""
        responses.add(
            responses.GET,
            "https://rss.arxiv.org/rss/cs.AI",
            status=500,
        )

        collector = ArxivCollector(categories=["cs.AI"])
        articles = collector.fetch_articles()

        assert articles == []

    def test_arxiv_collector_default_categories(self):
        """기본 카테고리"""
        collector = ArxivCollector()
        assert "cs.AI" in collector.categories
        assert "cs.LG" in collector.categories
        assert "cs.CL" in collector.categories


class TestGoogleBlogCollector:
    """GoogleBlogCollector 테스트"""

    @pytest.fixture
    def google_html(self):
        """Google 블로그 HTML 샘플"""
        return """<!DOCTYPE html>
<html>
<head><title>Google AI Blog</title></head>
<body>
<article>
    <a href="/technology/ai/gemini-update">
        <h3>Gemini Update: New Features</h3>
    </a>
    <time datetime="2024-04-05">April 5, 2024</time>
    <p>Preview of the new Gemini features.</p>
</article>
<article>
    <a href="/technology/ai/research-paper">
        <h3>New Research on LLMs</h3>
    </a>
    <time datetime="2024-04-04">April 4, 2024</time>
</article>
</body>
</html>"""

    @responses.activate
    def test_google_collector_fetch_articles(self, google_html):
        """Google 블로그 기사 수집"""
        collector = GoogleBlogCollector()
        # 실제 카테고리 URL에 응답 설정
        for category_path in collector.category_urls:
            url = f"{collector.base_url}{category_path}"
            responses.add(
                responses.GET,
                url,
                body=google_html,
                status=200,
            )

        articles = collector.fetch_articles()

        assert len(articles) >= 1
        assert articles[0].source == Source.GOOGLE_BLOG

    @responses.activate
    def test_google_collector_http_error(self):
        """HTTP 에러 처리"""
        collector = GoogleBlogCollector()
        for category_path in collector.category_urls:
            url = f"{collector.base_url}{category_path}"
            responses.add(
                responses.GET,
                url,
                status=500,
            )

        articles = collector.fetch_articles()

        assert articles == []


class TestAnthropicBlogCollector:
    """AnthropicBlogCollector 테스트"""

    @pytest.fixture
    def anthropic_html(self):
        """Anthropic 뉴스 HTML 샘플"""
        return """<!DOCTYPE html>
<html>
<head><title>Anthropic News</title></head>
<body>
<a href="/news/claude-update">
    <h2>Claude 3.5 Sonnet Released</h2>
</a>
<time datetime="2024-04-05">April 5, 2024</time>
<a href="/news/safety-research">
    <h2>AI Safety Research Update</h2>
</a>
<a href="/about">About Us</a>
</body>
</html>"""

    @responses.activate
    def test_anthropic_collector_fetch_articles(self, anthropic_html):
        """Anthropic 뉴스 수집"""
        responses.add(
            responses.GET,
            "https://www.anthropic.com/news",
            body=anthropic_html,
            status=200,
        )

        collector = AnthropicBlogCollector()
        articles = collector.fetch_articles()

        # /news/ 또는 /research/ 포함 링크만 수집
        assert len(articles) >= 1
        assert articles[0].source == Source.ANTHROPIC_BLOG
        # /about 링크는 제외되어야 함
        for article in articles:
            assert "/news/" in article.url or "/research/" in article.url

    @responses.activate
    def test_anthropic_collector_filters_links(self, anthropic_html):
        """링크 필터링 확인"""
        responses.add(
            responses.GET,
            "https://www.anthropic.com/news",
            body=anthropic_html,
            status=200,
        )

        collector = AnthropicBlogCollector()
        articles = collector.fetch_articles()

        # About 페이지는 제외
        urls = [a.url for a in articles]
        assert not any("/about" in url for url in urls)

    @responses.activate
    def test_anthropic_collector_http_error(self):
        """HTTP 에러 처리"""
        responses.add(
            responses.GET,
            "https://www.anthropic.com/news",
            status=500,
        )

        collector = AnthropicBlogCollector()
        articles = collector.fetch_articles()

        assert articles == []


class TestCollectorIntegration:
    """수집기 통합 테스트"""

    def test_all_collectors_have_source(self):
        """모든 수집기가 source 속성 가짐"""
        arxiv = ArxivCollector()
        google = GoogleBlogCollector()
        anthropic = AnthropicBlogCollector()

        assert arxiv.source == Source.ARXIV
        assert google.source == Source.GOOGLE_BLOG
        assert anthropic.source == Source.ANTHROPIC_BLOG

    def test_all_collectors_inherit_base(self):
        """모든 수집기가 BaseCollector 상속"""
        assert issubclass(ArxivCollector, BaseCollector)
        assert issubclass(GoogleBlogCollector, BaseCollector)
        assert issubclass(AnthropicBlogCollector, BaseCollector)
