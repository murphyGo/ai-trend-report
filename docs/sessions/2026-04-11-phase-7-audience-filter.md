# Session Log: 2026-04-11 - Phase 7 - Reader Audience Classification & Filter

## Overview
- **Date**: 2026-04-11
- **Phase**: 7 - 독자 레벨별 필터
- **Sub-task**: 7.1 ~ 7.5 (one coherent feature implemented in a single session)

## Work Summary

카테고리 · 소스 외에 "누가 읽기 위한 글인가"라는 직교 3rd 축을 추가.
사용자가 자기 수준(일반인 / 개발자 / ML 전문가)에 맞는 기사만 전 페이지에서
실시간으로 필터링할 수 있도록 했다.

Multi-tag 스킴 — 하나의 기사가 여러 레벨에 속할 수 있음 (예: GPT-5 발표는
일반인 뉴스이자 개발자 API 업데이트이자 ML 전문가 벤치마크). 태깅은 Claude가
`daily-report.yml`의 Stage 2 프롬프트 안에서 판단하며, 태그가 없는 레거시
리포트는 소스 기반 매핑(`SOURCE_AUDIENCE`)으로 즉시 fallback 분류됨.

UI는 히어로/페이지 헤더 바로 아래에 전역 필터 바(네 칩)를 노출하고 선택 값을
`localStorage`에 저장해 페이지 이동해도 유지. 카테고리/소스 인덱스 카드에는
audience 미니 통계(`일반 N · 개발 N · ML N`) 배지를 추가해 분포를 한눈에
파악 가능하게 함.

## Files Changed

### Created
- `src/static/templates/audience_filter.html` — 필터 바 파셜 (`{% include %}`용)
- `src/static/js/audience-filter.js` — localStorage + DOM 필터, 빈 섹션 숨김, empty state
- `tests/test_audience.py` — 40개 단위 테스트 (Enum, 직렬화, static_generator 헬퍼)
- `docs/sessions/2026-04-11-phase-7-audience-filter.md` — 이 파일

### Modified
- `src/models.py` — `Audience` Enum + `Article.audience: list[Audience]` 필드 + 관대한 파싱 + legacy-safe 역직렬화 + 중복 제거
- `src/static_generator.py` — `SOURCE_AUDIENCE` 매핑, `get_article_audience`, `get_audience_data_attr`, `get_audience_labels`, `count_audience` 헬퍼 + Jinja 필터 2종 등록 + `_generate_category_pages` / `_generate_source_pages`가 audience 카운트를 템플릿에 전달
- `src/static/templates/base.html` — `audience-filter.js` script 로드
- `src/static/templates/index.html` — 히어로 아래 필터 include
- `src/static/templates/report.html` — report-header 아래 필터 + article-card에 `data-audience` 속성 + audience-tag 배지
- `src/static/templates/category.html` — category-header 아래 필터 + `data-audience` + audience-tag
- `src/static/templates/source.html` — source-header 아래 필터 + `data-audience` + audience-tag
- `src/static/templates/categories_index.html` — 필터 + `category_entries` 스키마로 재작성 + `audience-mini` 미니 통계
- `src/static/templates/sources_index.html` — 필터 + `source_entries` 스키마로 재작성 + `audience-mini` 미니 통계
- `src/static/templates/search.html` — search-header 아래 필터 include
- `src/static/css/style.css` — `.audience-filter`, `.audience-chip`, `.audience-chip.active`, `.audience-empty-state`, `.audience-tag`, `.audience-mini`, `.aud-mini` (general/developer/ml-expert) 스타일
- `.github/workflows/daily-report.yml` — Stage 2 프롬프트에 audience 태깅 지시 + 판단 기준 + Python 예시 업데이트
- `docs/development-plan.md` — Phase 7 상태 전부 `[x]`, 상태 테이블·변경 이력 갱신
- `docs/requirements.md` — FR-036~040, NFR-016 추가, 변경 이력
- `docs/system-architecture.md` — Section 5.7 Audience 필터 신설, 변경 이력
- `CLAUDE.md` — Features에 독자 레벨 필터 bullet 추가
- `README.md` — 주요 기능에 독자 레벨 필터 bullet 추가

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| 3단계 스킴 유지 (일반인/개발자/ML 전문가) | 사용자가 명시적으로 이 스킴을 승인함. 더 세분화하면 분류 노이즈 증가 |
| Multi-tag 허용 | 현실 기사 상당수가 한 계층에 딱 맞지 않음. 예: "GPT-5 출시" = 3개 레벨 모두. Single-pick은 lossy |
| 하이브리드 태깅 (Claude + 소스 fallback) | Claude 판단의 정확도와 레거시 데이터 호환성의 균형. Phase 7 배포 즉시 구형 리포트도 필터 가능 |
| CSS custom property 방식의 accent | 이전 Phase 6의 `--cat-color` / `--src-color` 패턴과 일관성 유지 |
| 필터 바 위치 = 히어로 아래 | 사용자가 명시적으로 선택. Navbar보다 눈에 잘 띔, 페이지마다 컨텍스트 아래에 위치해 자연스러움 |
| `localStorage`로 선택 값 지속 | 페이지 이동 시 필터 재설정 UX 마찰 제거. private mode fallback으로 세션 내 동작 |
| Client-side 필터 (JS) | 정적 사이트 구조 유지. JS 실패 시 모든 기사 노출 (graceful degradation) |
| 카드 미니 통계 포함 (Phase 7.4) | 사용자가 명시적으로 포함 요청. 각 카테고리/소스의 audience 분포를 한눈에 볼 수 있어 드릴다운 판단에 도움 |
| `static_generator.category_entries` / `source_entries` 스키마 변경 | Tuple → Dict로 확장해 audience_counts 포함. 기존 `category_counts` / `source_counts` 변수명 버림 |
| article-meta에 audience-tag 배지 노출 | 사용자가 필터 없이도 각 기사의 타깃 레벨을 즉시 볼 수 있음 |

