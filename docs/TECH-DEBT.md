# Technical Debt Tracker

AI Report Service의 기술 부채를 추적하고 관리합니다.

---

## Summary

| Priority | Count | Oldest |
|----------|-------|--------|
| Critical | 0 | - |
| High | 0 | - |
| Medium | 3 | 2026-04-10 |
| Low | 2 | 2026-04-10 |

**Total Active Items**: 5

---

## Active Items

### Critical Priority

_No critical items._

### High Priority

_No high priority items._

### Medium Priority

### DEBT-001: Meta AI Blog 수집기 비활성

**Priority**: Medium
**Category**: Reliability
**Added**: 2026-04-10
**Location**: `src/collectors/meta_ai_blog.py`, `src/main.py:get_enabled_collectors`

**Description**:
`ai.meta.com/blog/`가 일반 HTTP 클라이언트에 400 Bad Request를 반환함.
User-Agent/헤더 조합을 여러 개 시도했으나 모두 거부됨. 헤드리스 브라우저
(Playwright 등) 없이는 접근 불가능. 현재 `MetaAIBlogCollector` 코드는
존재하지만 `main.py:get_enabled_collectors`에서 주석 처리된 상태.

**Impact**:
Meta의 Llama, FAIR, Reality Labs AI 연구 업데이트가 누락됨. Frontier Lab
커버리지에서 주요 축이 빠져있음.

**Remediation**:
- 옵션 A: Playwright/Puppeteer로 헤드리스 수집 (의존성 추가 + GitHub Actions 러너 부담)
- 옵션 B: Meta Research Blog (`research.facebook.com/blog/`) 대체 검토 — 현재 fbpixel
  차단으로 보임
- 옵션 C: `about.fb.com/news/category/announcements/` 같은 우회 URL 탐색
- 옵션 D: Meta 공식 X(트위터) 계정을 수집원으로 사용 (nitter 기반)

**Estimated Effort**: 4~8시간 (옵션 A 기준)

---

### DEBT-002: LG AI Research 수집기 비활성

**Priority**: Medium
**Category**: Reliability
**Added**: 2026-04-10
**Location**: `src/collectors/lg_ai_research.py`, `src/main.py:get_enabled_collectors`

**Description**:
`lgresearch.ai/blog`은 Nuxt.js SPA로 SSR HTML이 빈 상태(블로그 데이터
없음). 공개 API 엔드포인트 미발견 (`/api/blog`, `/api/research/blog` 등
전부 404). `sitemap.xml`은 200을 반환하나 블로그 포스트가 단 1건(seq=506)만
등재됨. 현재 `LGAIResearchCollector` 코드는 존재하지만 비활성.

**Impact**:
EXAONE 시리즈 등 LG AI연구원의 주요 발표 누락. 한국 Frontier AI 커버리지
약화.

**Remediation**:
- 옵션 A: Playwright 헤드리스 수집 (DEBT-001과 공통 인프라)
- 옵션 B: Nuxt 빌드가 fetch하는 내부 API 엔드포인트 네트워크 탭으로 역탐지
- 옵션 C: LG AI Research 공식 X / LinkedIn 계정 수집
- 옵션 D: EXAONE 관련 뉴스를 AI타임스에서 간접 수집 (이미 부분적으로 커버됨)

**Estimated Effort**: 4~8시간

---

### DEBT-003: arXiv `published_at` 파싱 누락

**Priority**: Medium
**Category**: Code Quality
**Added**: 2026-04-10
**Location**: `src/collectors/arxiv.py:_fetch_rss`

**Description**:
`ArxivCollector._fetch_rss`가 RSS `<pubDate>`를 추출하지 않아 모든 arXiv
기사의 `published_at`이 `None`임. 2026-04-10 리포트 분석 결과 680개 arxiv
기사 전부 None 확인. 다른 RSS 수집기(`RSSCollector`)는 feedparser로 자동
파싱하지만 arxiv만 `xml.etree.ElementTree`로 직접 파싱하면서 pubDate를
읽지 않음.

**Impact**:
- 최신순 정렬, 날짜 필터링, "오늘 올라온 것만" 필터링 등이 arxiv 기사에 대해
  작동 안 함.
- 리포트 페이지에서 published 날짜 배지가 arxiv 기사에만 없음.
- 향후 Claude 랭킹 프롬프트가 recency 가중치를 쓰면 arxiv가 불리.

