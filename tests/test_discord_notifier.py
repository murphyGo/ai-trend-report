"""Discord 알림 테스트"""

import pytest
import responses
from datetime import datetime

from src.discord_notifier import DiscordNotifier, EMBED_COLOR_DEFAULT, EMBED_COLOR_ERROR
from src.models import Article, Report, Category, Source
from src.config import Config, DiscordConfig


class TestDiscordNotifier:
    """DiscordNotifier 테스트"""

    @pytest.fixture
    def discord_config(self):
        """Discord 설정 fixture"""
        config = Config()
        config.discord = DiscordConfig(
            webhook_url="https://discord.com/api/webhooks/test/webhook"
        )
        return config

    @pytest.fixture
    def notifier(self, discord_config):
        """DiscordNotifier 인스턴스"""
        return DiscordNotifier(discord_config)

    @responses.activate
    def test_send_report_success(self, notifier, sample_report):
        """리포트 전송 성공"""
        responses.add(
            responses.POST,
            notifier.webhook_url,
            status=204,  # Discord returns 204 No Content on success
            body="",
        )

        result = notifier.send_report(sample_report)

        assert result is True
        assert len(responses.calls) >= 1

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

    def test_send_report_no_webhook_url(self, sample_report):
        """Webhook URL 없음"""
        config = Config()
        config.discord = DiscordConfig(webhook_url="")
        notifier = DiscordNotifier(config)

        result = notifier.send_report(sample_report)

        assert result is False

    @responses.activate
    def test_send_report_custom_webhook_url(self, discord_config, sample_report):
        """커스텀 Webhook URL 사용"""
        custom_url = "https://discord.com/api/webhooks/custom/url"
        responses.add(
            responses.POST,
            custom_url,
            status=204,
            body="",
        )

        notifier = DiscordNotifier(discord_config, webhook_url=custom_url)
        result = notifier.send_report(sample_report)

        assert result is True
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == custom_url

    @responses.activate
    def test_send_error_notification(self, notifier):
        """에러 알림 전송"""
        responses.add(
            responses.POST,
            notifier.webhook_url,
            status=204,
            body="",
        )

        result = notifier.send_error_notification("Test error message")

        assert result is True
        assert len(responses.calls) == 1
        # 요청 본문에 에러 메시지 포함 확인
        request_body = responses.calls[0].request.body
        if isinstance(request_body, bytes):
            request_body = request_body.decode("utf-8")
        assert "Test error message" in request_body


class TestBuildEmbeds:
    """Embed 메시지 빌드 테스트"""

    @pytest.fixture
    def notifier(self):
        config = Config()
        config.discord = DiscordConfig(
            webhook_url="https://discord.com/api/webhooks/test/webhook"
        )
        return DiscordNotifier(config)

    def test_build_embeds_header(self, notifier, sample_report):
        """헤더 embed 포함"""
        embeds = notifier._build_embeds(sample_report)

        # 첫 번째 embed가 헤더
        assert len(embeds) >= 1
        assert "리포트" in embeds[0]["title"]
        assert embeds[0]["color"] == EMBED_COLOR_DEFAULT

    def test_build_embeds_categories(self, notifier, sample_report):
        """카테고리별 embed"""
        embeds = notifier._build_embeds(sample_report)

        # 헤더 + 카테고리 embeds
        assert len(embeds) >= 2

        # 카테고리 embed 확인
        embed_titles = [e.get("title", "") for e in embeds[1:]]
        embed_str = " ".join(embed_titles)

        # sample_report에는 LLM과 VISION 카테고리 기사가 있음
        assert "LLM" in embed_str or "대규모 언어 모델" in embed_str

    def test_build_embeds_article_format(self, notifier):
        """기사 포맷 확인"""
        article = Article(
            title="Test Article Title",
            url="https://example.com/test",
            source=Source.ARXIV,
            summary="This is a test summary.",
            category=Category.LLM,
        )
        report = Report(articles=[article])

        embeds = notifier._build_embeds(report)

        # 카테고리 embed에서 기사 확인
        embed_str = str(embeds)
        assert "Test Article Title" in embed_str
        assert "example.com" in embed_str

    def test_build_embeds_timestamp(self, notifier, sample_report):
        """타임스탬프 포함"""
        embeds = notifier._build_embeds(sample_report)

        # 헤더 embed에 타임스탬프 있음
        assert "timestamp" in embeds[0]