## Code Review Results

자체 점검 (automated code-review 스킬 미실행, 인라인 리뷰):

| Category | Status | Notes |
|----------|--------|-------|
| Error Handling | ✅ | `Audience.from_string`이 None/empty 입력도 안전 처리. `get_article_audience`는 항상 non-empty 리스트 반환 |
| Resource Management | ✅ | 새 파일 시스템·네트워크 리소스 없음 |
| Security | ✅ | localStorage만 사용, 민감 정보 저장 없음. `data-audience`는 static HTML에 노출되는 enum name 뿐 |
| Type Hints | ✅ | 새 함수 전부 타입 힌트 (`list[Audience]`, `dict[str, int]` 등) |
| Tests | ✅ | 40개 신규 단위 테스트 추가, 205개 전체 suite 통과 (regression 없음) |
| Graceful Degradation | ✅ | JS 실패 시 기사 전부 노출. 레거시 리포트는 source fallback |
| Backward Compatibility | ✅ | `Article.audience`는 Phase 7 이전 JSON에서 빈 리스트로 복원. `from_dict`가 audience 필드 누락/None 모두 처리 |

### Minor observations (부채 아님)

- `audience-filter.js`에서 `Node.scope:` 셀렉터(`:scope > ...`)는 IE 미지원인데 프로젝트가 모던 브라우저만 타깃이라 OK.
- `search.js`에는 audience 필터와의 통합이 없음 — 검색 결과가 JS로 동적 생성되므로 기존 카드 필터 로직이 자동으로 적용 안 됨. 검색 결과는 현재 search-index.json에 audience 정보가 없어 검색 페이지에서는 필터가 동작하지 않음. **미래 개선 여지** — 별도 후속 이슈로 기록은 안 함 (사용자 요청 없음).

## Potential Risks

1. **Claude 판단 일관성**: 같은 기사가 날마다 다르게 태깅될 수 있음. 완벽한 일관성보다 대략적 분류가 목표라 수용 가능. 프롬프트에 명확한 기준을 넣었으므로 편차 제한적일 것.
2. **Yellow category 대비 이슈**: `.aud-mini.general` (청록), `.developer` (파랑), `.ml-expert` (보라) 3개 톤이라 FINANCE amber 같은 저대비 이슈 없음.
3. **레거시 리포트 824개의 태그**: 현재 2026-04-10 리포트 824 기사가 모두 source fallback으로 분류됨 (예: arxiv 680개는 모두 ML_EXPERT). 새 리포트가 누적되면서 이 왜곡은 자연 희석됨 (DEBT-005와 동일한 선상).
4. **검색 페이지 필터 미적용**: 위 코드 리뷰 참조.

## TECH-DEBT Items

**신규 항목 없음.** 구현 중 발견된 이슈가 있었지만:
- 검색 페이지 필터 통합은 사용자 요청에 포함되지 않았고, 별도 기능 확장에 해당
- 다른 모든 항목은 구현 내에서 해결됨

기존 DEBT-001~005와 독립적. Phase 7 관련 추가 없음.

## Verification

```bash
# 단위 테스트
$ python -m pytest tests/test_audience.py -q
........................................                                 [100%]
40 passed in 0.10s

# 전체 suite (regression 체크)
$ python -m pytest tests/ -q --ignore=tests/test_web.py
..............(생략)............ 205 passed in 1.43s

# 정적 사이트 빌드
$ SITE_BASE_URL=/ai-trend-report python -m src.main --generate-static --static-output /tmp/_site_aud
Static site generated: /tmp/_site_aud

# HTML 검증
$ grep -c "audience-filter" /tmp/_site_aud/{index,search}.html /tmp/_site_aud/reports/2026-04-10.html /tmp/_site_aud/{categories,sources}/index.html /tmp/_site_aud/categories/LLM.html /tmp/_site_aud/sources/ARXIV.html
(모든 파일 = 3)  ← label + chips div + chips items

$ grep -c "data-audience=" /tmp/_site_aud/reports/2026-04-10.html /tmp/_site_aud/categories/LLM.html /tmp/_site_aud/sources/ARXIV.html
(report 828, LLM 361, ARXIV 684)  ← legacy fallback으로 모든 카드 태깅됨

$ grep -E "audience-mini|aud-mini" /tmp/_site_aud/categories/index.html | head
(aud-mini general/developer/ml-expert 배지 정상 렌더)
```

## Test Coverage (Phase 7)

```
TestAudienceEnum                          2 tests
TestAudienceFromString                   21 tests (parametrized)
TestArticleAudience                       5 tests
TestArticleAudienceSerialization          4 tests
TestStaticGeneratorAudienceHelpers        7 tests
—
Total                                    40 tests (all passing)
```

## Next Phase Preview

Phase 7이 완료됨. Phase 8 후보 (아직 기획 안 됨):
- 레거시 리포트 재태깅 (DEBT-005 해소 병행)
- 검색 페이지의 audience 필터 통합
- 독자 레벨별 알림 분기 (예: 일반인만 받는 Slack 채널)
- 레벨별 개별 RSS 피드 생성
