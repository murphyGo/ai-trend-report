# AI Report Service - 요구사항 문서

## 개요

AI 관련 기술 동향을 17개 소스에서 자동 수집하고, Claude가 **중요도 기준 상위 20개**를
선별·한국어 요약한 데일리 리포트를 **Slack / Discord / 이메일**로 발송하며,
**GitHub Pages** 정적 사이트로 공개하는 서비스의 요구사항을 정의합니다.

---

## 기능 요구사항 (Functional Requirements)

### 데이터 수집 (17개 소스)

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-001 | arXiv에서 cs.AI, cs.LG, cs.CL 카테고리 논문 수집 (카테고리당 상위 20개) | High | Done |
| FR-002 | Google AI 블로그 (DeepMind, Research, Labs, Gemini) 기사 수집 | High | Done |
| FR-003 | Anthropic 뉴스/블로그 기사 수집 | High | Done |
| FR-011 | OpenAI News, Hugging Face Blog, HF Daily Papers 수집 | High | Done |
| FR-012 | 기업/학계 리서치: Microsoft Research, NVIDIA Developer, BAIR, Stanford AI Lab (RSS 기반) | High | Done |
| FR-013 | 미디어/큐레이션: MarkTechPost, TechCrunch AI, VentureBeat AI, MIT Tech Review (AI 키워드 필터) | Medium | Done |
| FR-014 | 한국 소스: AI타임스, 네이버 D2, 카카오 기술 블로그 | Medium | Done |
| FR-015 | RSSCollector 공통 베이스 클래스 — 신규 RSS 소스 추가 비용 최소화 | Medium | Done |

### AI 요약 / 선별

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-004 | Claude Code CLI(기본, Pro/Max OAuth) 또는 Anthropic API(`--use-api`)로 한국어 요약 | High | Done |
| FR-005 | 12개 카테고리 자동 분류 | High | Done |
| FR-016 | Claude가 중요도 기준으로 상위 20개 기사 선별 (rank-then-summarize 2단계 프롬프트) | High | Done |

> FR-016 판단 기준: 기술 신규성, 영향력(frontier lab/주요 모델 발표), 소스 신뢰도,
> 카테고리 다양성, 한국 관련성 보너스.

### 알림 (다채널)

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-006 | Slack Incoming Webhook 전송 | High | Done |
| FR-007 | Block Kit 기반 리치 메시지 포맷팅 | Medium | Done |
| FR-017 | Discord Webhook 전송 (`--discord`) | Medium | Done |
| FR-018 | SMTP 기반 이메일 전송 — HTML 템플릿, 다중 수신자 (`--email`) | Medium | Done |

### 정적 사이트 (GitHub Pages)

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-019 | Jinja2 기반 정적 사이트 생성 (`--generate-static`) | High | Done |
| FR-020 | GitHub Pages 자동 배포 (`deploy-pages.yml`, daily-report 완료 후 트리거) | High | Done |
| FR-021 | 홈 대시보드 — 히어로 CTA + 통계 + 카테고리/소스 미리보기 + 최근 리포트 | High | Done |
| FR-022 | 개별 리포트 페이지 (`/reports/{date}.html`) — 카테고리별 그룹, 풀 요약 | High | Done |
| FR-023 | 카테고리별 브라우징 — `/categories/` 인덱스 + 12개 카테고리 페이지 (전 리포트 누적) | High | Done |
| FR-024 | 소스별 브라우징 — `/sources/` 인덱스 + 19개 소스 페이지 (티어 색상) | High | Done |
| FR-025 | Fuse.js 기반 클라이언트 사이드 검색 (`/search.html`) — 카테고리 필터 지원 | Medium | Done |
| FR-026 | 서브패스 배포 지원 — `SITE_BASE_URL` 환경 변수로 모든 내부 링크 prefix | High | Done |

### 자동화

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-027 | GitHub Actions 매일 KST 09:00 스케줄 실행 (`daily-report.yml`) | High | Done |
| FR-028 | Claude Code CLI + OAuth 토큰으로 Pro/Max 구독 기반 무료 요약 | High | Done |
| FR-029 | 수동 실행 지원 (`workflow_dispatch`) — dry_run / limit / model 옵션 | Medium | Done |
| FR-030 | 실패 시 Slack 에러 알림 (`notify-on-failure` job) | High | Done |

### CLI

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-008 | Dry-run 모드 지원 (`--dry-run`) | Medium | Done |
| FR-009 | 기사 수 제한 옵션 (`--limit`) | Medium | Done |
| FR-010 | 상세 로그 모드 (`--verbose`) | Low | Done |
| FR-031 | 병렬 수집 (`--parallel`, ThreadPoolExecutor) | Medium | Done |
| FR-032 | 기사 캐시 기반 중복 제거 (`--no-cache`, `--cache-days`) | Medium | Done |
| FR-033 | 개별 단계 실행 (`--collect-only`, `--send-only`, `--input-json`) | Medium | Done |
| FR-034 | 로컬 FastAPI 대시보드 (`--serve --port`) | Low | Done |
| FR-035 | 정적 사이트 생성 (`--generate-static --static-output --base-url`) | High | Done |

