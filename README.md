# AI Report Automation Service

일일 AI 뉴스/논문 자동 수집 & 한국어 요약 리포트 서비스

17개 소스에서 AI 관련 기사·논문을 자동 수집하여 Claude가 **중요도 기준 상위 20개를 선별**,
한국어로 요약한 데일리 리포트를 **Slack / Discord / 이메일**로 발송하고
**GitHub Pages** 정적 사이트로 공개합니다.

## 주요 기능

- **17개 소스** 자동 수집 (아래 "데이터 소스" 참고)
- **Claude가 중요도 기준 상위 20개 선별** — 기술 신규성, 영향력, 소스 신뢰도, 카테고리 다양성, 한국 관련성
- **Claude Code CLI 기본 지원** — Pro/Max OAuth 토큰 사용, `ANTHROPIC_API_KEY` 불필요
- **12개 카테고리** 자동 분류 + 카테고리별 브라우징 페이지
- **다채널 알림**: Slack Webhook, Discord Webhook, 이메일(SMTP)
- **GitHub Pages 정적 사이트** 자동 배포 (홈 / 리포트 아카이브 / 카테고리 / 검색)
- **GitHub Actions 스케줄** (매일 KST 09:00) + 수동 trigger
- 병렬 수집, 캐시 기반 중복 제거, dry-run 모드, 로컬 FastAPI 대시보드

## 카테고리

| 카테고리 | 설명 |
|----------|------|
| LLM | 대규모 언어 모델 |
| AI 에이전트 & 자동화 | 에이전트, 자동화, tool-use |
| 컴퓨터 비전 & 멀티모달 | 이미지·영상 인식, 멀티모달 |
| 비디오 생성 | 비디오 생성 AI |
| 로보틱스 & 3D | 로봇공학, 3D/월드 모델 |
| AI 안전성 & 윤리 | alignment, safety, policy |
| 강화학습 | RL 연구 |
| ML 인프라 & 최적화 | GPU, 서빙, 양자화, 학습 인프라 |
| 의료 & 생명과학 | 의료·바이오 AI |
| 금융 & 트레이딩 | 금융 AI |
| 산업 동향 & 한국 소식 | 산업 뉴스, 한국 AI 생태계 |
| 기타 | 위에 해당하지 않는 것 |

## 데이터 소스

**연구/논문**
- arXiv (cs.AI, cs.LG, cs.CL — 카테고리당 상위 20개)
- Hugging Face Daily Papers (Takara 비공식 RSS)

**Frontier Lab 블로그**
- Anthropic News, OpenAI News, Google (DeepMind/Research/Labs/Gemini), Hugging Face Blog

**기업/학계 리서치**
- Microsoft Research, NVIDIA Developer, BAIR (Berkeley), Stanford AI Lab

**미디어/큐레이션**
- MarkTechPost, TechCrunch AI, VentureBeat AI, MIT Technology Review (AI 키워드 필터)

**한국**
- AI타임스, 네이버 D2, 카카오 기술 블로그

**비활성** (코드는 존재, 사이트 정책상 미사용): Meta AI Blog, LG AI Research — 향후 헤드리스 브라우저 우회법 발견 시 `src/main.py`에서 활성화.

## 요구사항

- **Python 3.9+**
- 인증 방식 중 하나:
  - **Claude Code CLI** + Pro/Max 구독 OAuth 토큰 (**권장**, GitHub Actions 기본 경로)
  - 또는 `ANTHROPIC_API_KEY` (`--use-api` 모드)
- 최소 1개 알림 채널: Slack / Discord / Email

## 설치

```bash
git clone <repository-url>
cd ai-report

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp config.example.yaml config.yaml
```

## 환경 변수

### GitHub Actions Secrets (프로덕션)
Settings → Secrets and variables → Actions 에서 등록.

