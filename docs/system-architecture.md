# AI Report Service - 시스템 아키텍처

## 1. 시스템 개요

AI Report Service는 여러 소스에서 AI 관련 기사/논문을 수집하고, 한국어 요약을 생성하여 Slack으로 전송하는 자동화 서비스입니다.

**두 가지 실행 모드 지원:**
- **Claude Code 모드 (기본)**: Claude Code 스킬이 요약 수행 (API 키 불필요)
- **API 모드 (--use-api)**: Anthropic API 직접 호출 (기존 방식)

---

## 2. 아키텍처 다이어그램

### Claude Code 모드 (기본, API 키 불필요)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Claude Code 모드                               │
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────┐ │
│  │   Sources   │     │  Collectors │     │    JSON     │     │Claude │ │
│  │             │────▶│             │────▶│   Storage   │────▶│ Code  │ │
│  │ arXiv/Blog  │     │   (Parse)   │     │  (data/)    │     │(Skill)│ │
│  └─────────────┘     └─────────────┘     └─────────────┘     └───────┘ │
│                                                 │                  │    │
│                                                 │                  ▼    │
│                                                 │            ┌───────┐ │
│                                                 └───────────▶│ Slack │ │
│                                                              │(Hook) │ │
│        External              Python CLI        Claude Code   └───────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### API 모드 (--use-api, Anthropic API 키 필요)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            API 모드                                     │
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌───────┐ │
│  │   Sources   │     │  Collectors │     │  Summarizer │     │ Slack │ │
│  │             │────▶│             │────▶│             │────▶│       │ │
│  │ arXiv/Blog  │     │   (Parse)   │     │(Claude API) │     │(Hook) │ │
│  └─────────────┘     └─────────────┘     └─────────────┘     └───────┘ │
│                                                                         │
│        External                    Internal                   External  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 데이터 흐름

### Claude Code 모드

```
1. Collection     2. Parsing        3. JSON Save       4. Summarization    5. Notification
┌──────────┐     ┌──────────┐      ┌──────────┐       ┌──────────┐        ┌──────────┐
│  Fetch   │────▶│  Parse   │─────▶│   Save   │──────▶│ Summarize│───────▶│   Send   │
│  URLs    │     │  Content │      │   JSON   │       │ + Classify│       │  Report  │
└──────────┘     └──────────┘      └──────────┘       └──────────┘        └──────────┘
     │                │                  │                  │                   │
     ▼                ▼                  ▼                  ▼                   ▼
 RSS/HTML         Article          articles_*.json    Claude Code가        Slack Message
 Response          Text            (data/ 디렉토리)    직접 요약 수행        (Block Kit)
```

### API 모드 (--use-api)

```
1. Collection     2. Parsing        3. Summarization    4. Notification
┌──────────┐     ┌──────────┐      ┌──────────┐        ┌──────────┐
│  Fetch   │────▶│  Parse   │─────▶│ Summarize│───────▶│   Send   │
│  URLs    │     │  Content │      │ + Classify│       │  Report  │
└──────────┘     └──────────┘      └──────────┘        └──────────┘
     │                │                  │                   │
     ▼                ▼                  ▼                   ▼
 RSS/HTML         Article           Anthropic API       Slack Message
 Response          Text            (summarizer.py)      (Block Kit)
```

### 단계별 설명

1. **Collection**: 각 소스에서 최신 기사/논문 목록을 가져옴
2. **Parsing**: HTML/XML에서 기사 본문 추출
3. **JSON Save** (Claude Code 모드): 수집된 기사를 `data/articles_*.json`에 저장
4. **Summarization**: 한국어 요약 생성 및 카테고리 분류
   - Claude Code 모드: 스킬이 직접 수행
   - API 모드: Anthropic API 호출
5. **Notification**: Slack Webhook으로 포맷팅된 리포트 전송

---

## 4. 모듈 구조

```
src/
├── __init__.py
├── main.py              # CLI 진입점, 파이프라인 오케스트레이션
├── config.py            # 설정 로더 (YAML + 환경 변수)
├── models.py            # 데이터 모델 (Article, Category, Source)
├── data_io.py           # JSON 읽기/쓰기 유틸리티
├── summarizer.py        # Claude API 요약 모듈 (--use-api 모드)
├── slack_notifier.py    # Slack Webhook 알림 모듈
└── collectors/          # 기사 수집기 모듈
    ├── __init__.py
    ├── base.py          # BaseCollector 추상 클래스
    ├── arxiv.py         # arXiv RSS 수집기
    ├── google_blog.py   # Google AI Blog 수집기
    └── anthropic_blog.py # Anthropic Blog 수집기

data/                    # 수집/요약 데이터 (JSON)
├── articles_*.json      # 수집된 원본 기사
└── report_*.json        # 요약된 리포트

.claude/skills/
└── ai-report/           # Claude Code 리포트 생성 스킬
    └── SKILL.md
```