class TestBuildCategoryEmbed:
    """카테고리 embed 테스트"""

    @pytest.fixture
    def notifier(self):
        config = Config()
        config.discord = DiscordConfig(
            webhook_url="https://discord.com/api/webhooks/test/webhook"
        )
        return DiscordNotifier(config)

    def test_build_category_embed_basic(self, notifier):
        """기본 카테고리 embed"""
        articles = [
            Article(
                title="Test LLM Article",
                url="https://example.com/llm",
                source=Source.ARXIV,
                summary="Test summary",
                category=Category.LLM,
            )
        ]

        embed = notifier._build_category_embed(Category.LLM, articles)

        assert "LLM" in embed["title"] or "대규모 언어 모델" in embed["title"]
        assert "Test LLM Article" in embed["description"]
        assert embed["color"] is not None

    def test_build_category_embed_multiple_articles(self, notifier):
        """여러 기사"""
        articles = [
            Article(
                title=f"Article {i}",
                url=f"https://example.com/{i}",
                source=Source.ARXIV,
                category=Category.LLM,
            )
            for i in range(5)
        ]

        embed = notifier._build_category_embed(Category.LLM, articles)

        for i in range(5):
            assert f"Article {i}" in embed["description"]

    def test_build_category_embed_max_articles(self, notifier):
        """최대 10개 기사 제한"""
        articles = [
            Article(
                title=f"Article {i}",
                url=f"https://example.com/{i}",
                source=Source.ARXIV,
                category=Category.LLM,
            )
            for i in range(15)
        ]

        embed = notifier._build_category_embed(Category.LLM, articles)

        # 10개까지만 포함
        assert "Article 0" in embed["description"]
        assert "Article 9" in embed["description"]
        # 11번째 이후는 포함되지 않음
        assert "Article 10" not in embed["description"]
        # 추가 기사 안내
        assert "외 5개 기사" in embed["description"]


class TestFormatArticle:
    """기사 포맷팅 테스트"""

    @pytest.fixture
    def notifier(self):
        config = Config()
        config.discord = DiscordConfig(
            webhook_url="https://discord.com/api/webhooks/test/webhook"
        )
        return DiscordNotifier(config)

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
        # Discord 마크다운 링크 형식
        assert "[Test Title](https://example.com)" in formatted

    def test_format_article_long_summary_truncated(self, notifier):
        """긴 요약 자르기"""
        article = Article(
            title="Test",
            url="https://example.com",
            source=Source.ARXIV,
            summary="A" * 300,  # 300자 요약
            category=Category.LLM,
        )

        formatted = notifier._format_article(article)

        # 200자로 잘리고 ... 추가
        assert "..." in formatted
        assert len(formatted) < 400

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
        assert "(요약 없음)" in formatted

    def test_format_article_source_labels(self, notifier):
        """소스별 라벨"""
        sources = [
            (Source.ARXIV, "arXiv"),
            (Source.GOOGLE_BLOG, "Google"),
            (Source.ANTHROPIC_BLOG, "Anthropic"),
            (Source.OPENAI_BLOG, "OpenAI"),
            (Source.HUGGINGFACE_BLOG, "HuggingFace"),
            (Source.KOREAN_NEWS, "한국 뉴스"),
        ]

        for source, expected_label in sources:
            article = Article(
                title="Test",
                url="https://example.com",
                source=source,
                category=Category.LLM,
            )
            formatted = notifier._format_article(article)
            assert expected_label in formatted


class TestDiscordConfig:
    """DiscordConfig 테스트"""

    def test_discord_config_defaults(self):
        """기본값 테스트"""
        config = DiscordConfig()

        assert config.webhook_url == ""

    def test_discord_config_custom_values(self):
        """커스텀 값 테스트"""
        config = DiscordConfig(
            webhook_url="https://discord.com/api/webhooks/123/abc"
        )

        assert config.webhook_url == "https://discord.com/api/webhooks/123/abc"


class TestConfigDiscordLoading:
    """Config의 Discord 설정 로딩 테스트"""

    def test_config_discord_from_yaml(self, tmp_path, monkeypatch):
        """YAML에서 Discord 설정 로드"""
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
discord:
  webhook_url: https://discord.com/api/webhooks/yaml/test
""")

        config = Config.load(config_file)

        assert config.discord.webhook_url == "https://discord.com/api/webhooks/yaml/test"

    def test_config_discord_env_override(self, tmp_path, monkeypatch):
        """환경 변수가 YAML보다 우선"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
discord:
  webhook_url: https://discord.com/api/webhooks/yaml/test
""")

        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/env/test")

        config = Config.load(config_file)

        # 환경 변수 값이 우선
        assert config.discord.webhook_url == "https://discord.com/api/webhooks/env/test"

    def test_config_discord_resolve_env(self, tmp_path, monkeypatch):
        """${ENV_VAR} 형식 치환"""
        monkeypatch.setenv("DISCORD_WEBHOOK_URL", "")  # 환경 변수 클리어
        monkeypatch.setenv("MY_DISCORD_WEBHOOK", "https://discord.com/api/webhooks/resolved/test")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
discord:
  webhook_url: ${MY_DISCORD_WEBHOOK}
""")

        config = Config.load(config_file)

        assert config.discord.webhook_url == "https://discord.com/api/webhooks/resolved/test"