| 변수 | 설명 | 필수 |
|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Pro/Max OAuth 토큰 | 권장 |
| `ANTHROPIC_API_KEY` | Claude API 키 (OAuth 없을 때 fallback) | 선택 |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook | Slack 사용 시 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook | Discord 사용 시 |
| `EMAIL_USERNAME` | SMTP 사용자 (Gmail 주소 등) | 이메일 사용 시 |
| `EMAIL_PASSWORD` | SMTP 비밀번호 / Gmail 앱 비밀번호 | 이메일 사용 시 |
| `EMAIL_RECIPIENTS` | 수신자 목록 (콤마 구분) | 이메일 사용 시 |

`SITE_BASE_URL`은 `deploy-pages.yml`이 저장소 이름에서 자동 생성하므로 Secret 등록 불필요.

### 로컬 개발 (`.env` 또는 shell export)

```bash
export ANTHROPIC_API_KEY="..."              # --use-api 모드
export SLACK_WEBHOOK_URL="https://..."      # Slack 테스트
export SITE_BASE_URL="/ai-trend-report"     # 정적 사이트 서브패스
```

## 사용법

### 자동 실행 (권장)

프로덕션은 **GitHub Actions가 자동으로 돌립니다** — 매일 UTC 00:00 (KST 09:00).
`.github/workflows/daily-report.yml`이 수집 → Claude 랭킹+요약 → 알림 → 데이터 커밋을 수행하고,
`deploy-pages.yml`이 이어서 GitHub Pages에 배포합니다. 수동 실행은 Actions 탭에서 가능합니다.

### 로컬 개발/테스트

```bash
# 수집만 (기본 모드, API 키 불필요)
python -m src.main                       # data/articles_YYYY-MM-DD.json 저장
python -m src.main --parallel            # 병렬 수집
python -m src.main --no-cache --limit 5  # 캐시 무시 + 5개만

# --use-api 모드 (전체 파이프라인, ANTHROPIC_API_KEY 필요)
python -m src.main --use-api
python -m src.main --use-api --dry-run

# 개별 단계
python -m src.main --collect-only
python -m src.main --send-only             # 기존 report JSON → Slack
python -m src.main --send-only --discord   # Discord로
python -m src.main --send-only --email     # 이메일로

# 로컬 FastAPI 대시보드
python -m src.main --serve --port 8000

# GitHub Pages용 정적 사이트 생성
python -m src.main --generate-static --base-url /ai-trend-report
```

## 프로젝트 구조

```
ai-report/
├── .github/workflows/      # daily-report, deploy-pages, ci
├── src/
│   ├── main.py             # CLI 진입점
│   ├── config.py           # 설정 로더
│   ├── models.py           # Article / Report / Category / Source
│   ├── data_io.py          # JSON I/O
│   ├── cache.py            # 기사 중복 캐시
│   ├── summarizer.py       # Anthropic API 요약 (--use-api)
│   ├── slack_notifier.py   # Slack 알림
│   ├── discord_notifier.py # Discord 알림
│   ├── email_notifier.py   # 이메일 알림
│   ├── static_generator.py # GitHub Pages 정적 사이트 생성
│   ├── web/                # FastAPI 로컬 대시보드
│   ├── static/             # CSS / JS / Jinja 템플릿
│   └── collectors/         # 17개 소스 수집기 (RSSCollector 공통 베이스)
├── data/                   # 리포트 JSON (report_*.json git 추적)
├── requirements.txt
└── CLAUDE.md               # 상세 프로젝트 문서
```

상세 구조와 각 파일 역할은 [CLAUDE.md](./CLAUDE.md) 참고.

## 기술 스택

- **수집**: `requests`, `beautifulsoup4`, `lxml`, `feedparser`
- **요약**: Claude Code CLI, `anthropic` SDK (선택)
- **알림**: `slack-sdk`, `smtplib`, Discord Webhook
- **정적 사이트**: `jinja2`
- **웹 대시보드**: `fastapi`, `uvicorn`
- **설정**: `PyYAML`, `python-dotenv`

## 라이선스

MIT License
