# AI Report Automation Service

일일 AI 뉴스/논문 자동 수집 및 요약 리포트 서비스

## Purpose
최신 AI 관련 기술 동향을 자동 수집 → Codex가 중요도 기준 최대 20개를 선별해
한국어로 요약한 데일리 리포트를 Slack/Discord/이메일로 발송하고
GitHub Pages 정적 사이트로 공개합니다.

## What to do
1. 17개 소스에서 AI 관련 기사/논문 수집
2. 비공개 Actions에서 Codex CLI로 최대 20개 선별 → 한국어 요약 + 카테고리 분류
3. Slack/Discord/이메일 알림 + GitHub Pages 배포

## Features
 - **17개 소스** 자동 수집 (arXiv, 주요 AI 랩 블로그, 미디어, 한국 소스)
 - **Recency + 크로스 리포트 중복 제거** (Phase 8) — 2일 시간창, 최근 7개 리포트 URL 차단
 - **Codex가 중요도 기준 최대 20개 선별** — 기술 신규성·영향력·소스 신뢰도·카테고리 다양성·한국 관련성
 - **Codex CLI + 자동화 전용 ChatGPT 인증** (비공개 런타임, `gpt-6-astra`)
 - 12개 카테고리 자동 분류 + 카테고리별 브라우징 페이지
 - **독자 레벨 필터** (Phase 7) — GENERAL / DEVELOPER / ML_EXPERT, 전역 필터 바로 실시간 토글
 - 다채널 알림: **Slack + Discord + 이메일(SMTP)** + Quiet-day 배너
 - **GitHub Pages 정적 사이트** 자동 배포 (홈, 리포트 아카이브, 카테고리, 소스, 검색)
 - **GitHub Actions 스케줄** (매일 KST 09:00) + 수동 trigger
 - 병렬 수집, dry-run 모드, 로컬 FastAPI 대시보드

## Categories
 - LLM (대규모 언어 모델)
 - AI 에이전트 & 자동화
 - 컴퓨터 비전 & 멀티모달
 - 비디오 생성
 - 로보틱스 & 3D
 - AI 안전성 & 윤리
 - 강화학습
 - ML 인프라 & 최적화
 - 의료 & 생명과학
 - 금융 & 트레이딩
 - 산업 동향 & 한국 소식
 - 기타

## Sources

### 연구/논문
 - **arXiv** — https://arxiv.org (cs.AI, cs.LG, cs.CL 카테고리)
 - **Hugging Face Daily Papers** — https://papers.takara.ai/api/feed (비공식 RSS, 큐레이션)

### Frontier Lab 블로그
 - **Anthropic** — https://www.anthropic.com/news
 - **OpenAI** — https://openai.com/news/
 - **Google** — blog.google (DeepMind, Research, Labs, Gemini 카테고리)
 - **Meta AI** — https://ai.meta.com/blog/
 - **Hugging Face** — https://huggingface.co/blog

### 기업/학계 리서치
 - **Microsoft Research** — https://www.microsoft.com/en-us/research/blog/feed/ (RSS)
 - **NVIDIA Developer** — https://developer.nvidia.com/blog/feed (RSS)
 - **BAIR (Berkeley)** — https://bair.berkeley.edu/blog/feed.xml (RSS)
 - **Stanford AI Lab** — https://ai.stanford.edu/blog/feed.xml (RSS)

### 미디어/큐레이션
 - **MarkTechPost** — https://www.marktechpost.com/feed/ (RSS)
 - **TechCrunch AI** — https://techcrunch.com/category/artificial-intelligence/feed/ (RSS)
 - **VentureBeat AI** — https://venturebeat.com/category/ai/feed/ (RSS)
 - **MIT Technology Review (AI)** — https://www.technologyreview.com/topic/artificial-intelligence/

### 한국 소스
 - **AI타임스** — https://www.aitimes.kr
 - **네이버 D2** — https://d2.naver.com/d2.atom (Atom)
 - **카카오 기술 블로그** — https://tech.kakao.com/feed/ (RSS)

