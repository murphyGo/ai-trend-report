"""AI Report Automation Service - 메인 진입점"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from .config import Config
from .models import Report
from .collectors import ArxivCollector, GoogleBlogCollector, AnthropicBlogCollector
from .summarizer import Summarizer
from .slack_notifier import SlackNotifier


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def collect_articles(config: Config) -> list:
    """모든 소스에서 기사 수집"""
    articles = []

    collectors = []

    if config.collectors.arxiv.enabled:
        collectors.append(ArxivCollector(
            categories=config.collectors.arxiv.categories
        ))

    if config.collectors.google_blog.enabled:
        collectors.append(GoogleBlogCollector())

    if config.collectors.anthropic_blog.enabled:
        collectors.append(AnthropicBlogCollector())

    for collector in collectors:
        try:
            logger.info(f"Collecting from {collector.source.value}...")
            collected = collector.collect()
            articles.extend(collected)
            logger.info(f"Collected {len(collected)} articles from {collector.source.value}")
        except Exception as e:
            logger.error(f"Failed to collect from {collector.source.value}: {e}")
            continue

    return articles


def run_pipeline(config: Config, dry_run: bool = False, limit: int = 0) -> bool:
    """전체 파이프라인 실행"""
    logger.info("=" * 50)
    logger.info("AI Report Pipeline Started")
    logger.info("=" * 50)

    # 1. 기사 수집
    logger.info("[1/3] Collecting articles...")
    articles = collect_articles(config)

    if not articles:
        logger.warning("No articles collected. Exiting.")
        return False

    logger.info(f"Total articles collected: {len(articles)}")

    # 기사 수 제한 (테스트용)
    if limit > 0:
        articles = articles[:limit]
        logger.info(f"Limited to {limit} articles for processing")

    # 2. 요약 생성
    logger.info("[2/3] Summarizing articles with Claude API...")
    summarizer = Summarizer(config)
    articles = summarizer.summarize_batch(articles)

    # 3. 리포트 생성
    report = Report(articles=articles)
    logger.info(f"Report created with {len(report.articles)} articles")

    # 카테고리별 통계
    by_category = report.articles_by_category()
    logger.info("Articles by category:")
    for cat, cat_articles in by_category.items():
        logger.info(f"  - {cat.value}: {len(cat_articles)}")

    # 4. 슬랙 전송
    if dry_run:
        logger.info("[3/3] Dry run mode - skipping Slack notification")
        logger.info("Sample output:")
        for article in articles[:3]:
            logger.info(f"  [{article.category.value}] {article.title}")
            logger.info(f"    Summary: {article.summary[:100]}...")
        return True

    logger.info("[3/3] Sending report to Slack...")
    notifier = SlackNotifier(config)
    success = notifier.send_report(report)

    if success:
        logger.info("Pipeline completed successfully!")
    else:
        logger.error("Failed to send Slack notification")

    return success


def main():
    """CLI 메인 함수"""
    parser = argparse.ArgumentParser(
        description="AI Report Automation Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main                    # 전체 파이프라인 실행
  python -m src.main --dry-run          # 슬랙 전송 없이 테스트
  python -m src.main --dry-run --limit 5  # 5개 기사만 테스트
  python -m src.main --config custom.yaml # 커스텀 설정 파일 사용
        """
    )

    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=None,
        help="설정 파일 경로 (기본: config.yaml)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="슬랙 전송 없이 테스트 모드로 실행",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=0,
        help="처리할 기사 수 제한 (0 = 무제한)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세 로그 출력",
    )

    args = parser.parse_args()

    # 로그 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 설정 로드
    try:
        config = Config.load(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    # 설정 검증 (dry-run이 아닐 때만)
    if not args.dry_run:
        errors = config.validate()
        if errors:
            for error in errors:
                logger.error(error)
            logger.error("Please set required environment variables or update config.yaml")
            sys.exit(1)

    # 파이프라인 실행
    try:
        success = run_pipeline(config, dry_run=args.dry_run, limit=args.limit)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")

        # 에러 알림 전송 시도
        if config.slack.webhook_url:
            try:
                notifier = SlackNotifier(config)
                notifier.send_error_notification(str(e))
            except Exception:
                pass

        sys.exit(1)


if __name__ == "__main__":
    main()
