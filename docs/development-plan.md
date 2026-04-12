# AI Report Service - 개발 계획

## 현재 상태

| 컴포넌트 | 상태 | 비고 |
|---------|------|------|
| 프로젝트 구조 | ✅ Complete | src/ 구조 완성 |
| 데이터 모델 | ✅ Complete | Article, Category, Source (19종) + 직렬화 |
| Collectors | ✅ Complete | **17개 활성** (arXiv, Frontier Lab 4, 리서치 4, 미디어 4, 한국 3) + 2개 비활성 |
| RSSCollector 공통 베이스 | ✅ Complete | feedparser 기반, 신규 RSS 소스 5줄로 추가 |
| Claude 랭킹 (상위 20) | ✅ Complete | daily-report.yml 2단계 프롬프트 (rank → summarize + audience 태깅) |
| 독자 레벨 필터 | ✅ Complete | Phase 7 — GENERAL/DEVELOPER/ML_EXPERT, 하이브리드 태깅, 전역 필터 바 |
| Recency + 크로스 리포트 Dedup | ✅ Complete | Phase 8 — 2일 시간창 + 7개 리포트 URL 차단, arxiv pubDate 파싱, Quiet-day 알림 |
| Summarizer | ✅ Complete | Claude Code CLI (기본) + Anthropic API (`--use-api`) |
| Slack / Discord / Email Notifier | ✅ Complete | 3채널 모두 구현 |
| CLI | ✅ Complete | main.py — 수집/요약/전송/대시보드/정적사이트 모드 |
| 데이터 I/O | ✅ Complete | JSON 직렬화, report 파일만 git 추적 |
| 캐시 / 병렬 수집 | ✅ Complete | cache.py + ThreadPoolExecutor |
| 테스트 | ✅ Complete | pytest 188개 테스트 |
| GitHub Actions | ✅ Complete | daily-report + deploy-pages + ci |
| GitHub Pages 정적 사이트 | ✅ Complete | 홈 대시보드 + 리포트 + 카테고리 브라우징 + 소스 브라우징 + 검색 |
| 서브패스 배포 지원 | ✅ Complete | `SITE_BASE_URL` 자동 주입 |
| 문서화 | ✅ Complete | CLAUDE.md, README.md, docs/ 4종 |

---

## Phase 1: 핵심 기능 (완료)

### 1.1 프로젝트 초기 설정
- [x] 프로젝트 구조 설정
- [x] requirements.txt 작성
- [x] config.yaml 설정 체계 구축
- [x] .gitignore 설정

### 1.2 데이터 모델 정의
- [x] Article 데이터클래스 정의
- [x] Category Enum 정의
- [x] Source Enum 정의

### 1.3 수집기 구현
- [x] BaseCollector 추상 클래스 구현
- [x] ArxivCollector 구현 (RSS 피드)
- [x] GoogleBlogCollector 구현 (HTML 스크래핑)
- [x] AnthropicBlogCollector 구현 (HTML 스크래핑)

### 1.4 요약기 구현
- [x] Claude API 연동
- [x] 한국어 요약 프롬프트 설계
- [x] 카테고리 분류 로직 구현

### 1.5 알림 구현
- [x] Slack Webhook 연동
- [x] Block Kit 메시지 포맷팅
- [x] 카테고리별 그룹핑

### 1.6 CLI 구현
- [x] main.py 진입점
- [x] --dry-run 옵션
- [x] --limit 옵션
- [x] --verbose 옵션

---

## Phase 1.5: Claude Code 기반 전환 (완료)

Anthropic API 직접 호출 대신 Claude Code 스킬 기반으로 요약 수행 가능하도록 전환.

### 1.5.1 데이터 직렬화
- [x] Article.to_dict() / from_dict() 추가
- [x] Report.to_dict() / from_dict() 추가
- [x] data_io.py 유틸리티 생성 (JSON 읽기/쓰기)
- [x] data/ 디렉토리 설정

### 1.5.2 CLI 모드 분리
- [x] --collect-only: 수집만 수행, JSON 저장
- [x] --use-api: 기존 API 방식 (Anthropic API)
- [x] --send-only: JSON에서 로드하여 Slack 전송만
- [x] --input-json: 입력 JSON 파일 지정
- [x] --output-dir: 출력 디렉토리 지정

### 1.5.3 Claude Code 스킬
- [x] /ai-report 스킬 생성 (프로덕션 실행용)
- [x] 요약/분류 워크플로우 문서화

### 실행 방식

```
# 기본 모드 (Claude Code에서 요약)
python -m src.main                    # 수집 → JSON 저장
/ai-report                            # 요약 → Slack 전송

# API 모드 (기존 방식)
python -m src.main --use-api          # 전체 파이프라인
```

---

## Phase 2: 안정화

### 2.1 에러 처리 강화
- [x] 수집 실패 시 재시도 로직 (src/utils/retry.py, collectors/base.py)
- [x] 요약 실패 시 폴백 처리 (summarizer.py - API 재시도 + 기존 폴백 유지)
- [x] Slack 전송 실패 시 재시도 (slack_notifier.py)

### 2.2 로깅 개선
- [x] 구조화된 로깅 (JSON 형식)
- [x] 로그 레벨 설정
- [x] 로그 파일 출력

