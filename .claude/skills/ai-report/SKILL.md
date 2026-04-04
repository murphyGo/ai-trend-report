# AI Report Skill

AI 뉴스/논문 수집 및 한국어 리포트 생성

## Arguments
- `--dry-run`: Slack 전송 없이 미리보기
- `--limit N`: 처리할 기사 수 제한 (기본: 전체)
- `--use-api`: Anthropic API 사용 (기존 방식, API 키 필요)

## Execution Flow

### Mode 1: Claude Code 요약 (기본)

```
Step 1: 기사 수집
        ↓
Step 2: JSON 로드 및 분석
        ↓
Step 3: 요약 및 분류 (Claude Code 직접 수행)
        ↓
Step 4: 리포트 JSON 저장
        ↓
Step 5: Slack 전송
```

### Mode 2: API 요약 (--use-api)
기존 파이프라인 실행: `python -m src.main --use-api`

---

## Step 1: 기사 수집

Python 스크립트로 기사를 수집합니다.

```bash
python -m src.main --collect-only [--limit N]
```

결과: `data/articles_YYYY-MM-DD.json` 생성

---

## Step 2: JSON 로드 및 분석

수집된 기사 JSON 파일을 읽습니다.

- 파일 경로: `data/articles_YYYY-MM-DD.json`
- 각 기사에서 `title`, `url`, `source`, `content` 필드 확인

---

## Step 3: 요약 및 분류

각 기사에 대해 한국어 요약과 카테고리 분류를 수행합니다.

### 요약 지침
- **길이**: 3-5문장
- **언어**: 한국어
- **내용**:
  - 핵심 기술/발견 요약
  - 기술적 의의
  - 실용적 영향 또는 활용 가능성
- **스타일**: 전문적이고 객관적인 톤

### 카테고리 분류
아래 12개 카테고리 중 하나를 선택합니다:

| 카테고리 | 설명 |
|---------|------|
| LLM (대규모 언어 모델) | GPT, Claude, LLaMA 등 언어 모델 관련 |
| AI 에이전트 & 자동화 | 에이전트, 자동화, 워크플로우 |
| 컴퓨터 비전 & 멀티모달 | 이미지/비전, 멀티모달 모델 |
| 비디오 생성 | Sora, Runway 등 비디오 생성 |
| 로보틱스 & 3D | 로봇, 3D 생성, 시뮬레이션 |
| AI 안전성 & 윤리 | 안전성, 정렬, 윤리적 AI |
| 강화학습 | RL, RLHF, 보상 학습 |
| ML 인프라 & 최적화 | 학습 최적화, 인프라, 효율성 |
| 의료 & 생명과학 | 의료 AI, 바이오, 신약 개발 |
| 금융 & 트레이딩 | 금융 AI, 알고리즘 트레이딩 |
| 산업 동향 & 한국 소식 | 기업 뉴스, 한국 AI 동향 |
| 기타 | 위 카테고리에 해당하지 않는 경우 |

---

## Step 4: 리포트 JSON 저장

요약이 완료된 기사들을 리포트 형식으로 저장합니다.

```python
# 저장 형식 (data/report_YYYY-MM-DD.json)
{
  "id": "uuid",
  "created_at": "2024-04-05T09:00:00",
  "articles": [
    {
      "id": "uuid",
      "title": "기사 제목",
      "url": "https://...",
      "source": "arxiv",
      "content": "원본 내용",
      "published_at": "2024-04-05T00:00:00",
      "summary": "한국어 요약 3-5문장...",
      "category": "LLM (대규모 언어 모델)"
    }
  ]
}
```

Python 코드로 저장:
```python
from src.data_io import save_report
from src.models import Report, Article

report = Report(articles=summarized_articles)
save_report(report)
```

---

## Step 5: Slack 전송

리포트를 Slack으로 전송합니다.

```bash
# dry-run (미리보기)
python -m src.main --send-only --dry-run

# 실제 전송
python -m src.main --send-only
```

---

## Dry-run 모드

`--dry-run` 옵션 사용 시:
- Step 1-4는 정상 수행
- Step 5에서 Slack 전송 대신 미리보기 출력

---

## 실행 예시

### 기본 실행 (수동)
```
User: /ai-report
Claude: 기사를 수집하고 요약을 시작합니다...
        [Step 1] 수집 중...
        [Step 2] JSON 분석 중...
        [Step 3] 요약 생성 중...
        [Step 4] 리포트 저장...
        [Step 5] Slack 전송...
        완료! 15개 기사가 Slack으로 전송되었습니다.
```

### Dry-run (테스트)
```
User: /ai-report --dry-run --limit 3
Claude: 테스트 모드로 3개 기사만 처리합니다...
        [결과 미리보기]
        - [LLM] Claude 3.5 Sonnet 발표...
        - [AI 에이전트] ...
```

### API 모드 (기존 방식)
```
User: /ai-report --use-api
Claude: Anthropic API를 사용하여 요약합니다...
        (ANTHROPIC_API_KEY 필요)
```

---

## 에러 처리

| 상황 | 대응 |
|------|------|
| 수집 실패 | 해당 소스 스킵, 다른 소스 계속 |
| 요약 실패 | 원본 title만 사용, 카테고리=기타 |
| Slack 전송 실패 | 에러 메시지 출력, 리포트는 JSON에 보관 |

---

## 파일 경로

| 파일 | 설명 |
|------|------|
| `data/articles_YYYY-MM-DD.json` | 수집된 원본 기사 |
| `data/report_YYYY-MM-DD.json` | 요약 완료된 리포트 |
| `src/main.py` | CLI 진입점 |
| `src/data_io.py` | JSON 읽기/쓰기 |
| `src/models.py` | 데이터 모델 |
