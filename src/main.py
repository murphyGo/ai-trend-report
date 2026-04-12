"""AI Report Automation Service - 메인 진입점"""

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import Config
from .models import Article, Report, Source
from .collectors import (
    ArxivCollector,
    GoogleBlogCollector,
    AnthropicBlogCollector,
    OpenAIBlogCollector,
    HuggingFaceBlogCollector,
    KoreanNewsCollector,
    # Tier 1: 공식 RSS
    MicrosoftResearchCollector,
    NvidiaDeveloperBlogCollector,
    MarkTechPostCollector,
    BAIRBlogCollector,
    StanfordAILabCollector,
    TechCrunchAICollector,
    VentureBeatAICollector,
    # Tier 2: HF Papers + HTML
    HFPapersCollector,
    MetaAIBlogCollector,
    MITTechReviewCollector,
    # Tier 3: 한국
    NaverD2Collector,
    KakaoTechCollector,
    LGAIResearchCollector,
)
from .summarizer import Summarizer
from .slack_notifier import SlackNotifier
from .discord_notifier import DiscordNotifier
from .email_notifier import EmailNotifier
from .data_io import (
    save_articles,
    load_articles,
    save_report,
    load_report,
    get_latest_file,
    load_recent_report_urls,
)
from .filters import filter_by_recency, filter_already_seen
from .utils.logging import setup_logging


logger = logging.getLogger(__name__)


# Phase 9.2 — 수집기 레지스트리. Source enum → (CollectorClass, kwargs) 매핑.
# get_enabled_collectors()에서 disabled_sources와 비교해 활성화 여부 결정.
# 새 수집기 추가 시 여기에 한 줄만 추가하면 config.yaml 제어가 자동 적용됨.
_COLLECTOR_REGISTRY: list[tuple] = [
    # (Source enum, CollectorClass, extra_kwargs_factory)
    # extra_kwargs_factory: lambda config → dict (config-dependent kwargs가 필요한 경우)
    (Source.ARXIV, ArxivCollector, lambda c: {"categories": c.collectors.arxiv.categories}),
    (Source.GOOGLE_BLOG, GoogleBlogCollector, None),
    (Source.ANTHROPIC_BLOG, AnthropicBlogCollector, None),
    (Source.OPENAI_BLOG, OpenAIBlogCollector, None),
    (Source.HUGGINGFACE_BLOG, HuggingFaceBlogCollector, None),
    (Source.KOREAN_NEWS, KoreanNewsCollector, None),
    (Source.MICROSOFT_RESEARCH, MicrosoftResearchCollector, None),
    (Source.NVIDIA_BLOG, NvidiaDeveloperBlogCollector, None),
    (Source.MARKTECHPOST, MarkTechPostCollector, None),
    (Source.BAIR_BLOG, BAIRBlogCollector, None),
    (Source.STANFORD_AI, StanfordAILabCollector, None),
    (Source.TECHCRUNCH_AI, TechCrunchAICollector, None),
    (Source.VENTUREBEAT_AI, VentureBeatAICollector, None),
    (Source.HF_PAPERS, HFPapersCollector, None),
    (Source.MIT_TECH_REVIEW, MITTechReviewCollector, None),
    # Meta AI / LG AI Research: 사이트 정책상 미사용 (DEBT-001/002).
    # disabled_sources에 넣지 않아도 레지스트리에 포함돼 있으면
    # config.yaml에서 disabled_sources 목록에서 빼면 자동 활성화.
    # 단, 현재 코드상으로 접속이 안 되므로 기본 비활성 처리.
    (Source.META_AI_BLOG, MetaAIBlogCollector, None),
    (Source.LG_AI_RESEARCH, LGAIResearchCollector, None),
    (Source.NAVER_D2, NaverD2Collector, None),
    (Source.KAKAO_TECH, KakaoTechCollector, None),
]

# 기본 비활성 소스 — DEBT-001/002에 해당. config.yaml에서 별도 설정 없으면 이 값 적용.
_DEFAULT_DISABLED = {"meta_ai", "lg_ai_research"}


