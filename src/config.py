"""설정 관리 모듈"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml
from dotenv import load_dotenv


@dataclass
class AnthropicConfig:
    """Anthropic API 설정"""
    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"


@dataclass
class SlackConfig:
    """Slack 설정"""
    webhook_url: str = ""


@dataclass
class DiscordConfig:
    """Discord 설정"""
    webhook_url: str = ""  # DISCORD_WEBHOOK_URL 환경 변수


@dataclass
class CollectorConfig:
    """수집기 설정"""
    enabled: bool = True
    categories: list[str] = field(default_factory=list)


@dataclass
class CollectorsConfig:
    """전체 수집기 설정"""
    arxiv: CollectorConfig = field(default_factory=lambda: CollectorConfig(
        categories=["cs.AI", "cs.LG", "cs.CL"]
    ))
    google_blog: CollectorConfig = field(default_factory=CollectorConfig)
    anthropic_blog: CollectorConfig = field(default_factory=CollectorConfig)


@dataclass
class LoggingConfig:
    """로깅 설정"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_file: Optional[str] = None  # 로그 파일 경로 또는 None


@dataclass
class EmailConfig:
    """이메일 설정"""
    enabled: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    use_tls: bool = True
    username: str = ""  # SMTP 사용자 (보통 이메일 주소)
    password: str = ""  # SMTP 비밀번호 또는 앱 비밀번호
    sender: str = ""    # 발신자 이메일
    recipients: list[str] = field(default_factory=list)  # 환경 변수 EMAIL_RECIPIENTS에서 로드


@dataclass
class Config:
    """전체 설정"""
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    slack: SlackConfig = field(default_factory=SlackConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    collectors: CollectorsConfig = field(default_factory=CollectorsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    email: EmailConfig = field(default_factory=EmailConfig)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """설정 파일 로드"""
        load_dotenv()

        config = cls()

        # 환경 변수에서 로드
        config.anthropic.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        config.slack.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        config.discord.webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")

        # 설정 파일이 있으면 로드
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # Anthropic 설정
            if "anthropic" in data:
                if "model" in data["anthropic"]:
                    config.anthropic.model = data["anthropic"]["model"]
                if "api_key" in data["anthropic"] and not config.anthropic.api_key:
                    config.anthropic.api_key = cls._resolve_env(data["anthropic"]["api_key"])

            # Slack 설정
            if "slack" in data:
                if "webhook_url" in data["slack"] and not config.slack.webhook_url:
                    config.slack.webhook_url = cls._resolve_env(data["slack"]["webhook_url"])

            # Discord 설정
            if "discord" in data:
                if "webhook_url" in data["discord"] and not config.discord.webhook_url:
                    config.discord.webhook_url = cls._resolve_env(data["discord"]["webhook_url"])

            # 수집기 설정
            if "collectors" in data:
                collectors_data = data["collectors"]
                if "arxiv" in collectors_data:
                    config.collectors.arxiv.enabled = collectors_data["arxiv"].get("enabled", True)
                    if "categories" in collectors_data["arxiv"]:
                        config.collectors.arxiv.categories = collectors_data["arxiv"]["categories"]
                if "google_blog" in collectors_data:
                    config.collectors.google_blog.enabled = collectors_data["google_blog"].get("enabled", True)
                if "anthropic_blog" in collectors_data:
                    config.collectors.anthropic_blog.enabled = collectors_data["anthropic_blog"].get("enabled", True)

            # 로깅 설정
            if "logging" in data:
                log_data = data["logging"]
                if "level" in log_data:
                    config.logging.level = log_data["level"]
                if "log_file" in log_data:
                    config.logging.log_file = log_data["log_file"]

            # 이메일 설정
            if "email" in data:
                email_data = data["email"]
                if "enabled" in email_data:
                    config.email.enabled = email_data["enabled"]
                if "smtp_host" in email_data:
                    config.email.smtp_host = email_data["smtp_host"]
                if "smtp_port" in email_data:
                    config.email.smtp_port = email_data["smtp_port"]
                if "use_tls" in email_data:
                    config.email.use_tls = email_data["use_tls"]
                if "username" in email_data:
                    config.email.username = cls._resolve_env(email_data["username"])
                if "password" in email_data:
                    config.email.password = cls._resolve_env(email_data["password"])
                if "sender" in email_data:
                    config.email.sender = email_data["sender"]
                if "recipients" in email_data:
                    config.email.recipients = email_data["recipients"]

        # 이메일 환경 변수 (YAML보다 우선)
        email_username = os.getenv("EMAIL_USERNAME")
        if email_username:
            config.email.username = email_username
        email_password = os.getenv("EMAIL_PASSWORD")
        if email_password:
            config.email.password = email_password
        email_recipients = os.getenv("EMAIL_RECIPIENTS")
        if email_recipients:
            config.email.recipients = [r.strip() for r in email_recipients.split(",")]

        return config

    @staticmethod
    def _resolve_env(value: str) -> str:
        """${ENV_VAR} 형식의 환경 변수 치환"""
        if value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.getenv(env_var, "")
        return value

    def validate(self) -> list[str]:
        """설정 유효성 검사"""
        errors = []
        if not self.anthropic.api_key:
            errors.append("ANTHROPIC_API_KEY가 설정되지 않았습니다.")
        if not self.slack.webhook_url:
            errors.append("SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        return errors