### 2.3 테스트 코드 추가
- [x] 단위 테스트 (pytest) - 142개 테스트 통과
- [x] Collector 모킹 테스트 - responses 라이브러리 사용
- [x] Summarizer 모킹 테스트 - API 모킹
- [x] 통합 테스트 - 데이터 파이프라인 및 E2E

### 2.4 문서화
- [x] README.md
- [x] CLAUDE.md
- [x] DESIGN.md
- [x] docs/requirements.md
- [x] docs/system-architecture.md
- [x] docs/development-plan.md

---

## Phase 3: 확장

### 3.1 새 소스 추가 (초기 3개 — Phase 6.1에서 13개 추가로 확장)
- [x] OpenAI 블로그 수집기 (openai_blog.py)
- [x] Hugging Face 블로그 수집기 (huggingface_blog.py)
- [x] 한국 AI 뉴스 수집기 (korean_news.py - AI타임스)

### 3.2 성능 최적화
- [x] 병렬 수집 (ThreadPoolExecutor) - src/main.py
- [x] 기사 캐싱 (중복 제거) - src/cache.py
- [x] CLI 옵션 추가 (--parallel, --no-cache, --cache-days)

### 3.3 이메일 알림 기능
- [x] EmailNotifier 클래스 구현 (SMTP)
- [x] HTML 이메일 템플릿 (카테고리별 섹션)
- [x] 다중 수신자 지원
- [x] CLI 플래그 추가 (`--email`, `--email-to`)
- [x] 설정 추가 (config.yaml: email 섹션)

```yaml
# config.yaml 예시
email:
  enabled: true
  smtp_host: smtp.gmail.com
  smtp_port: 587
  sender: ai-report@example.com
  recipients:
    - team@example.com
```

### 3.4 기타 확장
- [x] Discord Webhook 알림 (discord_notifier.py, --discord 플래그)
- [x] 웹 대시보드 (FastAPI + Jinja2, --serve 플래그)
- [ ] 기사 저장 (DB) — *deferred*

---

## Phase 4: 자동화 (완료)

### 4.1 GitHub Actions 스케줄러
- [x] 워크플로우 파일 생성 (`.github/workflows/daily-report.yml`)
- [x] 스케줄 설정 (매일 오전 9시 KST = UTC 00:00)
- [x] Secrets 설정 가이드
- [x] 리포트 아티팩트 자동 저장 (30일 보관)
- [x] 실패 시 Slack 알림

### 4.2 CI/CD 파이프라인
- [x] PR 시 테스트 자동 실행 (`.github/workflows/ci.yml`)
- [x] 린트/타입 체크 (flake8, mypy)
- [x] 테스트 커버리지 리포트 (Codecov 연동)
- [x] Python 3.9-3.12 매트릭스 테스트

### GitHub Secrets 설정 가이드

Repository Settings > Secrets and variables > Actions에서 다음 시크릿을 설정하세요:

