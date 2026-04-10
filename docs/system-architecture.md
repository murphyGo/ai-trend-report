# AI Report Service - 시스템 아키텍처

## 1. 시스템 개요

AI Report Service는 **17개 소스에서 AI 관련 기사/논문을 자동 수집**하고,
**Claude가 중요도 기준 상위 20개를 선별**해 한국어 요약을 생성,
**Slack / Discord / 이메일**로 발송하며 **GitHub Pages 정적 사이트**로 공개하는
자동화 서비스입니다.

**프로덕션 실행 경로: GitHub Actions 스케줄 (매일 KST 09:00)**

### 3가지 요약 경로
- **Claude Code CLI 모드 (기본, GitHub Actions 경로)**: `daily-report.yml`에서
  Claude Code CLI를 `-p` non-interactive로 실행. Pro/Max OAuth 토큰 사용 → API 키 불필요.
  랭킹+요약이 한 번의 CLI 호출 내부에서 2단계로 수행됨.
- **Anthropic API 모드 (`--use-api`)**: `src/summarizer.py`가 기사별로 Claude API를 직접 호출.
  `ANTHROPIC_API_KEY` 필요. 로컬 개발 또는 OAuth 토큰이 없는 환경용.
- **로컬 Claude Code CLI**: 로컬에서 같은 프롬프트를 `claude -p`로 수동 실행 가능.

---

## 2. 아키텍처 다이어그램

### 프로덕션 (GitHub Actions) - 기본 경로

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       GitHub Actions (KST 09:00)                         │
│                                                                          │
│  daily-report.yml                                                        │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────────────┐              │
│  │  17 Sources │──▶│ Python CLI   │──▶│ Claude Code CLI   │              │
│  │ (RSS/HTML)  │   │ collect-only │   │ (OAuth, -p, 2단계)│              │
│  └─────────────┘   └──────────────┘   └──────────┬────────┘              │
│                           │                      │                      │
│                    articles_*.json        report_*.json                  │
│                                                  │                      │
│                                                  ▼                      │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐               │
│  │    Slack    │◀──┤  Notifiers   │◀──┤  git commit      │               │
│  │   Discord   │   │ (slack/disc/ │   │  data/report_*   │               │
│  │   Email     │   │  email)      │   └────────┬─────────┘               │
│  └─────────────┘   └──────────────┘            │                         │
│                                                │ workflow_run trigger    │
│                                                ▼                         │
│  deploy-pages.yml                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │   static_generator.py → _site/ → actions/deploy-pages            │    │
│  │   SITE_BASE_URL=/${repo_name} 자동 주입 (서브패스 지원)          │    │
│  │   홈 대시보드, 리포트, 카테고리/소스/검색 페이지                 │    │
│  └─────────────────────────────────────────────┬────────────────────┘    │
│                                                │                         │
└────────────────────────────────────────────────┼─────────────────────────┘
                                                 ▼
                                       https://{user}.github.io/{repo}/
```

### 로컬 개발 (--use-api 모드)

```
┌──────────────────────────────────────────────────────────────┐
│                  Local CLI (--use-api)                       │
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐   ┌────────┐ │
│  │  Sources │──▶│Collectors│──▶│  Summarizer  │──▶│ Slack /│ │
│  │          │   │          │   │(Anthropic API│   │Discord/│ │
│  │          │   │          │   │ per article) │   │ Email  │ │
│  └──────────┘   └──────────┘   └──────────────┘   └────────┘ │
│                                                              │
│  → python -m src.main --use-api                              │
└──────────────────────────────────────────────────────────────┘
```

### 랭킹 + 요약 (Claude Code CLI 모드 내부)

```
articles_*.json  (~200개)
       │
       ▼
┌─────────────────────────────────────────────────────┐
│ Claude Code CLI (daily-report.yml 프롬프트)         │
│                                                     │
│  Stage 1: Rank                                      │
│  전 기사 평가 → 상위 20개 선별                      │
│  판단 기준: 기술 신규성 / 영향력 / 소스 신뢰도 /    │
│             카테고리 다양성 / 한국 관련성           │
│                                                     │
│  Stage 2: Summarize                                 │
│  선별된 20개만 한국어 요약 + 카테고리 분류          │
└─────────────┬───────────────────────────────────────┘
              ▼
        report_*.json (20개)
