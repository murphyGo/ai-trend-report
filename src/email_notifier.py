"""이메일을 통한 리포트 전송"""

import html
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from .models import Article, Report, Category
from .config import Config
from .constants import QUIET_DAY_THRESHOLD, CATEGORY_ORDER
from .notifier_base import BaseNotifier
from .utils.retry import retry_with_backoff


logger = logging.getLogger(__name__)

# 재시도할 예외 타입들 (일시적 네트워크 오류)
RETRYABLE_EXCEPTIONS = (
    smtplib.SMTPServerDisconnected,
    smtplib.SMTPConnectError,
    TimeoutError,
    ConnectionError,
)


def _esc(value: Optional[str]) -> str:
    """HTML 본문 삽입용 이스케이프. None-safe.

    Phase 8.6 — 이메일 HTML이 f-string으로 조립되기 때문에 기사 제목/요약에
    포함된 `<`, `>`, `"`, `'`, `&`가 그대로 태그로 해석되어 XSS / 구조 훼손
    가능. 모든 사용자 입력 필드는 이 함수로 감싸야 함.
    """
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _is_safe_url(url: Optional[str]) -> bool:
    """http/https/빈값만 허용. javascript:, data: 등 XSS 벡터 차단."""
    if not url:
        return False
    url_lower = url.strip().lower()
    return url_lower.startswith("http://") or url_lower.startswith("https://")


