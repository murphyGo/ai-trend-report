"""이메일을 통한 리포트 전송"""

import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from .models import Article, Report, Category
from .config import Config
from .utils.retry import retry_with_backoff


logger = logging.getLogger(__name__)

# 재시도할 예외 타입들 (일시적 네트워크 오류)
RETRYABLE_EXCEPTIONS = (
    smtplib.SMTPServerDisconnected,
    smtplib.SMTPConnectError,
    TimeoutError,
    ConnectionError,
)


class EmailNotifier:
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

    def send_report(self, report: Report) -> bool:
        """리포트를 이메일로 전송

        Args:
            report: 전송할 리포트

        Returns:
            성공 여부
        """
        if not report.articles:
            logger.warning("No articles to send")
            return False

        if not self.recipients:
            logger.error("No email recipients configured")
            return False

        subject = self._build_subject(report)
        html_content = self._build_html_message(report)

        try:
            self._send_with_retry(subject, html_content)
            logger.info(f"Email sent successfully to {len(self.recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    @retry_with_backoff(max_retries=3, exceptions=RETRYABLE_EXCEPTIONS)
    def _send_with_retry(self, subject: str, html_content: str) -> None:
        """이메일 전송 (재시도 포함)"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email_config.sender
        msg['To'] = ', '.join(self.recipients)

        # HTML 본문 첨부
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # SMTP 연결 및 전송
        with smtplib.SMTP(self.email_config.smtp_host, self.email_config.smtp_port) as server:
            if self.email_config.use_tls:
                server.starttls()
            if self.email_config.username and self.email_config.password:
                server.login(self.email_config.username, self.email_config.password)
            server.send_message(msg)

    def _build_subject(self, report: Report) -> str:
        """이메일 제목 생성"""
        date_str = report.created_at.strftime("%Y년 %m월 %d일")
        return f"[AI Report] {date_str} AI 데일리 리포트 ({len(report.articles)}개 기사)"

    def _build_html_message(self, report: Report) -> str:
        """HTML 이메일 본문 생성"""
        date_str = report.created_at.strftime("%Y년 %m월 %d일")
        time_str = report.created_at.strftime("%H:%M")

        # 카테고리별 기사 그룹화
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
        """개별 기사 HTML 포맷팅"""
        # 요약 처리
        summary = article.summary or "(요약 없음)"
        if len(summary) > 500:
            summary = summary[:500] + "..."

        # 소스 배지 스타일
        source_class = f"source-{article.source.value}"
        source_name = {
            "arxiv": "arXiv",
            "google": "Google",
            "anthropic": "Anthropic",
            "openai": "OpenAI",
            "huggingface": "HuggingFace",
            "korean": "한국 뉴스",
        }.get(article.source.value, article.source.value)

        return f'''
        <div class="article">
            <div class="article-title">
                <a href="{article.url}" target="_blank">{article.title}</a>
            </div>
            <div class="article-summary">{summary}</div>
            <div class="article-meta">
                <span class="source-badge {source_class}">{source_name}</span>
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
        <div class="error-message">{error_message}</div>
        <div class="timestamp">발생 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
</body>
</html>'''

        try:
            self._send_with_retry(subject, html_content)
            return True
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
            return False