### 모듈 의존성

```
main.py
   │
   ├── config.py
   │
   ├── data_io.py ◀── models.py (Article, Report)
   │
   ├── collectors/
   │      ├── base.py ◀── arxiv.py
   │      │           ◀── google_blog.py
   │      │           ◀── anthropic_blog.py
   │      └── models.py (Article, Source)
   │
   ├── summarizer.py (--use-api 모드에서만 사용)
   │      └── models.py (Article, Category)
   │
   └── slack_notifier.py
          └── models.py (Article, Category)
```

---

## 5. 핵심 컴포넌트

### 5.1 BaseCollector (추상 클래스)

```python
class BaseCollector(ABC):
    @abstractmethod
    def fetch_articles(self) -> List[Article]: ...

    @abstractmethod
    def parse_article_content(self, url: str) -> str: ...

    def collect(self) -> List[Article]: ...
```

### 5.2 Summarizer

```python
class Summarizer:
    def __init__(self, api_key: str, model: str): ...
    def summarize(self, article: Article) -> Article: ...
    def summarize_batch(self, articles: List[Article]) -> List[Article]: ...
```

### 5.3 SlackNotifier

```python
class SlackNotifier:
    def __init__(self, webhook_url: str): ...
    def send_report(self, articles: List[Article], date: datetime): ...
    def format_message(self, articles: List[Article]) -> dict: ...
```

---

## 6. 외부 의존성

| 라이브러리 | 용도 | 버전 |
|-----------|------|------|
| anthropic | Claude API 클라이언트 | latest |
| requests | HTTP 요청 | latest |
| beautifulsoup4 | HTML 파싱 | latest |
| lxml | XML/HTML 파서 | latest |
| slack-sdk | Slack API (Webhook) | latest |
| PyYAML | YAML 설정 파싱 | latest |
| python-dotenv | 환경 변수 로딩 | latest |

---

## 7. 설정 관리

### 7.1 환경 변수

```bash
ANTHROPIC_API_KEY=sk-ant-...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 7.2 config.yaml

```yaml
anthropic:
  model: claude-sonnet-4-20250514

collectors:
  arxiv:
    enabled: true
    categories: [cs.AI, cs.LG, cs.CL]
  google_blog:
    enabled: true
  anthropic_blog:
    enabled: true

slack:
  enabled: true
```

---

## 8. 에러 처리 전략

| 실패 지점 | 전략 | 영향 |
|----------|------|------|
| 소스 수집 실패 | 해당 소스 스킵, 로그 기록 | 다른 소스 계속 진행 |
| 기사 파싱 실패 | 해당 기사 스킵, 로그 기록 | 다른 기사 계속 진행 |
| 요약 실패 | 해당 기사 스킵 또는 제목만 포함 | 다른 기사 계속 진행 |
| Slack 전송 실패 | 재시도 (3회) | 실패 시 에러 로그 |

---

## 9. 확장 고려사항

### 새 소스 추가

1. `BaseCollector` 상속
2. `fetch_articles()`, `parse_article_content()` 구현
3. `collectors/__init__.py`에 등록
4. `config.yaml`에 설정 추가

### 새 알림 채널 추가

1. `BaseNotifier` 추상화
2. 새 알림 채널 구현체 추가 (Discord, Email 등)

### 성능 최적화

- 비동기 수집 (aiohttp)
- 기사 캐싱 (URL 해시 기반 중복 제거)
- 배치 요약 (API 호출 최소화)

---

## 10. 배포 구조

### Claude Code 모드 (수동 실행)

```
┌─────────────────────────────────────┐
│         Claude Code 환경            │
│                 │                   │
│                 ▼                   │
│    ┌────────────────────────┐       │
│    │  /ai-report 스킬 실행  │       │
│    │                        │       │
│    │ 1. python --collect-only│      │
│    │ 2. JSON 로드 및 요약    │       │
│    │ 3. python --send-only   │       │
│    └────────────────────────┘       │
│                 │                   │
│                 ▼                   │
│            Slack API                │
│            (External)               │
└─────────────────────────────────────┘
```

### API 모드 (자동화, Cron)

```
┌─────────────────────────────────────┐
│           Cron Scheduler            │
│         (매일 09:00 KST)            │
│                 │                   │
│                 ▼                   │
│    ┌────────────────────────┐       │
│    │    AI Report Service   │       │
│    │  (python -m src.main   │       │
│    │       --use-api)       │       │
│    └────────────────────────┘       │
│                 │                   │
│    ┌────────────┴────────────┐      │
│    ▼                         ▼      │
│ Anthropic API           Slack API   │
│ (External)              (External)  │
└─────────────────────────────────────┘
```

### Cron 설정 (API 모드)

```cron
0 9 * * * cd /path/to/ai-report && .venv/bin/python -m src.main --use-api >> /var/log/ai-report.log 2>&1
```