| Secret 이름 | 필수 | 설명 |
|------------|------|------|
| `CLAUDE_CODE_OAUTH_TOKEN` | ⭐ | Pro/Max 구독 OAuth 토큰 (`~/.claude/.credentials.json`에서 추출) |
| `ANTHROPIC_API_KEY` | ⭐ | Claude API 키 (세션 키 없을 때 폴백) |
| `SLACK_WEBHOOK_URL` | ✅ | Slack Incoming Webhook URL |
| `DISCORD_WEBHOOK_URL` | ❌ | Discord Webhook URL (선택) |
| `EMAIL_USERNAME` | ❌ | SMTP 사용자명 (Gmail 주소) |
| `EMAIL_PASSWORD` | ❌ | SMTP 앱 비밀번호 ([생성 방법](https://myaccount.google.com/apppasswords)) |
| `EMAIL_RECIPIENTS` | ❌ | 이메일 수신자 (쉼표 구분: `a@x.com,b@x.com`) |
| `CODECOV_TOKEN` | ❌ | Codecov 토큰 (커버리지 리포트용) |

> ⭐ `CLAUDE_SESSION_KEY` 또는 `ANTHROPIC_API_KEY` 중 하나 필수.
>
> 📧 이메일: `EMAIL_USERNAME` + `EMAIL_PASSWORD` 설정 시 자동 활성화.

### 4.3 Claude Code CLI 지원
- [x] GitHub Actions 워크플로우에 Claude Code CLI 모드 추가
- [x] `-p` 플래그로 non-interactive 실행
- [x] 모델 선택 옵션 (sonnet/haiku/opus)
- [x] `use_api` 옵션으로 API/CLI 모드 선택 가능

### 4.4 OAuth 토큰 인증 (Pro/Max 구독)
- [x] `CLAUDE_CODE_OAUTH_TOKEN` 환경 변수 지원
- [x] Pro/Max 구독 기반 무료 인증
- [x] API 키 폴백 유지

### 워크플로우 실행 옵션

GitHub Actions 탭에서 "Run workflow" 버튼으로 수동 실행 가능:

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `dry_run` | Slack 전송 없이 테스트 | false |
| `limit` | 처리할 기사 수 제한 | 전체 |
| `use_api` | Anthropic API 직접 사용 | false (CLI 모드) |
| `model` | Claude 모델 선택 | sonnet |

### 인증 방식 비교

| 방식 | 환경 변수 | 비용 | 추출 방법 |
|------|----------|------|----------|
| **세션 키** (권장) | `CLAUDE_SESSION_KEY` | Pro/Max 구독 포함 | `~/.claude/.credentials.json` |
| **API 키** | `ANTHROPIC_API_KEY` | 토큰당 과금 | console.anthropic.com |

### 실행 모드 비교

| 모드 | 설명 | 사용 시점 |
|------|------|----------|
| **CLI 모드** (기본) | Claude Code CLI + 세션 키 | Pro/Max 구독자 |
| **API 모드** | Anthropic API 직접 호출 | API 키만 있을 때 |

---

## Phase 5: GitHub Pages 배포 (완료)

### 5.1 정적 사이트 생성기
- [x] `src/static_generator.py` - 정적 HTML 생성 모듈
- [x] Jinja2 템플릿 기반 HTML 생성
- [x] 리포트별 개별 페이지 생성

### 5.2 정적 사이트 템플릿
- [x] `src/static/templates/index.html` - 메인 페이지 (최신 리포트)
- [x] `src/static/templates/report.html` - 개별 리포트 페이지
- [x] `src/static/templates/search.html` - 검색 페이지
- [x] 반응형 CSS 스타일 (`src/static/css/style.css`)

### 5.3 검색 기능
- [x] `search-index.json` 생성 (전체 기사 메타데이터)
- [x] Fuse.js 기반 클라이언트 사이드 검색 (`src/static/js/search.js`)
- [x] 카테고리 필터링

### 5.4 GitHub Actions 배포
- [x] GitHub Pages 자동 배포 (`.github/workflows/deploy-pages.yml`)
- [x] 일일 리포트 생성 후 정적 사이트 업데이트
- [x] daily-report 워크플로우와 연동

### CLI 명령
```bash
# 정적 사이트 생성
python -m src.main --generate-static --static-output _site

# 로컬 테스트
cd _site && python -m http.server 8000
```

### GitHub Pages 설정 가이드
1. Repository Settings > Pages
2. Source: "GitHub Actions" 선택
3. 워크플로우 실행 후 자동 배포

### 정적 사이트 구조 (Phase 6 완료 후)

```
_site/
├── index.html              # 홈 대시보드 (Phase 6.6)
├── search.html             # Fuse.js 검색 페이지
├── reports/
│   ├── 2026-04-05.html    # 개별 리포트 (카테고리별 그룹 + 풀 요약)
│   └── 2026-04-10.html
├── categories/             # Phase 6.3
│   ├── index.html          # 12개 카테고리 카드 그리드
│   ├── LLM.html
│   ├── AGENT.html
│   └── ...
├── sources/                # Phase 6.5
│   ├── index.html          # 19개 소스 카드 그리드 (티어 색상)
│   ├── ARXIV.html
│   ├── ANTHROPIC_BLOG.html
│   └── ...
├── data/
│   ├── reports.json
│   └── search-index.json
├── css/style.css
└── js/search.js
```

---

## Phase 6: 소스 확장 + 정적 사이트 고도화 (완료)

Phase 5 GitHub Pages 기본 배포 이후 이루어진 대규모 확장. 수집 소스를 17개로 늘리고,
브라우징 UX를 재설계하며, Claude 판단을 파이프라인에 통합.

### 6.1 Tier 1~3 소스 확장 (13개 추가)

**목표**: arXiv / Google / Anthropic / OpenAI / HuggingFace / 한국뉴스 6개 기반에서
17개로 확장. 공통 RSS 수집기 베이스로 신규 추가 비용 최소화.

- [x] `RSSCollector` 공통 베이스 클래스 — `feedparser` 기반 (rss_base.py)
- [x] **Tier 1 (공식 RSS 7개)**: Microsoft Research, NVIDIA Developer, MarkTechPost,
  BAIR (Berkeley), Stanford AI Lab, TechCrunch AI, VentureBeat AI
- [x] **Tier 2 (3개)**: HF Daily Papers (Takara 비공식 RSS), Meta AI Blog (HTML,
  *비활성* — DEBT-001), MIT Tech Review (RSS + AI 키워드 필터)
- [x] **Tier 3 한국 (3개)**: Naver D2 (Atom), Kakao Tech (RSS), LG AI Research
  (HTML, *비활성* — DEBT-002)
- [x] `feedparser` 의존성 추가
- [x] MarkTechPost용 Feedly UA 오버라이드 (Cloudflare 우회)
- [x] `BaseCollector` HTTP 헤더 보강 (Accept, Accept-Language)

### 6.2 GitHub Pages 서브패스 배포 버그 수정

**증상**: 배포는 성공하지만 CSS가 적용되지 않고 리포트 링크가 404. 원인은 템플릿이
`/css/style.css`, `/reports/...` 같은 루트 절대경로를 사용하는데 GitHub Pages는
`/{repo_name}/` 서브패스에 배포됨.

- [x] `StaticSiteGenerator`에 `base_url` 파라미터 추가 (`SITE_BASE_URL` env var)
- [x] 모든 템플릿의 내부 URL에 `{{ base_url }}` prefix 적용
- [x] `reports.json` / `search-index.json`의 URL 필드도 prefix 반영
- [x] `base.html`에서 `window.SITE_BASE_URL` 주입 — `search.js`가 활용
- [x] `deploy-pages.yml`에서 `SITE_BASE_URL=/${{ github.event.repository.name }}` 자동 설정
- [x] `main.py`에 `--base-url` CLI 인자 추가
- [x] 부수 버그 수정: `search.js`의 `displayResults` const/함수 이름 섀도잉
- [x] `.gitignore` 수정 — `report_*.json`은 추적, `articles_*.json`은 ignore

### 6.3 카테고리별 브라우징

**목표**: 카테고리마다 전 리포트의 기사 누적 아카이브 페이지 제공.

- [x] `_generate_category_pages()` 메서드 — 카테고리 × 기사 집계 후 HTML 렌더
- [x] `/categories/index.html` — 12개 카테고리 카드 그리드 (기사 수 많은 순)
- [x] `/categories/{NAME}.html` × 12 — 해당 카테고리의 전 기사 (최신순)
- [x] `base.html` nav에 "Categories" 링크
- [x] 홈/리포트 페이지의 카테고리 제목을 전용 페이지로 링크
- [x] 초기 CSS (`.category-grid`, `.category-card`, `.category-header`)
- [x] **UI 재설계** — 초기 "상단 4px 띠 + box-shadow" 조합이 조잡해 보여 다음과 같이 정돈:
  - 왼쪽 5px accent bar (`::before` pseudo-element)
  - 타이틀을 `category.value` 단독으로 단순화
  - count를 솔리드 카테고리색 pill badge (rounded-full)
  - 빈 카테고리는 단일 그리드 뒤쪽에 `.empty` 상태로 배치
  - 카테고리 페이지 헤더도 동일한 카드 컨테이너 스타일로 통일
  - 모든 카테고리 색은 `--cat-color` CSS 커스텀 프로퍼티로만 inline 주입

### 6.4 Claude 상위 20 랭킹 (rank-then-summarize)

**배경**: 2026-04-10 리포트 분석 결과 824개 기사 수집 (arXiv 680/83%). 중복은 없으나
전체 요약은 노이즈 과다 + 기사별 Claude 호출이 비용·시간 부담.

- [x] `ArxivCollector`에 `max_per_category=20` 상한 추가 → arXiv 680 → 60
- [x] `daily-report.yml`의 Claude Code CLI 프롬프트를 2단계 구조로 재설계
  - **Stage 1**: 전 기사를 중요도 기준으로 평가 후 상위 20 선별
    - 기술 신규성, 영향력, 소스 신뢰도, 카테고리 다양성, 한국 관련성
  - **Stage 2**: 선택된 20개만 한국어 요약 + 카테고리 분류
- [x] 저장되는 report는 선별된 20개만 포함
- [x] 카테고리 enum 이름을 models.py와 일치시킴 (AI_AGENT→AGENT 등)
- [x] 효과: 수집 824→~200, Claude 호출 824→21, 리포트 20개 핵심으로 집중

### 6.5 소스별 브라우징

**목표**: 카테고리와 동일한 패턴으로 소스(출처)별 아카이브 제공.

- [x] `get_source_label` / `get_source_color` / `get_source_tier` 헬퍼 + Jinja 필터
- [x] **티어 기반 색상 (4+1)**: Frontier Lab (#2563eb), Research (#7c3aed), Media (#ea580c), Korean (#db2777), Inactive (#64748b)
- [x] `_generate_source_pages()` 메서드
- [x] `/sources/index.html` — 19개 소스 카드 그리드
- [x] `/sources/{NAME}.html` × 19 — 해당 소스의 전 기사
- [x] `source.html` 은 역으로 category-link 노출해 카테고리 ↔ 소스 상호 이동
- [x] `base.html` nav에 "Sources" 링크
- [x] 홈/리포트/카테고리 페이지의 article-meta source 텍스트를 클릭 가능한 링크로 변경 (display label 사용)
- [x] CSS: `.category-card` / `.source-card` 콤마 셀렉터로 공유, `::before` 배경만 각자의 `--cat-color` / `--src-color` 변수 사용

### 6.6 홈 대시보드 재설계

**증상**: 홈이 최신 리포트의 전체 기사를 풀 요약 카드로 렌더해 스크롤이 15~20 뷰포트에 달함.

- [x] 홈을 탐색 허브로 전면 재설계:
  - **Hero**: tagline + date + "오늘의 리포트 보기" CTA pill 버튼
  - **Stats**: 4 카드 (Articles / Categories / Sources / Total Reports)
  - **Today's Categories**: 상위 8개 카테고리 카드 그리드 + "모두 보기" 링크
  - **Today's Sources**: 상위 8개 소스 카드 그리드 + "모두 보기" 링크
  - **Recent Reports**: 기존 아카이브 리스트 유지
- [x] 기존 "Latest Report" 기사 월 블록 제거 — 풀 기사는 `/reports/{date}.html`에서만
- [x] `_generate_index`에서 카테고리/소스 카운트 집계해 상위 8개 전달
- [x] CSS: `.hero-cta` (흰 pill 버튼 + hover elevation), `.dashboard-section`, `.section-header`

### 6.7 문서 정합성

- [x] CLAUDE.md 전면 갱신 — Features/Tech Stack/Project Structure/Usage/Environment Variables
- [x] README.md 재작성
- [x] docs/requirements.md 갱신 — FR-011~035, NFR-011~015, 17개 소스 테이블, 환경 변수 테이블
- [x] docs/development-plan.md 갱신 — Phase 6 신설, 상태 테이블, 변경 이력
- [x] docs/system-architecture.md 갱신 — 모듈 트리, 컴포넌트, 의존성, 배포 구조
- [x] docs/TECH-DEBT.md 갱신 — DEBT-001~005 공식 등록

---

## Phase 7: 독자 레벨별 필터 (완료)

카테고리/소스 외에 "누가 읽기 위한 글인가"라는 직교 축을 추가. 사용자가 자기
레벨에 맞는 기사만 볼 수 있도록 전역 필터를 제공.

**설계 결정 (확정)**:
- 3단계 스킴: `GENERAL` (일반인) / `DEVELOPER` (개발자) / `ML_EXPERT` (ML 전문가)
- Multi-tag 허용 — 기사 1개가 여러 레벨에 속할 수 있음
- 하이브리드 태깅 — Claude 판단(경로 B) + 소스 기반 fallback(경로 A) → 경로 C
- 필터 UX — 히어로/페이지 헤더 바로 아래 필터 바, `localStorage`로 전역 지속
- 카테고리/소스 카드에 audience 미니 통계 포함

### 7.1 데이터 레이어
- [x] `Audience` Enum 추가 (`src/models.py`) — GENERAL / DEVELOPER / ML_EXPERT
- [x] `Article.audience: list[Audience]` 필드 + `to_dict`/`from_dict` 직렬화
- [x] `Audience.from_string` classmethod (관대한 파싱, None-safe)
- [x] `__post_init__`에서 문자열 리스트 → Enum 정규화, 중복 제거
- [x] 단위 테스트 (`tests/test_audience.py`) — 40개 테스트 전부 통과

### 7.2 태깅 (하이브리드)
- [x] `static_generator.py`에 `SOURCE_AUDIENCE` 매핑 (19 소스 × 1~3 audience)
- [x] `get_article_audience()` 헬퍼 — Claude 태그 있으면 사용, 없으면 source fallback, 둘 다 없으면 전체
- [x] `get_audience_data_attr()` — data-audience 속성용 콤마 구분 문자열
- [x] `get_audience_labels()` — 한국어 라벨 리스트
- [x] `count_audience()` — 카드 미니 통계용 집계
- [x] Jinja 필터 등록: `audience_data`, `audience_labels`
- [x] `daily-report.yml` Stage 2 프롬프트에 audience 태깅 지시 추가
  - GENERAL/DEVELOPER/ML_EXPERT 각각의 판단 기준 명시
  - Python 예시 코드에 `article.audience = [Audience.GENERAL, ...]` 라인 추가
  - Multi-tag 허용 + inclusive 태깅 방향 지침

### 7.3 UI 필터
- [x] `src/static/templates/audience_filter.html` 파셜 신설 — 필터 바 HTML
- [x] `src/static/js/audience-filter.js` 신설 — localStorage 기반 client-side 필터
  - `[data-audience]` 선택자로 카드 숨김/표시
  - 칩 active 상태 + `aria-pressed` 토글
  - 빈 카테고리 섹션 자동 숨김
  - 빈 결과 `audience-empty-state` 동적 삽입
  - graceful degradation (JS 실패 시 모든 기사 노출)
- [x] `base.html`에 `<script src="{{ base_url }}/js/audience-filter.js">` 로드
- [x] 모든 페이지 템플릿에 `{% include "audience_filter.html" %}` 삽입:
  - `index.html` (히어로 아래)
  - `report.html` (report-header 아래)
  - `category.html` (category-header 아래)
  - `source.html` (source-header 아래)
  - `categories_index.html` (page-header 아래)
  - `sources_index.html` (page-header 아래)
  - `search.html` (search-header 아래)
- [x] article-card 렌더 지점에 `data-audience="..."` 속성 추가
  - `report.html` / `category.html` / `source.html`
- [x] article-meta에 `audience-tag` 배지 추가 (각 기사의 audience 라벨 노출)
- [x] CSS — `.audience-filter`, `.audience-chip`, `.audience-chip.active`, `.audience-empty-state`, `.audience-tag`

### 7.4 카테고리/소스 카드 미니 통계
- [x] `_generate_category_pages`에서 `category_entries` 리스트 구성 — 각 entry에 `audience_counts` 포함
- [x] `_generate_source_pages`에서 `source_entries` 리스트 구성 — 각 entry에 `audience_counts` 포함
- [x] `categories_index.html` / `sources_index.html` 카드에 `.audience-mini` 배지 3개
  - 예: `일반 12 · 개발 8 · ML 15` (0인 계층은 생략)
- [x] CSS — `.audience-mini`, `.aud-mini` 스타일 (general/developer/ml-expert 각 컬러)

### 7.5 문서 업데이트
- [x] `docs/requirements.md` — FR-036~040, NFR-016 추가
- [x] `docs/system-architecture.md` — Audience 섹션 추가
- [x] `CLAUDE.md` — Features에 Audience 필터 추가
- [x] `README.md` — 주요 기능에 Audience 필터 추가
- [x] `docs/development-plan.md` — 상태 테이블, 변경 이력
- [x] `docs/TECH-DEBT.md` — 신규 항목 없음 (구현 중 발견된 이슈 없음)

## Phase 8: Recency 필터 + 크로스 리포트 중복 제거 (완료)

RSS 수집은 "최신 N개"만 반환하지 지정된 기간 내 발행을 보장하지 않음. 또한
GitHub Actions 매 실행마다 `.article_cache.json`이 비어서 캐시가 의미 없음.
결과적으로 2026-04-11 리포트의 20개 중 18개가 2026-04-10과 URL 중복되는
심각한 노이즈 발생.

**설계 결정 (사용자 승인)**:
- 추천 조합 8.1~8.5 전체 한 번에
- Recency 창: 2일 (`--days 2`)
- Dedup 창: 7일 (`--dedup-days 7` — 최근 7개 리포트)
- `.article_cache.json` + `src/cache.py` 완전 제거 (리포트 기반 dedup이 대체)
- 빈 후보 풀 처리: Slack/Discord/Email 알림에 "조용한 날" 배너 추가
- 4월 11일 이전 레거시 리포트 삭제 (2026-04-05, 2026-04-10)

### 8.1 arxiv `published_at` 파싱 (DEBT-003 해소)
- [x] `src/collectors/arxiv.py:_fetch_rss`에서 `<pubDate>` / `<dc:date>` 추출
- [x] `email.utils.parsedate_to_datetime` + `datetime.fromisoformat` fallback
- [x] 단위 테스트 (`TestArxivDateParser` 7개) — fixture XML로 published_at 채워짐 검증
- [x] `docs/TECH-DEBT.md` DEBT-003 resolved로 이동

### 8.2 Recency 필터
- [x] `src/filters.py` 신설 — `filter_by_recency(articles, days, now=None)` 순수 함수
- [x] timezone-aware 비교 (tz naive published_at은 UTC 간주, `_ensure_aware` helper)
- [x] `published_at = None`이면 keep (conservative fallback)
- [x] `main.py`에 `--days N` 플래그 (기본 2)
- [x] `run_collect_only`에서 수집 직후 적용
- [x] 단위 테스트 9개 (`TestFilterByRecency`) — tz aware/naive/None/boundary 경로 검증

### 8.3 크로스 리포트 dedup
- [x] `src/data_io.py`에 `load_recent_report_urls(data_dir, n=7) -> set[str]` 추가
- [x] `src/filters.py`에 `filter_already_seen(articles, seen_urls)` 순수 함수
- [x] `main.py`에 `--dedup-days N` 플래그 (기본 7)
- [x] `run_collect_only`에서 recency 직후 적용
- [x] 단위 테스트 8개 (`TestFilterAlreadySeen` + `TestDataIOLoadRecentReportUrls`)

### 8.4 ArticleCache 제거
- [x] 레거시 리포트 2개 삭제 (`data/report_2026-04-05.json`, `data/report_2026-04-10.json`)
- [x] `src/cache.py` 삭제
- [x] `tests/test_cache.py` 삭제
- [x] `main.py`에서 `ArticleCache` import / 사용 제거
- [x] `--no-cache` / `--cache-days` 플래그는 deprecation 경고 후 no-op
- [x] `.gitignore`의 `.article_cache.json` 라인은 유지 (안전 gutter)

### 8.5 Quiet-day 알림 + 문서 + 테스트
- [x] Slack/Discord/Email 알림에 `len(articles) < threshold` 시 "조용한 날" 배너 prepend
- [x] 임계값 상수 (`QUIET_DAY_THRESHOLD = 3`)
- [x] 빈 리포트도 전송 (이전엔 `False` 반환 후 skip) — 동작 변경
- [x] 기존 notifier 테스트 4개 업데이트 (quiet-day 동작 반영)
- [x] Email subject에 "🔕 [조용한 날]" prefix, `test_build_subject_normal`/`_quiet_day` 분리
- [x] `daily-report.yml`에 `--days 2 --dedup-days 7` 명시
- [x] `docs/requirements.md` — FR-041~045, NFR-017~018 추가
- [x] `docs/system-architecture.md` — 데이터 흐름 다이어그램에 recency + dedup 단계
- [x] `CLAUDE.md`, `README.md` Features에 갱신
- [x] `docs/TECH-DEBT.md` — DEBT-003 resolved, DEBT-005 resolved (레거시 리포트 삭제)
- [x] 세션 로그 `docs/sessions/2026-04-12-phase-8-recency-dedup.md`

---

### 8.6 Hotfix — 보안 (XSS) + 이메일 신뢰성 (완료)

Phase 8 완료 후 전체 코드 리뷰에서 발견된 6건의 High priority 이슈를 즉시 처리.
나머지 16건은 Phase 9로 연기.

**H1 — search.js XSS 차단**
- [x] `escapeHtml` 을 모든 사용자 입력 필드(title, summary, source, date, url)에 적용
- [x] `safeUrl()` 신설 — http/https만 허용, `javascript:` / `data:` 등 차단
- [x] href 속성에 `escapeHtml(safeUrl(...))` 이중 처리

**H2 — email_notifier HTML escape**
- [x] `_esc()` 헬퍼 신설 (`html.escape(value, quote=True)`)
- [x] `_format_article_html`의 title/summary/url/source 전부 escape
- [x] `send_error_notification`의 error_message escape
- [x] `_is_safe_url()` 로 URL 프로토콜 검증 후 href 설정

**H3 — 이메일 수신자 프라이버시**
- [x] `To` 헤더를 sender 자신으로 설정 (self-addressed)
- [x] 실제 수신자는 `Bcc` 헤더로 (SMTP envelope에만 노출, RFC상 수신자에게 숨김)
- [x] `send_message(..., from_addr=..., to_addrs=...)` 명시적 전달

**H4 — MIMEMultipart('alternative') plain 대안**
- [x] `_build_plain_message()` 신설 — 카테고리별 평문 렌더
- [x] `msg.attach(MIMEText(plain, 'plain', 'utf-8'))` 를 html 앞에 추가
- [x] 에러 알림도 plain 대안 포함

**H5 — sender 빈 값 fallback**
- [x] `_effective_sender()` 메서드 — `sender or username`
- [x] From 헤더, from_addr 모두 fallback 값 사용

**H6 — search.js와 audience 필터 통합**
- [x] `_generate_search_index`가 각 엔트리에 `audience: [...]` 필드 추가
- [x] `search.js`가 `data-audience="..."` 속성을 카드에 부착
- [x] `audience-filter.js`에 `window.AudienceFilter.{apply,applyCurrent,getCurrent}` public API 노출
- [x] `search.js`의 `displayResults`가 렌더 후 `AudienceFilter.applyCurrent()` 호출 → 현재 필터가 검색 결과에도 즉시 적용

**회귀 방지 테스트**:
- [x] `tests/test_phase_8_6_security.py` — 21개 신규 테스트 (search.js 정적 분석 7 +
  email escape/bcc/plain/sender fallback 14)
- [x] 기존 `test_send_report_custom_recipients` 업데이트 (Bcc 동작 반영)
- [x] 전체 suite: 249 passed (기존 228 + 21)

---

## Phase 9: 코드 품질 / 리팩터 / 운영성 (계획)

Phase 8 전수 리뷰에서 발견된 나머지 16건을 주제별로 4개 sub-phase로 묶어 정리.

### 9.1 Notifier 리팩터 (중복 제거) — 완료
- [x] `BaseNotifier` 추상 클래스 신설 (`src/notifier_base.py`) — `send_report(abstract)` + `send_error_notification(default no-op)` + `is_quiet_day(static)`
- [x] `QUIET_DAY_THRESHOLD`를 `src/constants.py`로 이동 (M6) — 3개 notifier에서 제거
- [x] `CATEGORY_ORDER` 상수도 `src/constants.py`로 이동 — Slack/Email에서 공유
- [x] 3개 notifier가 `BaseNotifier` 상속, `is_quiet_day()` 호출로 통일 (M7)
- [x] 단위 테스트 15개 (`tests/test_notifier_base.py`) — 상수 검증, ABC, 상속, 로컬 상수 미존재 회귀

### 9.2 Config 확장 (사용자 제어권) — 완료
- [x] `CollectorsConfig.disabled_sources: list[str]` 필드 추가 + `_COLLECTOR_REGISTRY` 기반 `get_enabled_collectors` 재작성 (M5)
- [x] `validate()` → `validate_api_mode()` 리팩터 (API 키만 검증, Slack 의존 제거) (M4)
- [x] `validate_notifications()` 신설 — Slack/Discord/Email 중 최소 1개 검증 (L2)
- [x] 기존 `arxiv.enabled` / `google_blog.enabled` / `anthropic_blog.enabled` 하위 호환 유지
- [x] `_DEFAULT_DISABLED = {"meta_ai", "lg_ai_research"}` — DEBT-001/002 기본 비활성
- [x] `config.example.yaml`에 `disabled_sources` 예시 + 전체 Source enum value 목록 주석
- [x] 테스트: `validate_api_mode`/`validate_notifications` 5개 + `disabled_sources` 기본값 1개

### 9.3 코드 품질 정리 — 완료
- [x] `static_generator.py`의 `print()` 3건 → `logger.info/warning` 교체 (M1)
- [x] `web/service.py`의 검색 → `_cached_load_report` 인메모리 캐시 (M2)
- [x] `web/service.py` 미사용 `datetime`, `Article` import 제거 (M3)
- [x] `deploy-pages.yml`에 `notify-on-failure` job 추가 (M8)
- [x] `main.py` `filter_by_recency` 로그 메시지 명료화 (M9)
- [x] `rss_base.py` `mktime+fromtimestamp` → `datetime(*parsed[:6], tzinfo=utc)` 명시적 UTC (L1)
- [x] `config.py` 기본 모델 `claude-sonnet-4-20250514` → `claude-sonnet-4-6` (L4)
- [x] `test_web.py` 23개 테스트 all passing 확인 → `--ignore` 없이 전체 suite 포함 (L6)

### 9.4 기존 DEBT 해소
- [ ] DEBT-001 Meta AI Blog — Playwright 도입 또는 대체 소스 (L5)
- [ ] DEBT-002 LG AI Research — 동일 (L5)
- [ ] DEBT-004 HF Papers URL — Takara TLDR → HF/arxiv 변환 (L5)

---

### 7.6 Hotfix — 필터 칩 클릭 후 다른 레벨 전환 불가 수정

**증상**: 필터 바에서 특정 레벨(예: "개발자")을 클릭하면 나머지 세 칩("모두",
"일반인", "ML 전문가")이 사라져 다른 레벨로 전환할 수 없음. 페이지 새로고침도
localStorage의 값이 재적용돼 동일 상태 복귀. 사용자는 사실상 첫 선택에 잠김.

**원인**: `audience-filter.js`의 `applyFilter`가 `querySelectorAll('[data-audience]')`
로 필터 대상을 선택. 이 선택자는 article-card뿐 아니라 **필터 칩 자체**도 매치함
(칩은 클릭 라우팅용으로 `data-audience="GENERAL"` 등 속성 보유). 선택한 레벨과
매치되지 않는 칩도 `hidden`이 되어 사라짐.

**수정**:
- [x] `applyFilter` 내 selector를 `[data-audience]:not(.audience-chip)`로 변경
- [x] `.category-section` 및 `.article-list` 내부 visible 탐색도 동일하게 exclude 적용 (방어적)
- [x] 파일 상단 주석 갱신 — 칩이 `data-audience`를 필터 타깃이 아닌 클릭 라우팅용으로 쓴다고 명시
- [x] `audience_filter.html`에 동일 주의 사항 주석 추가
- [x] 회귀 방지 테스트 추가 (`tests/test_audience_filter_js.py`) — JS 파일 내용에 exclusion 셀렉터가 유지되는지 검증
- [x] 세션 로그 추가 (`docs/sessions/2026-04-11-phase-7.6-filter-chip-fix.md`)

---

## 우선순위 가이드

| 우선순위 | 설명 | 예시 |
|---------|------|------|
| P0 | 서비스 운영에 필수 | 핵심 기능 버그 수정 |
| P1 | 안정성/품질 개선 | 에러 처리, 테스트 |
| P2 | 기능 개선 | 새 소스 추가 |
| P3 | Nice-to-have | 대시보드, 통계 |

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|---------|
| 2024-04-05 | 1.0 | 초기 개발 계획 문서 작성 |
| 2026-04-05 | 1.5 | Claude Code 기반 전환 (Phase 1.5 추가) |
| 2026-04-05 | 1.6 | 이메일 알림 기능 계획 추가 (Phase 3.3) |
| 2026-04-05 | 2.1 | Phase 2.1 에러 처리 강화 완료 |
| 2026-04-05 | 2.2 | Phase 2.2 로깅 개선 완료 |
| 2026-04-05 | 2.3 | Phase 2.3 테스트 코드 추가 완료 (100개 테스트) |
| 2026-04-05 | 3.1 | Phase 3.1 새 소스 추가 완료 (OpenAI, HuggingFace, 한국 AI뉴스) |
| 2026-04-05 | 3.2 | Phase 3.2 성능 최적화 완료 (병렬 수집, 캐시) |
| 2026-04-05 | 3.3 | Phase 3.3 이메일 알림 기능 완료 (SMTP, HTML 템플릿) |
| 2026-04-05 | 3.4 | Phase 3.4 Discord Webhook 알림 기능 완료 |
| 2026-04-06 | 3.4 | Phase 3.4 웹 대시보드 기능 완료 (FastAPI + Jinja2) |
| 2026-04-06 | 4.0 | Phase 4 자동화 완료 (GitHub Actions 스케줄러, CI/CD) |
| 2026-04-06 | 4.3 | Phase 4.3 Claude Code CLI 지원 추가 |
| 2026-04-06 | 4.4 | Phase 4.4 세션 키 인증 추가 (Pro/Max 구독) |
| 2026-04-06 | 5.0 | Phase 5 GitHub Pages 배포 완료 (정적 사이트 생성기, 검색 기능) |
| 2026-04-10 | 6.1 | Phase 6.1 소스 확장 완료 (Tier 1-3 13개 추가, RSSCollector 공통 베이스) |
| 2026-04-10 | 6.2 | Phase 6.2 GitHub Pages 서브패스 배포 버그 수정 (SITE_BASE_URL, search.js 버그) |
| 2026-04-10 | 6.3 | Phase 6.3 카테고리별 브라우징 추가 + UI 재설계 |
| 2026-04-10 | 6.4 | Phase 6.4 Claude 상위 20 랭킹 완료 (arXiv 상한, rank-then-summarize 프롬프트) |
| 2026-04-10 | 6.5 | Phase 6.5 소스별 브라우징 완료 (티어 색상, 카테고리 ↔ 소스 크로스 네비) |
| 2026-04-11 | 6.6 | Phase 6.6 홈 대시보드 재설계 (기사 월 제거, 탐색 허브 구조) |
| 2026-04-11 | 6.7 | Phase 6.7 문서 정합성 갱신 (CLAUDE/README/docs 4종/TECH-DEBT) |
| 2026-04-11 | 7.0 | Phase 7 독자 레벨 필터 완료 — Audience enum + 하이브리드 태깅 + 전역 필터 바 + 카드 미니 통계 + 40개 테스트 추가 |
| 2026-04-11 | 7.6 | Phase 7.6 Hotfix — 필터 선택자가 칩 자체도 숨기던 버그 수정 (selector에 :not(.audience-chip) 추가) |
| 2026-04-12 | 8.0 | Phase 8 완료 — Recency 필터(2일), 크로스 리포트 dedup(7개 리포트), arxiv pubDate 파싱, ArticleCache 제거, Quiet-day 알림, 레거시 리포트 삭제 |
| 2026-04-12 | 8.6 | Phase 8.6 Hotfix — search.js XSS 차단, email html escape/Bcc/plain/sender fallback, search 결과에 audience 필터 통합. Phase 9 계획 등록 |
| 2026-04-12 | 9.1 | Phase 9.1 Notifier 리팩터 완료 — BaseNotifier ABC + constants.py (QUIET_DAY_THRESHOLD, CATEGORY_ORDER) + 15 테스트 |
| 2026-04-12 | 9.2 | Phase 9.2 Config 확장 완료 — disabled_sources + _COLLECTOR_REGISTRY + validate_api_mode/validate_notifications + 6 테스트 |
| 2026-04-12 | 9.3 | Phase 9.3 코드 품질 정리 완료 — print→logger, 캐시, UTC 명시, 모델 최신화, deploy notify, test_web 복구. 8건 일괄 |
