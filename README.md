# AI Report Automation Service

일일 AI 뉴스/논문 자동 수집 & 한국어 요약 리포트 서비스

17개 소스에서 AI 관련 기사·논문을 자동 수집하여 Codex가 **중요도 기준 최대 20개를 선별**,
한국어로 요약한 데일리 리포트를 **Slack / Discord / 이메일**로 발송하고
**GitHub Pages** 정적 사이트로 공개합니다.

## Codex 전환 상태 (2026-10-09)

비공개 `murphyGo/automation-runtime`의 `ai-report.yml`을 활성화하고,
이 저장소의 기존 Claude `daily-report.yml`은 비활성화했습니다.
모델은 `gpt-6-astra`, 예약은 매일 UTC 00:00 (KST 09:00)이며
기존 이메일 설정을 사용합니다. 실제 실행 시각은 GitHub Actions 대기열에 따라 지연될 수 있습니다.
실행 근거와 복구 절차는 [운영 전환 기록](docs/sessions/2026-10-09-codex-activation.md)을 참조하세요.

## 주요 기능

- **17개 소스** 자동 수집 (아래 "데이터 소스" 참고)
- **Recency 필터 + 크로스 리포트 중복 제거** — 지난 2일 이내 발행 & 최근 7개 리포트에 없던 기사만 후보 풀로 진입
- **Codex가 중요도 기준 최대 20개 선별** — 기술 신규성, 영향력, 소스 신뢰도, 카테고리 다양성, 한국 관련성
- **Codex CLI + ChatGPT 인증** — 비공개 Actions에서 실행, 인증 갱신을 보존한 뒤 게시
- **12개 카테고리** 자동 분류 + 카테고리별 브라우징 페이지
- **독자 레벨 필터** — 일반인 / 개발자 / ML 전문가 중 하나를 선택해 전 페이지에서 실시간 필터링 (localStorage 지속)
- **다채널 알림**: Slack Webhook, Discord Webhook, 이메일(SMTP) — 기사가 적은 날엔 "조용한 날" 배너
- **GitHub Pages 정적 사이트** 자동 배포 (홈 / 리포트 아카이브 / 카테고리 / 소스 / 검색)
- **GitHub Actions 스케줄** (매일 KST 09:00) + 수동 trigger
- 병렬 수집, dry-run 모드, 로컬 FastAPI 대시보드

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
- 운영: 비공개 런타임의 **Codex CLI + 자동화 전용 ChatGPT 인증**
- 선택적인 로컬 API 모드: `ANTHROPIC_API_KEY` (`--use-api`)
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
비공개 `murphyGo/automation-runtime`의 Settings → Environments → `codex-runtime`에 등록.

| 변수 | 설명 | 필수 |
|---|---|---|
| `CODEX_AUTH_JSON` | 자동화 전용 ChatGPT 인증, 기존 공용 런타임 사용 | 필수 |
| `CODEX_SECRET_WRITE_TOKEN` | 인증 갱신 보존용 PAT, 런타임 저장소 Environments 읽기/쓰기 | 필수 |
| `AI_REPORT_PUBLISH_TOKEN` | `ai-trend-report`만 선택한 Contents/Actions 읽기/쓰기 PAT | 필수 |
| `AI_REPORT_EMAIL_USERNAME` | 기존 SMTP 사용자 | 이메일 사용 시 |
| `AI_REPORT_EMAIL_PASSWORD` | 기존 SMTP 비밀번호 / 앱 비밀번호 | 이메일 사용 시 |
| `AI_REPORT_EMAIL_RECIPIENTS` | 기존 수신자 목록 | 이메일 사용 시 |

현재 운영 알림은 기존 이메일입니다. Codex 인증을 다른 저장소에 복제하지 않으며,
예약 실행에는 유료 API 자동 fallback이 없습니다. 비활성화한 Claude workflow와
로컬 `--use-api` 진입점은 호환·복구용으로 유지합니다.

`SITE_BASE_URL`은 `deploy-pages.yml`이 저장소 이름에서 자동 생성하므로 Secret 등록 불필요.

### 로컬 개발 (`.env` 또는 shell export)

```bash
export ANTHROPIC_API_KEY="..."              # --use-api 모드
export SLACK_WEBHOOK_URL="https://..."      # Slack 테스트
export SITE_BASE_URL="/ai-trend-report"     # 정적 사이트 서브패스
```

## 사용법

### 자동 실행 (권장)

프로덕션은 비공개 런타임의 **Codex AI trend report**가 매일 UTC 00:00 (KST 09:00)에 예약됩니다.
수집 → Codex 선별·요약 → 인증 보존 → 이 저장소에 보고서 커밋 → Pages 실행 요청 → 이메일 순서입니다.
수동 실행은 비공개 런타임 Actions에서 `dry_run=true`로 검증하거나 `false`로 실제 게시합니다.
`AI_REPORT_CODEX_ENABLED=1`이 운영 게이트이며 `AI_REPORT_REVIEWED_CODE_SHA`로 실행 코드를 고정합니다.

### 로컬 개발/테스트

```bash
# 수집만 (기본 모드, API 키 불필요)
python -m src.main                       # data/articles_YYYY-MM-DD.json 저장
python -m src.main --parallel            # 병렬 수집
python -m src.main --limit 5             # 5개만 테스트

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
├── .github/workflows/      # legacy daily-report (비활성), deploy-pages, ci
├── src/
│   ├── main.py             # CLI 진입점
│   ├── config.py           # 설정 로더
│   ├── models.py           # Article / Report / Category / Source / Audience
│   ├── data_io.py          # JSON I/O
│   ├── filters.py          # Recency + 크로스 리포트 중복 제거
│   ├── codex_report.py     # Codex 선별·요약 결과 검증
│   ├── constants.py        # 공유 상수
│   ├── summarizer.py       # Anthropic API 요약 (--use-api)
│   ├── notifier_base.py    # BaseNotifier ABC
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
- **운영 요약**: Codex CLI (`gpt-6-astra`); 로컬 API 모드는 `anthropic` SDK (선택)
- **알림**: `slack-sdk`, `smtplib`, Discord Webhook
- **정적 사이트**: `jinja2`
- **웹 대시보드**: `fastapi`, `uvicorn`
- **설정**: `PyYAML`, `python-dotenv`

## 라이선스

MIT License
