"""Slack Webhook을 통한 리포트 전송"""

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


class SlackNotifier:
    """Slack Incoming Webhook 알림 전송기"""

    def __init__(self, config: Config):
        self.config = config
        self.webhook_url = config.slack.webhook_url

    def send_report(self, report: Report) -> bool:
        """리포트를 슬랙으로 전송"""
        if not report.articles:
            logger.warning("No articles to send")
            return False

        blocks = self._build_message_blocks(report)
        payload = {"blocks": blocks}

        try:
            self._send_with_retry(payload)
            logger.info(f"Report sent successfully with {len(report.articles)} articles")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False

    @retry_with_backoff(max_retries=3, exceptions=RETRYABLE_EXCEPTIONS)
    def _send_with_retry(self, payload: dict) -> None:
        """Slack 메시지 전송 (재시도 포함)"""
        response = requests.post(
            self.webhook_url,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

    def _build_message_blocks(self, report: Report) -> list[dict[str, Any]]:
        """Slack Block Kit 메시지 생성"""
        blocks = []

        # 헤더
        date_str = report.created_at.strftime("%Y년 %m월 %d일")
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📰 {date_str} AI 데일리 리포트",
                "emoji": True,
            }
        })

        blocks.append({"type": "divider"})

        # 카테고리별 기사
        articles_by_category = report.articles_by_category()

        # 카테고리 순서 정의
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

            # 카테고리 헤더
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📂 {category.value}*",
                }
            })

            # 기사 목록
            for article in articles:
                article_text = self._format_article(article)
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": article_text,
                    }
                })

            blocks.append({"type": "divider"})

        # 푸터
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"총 {len(report.articles)}개의 기사 | 생성: {report.created_at.strftime('%H:%M')}"
                }
            ]
        })

        return blocks

    def _format_article(self, article: Article) -> str:
        """개별 기사 포맷팅"""
        # 제목 (링크)
        title_line = f"• <{article.url}|{article.title}>"

        # 요약
        summary = article.summary or "(요약 없음)"
        if len(summary) > 300:
            summary = summary[:300] + "..."

        # 출처 표시
        source_emoji = {
            "arxiv": "📄",
            "google": "🔵",
            "anthropic": "🟠",
        }
        source_icon = source_emoji.get(article.source.value, "📌")

        return f"{title_line}\n{source_icon} {summary}"

    def send_error_notification(self, error_message: str) -> bool:
        """에러 알림 전송"""
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "⚠️ AI Report 오류 발생",
                        "emoji": True,
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{error_message}```",
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"발생 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }

        try:
            self._send_with_retry(payload)
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to send error notification: {e}")
            return False
