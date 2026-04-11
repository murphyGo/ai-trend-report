# Technical Debt Tracker

AI Report Service의 기술 부채를 추적하고 관리합니다.

---

## Summary

| Priority | Count | Oldest |
|----------|-------|--------|
| Critical | 0 | - |
| High | 0 | - |
| Medium | 2 | 2026-04-10 |
| Low | 1 | 2026-04-10 |

**Total Active Items**: 3 (DEBT-003, DEBT-005 resolved 2026-04-12)

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

## Resolved Items

### DEBT-003: arXiv `published_at` 파싱 누락 (resolved 2026-04-12)

**Resolution**: Phase 8.1 — `src/collectors/arxiv.py:_fetch_rss`에서 `<pubDate>`
(RFC 822) 우선, `<dc:date>` (ISO 8601) fallback으로 파싱. `email.utils.
parsedate_to_datetime` + `datetime.fromisoformat` 조합. 단위 테스트
`tests/test_filters.py::TestArxivDateParser` 7개로 회귀 방지.

Phase 8.2 Recency 필터가 이 필드에 의존하므로 선결 조건으로 해소됨.

### DEBT-005: 레거시 pre-ranking 리포트 (resolved 2026-04-12)

**Resolution**: 사용자 요청으로 `data/report_2026-04-05.json`과
`data/report_2026-04-10.json`을 git에서 삭제 (Phase 8.4). `2026-04-11` 리포트
(20개)만 유지. 홈 대시보드 통계 왜곡 해소.

향후 이런 레거시 오염이 생기지 않도록 Phase 8.2+8.3 recency/dedup 필터가
선제적으로 차단함.

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
| 2026-04-12 | DEBT-003 (arxiv pubDate 파싱) 및 DEBT-005 (레거시 리포트 삭제) resolved — Phase 8 |
