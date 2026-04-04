# AI Report Service - 설계 문서

## 1. 시스템 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Sources   │ ──▶ │  Collectors │ ──▶ │  Summarizer │ ──▶ │   Slack     │
│ arXiv/Blog  │     │   (Parse)   │     │ (Claude AI) │     │  (Webhook)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 데이터 흐름
1. **수집 (Collection)**: 각 소스에서 최신 기사/논문 목록 수집
2. **파싱 (Parsing)**: 기사 본문 추출
3. **요약 (Summarization)**: Claude API로 한국어 요약 생성 및 카테고리 분류
4. **전송 (Notification)**: Slack Webhook으로 리포트 전송

## 2. 데이터 모델

### Article
```python
@dataclass
class Article:
    id: str              # UUID
    title: str           # 기사 제목
    url: str             # 원문 URL
    source: Source       # 출처 (arxiv | google | anthropic)
    content: str         # 원문 내용
    published_at: datetime  # 발행일
    summary: str         # AI 생성 요약
    category: Category   # 분류된 카테고리
```

### Category (12개)
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

## 3. 수집기 (Collectors)

### BaseCollector (추상 클래스)
모든 수집기의 공통 인터페이스:
- `fetch_articles() -> List[Article]`: 기사 목록 수집
- `parse_article_content(url) -> str`: 개별 기사 본문 파싱
- `collect() -> List[Article]`: 수집 + 파싱 통합

### ArxivCollector
- **소스**: arXiv RSS 피드
- **카테고리**: cs.AI, cs.LG, cs.CL
- **파싱**: XML (RSS), HTML (상세 페이지)

### GoogleBlogCollector
- **소스**: Google AI 블로그 (DeepMind, Research, Labs, Gemini)
- **파싱**: HTML (BeautifulSoup)

### AnthropicBlogCollector
- **소스**: Anthropic 뉴스/블로그
- **파싱**: HTML (BeautifulSoup)

## 4. 요약기 (Summarizer)

### Claude API 활용
- **Model**: claude-sonnet-4-20250514
- **출력**: JSON (summary + category)

### 프롬프트 구조
```
당신은 AI/ML 분야 전문 기술 에디터입니다.
다음 기사를 읽고 한국어로 요약해주세요.

## 요구사항
1. 3-5문장으로 핵심 내용을 요약
2. 기술적 의의와 실용적 영향을 포함
3. 전문 용어는 그대로 사용하되 필요시 간단히 설명

## 카테고리
[12개 카테고리 목록]

## 기사 제목
{title}

## 기사 내용
{content}

## 응답 형식 (JSON)
{"summary": "...", "category": "..."}
```

## 5. 슬랙 알림 (Slack Notifier)

### Webhook 방식
- Incoming Webhook URL 사용
- Block Kit으로 리치 메시지 포맷팅

### 메시지 구조
```
📰 2024년 01월 15일 AI 데일리 리포트
─────────────────────────────
📂 LLM (대규모 언어 모델)
• [제목] - 요약 내용... (링크)

📂 AI 에이전트 & 자동화
• [제목] - 요약 내용... (링크)
...
─────────────────────────────
총 15개의 기사 | 생성: 09:00
```

## 6. 설정 관리

### 환경 변수
- `ANTHROPIC_API_KEY`: Claude API 키 (필수)
- `SLACK_WEBHOOK_URL`: Slack Webhook URL (필수)

### config.yaml
```yaml
anthropic:
  api_key: ${ANTHROPIC_API_KEY}
  model: claude-sonnet-4-20250514

slack:
  webhook_url: ${SLACK_WEBHOOK_URL}

collectors:
  arxiv:
    enabled: true
    categories: [cs.AI, cs.LG, cs.CL]
  google_blog:
    enabled: true
  anthropic_blog:
    enabled: true
```

## 7. 에러 처리

### 전략
1. **수집 실패**: 해당 소스 스킵, 다른 소스 계속 진행
2. **요약 실패**: 해당 기사 스킵 또는 제목만 포함
3. **전송 실패**: 에러 로그 및 재시도
4. **전체 실패**: 에러 알림 슬랙 전송

### 로깅
- INFO: 정상 흐름 추적
- WARNING: 개별 실패 (계속 진행)
- ERROR: 심각한 오류

## 8. 확장 고려사항

### 새 소스 추가
1. `BaseCollector` 상속
2. `fetch_articles()`, `parse_article_content()` 구현
3. `collectors/__init__.py`에 등록
4. `main.py`의 수집 로직에 추가

### 다른 알림 채널
- `BaseNotifier` 추상화 후 구현체 추가
- Discord, Email, Telegram 등

### 성능 최적화
- 비동기 수집 (aiohttp)
- 기사 캐싱 (URL 해시 기반 dedup)
- 배치 요약 (API 호출 최소화)