### 비활성 (코드는 존재, 사이트 정책으로 미사용)
 - **Meta AI Blog** — `ai.meta.com/blog/`가 일반 HTTP 클라이언트에 400 응답. 헤드리스 브라우저 필요.
 - **LG AI Research** — Nuxt.js SPA로 SSR HTML에 데이터 없음. 공개 API 미발견.

   향후 우회법을 찾으면 `src/main.py:get_enabled_collectors`에서 주석을 해제하세요.

## Tech Stack
- **Python 3.9+**
- **수집**: `requests`, `beautifulsoup4`, `lxml`, `feedparser` (RSS/Atom)
- **운영 요약**: Codex CLI (`gpt-6-astra`); `anthropic` SDK는 선택적인 로컬 `--use-api` 모드
- **알림**: `slack-sdk`, `smtplib`(이메일), Discord Webhook(`requests`)
- **정적 사이트**: `jinja2` 템플릿 → `_site/` 디렉토리
- **웹 대시보드**: `fastapi`, `uvicorn` (`--serve` 로컬 미리보기)
- **설정**: `PyYAML`, `python-dotenv`

## Project Structure
```
ai-report/
├── CLAUDE.md / README.md       # 프로젝트 문서
├── docs/                       # 설계 문서 (system-architecture.md, TECH-DEBT.md 등)
├── requirements.txt            # Python 의존성
├── config.example.yaml         # 설정 예시 (실제는 config.yaml, gitignore)
├── data/                       # 리포트 JSON (report_*.json만 git 추적, articles_*.json은 ignore)
├── .github/workflows/
│   ├── daily-report.yml        # 레거시 Claude workflow (운영 비활성화)
│   ├── deploy-pages.yml        # 비공개 런타임 게시 후 실행 요청으로 GitHub Pages 배포
│   └── ci.yml                  # 테스트/린트
├── src/
│   ├── main.py                 # CLI 진입점
│   ├── config.py               # 설정 로더
│   ├── models.py               # Article / Report / Category / Source / Audience
│   ├── data_io.py              # JSON 읽기/쓰기
│   ├── filters.py              # Recency + 크로스 리포트 중복 제거 (Phase 8)
│   ├── codex_report.py         # Codex JSON 응답 검증, 원본 기사 ID 매핑
│   ├── constants.py            # 공유 상수 (Phase 9.1)
│   ├── summarizer.py           # Anthropic API 요약 (--use-api 모드)
│   ├── notifier_base.py        # BaseNotifier ABC (Phase 9.1)
│   ├── slack_notifier.py       # Slack 알림
│   ├── discord_notifier.py     # Discord Webhook 알림
│   ├── email_notifier.py       # SMTP 이메일 알림
│   ├── static_generator.py     # GitHub Pages용 정적 사이트 생성
│   ├── web/                    # FastAPI 로컬 대시보드 (--serve)
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/search.js
│   │   ├── js/audience-filter.js  # 독자 레벨 실시간 필터 (Phase 7)
│   │   └── templates/          # base, index, report, category(s), source(s), search, audience_filter
│   ├── utils/                  # retry, logging 헬퍼
│   └── collectors/
│       ├── base.py             # BaseCollector (HTTP 세션, 재시도)
│       ├── rss_base.py         # RSSCollector (feedparser 기반 공통 베이스)
│       ├── rss_tier1.py        # MS Research, NVIDIA, MarkTechPost, BAIR, Stanford, TechCrunch, VentureBeat
│       ├── arxiv.py            # arXiv (카테고리당 max_per_category=20)
│       ├── anthropic_blog.py   # Anthropic News
│       ├── openai_blog.py      # OpenAI News
│       ├── google_blog.py      # Google AI 블로그 (DeepMind/Research/Labs/Gemini)
│       ├── huggingface_blog.py # HuggingFace Blog
│       ├── hf_papers.py        # HuggingFace Daily Papers (Takara 비공식 RSS)
│       ├── mit_tech_review.py  # MIT Tech Review (AI 키워드 필터)
│       ├── korean_news.py      # AI타임스
│       ├── korean_rss.py       # Naver D2, Kakao Tech
│       ├── meta_ai_blog.py     # (비활성) Meta AI Blog — 강력 봇 차단
│       └── lg_ai_research.py   # (비활성) LG AI Research — Nuxt SPA
└── .gitignore
```