```

---

## 3. 데이터 흐름

### 전체 파이프라인 (프로덕션)

```
1. Collect          2. Persist            3. Rank+Summarize     4. Distribute         5. Publish
┌──────────┐       ┌──────────┐          ┌──────────────┐      ┌──────────┐         ┌──────────┐
│ Fetch    │──────▶│ Save     │─────────▶│ Claude Code  │─────▶│ Notify   │────────▶│ Deploy   │
│ 17 src   │       │ articles │          │ CLI (2-stage)│      │ channels │         │ GH Pages │
└──────────┘       └──────────┘          └──────────────┘      └──────────┘         └──────────┘
     │                  │                       │                    │                   │
     ▼                  ▼                       ▼                    ▼                   ▼
 RSS/HTML         articles_*.json        report_*.json        Slack/Discord/       _site/ →
 fetch            (gitignore)            (git 추적)            Email 전송           GH Pages
```

### 단계별 설명

1. **Collect**: `src/main.py --collect-only` → 17개 collector 순차/병렬 수집.
   `ArxivCollector`는 카테고리당 20개 상한, 다른 RSS 수집기는 `max_items=15`.
2. **Persist**: `data_io.save_articles` → `data/articles_YYYY-MM-DD.json` (gitignore).
3. **Rank + Summarize**: Claude Code CLI가 `daily-report.yml`의 2단계 프롬프트로
   상위 20 선별 → 한국어 요약 → `data/report_YYYY-MM-DD.json` (git 추적).
4. **Distribute**: `--send-only`로 Slack/Discord/Email 알림. 설정된 채널만.
5. **Publish**: `data/report_*.json` 커밋 → `deploy-pages.yml` `workflow_run` 트리거 →
   `static_generator.py`가 홈/리포트/카테고리/소스/검색 HTML 생성 → GitHub Pages 배포.

---

## 4. 모듈 구조

```
src/
├── __init__.py
├── main.py                   # CLI 진입점 (수집/요약/전송/대시보드/정적 사이트)
├── config.py                 # 설정 로더 (YAML + 환경 변수 + .env)
├── models.py                 # Article / Report / Category (12) / Source (19)
├── data_io.py                # JSON 읽기/쓰기, 파일명 규칙
├── cache.py                  # 기사 중복 캐시 (.article_cache.json, URL 해시)
├── summarizer.py             # Anthropic API 요약 (--use-api 경로)
│
├── slack_notifier.py         # Slack Block Kit 메시지
├── discord_notifier.py       # Discord Webhook
├── email_notifier.py         # SMTP 이메일 (HTML 템플릿)
│
├── static_generator.py       # GitHub Pages 정적 사이트 생성 (Jinja2)
│                             #   - 홈 대시보드 / 리포트 / 카테고리 / 소스 / 검색
│                             #   - base_url prefix 지원 (SITE_BASE_URL)
│                             #   - category / source label·color·tier 헬퍼
├── web/                      # FastAPI 로컬 대시보드 (--serve)
│   ├── app.py
│   └── ...
├── static/
│   ├── css/style.css         # 단일 스타일시트
│   ├── js/search.js          # Fuse.js 검색 (window.SITE_BASE_URL 사용)
│   └── templates/
│       ├── base.html         # 공통 레이아웃 + 네비 (Home/Categories/Sources/Search)
│       ├── index.html        # 홈 대시보드
│       ├── report.html       # 개별 리포트 페이지
│       ├── categories_index.html  # /categories/ 그리드 인덱스
│       ├── category.html     # /categories/{NAME}.html
│       ├── sources_index.html     # /sources/ 그리드 인덱스
│       ├── source.html       # /sources/{NAME}.html
│       └── search.html       # 검색 페이지
│
├── utils/                    # retry, logging 헬퍼
│   ├── retry.py
│   └── logging.py
│
└── collectors/
    ├── __init__.py
    ├── base.py               # BaseCollector (HTTP 세션 + 재시도)
    ├── rss_base.py           # RSSCollector — feedparser 기반 공통 베이스
    │
    ├── arxiv.py              # arXiv (max_per_category=20)
    ├── anthropic_blog.py     # Anthropic News
    ├── openai_blog.py        # OpenAI News
    ├── google_blog.py        # Google DeepMind/Research/Labs/Gemini
    ├── huggingface_blog.py   # Hugging Face Blog
    │
    ├── rss_tier1.py          # MS Research, NVIDIA Dev, MarkTechPost,
    │                         # BAIR, Stanford AI, TechCrunch, VentureBeat (7개)
    ├── hf_papers.py          # HF Daily Papers (Takara 비공식 RSS)
    ├── mit_tech_review.py    # MIT Tech Review (RSS + AI 키워드 필터)
    │
    ├── korean_news.py        # AI타임스 (HTML 스크래핑)
    ├── korean_rss.py         # Naver D2 (Atom), Kakao Tech (RSS)
    │
    ├── meta_ai_blog.py       # (비활성 — DEBT-001, 봇 차단)
    └── lg_ai_research.py     # (비활성 — DEBT-002, Nuxt SPA)

