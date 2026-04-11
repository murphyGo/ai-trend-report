# AI Report Automation Service

일일 AI 뉴스/논문 자동 수집 및 요약 리포트 서비스

## Purpose
최신 AI 관련 기술 동향을 자동 수집 → Claude가 중요도 기준 상위 20개를 선별해
한국어로 요약한 데일리 리포트를 Slack/Discord/이메일로 발송하고
GitHub Pages 정적 사이트로 공개합니다.

## What to do
1. 17개 소스에서 AI 관련 기사/논문 수집
2. Claude Code CLI(또는 `--use-api`)로 상위 20개 랭킹 → 한국어 요약 + 카테고리 분류
3. Slack/Discord/이메일 알림 + GitHub Pages 배포

## Features
 - **17개 소스** 자동 수집 (arXiv, 주요 AI 랩 블로그, 미디어, 한국 소스)
 - **Recency + 크로스 리포트 중복 제거** (Phase 8) — 2일 시간창, 최근 7개 리포트 URL 차단
 - **Claude가 중요도 기준 상위 20개 선별** — 기술 신규성·영향력·소스 신뢰도·카테고리 다양성·한국 관련성
 - **Claude Code CLI 기본 지원** (Pro/Max 구독 사용, `ANTHROPIC_API_KEY` 불필요)
 - 12개 카테고리 자동 분류 + 카테고리별 브라우징 페이지
 - **독자 레벨 필터** (Phase 7) — GENERAL / DEVELOPER / ML_EXPERT, 전역 필터 바로 실시간 토글
 - 다채널 알림: **Slack + Discord + 이메일(SMTP)** + Quiet-day 배너
 - **GitHub Pages 정적 사이트** 자동 배포 (홈, 리포트 아카이브, 카테고리, 소스, 검색)
 - **GitHub Actions 스케줄** (매일 KST 09:00) + 수동 trigger
 - 병렬 수집, 캐시 기반 중복 제거, dry-run 모드, 로컬 FastAPI 대시보드

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
- **요약**: Claude Code CLI (기본 모드, Pro/Max OAuth), `anthropic` SDK (`--use-api` 모드)
- **알림**: `slack-sdk`, `smtplib`(이메일), Discord Webhook(`requests`)
- **정적 사이트**: `jinja2` 템플릿 → `_site/` 디렉토리
- **웹 대시보드**: `fastapi`, `uvicorn` (`--serve` 로컬 미리보기)
- **설정**: `PyYAML`, `python-dotenv`

## Project Structure
```
ai-report/
├── CLAUDE.md / README.md       # 프로젝트 문서
├── DESIGN.md                   # 상세 설계 문서
├── requirements.txt            # Python 의존성
├── config.example.yaml         # 설정 예시 (실제는 config.yaml, gitignore)
├── data/                       # 리포트 JSON (report_*.json만 git 추적, articles_*.json은 ignore)
├── .github/workflows/
│   ├── daily-report.yml        # 매일 KST 09:00 자동 실행 (수집 → Claude 랭킹+요약 → 알림 → 커밋)
│   ├── deploy-pages.yml        # daily-report 성공 후 GitHub Pages 배포
│   └── ci.yml                  # 테스트/린트
├── src/
│   ├── main.py                 # CLI 진입점
│   ├── config.py               # 설정 로더
│   ├── models.py               # Article / Report / Category / Source
│   ├── data_io.py              # JSON 읽기/쓰기
│   ├── cache.py                # 기사 중복 캐시 (.article_cache.json)
│   ├── summarizer.py           # Anthropic API 요약 (--use-api 모드)
│   ├── slack_notifier.py       # Slack 알림
│   ├── discord_notifier.py     # Discord Webhook 알림
│   ├── email_notifier.py       # SMTP 이메일 알림
│   ├── static_generator.py     # GitHub Pages용 정적 사이트 생성
│   ├── web/                    # FastAPI 로컬 대시보드 (--serve)
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/search.js
│   │   └── templates/          # base, index, report, category(s), search
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
python -m src.main                       # 수집 + 캐시 필터 → data/articles_YYYY-MM-DD.json
python -m src.main --parallel            # 병렬 수집 (빠름)
python -m src.main --no-cache --limit 5  # 캐시 무시 + 5개만
```

요약 단계는 GitHub Actions에서 Claude Code CLI가 `daily-report.yml`의 2단계 프롬프트
(랭킹 → 상위 20 → 요약)로 처리합니다. 로컬에서 같은 프롬프트를 돌리려면 `claude -p`로 직접 실행하세요.

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

프로덕션 파이프라인은 GitHub Actions가 스케줄로 실행합니다.

### `daily-report.yml` — 매일 UTC 00:00 (KST 09:00)
1. 17개 소스에서 기사 수집
2. Claude Code CLI가 **중요도 기준 상위 20개 선별** (OAuth 토큰으로 인증, Pro/Max 구독 사용)
3. 선별된 20개만 한국어 요약 + 카테고리 분류
4. Slack / Discord / 이메일 알림 전송 (설정된 채널만)
5. `data/report_*.json` 커밋 & push

### `deploy-pages.yml` — daily-report 성공 후 자동 트리거
- `report_*.json`들을 Jinja2 템플릿으로 정적 HTML 변환
- `SITE_BASE_URL=/${{ github.event.repository.name }}`이 자동 주입되어 GitHub Pages 프로젝트 사이트 서브패스 지원
- 홈, 개별 리포트, 카테고리 브라우징(12개), 검색 페이지 생성

**수동 실행**: Actions 탭 → *Daily AI Report* → *Run workflow*

**로컬 cron (대안)**:
```cron
0 9 * * * cd /path/to/ai-report && /path/to/.venv/bin/python -m src.main --use-api >> /var/log/ai-report.log 2>&1
```

## Environment Variables

### GitHub Actions Secrets (프로덕션)
Settings → Secrets and variables → Actions 에서 등록.

| 변수 | 설명 | 필수 |
|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Pro/Max OAuth 토큰 (랭킹+요약용, 우선순위 1) | 권장 |
| `ANTHROPIC_API_KEY` | Claude API 키 (OAuth 없을 때 fallback, `--use-api` 모드 전용) | 선택 |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook | Slack 사용 시 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook | Discord 사용 시 |
| `EMAIL_USERNAME` | SMTP 사용자 (Gmail 주소 등) | 이메일 사용 시 |
| `EMAIL_PASSWORD` | SMTP 비밀번호 / Gmail 앱 비밀번호 | 이메일 사용 시 |
| `EMAIL_RECIPIENTS` | 수신자 목록 (콤마 구분) | 이메일 사용 시 |

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