**Remediation**:
`item.find("pubDate")` 추출 후 `email.utils.parsedate_to_datetime` 또는
`dateutil.parser.parse`로 변환해 `Article.published_at`에 설정.
또는 `ArxivCollector`를 `RSSCollector` 상속으로 리팩터해 feedparser 재사용
(더 큰 변경).

**Estimated Effort**: 30분 (단순 fix) / 2시간 (RSSCollector 리팩터)

---

### Low Priority

### DEBT-004: HF Papers URL이 Takara TLDR로 리다이렉트

**Priority**: Low
**Category**: Code Quality
**Added**: 2026-04-10
**Location**: `src/collectors/hf_papers.py`

**Description**:
`HFPapersCollector`는 `papers.takara.ai/api/feed` 비공식 RSS를 사용하는데,
이 피드가 반환하는 entry URL이 `https://tldr.takara.ai/p/{arxiv_id}` 형태임.
사용자는 "Hugging Face Daily Papers"로 수집된 링크가 `huggingface.co/papers/{id}`
또는 `arxiv.org/abs/{id}`로 가기를 기대할 가능성이 높음.

**Impact**:
클릭 시 원본(HF/arxiv)이 아닌 Takara의 TLDR 요약 페이지로 이동해 UX가 일관성 없음.

**Remediation**:
`fetch_articles`에서 entry URL이 `tldr.takara.ai/p/{id}` 패턴이면 id를
추출해 `https://huggingface.co/papers/{id}` 또는 `https://arxiv.org/abs/{id}`로
변환. HF papers 공식 페이지 가는 게 더 자연스러움.

**Estimated Effort**: 30분

---

### DEBT-005: 레거시 pre-ranking 리포트 (2026-04-05, 2026-04-10)

**Priority**: Low
**Category**: Code Quality
**Added**: 2026-04-11
**Location**: `data/report_2026-04-05.json`, `data/report_2026-04-10.json`

**Description**:
Claude 상위 20개 랭킹 프롬프트는 커밋 `b8c50a2` 에서 도입됐는데, 기존에
커밋되어 있던 2026-04-05(1개), 2026-04-10(824개) 리포트는 랭킹 전에 생성된
데이터. 특히 2026-04-10 리포트는 수집된 824개 기사 전부를 요약 없이 담고
있어(Claude Code CLI가 구버전 프롬프트로 실행됨) 홈 대시보드의 "Today's
Categories/Sources" 미리보기와 카테고리/소스 페이지의 누적 통계가 왜곡됨
(예: 홈 stats "824 Articles").

**Impact**:
- 홈 대시보드 통계가 한동안 과대 표시
- 카테고리 브라우징 페이지의 누적 카운트가 왜곡
- 새 리포트가 쌓이면 자연히 시각적 비중이 줄어들지만 당분간 눈에 띔

**Remediation**:
- 옵션 A: `data/report_2026-04-10.json`을 삭제하거나 20개로 수동 트리밍
- 옵션 B: 자동 재생성 — 저장된 articles snapshot이 없어 원상 복구 불가능
- 옵션 C: 그대로 두고 새 리포트 누적으로 희석 — 수일 내에 자연 해소

**Estimated Effort**: 5분 (옵션 A) / 0분 (옵션 C)

---

## Item Template

새 기술 부채 항목 추가 시 아래 템플릿을 사용하세요:

```markdown
### DEBT-NNN: [Short Title]

**Priority**: Critical / High / Medium / Low
**Category**: Performance / Security / Testing / Reliability / Code Quality
**Added**: YYYY-MM-DD
**Location**: `path/to/file.py:line`

**Description**:
[문제에 대한 설명]

**Impact**:
[해결하지 않을 경우의 영향]

**Remediation**:
[해결 방법]

**Estimated Effort**: [시간 추정]

**Blocked By**: (optional)
[선행 작업이 있는 경우]
```

---

## Categories

| Category | Description |
|----------|-------------|
| Performance | 성능 관련 이슈 |
| Security | 보안 취약점 |
| Testing | 테스트 커버리지 부족 |
| Reliability | 안정성/에러 처리 |
| Code Quality | 코드 품질/가독성 |

---

## Escalation Thresholds

| Priority | Age Threshold | Action |
|----------|---------------|--------|
| Critical | 0 days | 즉시 처리 |
| High | 14 days | 다음 스프린트에 포함 |
| Medium | 21 days | 검토 및 우선순위 재평가 |
| Low | 30 days | 검토 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|---------|
| 2024-04-05 | 초기 문서 생성 |
| 2026-04-11 | DEBT-001~005 등록 (Meta AI/LG AI 비활성, arxiv published_at, HF Papers URL, 레거시 리포트) |
