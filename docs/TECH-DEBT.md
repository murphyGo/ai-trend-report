# Technical Debt Tracker

AI Report Service의 기술 부채를 추적하고 관리합니다.

---

## Summary

| Priority | Count | Oldest |
|----------|-------|--------|
| Critical | 0 | - |
| High | 0 | - |
| Medium | 0 | - |
| Low | 0 | - |

**Total Active Items**: 0

---

## Active Items

### Critical Priority

_No critical items._

### High Priority

_No high priority items._

### Medium Priority

_No medium priority items._

### Low Priority

_No low priority items._

---

## Resolved Items

_No resolved items._

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