## Setup

### 1. 의존성 설치
```bash
cd ai-report
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 설정 파일 (선택)
```bash
cp config.example.yaml config.yaml
# config.yaml은 gitignore. 수집기 on/off, 로깅 등 고급 설정용.
# 대부분의 값은 환경 변수로도 주입 가능하므로 없어도 동작함.
```

### 3. 환경 변수 (최소 구성)
```bash
# 프로덕션 (GitHub Actions): 위 "Environment Variables" 섹션의 Secrets를 등록
# 로컬 개발: .env 파일 또는 shell export
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."  # 알림 채널 최소 1개
export ANTHROPIC_API_KEY="..."                                    # --use-api 모드에서만 필요
```

### 4. 알림 채널 설정 (원하는 것만)
- **Slack**: https://api.slack.com/apps 에서 앱 생성 → Incoming Webhooks 활성화 → 채널 추가 → URL을 `SLACK_WEBHOOK_URL`로
- **Discord**: 서버 설정 → 연동 → 웹훅 → URL을 `DISCORD_WEBHOOK_URL`로
- **이메일**: Gmail은 2FA 활성화 후 앱 비밀번호 발급 → `EMAIL_USERNAME`/`EMAIL_PASSWORD`/`EMAIL_RECIPIENTS` 등록

## Usage

> 프로덕션 파이프라인은 GitHub Actions가 자동으로 돌립니다 (아래 "자동 실행" 참고).
> 아래는 로컬 개발/테스트용 명령입니다.

### 기본 모드 (수집 전용, API 키 불필요)

```bash
python -m src.main                       # 수집 + recency/dedup 필터 → data/articles_YYYY-MM-DD.json
python -m src.main --parallel            # 병렬 수집 (빠름)
python -m src.main --limit 5             # 5개만 테스트
```

운영 요약은 비공개 `murphyGo/investo-runtime`의 `ai-report.yml`에서 Codex CLI가 처리합니다.
검증된 코드를 설치하고 기사 데이터를 stdin으로 전달하며, 모델에는 도구를 제공하지 않습니다.
`src.codex_report`가 JSON 응답을 검증한 뒤 원본 기사 ID와 연결합니다.

### API 모드 (ANTHROPIC_API_KEY 필요)

```bash
python -m src.main --use-api             # 수집 → 요약 → Slack 전송
python -m src.main --use-api --dry-run   # 전송 없이 미리보기
python -m src.main --use-api --limit 5   # 5개 기사만 테스트
```

### 개별 단계

```bash
python -m src.main --collect-only                             # 수집만
python -m src.main --send-only                                # 기존 report JSON → Slack
python -m src.main --send-only --discord                      # Discord로 전송
python -m src.main --send-only --email                        # 이메일로 전송
python -m src.main --send-only --email --email-to a@b.com     # 특정 수신자
python -m src.main --send-only --input-json data/report_2026-04-10.json
```

### 웹 대시보드 / 정적 사이트

```bash
# 로컬 FastAPI 대시보드
python -m src.main --serve --port 8000