def get_enabled_collectors(config: Config) -> list:
    """활성화된 수집기 목록 반환 (Phase 9.2 레지스트리 기반)

    비활성화 판단 순서:
    1. `config.collectors.disabled_sources` 리스트 (사용자 명시)
    2. 기존 `config.collectors.{arxiv,google_blog,anthropic_blog}.enabled` 플래그 (하위 호환)
    3. `_DEFAULT_DISABLED` (DEBT-001/002 기본 비활성)
    """
    # 1. 명시적 disabled_sources
    disabled: set[str] = set(config.collectors.disabled_sources)

    # 2. 하위 호환: 기존 per-source enabled 플래그 (False면 disabled에 추가)
    if not config.collectors.arxiv.enabled:
        disabled.add(Source.ARXIV.value)
    if not config.collectors.google_blog.enabled:
        disabled.add(Source.GOOGLE_BLOG.value)
    if not config.collectors.anthropic_blog.enabled:
        disabled.add(Source.ANTHROPIC_BLOG.value)

    # 3. 기본 비활성 (disabled_sources에 이미 등록된 것은 제외하고 default만 추가)
    # 사용자가 config.yaml에서 disabled_sources를 명시하지 않으면 default 적용
    if not config.collectors.disabled_sources:
        disabled |= _DEFAULT_DISABLED

    collectors = []
    for source, cls, kwargs_factory in _COLLECTOR_REGISTRY:
        if source.value in disabled:
            logger.debug(f"Skipping disabled source: {source.value}")
            continue
        kwargs = kwargs_factory(config) if kwargs_factory else {}
        collectors.append(cls(**kwargs))

    logger.info(f"Enabled collectors: {len(collectors)} / {len(_COLLECTOR_REGISTRY)}")
    return collectors


def collect_articles(config: Config, parallel: bool = False, max_workers: int = 3) -> list:
    """모든 소스에서 기사 수집

    Args:
        config: 설정 객체
        parallel: 병렬 수집 여부 (기본: False)
        max_workers: 병렬 작업자 수 (기본: 3)

    Returns:
        수집된 기사 목록
    """
    collectors = get_enabled_collectors(config)

    if not collectors:
        logger.warning("No collectors enabled")
        return []

    if parallel:
        return collect_articles_parallel(collectors, max_workers)
    else:
        return collect_articles_sequential(collectors)


def collect_articles_sequential(collectors: list) -> list:
    """순차적으로 기사 수집"""
    articles = []

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


