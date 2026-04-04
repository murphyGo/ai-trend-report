# AI Report Automation Service

일일 AI 뉴스/논문 자동 수집 및 요약 리포트 서비스

최신 AI 관련 기술 동향을 자동으로 수집하여 한국어로 요약한 데일리 리포트를 Slack으로 전송합니다.

## 주요 기능

- 여러 소스에서 AI 관련 기사/논문 자동 수집 (arXiv, Google AI Blog, Anthropic Blog)
- Claude API를 활용한 한국어 요약 생성
- 12개 카테고리 자동 분류
- Slack Webhook을 통한 리포트 전송
- CLI 기반 실행 및 Cron 스케줄링 지원
- Dry-run 모드 지원

## 카테고리

| 카테고리 | 설명 |
|----------|------|
| LLM | 대규모 언어 모델 |
| AI 에이전트 & 자동화 | 에이전트 및 자동화 관련 |
| 컴퓨터 비전 & 멀티모달 | 이미지/영상 인식, 멀티모달 |
| 비디오 생성 | 비디오 생성 AI |
| 로보틱스 & 3D | 로봇공학 및 3D 관련 |
| AI 안전성 & 윤리 | AI 안전 및 윤리 |
| 강화학습 | RL 관련 연구 |
| ML 인프라 & 최적화 | 인프라 및 최적화 |
| 의료 & 생명과학 | 의료/바이오 AI |
| 금융 & 트레이딩 | 금융 AI |
| 산업 동향 & 한국 소식 | 산업 뉴스 |
| 기타 | 기타 |

## 요구사항

- Python 3.9+
- Anthropic API Key
- Slack Incoming Webhook URL

## 설치

```bash
# 저장소 클론
git clone <repository-url>
cd ai-report

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 설정 파일 복사
cp config.example.yaml config.yaml
```

## 환경 변수 설정

`.env` 파일을 생성하거나 환경 변수를 직접 설정합니다.

```bash
export ANTHROPIC_API_KEY="your-api-key"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

| 변수 | 설명 | 필수 |
|------|------|------|
| ANTHROPIC_API_KEY | Claude API 키 | O |
| SLACK_WEBHOOK_URL | Slack Incoming Webhook URL | O |

### Slack Webhook 설정

1. https://api.slack.com/apps 에서 앱 생성
2. Incoming Webhooks 활성화
3. 채널에 Webhook 추가
4. Webhook URL을 환경 변수에 설정

## 사용법

```bash
# 전체 파이프라인 실행
python -m src.main

# Slack 전송 없이 테스트 (dry-run)
python -m src.main --dry-run

# 기사 수 제한하여 테스트
python -m src.main --dry-run --limit 5

# 상세 로그 출력
python -m src.main --verbose
```

## Cron 설정

매일 오전 9시에 자동 실행:

```cron
0 9 * * * cd /path/to/ai-report && /path/to/.venv/bin/python -m src.main >> /var/log/ai-report.log 2>&1
```

## 프로젝트 구조

```
ai-report/
├── README.md              # 이 파일
├── CLAUDE.md              # 프로젝트 문서
├── DESIGN.md              # 상세 설계 문서
├── requirements.txt       # Python 의존성
├── config.example.yaml    # 설정 예시
├── config.yaml            # 실제 설정 (gitignore)
├── src/
│   ├── __init__.py
│   ├── main.py            # CLI 진입점
│   ├── config.py          # 설정 로더
│   ├── models.py          # 데이터 모델
│   ├── summarizer.py      # AI 요약
│   ├── slack_notifier.py  # 알림 전송
│   └── collectors/        # 기사 수집기
│       ├── base.py        # 추상 수집기
│       ├── arxiv.py       # arXiv 수집기
│       ├── google_blog.py # Google 블로그 수집기
│       └── anthropic_blog.py  # Anthropic 블로그 수집기
└── .gitignore
```

## 데이터 소스

- [arXiv](https://arxiv.org) - cs.AI, cs.LG, cs.CL 카테고리
- [Google AI Blog](https://blog.google/technology/ai/) - DeepMind, Google Research, Google Labs, Gemini
- [Anthropic News](https://www.anthropic.com/news)

## 기술 스택

- **anthropic** - Claude API 클라이언트
- **requests, beautifulsoup4, lxml** - 웹 스크래핑
- **slack-sdk** - Slack 알림
- **PyYAML, python-dotenv** - 설정 관리

## 라이선스

MIT License
