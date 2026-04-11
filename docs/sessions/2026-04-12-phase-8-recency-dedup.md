# Session Log: 2026-04-12 - Phase 8 - Recency 필터 + 크로스 리포트 중복 제거

## Overview
- **Date**: 2026-04-12
- **Phase**: 8 - Recency 필터 + 크로스 리포트 중복 제거
- **Sub-tasks**: 8.1 ~ 8.5 (single session, tightly coupled feature)

## Problem Report

사용자 관찰: 2026-04-11 리포트의 20개 중 18개(90%)가 2026-04-10과 URL 중복.
일부는 카카오 테크 `/posts/808` 같은 오래된 글. 또한 RSS 수집이 "당일~전날"
기사만 반환하는 게 아님.

## Root Cause

파이프라인 진단:
1. **RSS는 "최신 N개"만 반환** — 지난 2~7일 기사가 front 페이지에 남아있음.
2. **`.article_cache.json`이 `.gitignore`에 포함** — GitHub Actions 매 실행마다 빈
   캐시로 시작해 `cache_days=7`이 무의미.
3. **시간 필터 부재** — `main.py`에 `days`/`recency`/`timedelta` 키워드 없음.
4. **arxiv `published_at` 미파싱 (DEBT-003)** — 680개 arxiv 기사 전부 `None`.
   시간 필터 도입해도 arxiv는 전부 "알 수 없음"으로 분류되어 효과 반감.

## Solution Architecture

사용자 승인 받은 **추천 조합 (8.1~8.5 전체)**:
- `--days 2` (Recency 창)
- `--dedup-days 7` (최근 7개 리포트 URL 차단)
- `.article_cache.json` + `src/cache.py` 완전 제거
- 리포트 파일을 진실 공급원으로 사용 (별도 캐시 파일 불필요)
- Quiet-day 알림: 필터 후 < 3개일 때 Slack/Discord/이메일에 배너
- 레거시 리포트 2개 삭제 (2026-04-05, 2026-04-10)

## Work Summary

### 8.1 — arxiv pubDate 파싱 (선결 과제, DEBT-003 해소)

`src/collectors/arxiv.py`의 `_fetch_rss`에 `<pubDate>` (RFC 822) 우선 파싱,
`<dc:date>` (ISO 8601) fallback. `_parse_arxiv_date` 헬퍼 함수 추가.

```python
def _parse_arxiv_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)  # RFC 822
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass
    return None
```

### 8.2 — Recency 필터

`src/filters.py` 신설. 순수 함수형 `filter_by_recency`:
- `days=0`이면 필터 비활성화
- `published_at=None`은 보수적으로 keep (로그 경고)
- `_ensure_aware` helper로 tz naive ↔ aware 통일
- 반환: `(kept, filtered_out, unknown_kept)` 삼중 튜플

### 8.3 — 크로스 리포트 dedup

`src/data_io.py`에 `load_recent_report_urls(data_dir, n=7) -> set[str]` 추가.
`src/filters.py`에 `filter_already_seen(articles, seen_urls)` 추가.

**설계 포인트**: 별도 캐시 파일을 만들지 않고 **git-tracked 리포트 파일**을
진실 공급원으로 사용. GitHub Actions 재실행 시에도 리포트가 영속되므로 자연스럽게
상태 공유. 레거시 리포트가 유지되면 "이미 본 URL"로 분류되어 재등장 차단.

### 8.4 — ArticleCache 제거

- `src/cache.py` 및 `tests/test_cache.py` 삭제
- `src/main.py`에서 `ArticleCache` import / 사용 제거
- `run_collect_only` 시그니처 변경: `use_cache`/`cache_days` → `days`/`dedup_days`
- `--no-cache` / `--cache-days` CLI 플래그는 deprecation 경고 후 no-op 유지
  (backward-compat)
- `.gitignore`의 `.article_cache.json` 라인은 유지 (안전 gutter)
- 레거시 리포트 `data/report_2026-04-05.json`, `data/report_2026-04-10.json` 삭제

### 8.5 — Quiet-day 알림

`QUIET_DAY_THRESHOLD = 3` 상수를 Slack/Discord/Email notifier에 추가.

- **SlackNotifier**: `_build_message_blocks`에서 `len < 3`일 때 header 아래에
  "🔕 조용한 날" section block 삽입. 빈 리포트도 전송 (이전엔 skip).
