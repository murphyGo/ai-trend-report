"""Discord Webhook을 통한 리포트 전송"""

import logging
from datetime import datetime
from typing import Any

import requests

from .models import Article, Report, Category
from .config import Config
from .utils.retry import retry_with_backoff


logger = logging.getLogger(__name__)

# 재시도할 예외 타입들 (일시적 네트워크 오류)
RETRYABLE_EXCEPTIONS = (requests.Timeout, requests.ConnectionError)

# Discord embed 색상 (decimal)
EMBED_COLOR_DEFAULT = 5814783  # #58ACFF (파란색)
EMBED_COLOR_ERROR = 15158332   # #E74C3C (빨간색)
EMBED_COLOR_QUIET = 15844367   # #F1C40F (노란색, quiet-day 배너)

# Phase 8.5 — Quiet-day 임계값
QUIET_DAY_THRESHOLD = 3

# 카테고리별 색상
CATEGORY_COLORS = {
    Category.LLM: 3447003,       # #3498DB (파란색)
    Category.AGENT: 10181046,    # #9B59B6 (보라색)
    Category.VISION: 15844367,   # #F1C40F (노란색)
    Category.VIDEO: 15105570,    # #E67E22 (주황색)
    Category.ROBOTICS: 8359053,  # #7F8C8D (회색)
    Category.SAFETY: 15158332,   # #E74C3C (빨간색)
    Category.RL: 1752220,        # #1ABC9C (청록색)
    Category.INFRA: 9807270,     # #95A5A6 (회색)
    Category.MEDICAL: 3066993,   # #2ECC71 (초록색)
    Category.FINANCE: 15844367,  # #F1C40F (노란색)
    Category.INDUSTRY: 9936031,  # #979C9F (회색)
    Category.OTHER: 9807270,     # #95A5A6 (회색)
}


