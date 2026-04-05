# AI Report Service - 개발 계획

## 현재 상태

| 컴포넌트 | 상태 | 비고 |
|---------|------|------|
| 프로젝트 구조 | ✅ Complete | src/ 구조 완성 |
| 데이터 모델 | ✅ Complete | Article, Category, Source + 직렬화 |
| Collectors | ✅ Complete | arXiv, Google, Anthropic |
| Summarizer | ✅ Complete | Claude API 연동 (--use-api) |
| Slack Notifier | ✅ Complete | Webhook 연동 |
| Email Notifier | ✅ Complete | SMTP 기반 이메일 전송 |
| CLI | ✅ Complete | main.py (다중 모드 지원) |
| Claude Code 스킬 | ✅ Complete | /ai-report 스킬 |
| 데이터 I/O | ✅ Complete | JSON 직렬화/역직렬화 |
| 테스트 | ✅ Complete | pytest 188개 테스트 |
| 문서화 | ✅ Complete | docs/ 완성 |
| GitHub Actions | ✅ Complete | Daily report + CI/CD |

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

### 3.1 새 소스 추가
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
