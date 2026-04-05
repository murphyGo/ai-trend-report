# AI Report Service - 개발 계획

## 현재 상태

| 컴포넌트 | 상태 | 비고 |
|---------|------|------|
| 프로젝트 구조 | ✅ Complete | src/ 구조 완성 |
| 데이터 모델 | ✅ Complete | Article, Category, Source + 직렬화 |
| Collectors | ✅ Complete | arXiv, Google, Anthropic |
| Summarizer | ✅ Complete | Claude API 연동 (--use-api) |
| Slack Notifier | ✅ Complete | Webhook 연동 |
| Email Notifier | 📋 Planned | Phase 3.3 예정 |
| CLI | ✅ Complete | main.py (다중 모드 지원) |
| Claude Code 스킬 | ✅ Complete | /ai-report 스킬 |
| 데이터 I/O | ✅ Complete | JSON 직렬화/역직렬화 |
| 테스트 | ❌ Missing | 테스트 코드 없음 |
| 문서화 | 🔄 In Progress | docs/ 구축 중 |

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
- [ ] 단위 테스트 (pytest)
- [ ] Collector 모킹 테스트
- [ ] Summarizer 모킹 테스트
- [ ] 통합 테스트

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
- [ ] OpenAI 블로그 수집기
- [ ] Hugging Face 블로그 수집기
- [ ] 한국 AI 뉴스 수집기

### 3.2 성능 최적화
- [ ] 비동기 수집 (aiohttp)
- [ ] 기사 캐싱 (중복 제거)
- [ ] 배치 요약 (API 호출 최소화)

### 3.3 이메일 알림 기능
- [ ] EmailNotifier 클래스 구현 (SMTP)
- [ ] HTML 이메일 템플릿 (카테고리별 섹션)
- [ ] 다중 수신자 지원
- [ ] CLI 플래그 추가 (`--email`, `--email-to`)
- [ ] 설정 추가 (config.yaml: smtp 섹션)

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
- [ ] Discord Webhook 알림
- [ ] 웹 대시보드
- [ ] 기사 저장 (DB)

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