data/
├── articles_*.json           # 수집된 원본 (gitignore)
└── report_*.json             # Claude 요약 리포트 (git 추적)

.github/workflows/
├── daily-report.yml          # 매일 수집 → 랭킹+요약 → 알림 → 커밋
├── deploy-pages.yml          # daily-report 성공 후 GitHub Pages 배포
└── ci.yml                    # PR 테스트/린트 (Python 3.9~3.12 매트릭스)
```

### 모듈 의존성 (단순화)

```
main.py
   │
   ├── config.py
   ├── cache.py
   ├── data_io.py ──▶ models.py
   │
   ├── collectors/
   │     ├── base.py
   │     ├── rss_base.py ──▶ base.py (feedparser 사용)
   │     └── (구체 수집기 17개) ──▶ base.py / rss_base.py ──▶ models.py
   │
   ├── summarizer.py (--use-api)
   │
   ├── {slack, discord, email}_notifier.py
   │
   ├── static_generator.py ──▶ Jinja2, models.py
   │
   └── web/app.py (FastAPI, --serve)
```

---

## 5. 핵심 컴포넌트

### 5.1 BaseCollector (추상 클래스)

```python
class BaseCollector(ABC):
    source: Source            # 서브클래스가 지정
    base_url: str

    @abstractmethod
    def fetch_articles(self) -> list[Article]: ...

    @abstractmethod
    def parse_article_content(self, url: str) -> str: ...

    def _fetch_html(self, url) -> Optional[BeautifulSoup]: ...  # 재시도 포함
    def _fetch_text(self, url) -> Optional[str]: ...
    def collect(self) -> list[Article]: ...
```

### 5.2 RSSCollector (RSS/Atom 공통 베이스)

```python
class RSSCollector(BaseCollector):
    feed_url: str = ""
    max_items: int = 15
    feed_user_agent: Optional[str] = None  # Cloudflare 우회용

    def fetch_articles(self) -> list[Article]:
        # feedparser로 파싱, entry 메타데이터 + content 추출
        # parse_article_content는 기본 빈 문자열 (RSS content 이미 포함)
```

17개 수집기 중 **10개가 이 베이스를 상속** (arXiv는 레거시 ElementTree 기반으로 별도,
Google/Anthropic/OpenAI/HF Blog/AI타임스/Meta/LG는 HTML 스크래핑).

### 5.3 Summarizer (`--use-api` 전용)

```python
class Summarizer:
    def __init__(self, config: Config): ...
    def summarize(self, article: Article) -> Article: ...
    def summarize_batch(self, articles: list[Article]) -> list[Article]: ...
