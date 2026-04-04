# AI Report Automation Service

일일 AI 뉴스/논문 자동 수집 및 요약 리포트 서비스

## Purpose
최신 AI 관련 기술 동향을 자동으로 수집하여 한국어로 요약한 데일리 리포트를 슬랙으로 전송합니다.

## What to do
1. 여러 소스에서 AI 관련 기사/논문 수집
2. 한국어 요약 생성 및 카테고리 분류 (Claude Code 또는 API)
3. Slack Webhook으로 리포트 전송

## Features
 - Slack 메시지는 한국어로 작성
 - 12개 카테고리로 자동 분류
 - CLI + Cron 기반 스케줄링
 - Dry-run 모드 지원

## Categories
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

## Sources
 - https://arxiv.org (cs.AI, cs.LG, cs.CL 카테고리)
 - https://blog.google/innovation-and-ai/models-and-research/google-deepmind/
 - https://blog.google/innovation-and-ai/models-and-research/google-research/
 - https://blog.google/innovation-and-ai/models-and-research/google-labs/
 - https://blog.google/innovation-and-ai/models-and-research/gemini-models/
 - https://www.anthropic.com/news

## Tech Stack
- Python 3.9+
- anthropic (Claude API)
- requests, beautifulsoup4, lxml (웹 스크래핑)
- slack-sdk (알림)
- PyYAML, python-dotenv (설정)

## Project Structure
```
ai-report/
├── CLAUDE.md              # 프로젝트 문서 (이 파일)
├── DESIGN.md              # 상세 설계 문서
├── requirements.txt       # Python 의존성
├── config.example.yaml    # 설정 예시
├── config.yaml            # 실제 설정 (gitignore)
├── data/                  # 수집/요약 데이터 (JSON)
├── src/
│   ├── __init__.py
│   ├── main.py            # CLI 진입점
│   ├── config.py          # 설정 로더
│   ├── models.py          # 데이터 모델
│   ├── data_io.py         # JSON 읽기/쓰기
│   ├── summarizer.py      # AI 요약 (--use-api 모드)
│   ├── slack_notifier.py  # 알림 전송
│   └── collectors/        # 기사 수집기
│       ├── base.py        # 추상 수집기
│       ├── arxiv.py       # arXiv 수집기
│       ├── google_blog.py # Google 블로그 수집기
│       └── anthropic_blog.py  # Anthropic 블로그 수집기
├── .claude/skills/
│   └── ai-report/         # 리포트 생성 스킬
└── .gitignore
```

## Setup

### 1. 의존성 설치
```bash
cd ai-report
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 설정
```bash
# 설정 파일 복사
cp config.example.yaml config.yaml

# 환경 변수 설정 (.env 파일 또는 직접)
export ANTHROPIC_API_KEY="your-api-key"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### 3. Slack Webhook 설정
1. https://api.slack.com/apps 에서 앱 생성
2. Incoming Webhooks 활성화
3. 채널에 Webhook 추가
4. Webhook URL을 환경 변수에 설정

## Usage

### Claude Code 모드 (권장, API 키 불필요)

```bash
# 1. 기사 수집 (JSON 저장)
python -m src.main                    # data/articles_YYYY-MM-DD.json 생성
python -m src.main --limit 5          # 5개 기사만 수집

# 2. Claude Code에서 /ai-report 스킬 실행
/ai-report                            # 요약 생성 → Slack 전송
/ai-report --dry-run                  # Slack 전송 없이 미리보기
```

### API 모드 (기존 방식, ANTHROPIC_API_KEY 필요)

```bash
# 전체 파이프라인 실행
python -m src.main --use-api

# 슬랙 전송 없이 테스트
python -m src.main --use-api --dry-run

# 기사 수 제한하여 테스트
python -m src.main --use-api --dry-run --limit 5
```

### 개별 단계 실행

```bash
# 수집만 (명시적)
python -m src.main --collect-only

# Slack 전송만 (기존 리포트 JSON 사용)
python -m src.main --send-only
python -m src.main --send-only --input-json data/report_2024-01-01.json
```

## Cron 설정 (API 모드, 매일 오전 9시)
```cron
0 9 * * * cd /path/to/ai-report && /path/to/.venv/bin/python -m src.main --use-api >> /var/log/ai-report.log 2>&1
```

## Environment Variables
| 변수 | 설명 | 필수 |
|------|------|------|
| ANTHROPIC_API_KEY | Claude API 키 | --use-api 모드에서만 필요 |
| SLACK_WEBHOOK_URL | Slack Incoming Webhook URL | Slack 전송 시 필요 |