class DiscordNotifier:
    """Discord Webhook 알림 전송기"""

    def __init__(self, config: Config, webhook_url: str = None):
        """
        Args:
            config: 설정 객체
            webhook_url: Webhook URL (None이면 설정에서 로드)
        """
        self.config = config
        self.webhook_url = webhook_url or config.discord.webhook_url

    def send_report(self, report: Report) -> bool:
        """리포트를 Discord로 전송

        Phase 8.5: 빈 리포트도 "조용한 날" 배너 embed로 전송.

        Args:
            report: 전송할 리포트

        Returns:
            성공 여부
        """
        if not self.webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False

        embeds = self._build_embeds(report)

        # Quiet-day 배너 embed prepend
        if len(report.articles) < QUIET_DAY_THRESHOLD:
            count = len(report.articles)
            if count == 0:
                desc = (
                    "오늘은 신규로 올라온 AI 기사가 없습니다.\n"
                    "Recency 필터(2일) + 최근 7개 리포트 중복 제거 결과 후보가 0개."
                )
            else:
                desc = (
                    f"오늘은 필터 통과 기사가 **{count}개**뿐입니다.\n"
                    "Recency 필터(2일) + 최근 7개 리포트 중복 제거로 대부분의 후보가 제외됨."
                )
            quiet_embed = {
                "title": "🔕 조용한 날",
                "description": desc,
                "color": EMBED_COLOR_QUIET,
            }
            embeds.insert(0, quiet_embed)

        # Discord는 한 번에 최대 10개 embed만 전송 가능
        # 여러 번 나눠서 전송
        for i in range(0, len(embeds), 10):
            batch = embeds[i:i + 10]
            payload = {"embeds": batch}

            try:
                self._send_with_retry(payload)
            except requests.RequestException as e:
                logger.error(f"Failed to send Discord message: {e}")
                return False

        logger.info(f"Report sent successfully with {len(report.articles)} articles")
        return True

    @retry_with_backoff(max_retries=3, exceptions=RETRYABLE_EXCEPTIONS)
    def _send_with_retry(self, payload: dict) -> None:
        """Discord 메시지 전송 (재시도 포함)"""
        response = requests.post(
            self.webhook_url,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

    def _build_embeds(self, report: Report) -> list[dict[str, Any]]:
        """Discord embed 메시지 생성

        Args:
            report: 리포트 객체

        Returns:
            embed 리스트
        """
        embeds = []

        # 헤더 embed
        date_str = report.created_at.strftime("%Y년 %m월 %d일")
        header_embed = {
            "title": f"📰 {date_str} AI 데일리 리포트",
            "description": f"총 {len(report.articles)}개의 AI 관련 기사/논문을 수집했습니다.",
            "color": EMBED_COLOR_DEFAULT,
            "timestamp": report.created_at.isoformat(),
        }
        embeds.append(header_embed)

        # 카테고리별 embed
        articles_by_category = report.articles_by_category()

        category_order = [
            Category.LLM,
            Category.AGENT,
            Category.VISION,
            Category.VIDEO,
            Category.ROBOTICS,
            Category.SAFETY,
            Category.RL,
            Category.INFRA,
            Category.MEDICAL,
            Category.FINANCE,
            Category.INDUSTRY,
            Category.OTHER,
        ]

        for category in category_order:
            if category not in articles_by_category:
                continue

            articles = articles_by_category[category]
            category_embed = self._build_category_embed(category, articles)
            embeds.append(category_embed)

        return embeds

    def _build_category_embed(
        self, category: Category, articles: list[Article]
    ) -> dict[str, Any]:
        """카테고리별 embed 생성

        Args:
            category: 카테고리
            articles: 해당 카테고리의 기사 목록

        Returns:
            embed dict
        """
        # 카테고리 이모지
        category_emoji = {
            Category.LLM: "🤖",
            Category.AGENT: "🔧",
            Category.VISION: "👁️",
            Category.VIDEO: "🎬",
            Category.ROBOTICS: "🦾",
            Category.SAFETY: "🛡️",
            Category.RL: "🎮",
            Category.INFRA: "⚙️",
            Category.MEDICAL: "🏥",
            Category.FINANCE: "💰",
            Category.INDUSTRY: "📈",
            Category.OTHER: "📌",
        }

        emoji = category_emoji.get(category, "📌")
        color = CATEGORY_COLORS.get(category, EMBED_COLOR_DEFAULT)

        # 기사 목록을 description으로 구성
        description_lines = []
        for article in articles[:10]:  # 최대 10개 기사
            formatted = self._format_article(article)
            description_lines.append(formatted)

        if len(articles) > 10:
            description_lines.append(f"\n*...외 {len(articles) - 10}개 기사*")

        description = "\n\n".join(description_lines)

        # Discord embed description 최대 4096자
        if len(description) > 4000:
            description = description[:4000] + "..."

        return {
            "title": f"{emoji} {category.value}",
            "description": description,
            "color": color,
        }

    def _format_article(self, article: Article) -> str:
        """개별 기사 포맷팅 (Discord 마크다운)

        Args:
            article: 기사 객체

        Returns:
            포맷팅된 문자열
        """
        # 제목 (링크) - Discord 마크다운 형식
        title_line = f"**[{article.title}]({article.url})**"

        # 요약
        summary = article.summary or "(요약 없음)"
        if len(summary) > 200:
            summary = summary[:200] + "..."

        # 출처 표시
        source_names = {
            "arxiv": "📄 arXiv",
            "google": "🔵 Google",
            "anthropic": "🟠 Anthropic",
            "openai": "🟢 OpenAI",
            "huggingface": "🤗 HuggingFace",
            "korean": "🇰🇷 한국 뉴스",
        }
        source_label = source_names.get(article.source.value, f"📌 {article.source.value}")

        return f"{title_line}\n{source_label} | {summary}"

    def send_error_notification(self, error_message: str) -> bool:
        """에러 알림 전송

        Args:
            error_message: 에러 메시지

        Returns:
            성공 여부
        """
        if not self.webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False

        payload = {
            "embeds": [
                {
                    "title": "⚠️ AI Report 오류 발생",
                    "description": f"```\n{error_message}\n```",
                    "color": EMBED_COLOR_ERROR,
                    "timestamp": datetime.now().isoformat(),
                    "footer": {
                        "text": "AI Report Automation Service"
                    }
                }
            ]
        }

        try:
            self._send_with_retry(payload)
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to send error notification: {e}")
            return False
