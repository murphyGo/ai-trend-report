"""AI Report Automation Service - 메인 진입점"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from .config import Config
from .models import Article, Report
from .collectors import ArxivCollector, GoogleBlogCollector, AnthropicBlogCollector
from .summarizer import Summarizer
from .slack_notifier import SlackNotifier
from .data_io import save_articles, load_articles, save_report, load_report, get_latest_file
from .utils.logging import setup_logging


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


def run_collect_only(config: Config, output_dir: Path, limit: int = 0) -> bool:
    """수집 전용 파이프라인 - JSON 저장만"""
    logger.info("=" * 50)
    logger.info("AI Report - Collect Only Mode")
    logger.info("=" * 50)

    # 1. 기사 수집
    logger.info("[1/2] Collecting articles...")
    articles = collect_articles(config)

    if not articles:
        logger.warning("No articles collected.")
        return False

    logger.info(f"Total articles collected: {len(articles)}")

    # 기사 수 제한
    if limit > 0:
        articles = articles[:limit]
        logger.info(f"Limited to {limit} articles")

    # 2. JSON 저장
    logger.info("[2/2] Saving articles to JSON...")
    filepath = save_articles(articles, output_dir)
    logger.info(f"Articles saved to: {filepath}")

    return True


def run_send_only(config: Config, input_json: Path = None, dry_run: bool = False) -> bool:
    """전송 전용 파이프라인 - JSON에서 로드하여 Slack 전송"""
    logger.info("=" * 50)
    logger.info("AI Report - Send Only Mode")
    logger.info("=" * 50)

    # 1. JSON 파일 찾기
    if input_json:
        filepath = input_json
    else:
        filepath = get_latest_file(prefix="report")
        if not filepath:
            logger.error("No report JSON file found. Use --input-json to specify.")
            return False

    logger.info(f"[1/2] Loading report from: {filepath}")

    # 2. 리포트 로드
    try:
        report = load_report(filepath)
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return False

    logger.info(f"Loaded report with {len(report.articles)} articles")

    # 3. Slack 전송
    if dry_run:
        logger.info("[2/2] Dry run mode - skipping Slack notification")
        by_category = report.articles_by_category()
        for cat, cat_articles in by_category.items():
            logger.info(f"  [{cat.value}] {len(cat_articles)} articles")
            for article in cat_articles[:2]:
                logger.info(f"    - {article.title[:50]}...")
        return True

    logger.info("[2/2] Sending report to Slack...")
    notifier = SlackNotifier(config)
    success = notifier.send_report(report)

    if success:
        logger.info("Report sent successfully!")
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
  # 기본 모드 (수집만, Claude Code에서 요약)
  python -m src.main                        # 수집 → JSON 저장
  python -m src.main --limit 5              # 5개 기사만 수집

  # API 모드 (기존 방식, Anthropic API 사용)
  python -m src.main --use-api              # 전체 파이프라인
  python -m src.main --use-api --dry-run    # 슬랙 전송 없이 테스트

  # 개별 단계 실행
  python -m src.main --collect-only         # 수집만 (명시적)
  python -m src.main --send-only            # Slack 전송만
  python -m src.main --send-only --input-json data/report_2024-01-01.json
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
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="수집만 수행하고 JSON으로 저장 (요약 없이, API 키 불필요)",
    )
    parser.add_argument(
        "--use-api",
        action="store_true",
        help="Anthropic API로 요약 수행 (기존 방식)",
    )
    parser.add_argument(
        "--send-only",
        action="store_true",
        help="JSON 파일에서 로드하여 Slack 전송만 수행",
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        default=None,
        help="입력 JSON 파일 경로 (--send-only와 함께 사용)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="출력 디렉토리 (기본: data/)",
    )

    args = parser.parse_args()

    # 설정 로드
    try:
        config = Config.load(args.config)
    except Exception as e:
        # 설정 로드 실패 시 기본 로깅으로 에러 출력
        logging.basicConfig(level=logging.ERROR)
        logging.error(f"Failed to load config: {e}")
        sys.exit(1)

    # 로깅 설정 (config 로드 후, verbose 플래그가 config보다 우선)
    setup_logging(
        level=config.logging.level,
        log_file=Path(config.logging.log_file) if config.logging.log_file else None,
        verbose=args.verbose,
    )

    # 모드 결정
    if args.collect_only:
        # 수집 전용 모드: API 키 불필요
        try:
            success = run_collect_only(config, args.output_dir, args.limit)
            sys.exit(0 if success else 1)
        except Exception as e:
            logger.exception(f"Collection failed: {e}")
            sys.exit(1)

    elif args.send_only:
        # 전송 전용 모드: JSON 파일에서 로드
        try:
            success = run_send_only(config, args.input_json, args.dry_run)
            sys.exit(0 if success else 1)
        except Exception as e:
            logger.exception(f"Send failed: {e}")
            sys.exit(1)

    elif args.use_api:
        # API 모드: 기존 전체 파이프라인
        # 설정 검증 (API 키 필요)
        if not args.dry_run:
            errors = config.validate()
            if errors:
                for error in errors:
                    logger.error(error)
                logger.error("Please set required environment variables or update config.yaml")
                sys.exit(1)

        try:
            success = run_pipeline(config, dry_run=args.dry_run, limit=args.limit)
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            sys.exit(130)
        except Exception as e:
            logger.exception(f"Pipeline failed: {e}")
            if config.slack.webhook_url:
                try:
                    notifier = SlackNotifier(config)
                    notifier.send_error_notification(str(e))
                except Exception:
                    pass
            sys.exit(1)

    else:
        # 기본 모드: collect-only와 동일 (Claude Code에서 요약)
        logger.info("Default mode: collecting articles only (use --use-api for full pipeline)")
        try:
            success = run_collect_only(config, args.output_dir, args.limit)
            sys.exit(0 if success else 1)
        except Exception as e:
            logger.exception(f"Collection failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