class EmailNotifier(BaseNotifier):
    """SMTP 이메일 알림 전송기"""

    def __init__(self, config: Config, recipients: Optional[list[str]] = None):
        """EmailNotifier 초기화

        Args:
            config: 설정 객체
            recipients: 수신자 목록 (None이면 설정 파일의 기본값 사용)
        """
        self.config = config
        self.email_config = config.email
        self.recipients = recipients or self.email_config.recipients

    def _effective_sender(self) -> str:
        """발신자 주소 결정.

        Phase 8.6 — `sender`가 비어 있으면 SMTP `username`으로 fallback.
        Gmail 등 대부분의 SMTP 서버가 빈 From 헤더를 거부하기 때문.
        """
        return self.email_config.sender or self.email_config.username

    def send_report(self, report: Report) -> bool:
        """리포트를 이메일로 전송

        Phase 8.5: 빈/저조한 리포트도 quiet-day 배너 포함해 발송.
        Phase 8.6: html escape, Bcc 수신자, plain text 대안, sender fallback.

        Args:
            report: 전송할 리포트

        Returns:
            성공 여부
        """
        if not self.recipients:
            logger.error("No email recipients configured")
            return False

        subject = self._build_subject(report)
        html_content = self._build_html_message(report)
        plain_content = self._build_plain_message(report)

        try:
            self._send_with_retry(subject, html_content, plain_content)
            logger.info(f"Email sent successfully to {len(self.recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    @retry_with_backoff(max_retries=3, exceptions=RETRYABLE_EXCEPTIONS)
    def _send_with_retry(
        self,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
    ) -> None:
        """이메일 전송 (재시도 포함).

        Phase 8.6 변경점:
        - 수신자는 Bcc 헤더로 감춤 (프라이버시). `To` 헤더는 발신자 자신으로 설정.
        - `multipart/alternative`에 plain text 대안 포함 (RFC 준수 + 스팸 필터).
        - `From`은 `_effective_sender()` 결과 사용 (빈 sender면 username fallback).
        """
        sender = self._effective_sender()

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        # 프라이버시 — 수신자 주소 서로 노출 방지. To는 발신자 자신으로 self-addressed.
        msg['To'] = sender or 'undisclosed-recipients:;'
        msg['Bcc'] = ', '.join(self.recipients)

        # multipart/alternative는 먼저 첨부된 것이 "덜 선호"되므로 plain 먼저, html 나중
        if plain_content:
            msg.attach(MIMEText(plain_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # SMTP 연결 및 전송
        with smtplib.SMTP(self.email_config.smtp_host, self.email_config.smtp_port) as server:
            if self.email_config.use_tls:
                server.starttls()
            if self.email_config.username and self.email_config.password:
                server.login(self.email_config.username, self.email_config.password)
            # send_message는 To/Cc/Bcc 헤더 모두를 envelope recipient로 사용.
            # Bcc는 RFC 5322에 의해 실제 전송 시 헤더에서 제거됨 (수신자에게 안 보임).
            server.send_message(
                msg,
                from_addr=sender,
                to_addrs=self.recipients,
            )

    def _build_subject(self, report: Report) -> str:
        """이메일 제목 생성"""
        date_str = report.created_at.strftime("%Y년 %m월 %d일")
        prefix = "🔕 [조용한 날] " if self.is_quiet_day(report) else "[AI Report] "
        return f"{prefix}{date_str} AI 데일리 리포트 ({len(report.articles)}개 기사)"

    def _build_plain_message(self, report: Report) -> str:
        """Plain text 대안 본문 생성 (Phase 8.6).

        MIMEMultipart('alternative') 규격상 HTML과 함께 plain 버전도 제공해야
        RFC 준수 + 스팸 필터 통과율 향상.
        """
        lines: list[str] = []
        date_str = report.created_at.strftime("%Y년 %m월 %d일")
        lines.append(f"AI 데일리 리포트 — {date_str}")
        lines.append("=" * 50)
        lines.append("")

        count = len(report.articles)
        if count < QUIET_DAY_THRESHOLD:
            if count == 0:
                lines.append("🔕 조용한 날 — 오늘은 신규 AI 기사가 없습니다.")
            else:
                lines.append(f"🔕 조용한 날 — 오늘은 필터 통과 기사가 {count}개뿐입니다.")
            lines.append("(Recency 필터 2일 + 최근 7개 리포트 중복 제거)")
            lines.append("")

        articles_by_category = report.articles_by_category()
        category_order = [
            Category.LLM, Category.AGENT, Category.VISION, Category.VIDEO,
            Category.ROBOTICS, Category.SAFETY, Category.RL, Category.INFRA,
            Category.MEDICAL, Category.FINANCE, Category.INDUSTRY, Category.OTHER,
        ]

        for category in category_order:
            if category not in articles_by_category:
                continue
            lines.append(f"[{category.value}]")
            lines.append("-" * 50)
            for article in articles_by_category[category]:
                lines.append(f"• {article.title}")
                if article.summary:
                    summary = article.summary.strip()
                    if len(summary) > 400:
                        summary = summary[:400] + "..."
                    lines.append(f"  {summary}")
                lines.append(f"  출처: {article.source.value if article.source else 'Unknown'}")
                lines.append(f"  링크: {article.url}")
                lines.append("")
            lines.append("")

        lines.append("—")
        lines.append(f"총 {count}개 기사 | 생성: {report.created_at.strftime('%H:%M')}")
        lines.append("AI Report Automation Service")
        return "\n".join(lines)

    def _build_html_message(self, report: Report) -> str:
        """HTML 이메일 본문 생성"""
        date_str = report.created_at.strftime("%Y년 %m월 %d일")
        time_str = report.created_at.strftime("%H:%M")

        # 카테고리별 기사 그룹화
        articles_by_category = report.articles_by_category()

        category_order = CATEGORY_ORDER

        # Phase 8.5 — Quiet-day 배너
        quiet_banner = ""
        count = len(report.articles)
        if self.is_quiet_day(report):
            if count == 0:
                quiet_banner = (
                    '<div style="background:#fff8e1;border-left:4px solid #f1c40f;'
                    'padding:15px;margin:20px 0;border-radius:4px;">'
                    '<strong>🔕 조용한 날</strong><br>'
                    '오늘은 신규로 올라온 AI 기사가 없습니다. '
                    'Recency 필터(2일) + 최근 7개 리포트 중복 제거 결과 후보가 0개입니다.'
                    '</div>'
                )
            else:
                quiet_banner = (
                    f'<div style="background:#fff8e1;border-left:4px solid #f1c40f;'
                    f'padding:15px;margin:20px 0;border-radius:4px;">'
                    f'<strong>🔕 조용한 날</strong><br>'
                    f'오늘은 필터 통과 기사가 <strong>{count}개</strong>뿐입니다. '
                    f'Recency 필터(2일) + 최근 7개 리포트 중복 제거로 대부분 후보가 제외됨.'
                    f'</div>'
                )

        # 카테고리별 HTML 섹션 생성
        category_sections = []
        for category in category_order:
            if category not in articles_by_category:
                continue

            articles = articles_by_category[category]
            articles_html = '\n'.join(
                self._format_article_html(article)
                for article in articles
            )

            category_sections.append(f'''
            <div class="category">
                <h2 class="category-title">{category.value}</h2>
                {articles_html}
            </div>
            ''')

        categories_html = '\n'.join(category_sections)

        # 전체 HTML 구성
        html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .header .date {{
            margin-top: 8px;
            opacity: 0.9;
            font-size: 14px;
        }}
        .content {{
            padding: 20px 30px;
        }}
        .category {{
            margin-bottom: 30px;
        }}
        .category-title {{
            color: #0066cc;
            font-size: 18px;
            border-bottom: 2px solid #0066cc;
            padding-bottom: 8px;
            margin-bottom: 15px;
        }}
        .article {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #0066cc;
        }}
        .article-title {{
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 8px;
        }}
        .article-title a {{
            color: #1a1a2e;
            text-decoration: none;
        }}
        .article-title a:hover {{
            color: #0066cc;
            text-decoration: underline;
        }}
        .article-summary {{
            color: #555;
            font-size: 14px;
            margin-bottom: 8px;
        }}
        .article-meta {{
            font-size: 12px;
            color: #888;
        }}
        .source-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
        }}
        .source-arxiv {{ background-color: #e3f2fd; color: #1565c0; }}
        .source-google {{ background-color: #e8f5e9; color: #2e7d32; }}
        .source-anthropic {{ background-color: #fff3e0; color: #ef6c00; }}
        .source-openai {{ background-color: #f3e5f5; color: #7b1fa2; }}
        .source-huggingface {{ background-color: #fff8e1; color: #f57f17; }}
        .source-korean {{ background-color: #fce4ec; color: #c2185b; }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            font-size: 12px;
            color: #888;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AI 데일리 리포트</h1>
            <div class="date">{date_str}</div>
        </div>
        <div class="content">
            {quiet_banner}
            {categories_html}
        </div>
        <div class="footer">
            총 {len(report.articles)}개의 기사 | 생성: {time_str}<br>
            AI Report Automation Service
        </div>
    </div>
</body>
</html>'''

        return html

    def _format_article_html(self, article: Article) -> str:
        """개별 기사 HTML 포맷팅

        Phase 8.6 — 모든 사용자 입력 필드를 `_esc()`로 이스케이프해 XSS 차단.
        url은 http/https만 허용, 그 외엔 '#'으로 대체.
        """
        # 요약 처리
        summary = article.summary or "(요약 없음)"
        if len(summary) > 500:
            summary = summary[:500] + "..."

        # 소스 배지 — source.value는 enum 고정값이라 escape 불필요하지만 일관성을 위해 처리
        source_value = article.source.value if article.source else ""
        source_class = f"source-{source_value}"
        source_name = {
            "arxiv": "arXiv",
            "google": "Google",
            "anthropic": "Anthropic",
            "openai": "OpenAI",
            "huggingface": "HuggingFace",
            "korean": "한국 뉴스",
        }.get(source_value, source_value)

        # URL safety — http/https만 허용
        safe_url = article.url if _is_safe_url(article.url) else "#"

        return f'''
        <div class="article">
            <div class="article-title">
                <a href="{_esc(safe_url)}" target="_blank">{_esc(article.title)}</a>
            </div>
            <div class="article-summary">{_esc(summary)}</div>
            <div class="article-meta">
                <span class="source-badge {_esc(source_class)}">{_esc(source_name)}</span>
            </div>
        </div>
        '''

    def send_error_notification(self, error_message: str) -> bool:
        """에러 알림 전송

        Args:
            error_message: 에러 메시지

        Returns:
            성공 여부
        """
        if not self.recipients:
            logger.error("No email recipients configured")
            return False

        subject = "[AI Report] 오류 발생"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        html_content = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            padding: 20px;
        }}
        .error-box {{
            background-color: #fff3f3;
            border: 1px solid #ffcdd2;
            border-left: 4px solid #f44336;
            padding: 20px;
            border-radius: 4px;
        }}
        .error-title {{
            color: #c62828;
            font-size: 18px;
            margin-bottom: 10px;
        }}
        .error-message {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            font-family: monospace;
            white-space: pre-wrap;
        }}
        .timestamp {{
            color: #888;
            font-size: 12px;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="error-box">
        <div class="error-title">AI Report 오류 발생</div>
        <div class="error-message">{_esc(error_message)}</div>
        <div class="timestamp">발생 시각: {_esc(timestamp)}</div>
    </div>
</body>
</html>'''
        plain_content = (
            f"AI Report 오류 발생\n"
            f"{'=' * 50}\n\n"
            f"{error_message}\n\n"
            f"발생 시각: {timestamp}\n"
        )

        try:
            self._send_with_retry(subject, html_content, plain_content)
            return True
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False