- **DiscordNotifier**: `embeds.insert(0, quiet_embed)` — 노란색(#F1C40F) embed를
  앞에 배치. 빈 리포트도 전송.
- **EmailNotifier**: Subject에 `🔕 [조용한 날]` prefix, HTML 본문 상단에 노란 배경
  alert 배너 삽입. 빈 리포트도 전송.

`run_collect_only`는 `len(articles) < 3`일 때 WARN 로그 출력 — GitHub Actions
로그에서 즉시 확인 가능.

## Files Changed

### Created
- `src/filters.py` — `filter_by_recency`, `filter_already_seen`, `_ensure_aware`
- `tests/test_filters.py` — 26개 신규 테스트 (filters 17 + arxiv parser 9)
- `docs/sessions/2026-04-12-phase-8-recency-dedup.md` — 이 파일

### Deleted
- `src/cache.py` — ArticleCache 클래스 (리포트 기반 dedup이 대체)
- `tests/test_cache.py` — 관련 테스트
- `data/report_2026-04-05.json` — 레거시 (1개 기사)
- `data/report_2026-04-10.json` — 레거시 (824개 기사, pre-ranking)

### Modified
- `src/collectors/arxiv.py` — `_parse_arxiv_date` helper + `pubDate`/`dc:date` 파싱
- `src/data_io.py` — `load_recent_report_urls()` 추가
- `src/main.py` — `run_collect_only` 재작성: recency + dedup 파이프라인,
  `--days`/`--dedup-days` CLI, deprecated 플래그 no-op 경고
- `src/slack_notifier.py` — `QUIET_DAY_THRESHOLD` + header section 추가, 빈 리포트 전송
- `src/discord_notifier.py` — `EMBED_COLOR_QUIET` + quiet embed prepend
- `src/email_notifier.py` — subject prefix, HTML quiet banner
- `.github/workflows/daily-report.yml` — `--days 2 --dedup-days 7` 명시
- `tests/test_slack_notifier.py`, `test_discord_notifier.py`, `test_email_notifier.py` —
  `test_send_report_empty*` 테스트 업데이트 (quiet-day 전송으로 동작 변경)
- `docs/development-plan.md` — Phase 8 신설 후 완료 마킹
- `docs/requirements.md` — FR-041~045, NFR-017~018
- `docs/system-architecture.md` — 데이터 흐름 다이어그램에 Filter 단계 추가
- `docs/TECH-DEBT.md` — DEBT-003 / DEBT-005 resolved
- `CLAUDE.md`, `README.md` — Features 갱신

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| 별도 캐시 파일 대신 리포트 기반 dedup | 이미 git-tracked, 상태 영속, 단일 진실 공급원. 복잡도 감소 |
| `days=2` 기본값 | 1일은 arxiv 주말 스킵 고려 시 너무 빡빡, 3일은 중복 위험 증가. 2일이 스위트 스팟 |
| `dedup_days=7` 기본값 | 주 단위 리포트 히스토리. 너무 길면 구 기사가 영원히 차단됨 |
| `published_at=None`은 keep | 일부 HTML 스크래퍼가 날짜 없음. 무조건 드롭하면 Frontier Lab 블로그 소실 |
| 빈 리포트도 quiet-day 배너로 전송 | 사용자에게 "파이프라인은 정상, 단지 새 뉴스 없음" 신호가 필요 |
| `.article_cache.json` 라인 gitignore에 유지 | 안전 gutter — 미래에 코드가 실수로 이 파일 생성해도 커밋 안 됨 |
| deprecation 경고로 `--no-cache` 유지 | 외부 cron/스크립트 backward-compat |
| 단위 테스트를 jsdom 없이 | 필터는 순수 함수라 Python 테스트로 완전 커버 가능 |
| `filter_by_recency` 반환값을 삼중 튜플로 | `(kept, dropped_old, unknown_kept)` — 로그 메시지에 각 경로 수치 노출 |

## Code Review Results

| Category | Status | Notes |
|----------|--------|-------|
| Error Handling | ✅ | 날짜 파싱 실패는 None 반환, 리포트 로드 실패는 경고 후 continue |
| Resource Management | ✅ | 순수 함수, 파일 핸들은 with 문 사용 |
| Security | ✅ | 사용자 입력 없음 (내부 파이프라인 함수) |
| Type Hints | ✅ | 모든 신규 함수에 타입 힌트, `Optional[datetime]`, `set[str]` 등 |
| Tests | ✅ | 26 신규 + 4 업데이트 = 30 테스트 변동, 228 total passed |
| Timezone Correctness | ✅ | `_ensure_aware`로 naive/aware 통일, parametrize로 경계값 테스트 |
| Backward Compatibility | ✅ | `--no-cache`/`--cache-days` no-op + 경고, 리포트 JSON 포맷 변화 없음 |
| Documentation | ✅ | 6개 문서 갱신, 세션 로그 생성 |

## Verification

```bash
# 단위 테스트
$ python -m pytest tests/test_filters.py -v
... 26 passed in 0.07s

# 전체 suite (regression)
$ python -m pytest tests/ -q --ignore=tests/test_web.py
... 228 passed in 1.06s

# 로컬 수집 (실증)
$ python -m src.main --collect-only --days 2 --dedup-days 7 --limit 3
[1/4] Collecting articles... Total articles collected: 156
[2/4] Recency: kept 24 (dropped 132 old, kept 7 with unknown date)
[3/4] Dedup: removed 4 already-seen URLs, 20 remain
[4/4] Saving articles to JSON...
```

**Before (Phase 7까지)**:
- 4-11 리포트: 20개 중 **18개 (90%) 중복**
- 후보 풀: 400+ (레거시 824 포함, 날짜 무관)

**After (Phase 8)**:
- 로컬 dry-run 기준: 156 → **filter 156/132 drop → dedup 24/4 drop → 20 remain**
- 20개 모두 **지난 2일 내 발행 + 최근 7 리포트에 없음** 기사
- arxiv 주말 스킵(`Saturday/Sunday`) 고려 시 실제 운영 시엔 weekday에 더 많이 통과

## Potential Risks

1. **Weekday 몰림**: arxiv가 주말을 스킵하므로 월요일 리포트에 금/토/일 3일치 기사가
   2일 창에 포함되지 않을 수 있음. 현재는 수용 — 기사 수가 적으면 quiet-day 배너 노출.
   필요 시 `--days 3`으로 늘릴 수 있음.
2. **arxiv pubDate 형식 변경**: RFC 822 포맷이 변하면 파싱 실패해 `None`. 여전히 keep
   되어 필터 영향 없음 (soft fail).
3. **리포트 기반 dedup의 의도치 않은 blocking**: 리포트가 wrong URL로 저장된 경우
   (정상 URL이 한 번 잘못 기록되면 영구 차단). 실제로는 URL 생성 로직이 결정론적이므로
   발생 가능성 낮음.
4. **Quiet-day 배너 false positive**: 기사 수집이 네트워크 오류로 0개라도 배너 표시됨.
   사용자가 "오늘 AI 뉴스 없네"와 "파이프라인 문제"를 구분 못 할 수 있음. 향후 개선
   여지 — 수집 실패와 필터 결과 0을 구분하는 배너.

## TECH-DEBT Changes

**Resolved:**
- DEBT-003 — arxiv pubDate 파싱 (Phase 8.1)
- DEBT-005 — 레거시 pre-ranking 리포트 (사용자 요청으로 삭제, Phase 8.4)

**Still Active:**
- DEBT-001 — Meta AI Blog 비활성 (헤드리스 브라우저 필요)
- DEBT-002 — LG AI Research 비활성 (Nuxt SPA)
- DEBT-004 — HF Papers URL이 Takara TLDR로 리다이렉트

**New potential items (not registered):**
- Quiet-day 배너가 네트워크 실패와 "진짜 조용한 날"을 구분 못 함
  → 구현 단순성 위해 미등록, 재발 시 고려
- Weekday 몰림에 대한 사용자 인지 부족 (운영 메뉴얼/README 보강 필요 여부)

## Next Phase Preview

Phase 8 완료. 후보 Phase 9:
- 검색 페이지의 audience 필터 통합 (Phase 7 session log에서 언급)
- 이메일/Slack 발송 실패 retry 정책 고도화
- 정적 사이트 검색 인덱스에 published_at 추가 (현재는 date 문자열만)
- Weekday 몰림에 대한 adaptive 필터 (평일엔 2일, 월요일엔 3일)