```

기사당 1회 Anthropic API 호출. 로컬 개발 또는 OAuth 토큰이 없는 경우에만 사용.
프로덕션 경로는 Claude Code CLI가 `daily-report.yml` 프롬프트 안에서 처리하며
이 모듈을 호출하지 않음.

### 5.4 Notifiers

```python
class SlackNotifier:       # Block Kit 리치 메시지
class DiscordNotifier:     # Webhook + Embed
class EmailNotifier:       # SMTP + HTML 템플릿, 다중 수신자
```

셋 다 `Config`에서 웹훅/SMTP 정보 로드. 설정된 채널만 활성화.

### 5.5 StaticSiteGenerator

```python
class StaticSiteGenerator:
    def __init__(self, data_dir, output_dir, base_url=None):
        # base_url: None이면 SITE_BASE_URL 환경변수 또는 빈 문자열

    def generate(self) -> None:
        # _prepare_output_dir, _copy_static_files
        # _generate_index, _generate_report_pages,
        # _generate_category_pages, _generate_source_pages,
        # _generate_search_page
        # _generate_reports_json, _generate_search_index
```

Jinja2 환경에 커스텀 필터 등록:
`category_color`, `category_label`, `source_label`, `source_color`, `source_tier`.

### 5.6 홈 대시보드 (index.html)

기사 월 대신 **탐색 허브** 구조:
- Hero + CTA 버튼 (오늘의 리포트 보기)
- Stats 4 카드 (Articles / Categories / Sources / Total Reports)
- Today's Categories 그리드 (상위 8개, 기사 수 많은 순)
- Today's Sources 그리드 (상위 8개)
- Recent Reports 리스트

풀 기사 목록은 `/reports/{date}.html` 에만 렌더.

---

## 6. 외부 의존성

| 라이브러리 | 용도 |
|-----------|------|
| `requests` | HTTP 요청 |
| `beautifulsoup4`, `lxml` | HTML 파싱 |
| `feedparser` | RSS / Atom 피드 파싱 (RSSCollector) |
| `anthropic` | Claude API 클라이언트 (`--use-api` 경로) |
| `slack-sdk` | Slack Block Kit |
| `jinja2` | 정적 사이트 템플릿 |
| `fastapi`, `uvicorn` | 로컬 웹 대시보드 (`--serve`) |
| `PyYAML` | YAML 설정 파싱 |
| `python-dotenv` | `.env` 환경 변수 로드 |
| `python-dateutil` | 날짜 파싱 |
| `pytest`, `pytest-mock`, `responses` | 테스트 |

외부 서비스:
- **Claude Code CLI** (GitHub Actions에서 `npm install -g @anthropic-ai/claude-code`)
- **GitHub Actions + GitHub Pages**
- **Slack / Discord Webhooks**, **SMTP 서버** (Gmail 등)

---

## 7. 설정 관리

### 7.1 환경 변수 (GitHub Secrets / .env)

| 변수 | 설명 | 우선순위 |
|------|------|---------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Pro/Max OAuth 토큰 | 1 (프로덕션 기본) |
| `ANTHROPIC_API_KEY` | Claude API 키 | 2 (폴백 / `--use-api`) |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook | — |
| `DISCORD_WEBHOOK_URL` | Discord Webhook | — |
| `EMAIL_USERNAME` / `EMAIL_PASSWORD` / `EMAIL_RECIPIENTS` | SMTP | — |
| `SITE_BASE_URL` | 정적 사이트 URL prefix | `deploy-pages.yml`이 자동 주입 |

### 7.2 config.yaml (선택, gitignore)

```yaml
anthropic:
  model: claude-sonnet-4-20250514  # --use-api 전용

collectors:
  arxiv:
    enabled: true
    categories: [cs.AI, cs.LG, cs.CL]
  google_blog:
    enabled: true
  anthropic_blog:
    enabled: true

slack:
  webhook_url: ${SLACK_WEBHOOK_URL}

discord:
  webhook_url: ${DISCORD_WEBHOOK_URL}

email:
  enabled: false
  smtp_host: smtp.gmail.com
  smtp_port: 587
  use_tls: true
  username: ${EMAIL_USERNAME}
  password: ${EMAIL_PASSWORD}
  sender: ai-report@example.com
  recipients: [user@example.com]

logging:
  level: INFO
  log_file: null
