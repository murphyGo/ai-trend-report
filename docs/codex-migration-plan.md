# Codex Actions migration

User authorization: migrate this project's scheduled Claude usage to Codex.
Related requirements: FR-004/016/027/028/029/036/037, existing recency/dedup,
notifications and Pages contracts. Historical local/API entry points remain
available; scheduled generation has no automatic paid API fallback.

- [x] Implement tool-free rank/summarize with strict source-ID validation.
- [x] Install reviewed application code separately from current public data.
- [ ] Use the existing private `investo-runtime` Environment and shared
  `investo-codex-auth-v1` concurrency group; persist refreshed auth before
  publication. Never copy the same refresh stream to another repository.
- [ ] Reuse existing notification Secrets by encrypted transfer, with
  `AI_REPORT_` names; verify a publisher PAT scoped to this public repository.
- [ ] Qualify a real Codex dry-run without notifications or public writes.
- [ ] Stop/drain the old public daily workflow, then enable only the private
  daily owner at the existing 09:00 KST schedule.
- [ ] Verify publishing, Pages and existing notification wiring; document
  exact revisions, results and rollback, preserving unrelated local changes.

Model/policy: same qualified `gpt-6-astra` / native CLI 0.153.4 as Investo.
The model receives article data over stdin and returns JSON only. Trusted code
maps selected IDs back to original articles and owns every file/network effect.
No shell/read/write tools are exposed to the model. Invalid or failed model
output stops before publication. Auth cleanup/persistence also runs on failure.

Rollback: disable the private AI Report gate, wait for its active runs to end,
inspect report/email history, and only then re-enable the public daily workflow.
Do not alter Investo's independent activation gate or running production job.

## Local validation (2026-10-05 KST)

311 tests pass. The unchanged baseline reproduced six FastAPI web failures with
current allowed dependencies; three TemplateResponse calls now use explicit
request/name/context arguments as documented by FastAPI, restoring all six.
Changed Python files pass flake8. Existing whole-repository lint findings
(unused imports/formatting outside this scope) remain pre-existing debt.

The private runtime has 12 regression tests covering rotating-auth success,
model failure, checkpoint failure and cancellation; fixed-destination Git
credentials; shared concurrency; and dry-run notification isolation. Fresh
review found one missing failure alert, which was restored.

Official compatibility reference: https://fastapi.tiangolo.com/advanced/templates/
