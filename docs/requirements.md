# AI Report Service - 요구사항 문서

## 개요

AI 관련 기술 동향을 자동으로 수집하여 한국어로 요약한 데일리 리포트를 Slack으로 전송하는 서비스의 요구사항을 정의합니다.

---

## 기능 요구사항 (Functional Requirements)

### 데이터 수집

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-001 | arXiv에서 cs.AI, cs.LG, cs.CL 카테고리 논문 수집 | High | Done |
| FR-002 | Google AI 블로그 (DeepMind, Research, Labs, Gemini) 기사 수집 | High | Done |
| FR-003 | Anthropic 뉴스/블로그 기사 수집 | High | Done |

### AI 요약

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-004 | Claude API를 활용한 한국어 요약 생성 | High | Done |
| FR-005 | 12개 카테고리 자동 분류 | High | Done |

### 알림

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-006 | Slack Webhook을 통한 리포트 전송 | High | Done |
| FR-007 | Block Kit 기반 리치 메시지 포맷팅 | Medium | Done |

### CLI

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| FR-008 | Dry-run 모드 지원 (--dry-run) | Medium | Done |
| FR-009 | 기사 수 제한 옵션 (--limit) | Medium | Done |
| FR-010 | 상세 로그 모드 (--verbose) | Low | Done |

---

## 비기능 요구사항 (Non-Functional Requirements)

### 안정성

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| NFR-001 | 개별 소스 수집 실패 시 다른 소스 계속 진행 | High | Done |
| NFR-002 | 개별 기사 요약 실패 시 해당 기사 스킵 | High | Done |
| NFR-003 | 전체 실패 시 에러 알림 전송 | Medium | TODO |

### 보안

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| NFR-004 | 환경 변수로 API 키 관리 | High | Done |
| NFR-005 | config.yaml에 민감 정보 미포함 | High | Done |

### 운영

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| NFR-006 | CLI 기반 실행 | High | Done |
| NFR-007 | Cron 스케줄링 지원 | Medium | Done |
| NFR-008 | 로그 파일 출력 지원 | Low | Done |

### 성능

| ID | 요구사항 | 우선순위 | 상태 |
|----|---------|---------|------|
| NFR-009 | 비동기 수집으로 성능 최적화 | Low | TODO |
| NFR-010 | 기사 캐싱으로 중복 처리 방지 | Low | TODO |

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

## 데이터 소스

| 소스 | URL | 수집 방식 |
|------|-----|---------|
| arXiv | https://arxiv.org | RSS 피드 |
| Google DeepMind | https://blog.google/technology/ai/ | HTML 스크래핑 |
| Google Research | https://blog.google/technology/research/ | HTML 스크래핑 |
| Anthropic | https://www.anthropic.com/news | HTML 스크래핑 |

---

## 환경 변수

| 변수 | 설명 | 필수 |
|------|------|------|
| ANTHROPIC_API_KEY | Claude API 키 | O |
| SLACK_WEBHOOK_URL | Slack Incoming Webhook URL | O |

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|---------|
| 2024-04-05 | 1.0 | 초기 요구사항 문서 작성 |
