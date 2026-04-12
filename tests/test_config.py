"""설정 관리 테스트"""

import pytest
import os
from pathlib import Path

from src.config import Config, LoggingConfig


class TestConfig:
    """Config 클래스 테스트"""

    def test_config_default_values(self):
        """기본 설정값 확인"""
        config = Config()
        assert config.anthropic.model == "claude-sonnet-4-6"
        assert config.anthropic.api_key == ""
        assert config.slack.webhook_url == ""
        assert config.logging.level == "INFO"
        assert config.logging.log_file is None

    def test_config_collectors_default(self):
        """수집기 기본 설정"""
        config = Config()
        assert config.collectors.arxiv.enabled is True
        assert config.collectors.google_blog.enabled is True
        assert config.collectors.anthropic_blog.enabled is True
        assert "cs.AI" in config.collectors.arxiv.categories

    def test_config_resolve_env_with_env_syntax(self):
        """${ENV_VAR} 형식 환경 변수 치환"""
        os.environ["TEST_VAR"] = "test_value"
        try:
            result = Config._resolve_env("${TEST_VAR}")
            assert result == "test_value"
        finally:
            del os.environ["TEST_VAR"]

    def test_config_resolve_env_missing_var(self):
        """존재하지 않는 환경 변수"""
        result = Config._resolve_env("${NONEXISTENT_VAR}")
        assert result == ""

    def test_config_resolve_env_plain_string(self):
        """일반 문자열은 그대로 반환"""
        result = Config._resolve_env("plain_string")
        assert result == "plain_string"

    def test_config_validate_missing_api_key(self):
        """API 키 누락 검증"""
        config = Config()
        config.anthropic.api_key = ""
        config.slack.webhook_url = "https://hooks.slack.com/test"
        errors = config.validate()
        assert any("ANTHROPIC_API_KEY" in e for e in errors)

    def test_config_validate_api_mode_no_slack_check(self):
        """Phase 9.2: validate_api_mode는 Slack 설정을 검사하지 않음"""
        config = Config()
        config.anthropic.api_key = "test-key"
        config.slack.webhook_url = ""
        errors = config.validate_api_mode()
        assert len(errors) == 0  # API 키만 있으면 통과

    def test_config_validate_all_valid(self):
        """모든 설정 유효"""
        config = Config()
        config.anthropic.api_key = "test-key"
        config.slack.webhook_url = "https://hooks.slack.com/test"
        errors = config.validate_api_mode()
        assert len(errors) == 0

    def test_config_validate_notifications_slack_only(self):
        """Slack만 설정해도 알림 검증 통과"""
        config = Config()
        config.slack.webhook_url = "https://hooks.slack.com/test"
        errors = config.validate_notifications()
        assert len(errors) == 0

    def test_config_validate_notifications_discord_only(self):
        """Discord만 설정해도 알림 검증 통과"""
        config = Config()
        config.discord.webhook_url = "https://discord.com/api/webhooks/test"
        errors = config.validate_notifications()
        assert len(errors) == 0

    def test_config_validate_notifications_email_only(self):
        """Email만 설정해도 알림 검증 통과"""
        config = Config()
        config.email.username = "user@test.com"
        config.email.password = "pass"
        config.email.recipients = ["a@test.com"]
        errors = config.validate_notifications()
        assert len(errors) == 0

    def test_config_validate_notifications_none_fails(self):
        """아무 채널도 없으면 검증 실패"""
        config = Config()
        errors = config.validate_notifications()
        assert len(errors) == 1
        assert "최소 1개" in errors[0]

    def test_config_disabled_sources(self):
        """disabled_sources 필드 기본값은 빈 리스트"""
        config = Config()
        assert config.collectors.disabled_sources == []

    def test_config_load_with_env_vars(self, tmp_path, monkeypatch):
        """환경 변수에서 설정 로드"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env-api-key")
        monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/env")

        # 빈 config 파일 생성
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")

        config = Config.load(config_file)
        assert config.anthropic.api_key == "env-api-key"
        assert config.slack.webhook_url == "https://hooks.slack.com/env"

    def test_config_load_from_yaml(self, tmp_path, monkeypatch):
        """YAML 파일에서 설정 로드"""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

        config_content = """
anthropic:
  model: claude-3-opus

collectors:
  arxiv:
    enabled: false
    categories:
      - cs.AI

logging:
  level: DEBUG
  log_file: logs/test.log
"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = Config.load(config_file)
        assert config.anthropic.model == "claude-3-opus"
        assert config.collectors.arxiv.enabled is False
        assert config.logging.level == "DEBUG"
        assert config.logging.log_file == "logs/test.log"

    def test_config_load_missing_file(self, tmp_path, monkeypatch):
        """설정 파일 없을 때 기본값 사용"""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

        config_file = tmp_path / "nonexistent.yaml"
        config = Config.load(config_file)

        # 기본값 확인
        assert config.anthropic.model == "claude-sonnet-4-6"
        assert config.logging.level == "INFO"


class TestLoggingConfig:
    """LoggingConfig 테스트"""

    def test_logging_config_defaults(self):
        """로깅 설정 기본값"""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.log_file is None

    def test_logging_config_custom_values(self):
        """커스텀 로깅 설정"""
        config = LoggingConfig(level="DEBUG", log_file="logs/app.log")
        assert config.level == "DEBUG"
        assert config.log_file == "logs/app.log"