```

대부분 값은 환경 변수로 주입되므로 `config.yaml`이 없어도 동작함.

---

## 8. 에러 처리 전략

| 실패 지점 | 전략 | 영향 |
|----------|------|------|
| 소스 수집 실패 | 해당 소스 스킵, 로그 기록 | 다른 16개 계속 진행 |
| 기사 파싱 실패 | 해당 기사 스킵, 로그 기록 | 다른 기사 계속 진행 |
| HTTP 일시 오류 | `utils/retry.py` 지수 backoff, 최대 3회 | 대부분 복구 |
| Cloudflare 403 (MarkTechPost) | Feedly UA fallback | 정상 수집 |
| Claude CLI 실패 | 워크플로우 실패 → `notify-on-failure` Slack 알림 | 해당 날 리포트 누락 |
| Slack/Discord/Email 전송 실패 | 재시도 후 로그 | 다른 채널에는 영향 없음 |
| 정적 사이트 빌드 실패 | `deploy-pages.yml` 실패 | 이전 배포 유지 |

---

## 9. 확장 고려사항

### 새 RSS 소스 추가 (가장 흔함)

1. `Source` enum에 항목 추가 (`src/models.py`)
2. `rss_tier1.py` 또는 신규 파일에 `RSSCollector` 상속 클래스 작성 (~5줄)
3. `src/collectors/__init__.py`에 export
4. `src/main.py:get_enabled_collectors()`에 등록
5. (선택) `static_generator.py`의 `SOURCE_LABELS`/`SOURCE_TIER_MAP`에 display 정보 추가

### 새 HTML 스크래핑 소스

1. `BaseCollector` 상속, `fetch_articles` / `parse_article_content` 구현
2. 위 단계 3~5 동일

### 새 알림 채널

1. `BaseNotifier` 패턴은 아직 추상화되지 않음. 신규 notifier 파일 생성
2. `Config`에 섹션 추가, `main.py:run_send_only()`에 분기
3. GitHub Actions env 주입

### 카테고리/소스 브라우징 확장

- 카테고리/소스 색상은 `static_generator.py`의 맵에서 수정
- 새 카테고리 추가 시 `Category` enum + `get_category_color/label` 맵 동기화

---

## 10. 배포 구조

### GitHub Actions (프로덕션, 기본)

```
┌───────────────────────────────────────────────────────────────────┐
│                    GitHub Actions Scheduler                       │
│                  (cron: '0 0 * * *' = KST 09:00)                  │
│                                                                   │
│  daily-report.yml                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  1. Checkout + Setup Python 3.11 + Install deps             │  │
│  │  2. Setup Node.js + Install Claude Code CLI                 │  │
│  │  3. python -m src.main --collect-only                       │  │
│  │  4. claude --model sonnet -p "...2단계 프롬프트..." (OAuth)  │  │
│  │  5. python -m src.main --send-only  (Slack/Discord/Email)   │  │
│  │  6. git commit data/report_*.json && git push               │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              │ workflow_run                       │
│                              ▼                                    │
│  deploy-pages.yml                                                 │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  1. Checkout (head_branch)                                  │  │
│  │  2. SITE_BASE_URL=/${{ github.event.repository.name }}      │  │
│  │  3. python -m src.main --generate-static --static-output _site │
│  │  4. actions/upload-pages-artifact                           │  │
│  │  5. actions/deploy-pages                                    │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                              │                                    │
└──────────────────────────────┼────────────────────────────────────┘
                               ▼
                  https://{user}.github.io/{repo}/
                    ├── index.html        (대시보드)
                    ├── reports/
                    ├── categories/
                    ├── sources/
                    └── search.html
```

### 로컬 Cron (대안)

```cron
0 9 * * * cd /path/to/ai-report && .venv/bin/python -m src.main --use-api \
  >> /var/log/ai-report.log 2>&1
```

이 경우 `ANTHROPIC_API_KEY`가 필요하며 GitHub Pages 자동 배포는 사용할 수 없음
(수동으로 `--generate-static` 실행 후 별도 호스팅).

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|---------|
| 2024-04-05 | 1.0 | 초기 아키텍처 문서 작성 |
| 2026-04-11 | 2.0 | Phase 6 반영 — 17 소스 / RSSCollector / Claude 상위 20 랭킹 / 카테고리·소스 브라우징 / 홈 대시보드 / GitHub Actions + Pages 배포 구조 |