### 독자 레벨 필터 (Phase 7)

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-036 | 기사마다 독자 레벨 태그 — GENERAL / DEVELOPER / ML_EXPERT (multi-tag) | High | Done |
| FR-037 | 하이브리드 태깅 — Claude 판단 우선, 미설정 시 소스 기반 fallback | High | Done |
| FR-038 | 전역 필터 바 — 모든 페이지에 노출, `localStorage`로 페이지 간 지속 | High | Done |
| FR-039 | 카테고리/소스 인덱스 카드에 audience 미니 통계 (일반 N · 개발 N · ML N) | Medium | Done |
| FR-040 | 레거시 리포트(태그 없음)도 소스 fallback으로 즉시 분류됨 | High | Done |

### Recency + 중복 제거 (Phase 8)

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-041 | 수집된 기사를 지난 N일(기본 2) 이내 발행된 것으로 필터링 (`--days`) | High | Done |
| FR-042 | 최근 N개 리포트(기본 7)의 URL과 겹치는 기사는 제거 (`--dedup-days`) | High | Done |
| FR-043 | arXiv RSS의 `<pubDate>` / `<dc:date>` 파싱 (DEBT-003 해소) | High | Done |
| FR-044 | Quiet-day 알림 — 필터 후 < 3개일 때 Slack/Discord/이메일에 배너 추가 | Medium | Done |
| FR-045 | 빈 리포트도 quiet-day 배너로 전송 (기존엔 skip) | Medium | Done |

> FR-041 `published_at`이 없는 기사(일부 HTML 스크래퍼)는 보수적으로 유지.
> FR-042 리포트 파일 기반 (별도 캐시 파일 불필요, 리포트는 이미 git 추적).

> FR-036 판단 기준:
> - **GENERAL (일반인)**: 제품/산업 뉴스, 정책, 윤리, 비즈니스 영향, "AI가 X를 어떻게 바꾸는가" 류 해설, AI 활용 팁. 기술 배경 불필요.
> - **DEVELOPER (개발자)**: API 업데이트, 라이브러리 릴리스, 코딩 튜토리얼, 시스템 아키텍처, 프레임워크 비교, AI 코딩 도구(Cursor/Copilot), 통합 가이드. 프로그래밍 배경 전제, ML 전문성은 불요.
> - **ML_EXPERT (ML 전문가)**: 논문, 새 아키텍처, 학습 방법론, 벤치마크, 수학/통계 heavy, 모델 릴리스의 기술 디테일(파라미터·데이터셋·scaling law). ML 배경 전제.

---

## 비기능 요구사항 (Non-Functional Requirements)

### 안정성

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| NFR-001 | 개별 소스 수집 실패 시 다른 소스 계속 진행 | High | Done |
| NFR-002 | 개별 기사 요약 실패 시 해당 기사 스킵 | High | Done |
| NFR-003 | 전체 실패 시 에러 알림 전송 (GitHub Actions `notify-on-failure` job) | Medium | Done |
| NFR-011 | 네트워크 오류에 대한 재시도 로직 (`utils/retry.py`, 최대 3회 backoff) | High | Done |

### 보안

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| NFR-004 | 환경 변수 / GitHub Secrets로 API 키·웹훅 관리 | High | Done |
| NFR-005 | config.yaml에 민감 정보 미포함 (gitignore) | High | Done |
| NFR-012 | OAuth 토큰 기반 인증 우선 (Pro/Max 구독), API 키는 폴백 | Medium | Done |

### 운영

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| NFR-006 | CLI 기반 실행 | High | Done |
| NFR-007 | GitHub Actions 스케줄링 (로컬 Cron은 대안) | Medium | Done |
| NFR-008 | 로그 파일 출력 지원 (JSON 구조화) | Low | Done |
| NFR-013 | `report_*.json`은 git 추적, `articles_*.json`은 gitignore로 GitHub Pages 배포와 정합성 유지 | High | Done |

### 성능

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| NFR-009 | 병렬 수집으로 성능 최적화 (`--parallel`, `ThreadPoolExecutor`) | Low | Done |
| NFR-010 | 기사 캐싱으로 중복 처리 방지 (`cache.py`, URL 기반) | Low | Done |
| NFR-014 | arXiv 수집 상한 (카테고리당 20개) — 수집 시간 및 Claude 입력 토큰 절감 | Medium | Done |
| NFR-015 | Claude는 기사별 1회 호출 대신 랭킹 1회 + 요약 N회로 API 사용 최적화 | Medium | Done |
| NFR-016 | 필터링은 client-side JS — 정적 HTML 배포 구조 유지, graceful degradation | High | Done |
| NFR-017 | 상태 영속성은 git-tracked 리포트 파일만 사용 — 별도 캐시 파일 불필요 | High | Done |
| NFR-018 | 필터 파이프라인 순수 함수형 — `filter_by_recency`/`filter_already_seen` 테스트 용이 | Medium | Done |

---

## 카테고리 목록

12개의 분류 카테고리:

1. LLM (대규모 언어 모델)
2. AI 에이전트 & 자동화
3. 컴퓨터 비전 & 멀티모달
4. 비디오 생성
5. 로보틱스 & 3D
6. AI 안전성 & 윤리
7. 강화학습
8. ML 인프라 & 최적화
9. 의료 & 생명과학
10. 금융 & 트레이딩
11. 산업 동향 & 한국 소식
12. 기타

---

## 데이터 소스 (17개 활성 + 2개 비활성)

### 연구/논문
| 소스 | URL | 수집 방식 |
|------|-----|---------|
| arXiv | https://arxiv.org | RSS (cs.AI / cs.LG / cs.CL, 카테고리당 20) |
| Hugging Face Daily Papers | https://papers.takara.ai/api/feed | 비공식 RSS (Takara) |

### Frontier Lab 블로그
| 소스 | URL | 수집 방식 |
|------|-----|---------|
| Anthropic | https://www.anthropic.com/news | HTML 스크래핑 |
| OpenAI | https://openai.com/news/ | HTML 스크래핑 |
| Google AI | https://blog.google/innovation-and-ai/ | HTML 스크래핑 (DeepMind/Research/Labs/Gemini) |
| Hugging Face Blog | https://huggingface.co/blog | HTML 스크래핑 |

### 기업/학계 리서치
| 소스 | URL | 수집 방식 |
|------|-----|---------|
| Microsoft Research | https://www.microsoft.com/en-us/research/blog/feed/ | RSS |
| NVIDIA Developer | https://developer.nvidia.com/blog/feed | RSS |
| BAIR (Berkeley) | https://bair.berkeley.edu/blog/feed.xml | RSS |
| Stanford AI Lab | https://ai.stanford.edu/blog/feed.xml | RSS |

### 미디어/큐레이션
| 소스 | URL | 수집 방식 |
|------|-----|---------|
| MarkTechPost | https://www.marktechpost.com/feed/ | RSS (Cloudflare 우회용 Feedly UA) |
| TechCrunch AI | https://techcrunch.com/category/artificial-intelligence/feed/ | RSS |
| VentureBeat AI | https://venturebeat.com/category/ai/feed/ | RSS |
| MIT Technology Review (AI) | https://www.technologyreview.com/feed/ | RSS + AI 키워드 필터 |

### 한국
| 소스 | URL | 수집 방식 |
|------|-----|---------|
| AI타임스 | https://www.aitimes.kr | HTML 스크래핑 |
| 네이버 D2 | https://d2.naver.com/d2.atom | Atom 피드 |
| 카카오 기술 블로그 | https://tech.kakao.com/feed/ | RSS |

### 비활성 (코드 존재, 사이트 정책으로 미사용)
| 소스 | 사유 | 참조 |
|------|------|------|
| Meta AI Blog | `ai.meta.com/blog/`가 일반 HTTP에 400 응답 | DEBT-001 |
| LG AI Research | Nuxt.js SPA + 공개 API 미발견 | DEBT-002 |

---

## 환경 변수

### GitHub Actions Secrets (프로덕션)
| 변수 | 설명 | 필수 |
|------|------|------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Pro/Max OAuth 토큰 | 권장 (우선) |
| `ANTHROPIC_API_KEY` | Claude API 키 (OAuth 없을 때 fallback 또는 `--use-api`) | 선택 |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook | Slack 사용 시 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook | Discord 사용 시 |
| `EMAIL_USERNAME` | SMTP 사용자 (Gmail 주소 등) | 이메일 사용 시 |
| `EMAIL_PASSWORD` | SMTP 비밀번호 / Gmail 앱 비밀번호 | 이메일 사용 시 |
| `EMAIL_RECIPIENTS` | 수신자 목록 (콤마 구분) | 이메일 사용 시 |

> `SITE_BASE_URL`은 `deploy-pages.yml`에서 `github.event.repository.name`으로 자동 주입.
> Secret 등록 불필요.

### 로컬 개발 (.env 또는 shell)
| 변수 | 용도 |
|------|------|
| `ANTHROPIC_API_KEY` | `--use-api` 모드 |
| `SLACK_WEBHOOK_URL` | Slack 전송 테스트 |
| `DISCORD_WEBHOOK_URL` | Discord 전송 테스트 |
| `EMAIL_USERNAME` / `EMAIL_PASSWORD` / `EMAIL_RECIPIENTS` | 이메일 전송 테스트 |
| `SITE_BASE_URL` | `--generate-static` 서브패스 배포 (로컬 루트는 비워둠) |

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|---------|
| 2024-04-05 | 1.0 | 초기 요구사항 문서 작성 |
| 2026-04-11 | 2.0 | 17개 소스 확장, 다채널 알림, GitHub Pages, 카테고리/소스 브라우징, Claude 상위 20 랭킹, 홈 대시보드, GitHub Actions 자동화 반영. FR 및 NFR 일괄 갱신 |
| 2026-04-11 | 2.1 | Phase 7 독자 레벨 필터 — FR-036~040, NFR-016 추가 |
| 2026-04-12 | 2.2 | Phase 8 Recency + 중복 제거 — FR-041~045, NFR-017~018 추가, DEBT-003/005 resolved |