# GitHub Pages용 정적 사이트 생성
python -m src.main --generate-static --static-output _site
#   서브패스 배포 시:
python -m src.main --generate-static --base-url /ai-trend-report
#   또는 환경 변수:
SITE_BASE_URL=/ai-trend-report python -m src.main --generate-static
```

## 자동 실행 (GitHub Actions)

프로덕션 파이프라인은 비공개 `murphyGo/investo-runtime`에서 실행합니다.
이 공개 저장소의 `daily-report.yml`은 2026-10-09에 비활성화했습니다.
실행 근거는 [운영 전환 기록](docs/sessions/2026-10-09-codex-activation.md)을 참조하세요.

### 비공개 `ai-report.yml` — 매일 UTC 00:00 (KST 09:00) 예약
1. 17개 소스에서 기사 수집
2. Codex CLI (`gpt-6-astra`)가 **중요도 기준 최대 20개 선별·한국어 요약·분류**
3. 응답 검증과 갱신된 인증 보존
4. 해당 날짜의 `data/report_*.json` 커밋 & push, Pages 실행 요청
5. 기존 이메일 설정으로 보고서 전송

GitHub Actions 대기열에 따라 실제 시작은 지연될 수 있습니다.
`AI_REPORT_CODEX_ENABLED=1`이 운영 게이트이며 `AI_REPORT_REVIEWED_CODE_SHA`가 실행 코드를 고정합니다.
Investo와 같은 인증 스트림을 공유 큐에서 직렬로 사용합니다. 인증을 다른 저장소에 복제하지 마세요.

### `deploy-pages.yml` — 비공개 런타임 게시 후 명시적으로 실행 요청
- `report_*.json`들을 Jinja2 템플릿으로 정적 HTML 변환
- `SITE_BASE_URL=/${{ github.event.repository.name }}`이 자동 주입되어 GitHub Pages 프로젝트 사이트 서브패스 지원
- 홈, 개별 리포트, 카테고리 브라우징(12개), 검색 페이지 생성

**수동 실행**: 비공개 런타임 Actions → *Codex AI trend report* → *Run workflow*.
`dry_run=true`는 생성/인증 보존만 검증하고, `false`는 실제 게시/이메일 전송까지 수행합니다.

**로컬 cron (대안)**:
```cron
0 9 * * * cd /path/to/ai-report && /path/to/.venv/bin/python -m src.main --use-api >> /var/log/ai-report.log 2>&1
```

## Environment Variables

### GitHub Actions Secrets (프로덕션)
비공개 `murphyGo/investo-runtime`의 Settings → Environments → `codex-runtime`에서 관리합니다.

| 변수 | 설명 | 필수 |
|---|---|---|
| `CODEX_AUTH_JSON` | 공용 런타임의 자동화 전용 ChatGPT 인증 | 필수 |
| `CODEX_SECRET_WRITE_TOKEN` | 런타임 저장소 Environments 읽기/쓰기 PAT | 필수 |
| `AI_REPORT_PUBLISH_TOKEN` | 이 공개 저장소만 선택한 Contents/Actions 읽기/쓰기 PAT | 필수 |
| `AI_REPORT_EMAIL_USERNAME` | 기존 SMTP 사용자 | 이메일 사용 시 |
| `AI_REPORT_EMAIL_PASSWORD` | 기존 SMTP 비밀번호 / 앱 비밀번호 | 이메일 사용 시 |
| `AI_REPORT_EMAIL_RECIPIENTS` | 기존 수신자 목록 | 이메일 사용 시 |
| `AI_REPORT_SLACK_WEBHOOK_URL` | 실제 운영 실패 알림용 웹훅 | 선택 |

현재 운영 알림은 이메일입니다. 유료 API 자동 fallback은 없습니다.
레거시 Claude workflow는 복구용으로 남아 있으며, 활성화하기 전에 비공개 일일 실행을
중단하고 진행 중인 작업 및 해당 날짜의 게시/이메일 이력을 확인해야 합니다.

> `SITE_BASE_URL`은 `deploy-pages.yml`에서 `github.event.repository.name`으로
> 자동 주입되므로 Secret 등록 불필요.

### 로컬 개발 (.env 또는 shell export)
| 변수 | 용도 |
|---|---|
| `ANTHROPIC_API_KEY` | `--use-api` 모드 |
| `SLACK_WEBHOOK_URL` | Slack 전송 테스트 |
| `DISCORD_WEBHOOK_URL` | Discord 전송 테스트 |
| `EMAIL_USERNAME/PASSWORD/RECIPIENTS` | 이메일 전송 테스트 |
| `SITE_BASE_URL` | `--generate-static` 시 URL prefix (로컬 루트 배포면 비워둠) |