def collect_articles_parallel(collectors: list, max_workers: int = 3) -> list:
    """병렬로 기사 수집 (ThreadPoolExecutor 사용)

    Args:
        collectors: 수집기 목록
        max_workers: 최대 동시 작업 수

    Returns:
        수집된 기사 목록
    """
    articles = []

    logger.info(f"Starting parallel collection with {max_workers} workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 각 수집기에 대한 Future 생성
        future_to_collector = {
            executor.submit(collector.collect): collector
            for collector in collectors
        }

        # 완료된 순서대로 결과 수집
        for future in as_completed(future_to_collector):
            collector = future_to_collector[future]
            try:
                collected = future.result()
                articles.extend(collected)
                logger.info(f"Collected {len(collected)} articles from {collector.source.value}")
            except Exception as e:
                logger.error(f"Failed to collect from {collector.source.value}: {e}")

    logger.info(f"Parallel collection complete: {len(articles)} total articles")
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


def run_collect_only(
    config: Config,
    output_dir: Path,
    limit: int = 0,
    parallel: bool = False,
    days: int = 2,
    dedup_days: int = 7,
) -> bool:
    """수집 전용 파이프라인 — Phase 8에서 ArticleCache 대신 recency + 리포트 기반 dedup

    Args:
        config: 설정 객체
        output_dir: 출력 디렉토리
        limit: 기사 수 제한 (0 = 무제한)
        parallel: 병렬 수집 여부
        days: recency 필터 — 지난 N일 이내 발행된 기사만 유지 (0 = 비활성화)
        dedup_days: 크로스 리포트 dedup — 최근 N개 리포트의 URL 제외 (0 = 비활성화)

    Returns:
        성공 여부
    """
    logger.info("=" * 50)
    logger.info("AI Report - Collect Only Mode")
    if parallel:
        logger.info("(Parallel collection enabled)")
    logger.info(
        f"(Recency filter: {days} days, Cross-report dedup: last {dedup_days} reports)"
    )
    logger.info("=" * 50)

    # 1. 기사 수집
    logger.info("[1/4] Collecting articles...")
    articles = collect_articles(config, parallel=parallel)

    if not articles:
        logger.warning("No articles collected.")
        return False

    logger.info(f"Total articles collected: {len(articles)}")

    # 2. Recency 필터 (Phase 8.2)
    logger.info(f"[2/4] Applying recency filter ({days} days)...")
    articles, dropped_old, unknown_kept = filter_by_recency(articles, days)
    logger.info(
        f"Recency: kept {len(articles)} "
        f"(dropped {dropped_old} old, kept {unknown_kept} with unknown date)"
    )

    # 3. 크로스 리포트 중복 제거 (Phase 8.3)
    logger.info(f"[3/4] Loading last {dedup_days} reports for cross-report dedup...")
    seen_urls = load_recent_report_urls(output_dir, n=dedup_days)
    articles, dedup_removed = filter_already_seen(articles, seen_urls)
    logger.info(f"Dedup: removed {dedup_removed} already-seen URLs, {len(articles)} remain")

    # Quiet-day 경고 (Phase 8.5)
    if len(articles) == 0:
        logger.warning(
            "🔕 QUIET DAY: recency + dedup filters left 0 articles. "
            "Saving empty articles file; downstream notifier should show quiet-day banner."
        )
    elif len(articles) < 3:
        logger.warning(
            f"🔕 QUIET DAY: only {len(articles)} articles passed filters "
            f"(threshold: 3). Downstream notifier will show quiet-day banner."
        )

    # 기사 수 제한
    if limit > 0:
        articles = articles[:limit]
        logger.info(f"Limited to {limit} articles")

    # 4. JSON 저장 (비어 있어도 저장)
    logger.info("[4/4] Saving articles to JSON...")
    filepath = save_articles(articles, output_dir)
    logger.info(f"Articles saved to: {filepath}")

    return True


def run_send_only(
    config: Config,
    input_json: Path = None,
    dry_run: bool = False,
    send_email: bool = False,
    email_recipients: list[str] = None,
    send_discord: bool = False,
    discord_url: str = None,
) -> bool:
    """전송 전용 파이프라인 - JSON에서 로드하여 Slack/Discord/이메일 전송

    Args:
        config: 설정 객체
        input_json: 입력 JSON 파일 경로
        dry_run: 실제 전송 없이 미리보기
        send_email: 이메일 전송 여부
        email_recipients: 이메일 수신자 목록 (None이면 설정 기본값)
        send_discord: Discord 전송 여부
        discord_url: Discord Webhook URL (None이면 설정 기본값)

    Returns:
        성공 여부
    """
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

    # 3. 전송
    if dry_run:
        logger.info("[2/2] Dry run mode - skipping notifications")
        by_category = report.articles_by_category()
        for cat, cat_articles in by_category.items():
            logger.info(f"  [{cat.value}] {len(cat_articles)} articles")
            for article in cat_articles[:2]:
                logger.info(f"    - {article.title[:50]}...")
        return True

    success = True

    # Slack 전송 (다른 채널이 명시적으로 요청된 경우가 아니면)
    if not send_email and not send_discord:
        if config.slack.webhook_url:
            logger.info("[2/2] Sending report to Slack...")
            slack_notifier = SlackNotifier(config)
            slack_success = slack_notifier.send_report(report)
            if slack_success:
                logger.info("Slack notification sent successfully!")
            else:
                logger.error("Failed to send Slack notification")
                success = False

    # Discord 전송
    if send_discord:
        logger.info("[2/2] Sending report to Discord...")
        discord_notifier = DiscordNotifier(config, webhook_url=discord_url)
        discord_success = discord_notifier.send_report(report)
        if discord_success:
            logger.info("Discord notification sent successfully!")
        else:
            logger.error("Failed to send Discord notification")
            success = False

    # 이메일 전송
    if send_email:
        logger.info("[2/2] Sending report via email...")
        email_notifier = EmailNotifier(config, recipients=email_recipients)
        email_success = email_notifier.send_report(report)
        if email_success:
            logger.info("Email sent successfully!")
        else:
            logger.error("Failed to send email")
            success = False

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
  python -m src.main --parallel             # 병렬 수집 (빠름)
  python -m src.main --no-cache             # 캐시 무시 (전체 수집)

  # API 모드 (기존 방식, Anthropic API 사용)
  python -m src.main --use-api              # 전체 파이프라인
  python -m src.main --use-api --dry-run    # 슬랙 전송 없이 테스트

  # 개별 단계 실행
  python -m src.main --collect-only         # 수집만 (명시적)
  python -m src.main --send-only            # Slack 전송만
  python -m src.main --send-only --input-json data/report_2024-01-01.json

  # 이메일 전송
  python -m src.main --send-only --email    # 이메일로 전송
  python -m src.main --send-only --email --email-to user@example.com  # 특정 수신자

  # Discord 전송
  python -m src.main --send-only --discord  # Discord로 전송
  python -m src.main --send-only --discord --discord-url https://discord.com/api/webhooks/...

  # 웹 대시보드
  python -m src.main --serve               # 대시보드 서버 시작 (http://localhost:8000)
  python -m src.main --serve --port 8080   # 포트 지정
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
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="병렬 수집 활성화 (ThreadPoolExecutor)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=2,
        help="Recency 필터: 지난 N일 이내 발행된 기사만 유지 (기본: 2, 0=비활성화)",
    )
    parser.add_argument(
        "--dedup-days",
        type=int,
        default=7,
        help="크로스 리포트 dedup: 최근 N개 리포트의 URL 제외 (기본: 7, 0=비활성화)",
    )
    # Deprecated (Phase 8에서 ArticleCache 제거됨) — 호환성 유지용 no-op
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="(deprecated, no-op) ArticleCache는 Phase 8에서 제거됨",
    )
    parser.add_argument(
        "--cache-days",
        type=int,
        default=None,
        help="(deprecated, no-op) --dedup-days 사용 권장",
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="이메일로 리포트 전송 (SMTP 설정 필요)",
    )
    parser.add_argument(
        "--email-to",
        type=str,
        nargs="+",
        help="이메일 수신자 (기본: 설정 파일의 recipients)",
    )
    parser.add_argument(
        "--discord",
        action="store_true",
        help="Discord로 리포트 전송",
    )
    parser.add_argument(
        "--discord-url",
        type=str,
        default=None,
        help="Discord Webhook URL (기본: 설정 파일의 webhook_url)",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="웹 대시보드 서버 시작",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="웹 서버 포트 (기본: 8000)",
    )
    parser.add_argument(
        "--generate-static",
        action="store_true",
        help="정적 사이트 생성 (GitHub Pages용)",
    )
    parser.add_argument(
        "--static-output",
        type=str,
        default="_site",
        help="정적 사이트 출력 디렉토리 (기본: _site)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="정적 사이트 URL prefix (예: /ai-trend-report). "
             "미지정 시 SITE_BASE_URL 환경변수 사용. GitHub Pages 프로젝트 사이트에 필요.",
    )

    args = parser.parse_args()

    # Deprecated 플래그 경고 (Phase 8)
    if args.no_cache or args.cache_days is not None:
        logging.warning(
            "--no-cache / --cache-days are deprecated no-ops since Phase 8. "
            "Use --days (recency) and --dedup-days (cross-report dedup) instead."
        )

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
    if args.generate_static:
        # 정적 사이트 생성 모드
        logger.info(f"Generating static site to {args.static_output}...")
        try:
            from .static_generator import generate_static_site
            data_dir = Path(args.output_dir) if args.output_dir else Path("data")
            output_dir = Path(args.static_output)
            generate_static_site(
                data_dir=data_dir,
                output_dir=output_dir,
                base_url=args.base_url,
            )
            logger.info(f"Static site generated: {output_dir}")
        except Exception as e:
            logger.exception(f"Static site generation failed: {e}")
            sys.exit(1)
    elif args.serve:
        # 웹 대시보드 서버 모드
        logger.info(f"Starting web dashboard server on port {args.port}...")
        try:
            from .web.app import run_server
            run_server(host="0.0.0.0", port=args.port)
        except ImportError as e:
            logger.error(f"Failed to import web module: {e}")
            logger.error("Install web dependencies: pip install fastapi uvicorn jinja2")
            sys.exit(1)
        except Exception as e:
            logger.exception(f"Server failed: {e}")
            sys.exit(1)

    elif args.collect_only:
        # 수집 전용 모드: API 키 불필요
        try:
            success = run_collect_only(
                config,
                args.output_dir,
                limit=args.limit,
                parallel=args.parallel,
                days=args.days,
                dedup_days=args.dedup_days,
            )
            sys.exit(0 if success else 1)
        except Exception as e:
            logger.exception(f"Collection failed: {e}")
            sys.exit(1)

    elif args.send_only:
        # 전송 전용 모드: JSON 파일에서 로드
        try:
            success = run_send_only(
                config,
                input_json=args.input_json,
                dry_run=args.dry_run,
                send_email=args.email,
                email_recipients=args.email_to,
                send_discord=args.discord,
                discord_url=args.discord_url,
            )
            sys.exit(0 if success else 1)
        except Exception as e:
            logger.exception(f"Send failed: {e}")
            sys.exit(1)

    elif args.use_api:
        # API 모드: 기존 전체 파이프라인
        # 설정 검증 (API 키 필요)
        if not args.dry_run:
            errors = config.validate_api_mode()
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
            success = run_collect_only(
                config,
                args.output_dir,
                limit=args.limit,
                parallel=args.parallel,
                days=args.days,
                dedup_days=args.dedup_days,
            )
            sys.exit(0 if success else 1)
        except Exception as e:
            logger.exception(f"Collection failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
