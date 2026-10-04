# Codex Actions migration — 2026-10-05 KST

The operator requested the same Claude-to-Codex migration already completed
for Investo. Work preserves unrelated local `.claude/settings.local.json`.

## Implemented and verified

- Public application `53037fc20e34a685f357c74c783e5dd4a39e47e4` adds a
  tool-free rank/summarize adapter. Validated source IDs retain original URLs,
  titles, content and timestamps; the model returns only summaries/categories/
  audience tags. No model-generated code or filesystem operations execute.
- The application is packaged and installed from a reviewed SHA. Current
  public report data is a separate checkout, never an executable source path.
- Private runtime integration `941658f5e0d4d57d12cc7fe99067cb5d05c8057a` adds
  `ai-report.yml`, auth supervisor and destination-only publisher credentials.
  The qualified Investo runner/policy is pinned independently to `056dd8a1...`.
- Same `codex-runtime` Environment and `investo-codex-auth-v1` concurrency group
  reuse the existing managed authentication stream. Auth is checkpointed before
  any publication, preserved on failures/cancellation, then removed locally.
- Private `822cc06` adds `queue: max` to all four workflows sharing that auth
  stream. This prevents pending work from replacing another pending workflow.
  An independently added event-preview workflow was preserved during rebase.
- Local full suite **311 tests passed**. Remote CI
  [37213491855](https://github.com/murphyGo/ai-trend-report/actions/runs/37213491855)
  passed tests on Python 3.9, 3.10, 3.11 and 3.12. Its lint failure is the
  pre-existing repository-wide lint baseline, tracked as DEBT-006; changed
  Python files pass flake8.
- Current allowed FastAPI/Starlette dependencies exposed six failures also
  reproduced on untouched main. Three template calls now use explicit
  request/name/context arguments, restoring all six existing tests.
- Private regression suite **12 tests passed**, including actual synthetic
  child-process shutdown, rotating-auth success/failure/cancellation, failed
  auth checkpoint before output, and fixed-destination credential behavior.
  Independent review passed after restoring the existing Slack failure alert.

## Existing notification settings reused

The three existing public EMAIL Secrets were sealed with the private
Environment's public key. One-use run
[37214096383](https://github.com/murphyGo/ai-trend-report/actions/runs/37214096383)
at `0f9306a6ff6637dcb3dbc82fa098a858e28a0a17` succeeded. The reviewed consumer
validated source run/SHA/ref/artifact/destination/key and rejected collisions,
then registered `AI_REPORT_EMAIL_USERNAME`, `AI_REPORT_EMAIL_PASSWORD` and
`AI_REPORT_EMAIL_RECIPIENTS`. Metadata confirmed 2026-10-04 15:44:52–53 UTC.
The ciphertext artifact and one-use remote branch were deleted. No raw values,
hashes or account credentials were logged or copied to local files.

An initial transfer attempt failed because isolated Python could not import a
user-site dependency; an explicit temporary venv fixed it before any transfer.
Consumer review covered 14 synthetic branches including optimized Python,
registration failure cleanup, existing-secret collision and invalid payloads.

## Activation prerequisites and current ownership

`AI_REPORT_REVIEWED_CODE_SHA=53037fc...` is registered. Real full dry-run
[37213542160](https://github.com/murphyGo/investo-runtime/actions/runs/37213542160)
**succeeded**, after waiting for the existing event preview in the shared queue.
It collected 157 articles, retained 32 after recency and 8 after dedup, then
Codex selected/summarized 4 articles. Receipt: `codex` / `gpt-6-astra`,
`auth=unchanged`, exit 0, native call 36.708s, supervisor 37.076s, whole job
1m23s (2026-10-04 15:45:04–15:46:27 UTC). Publication, normal notifications and
failure notifications were all skipped. No public report or email was changed.

Publisher preflight
[37213540046](https://github.com/murphyGo/investo-runtime/actions/runs/37213540046)
proved the existing Investo PAT cannot write this repository (Git HTTP 403).
The operator was asked to register `AI_REPORT_PUBLISH_TOKEN` in the private
`codex-runtime` Environment: fine-grained PAT selecting only
`murphyGo/ai-trend-report`, Contents and Actions read/write. The workflow can
also reuse the existing publisher PAT if the operator adds that repository.
Neither personal GitHub CLI auth nor managed Codex auth is used for publishing.

Until that capability and actual generation are verified, the public
`daily-report.yml` remains the active 09:00 KST owner and
`AI_REPORT_CODEX_ENABLED` remains unset. The new private dry-run cannot publish
or notify. Do not claim the operational switch has completed from code alone.

After prerequisites pass: disable/drain the public daily workflow, set
`AI_REPORT_CODEX_ENABLED=1`, and verify actual report commit, Pages and
notification outcomes separately. Rollback disables/drains the private owner
before restoring public Claude; inspect date/email history before replaying.

## References

- [FastAPI template arguments](https://fastapi.tiangolo.com/advanced/templates/)
- [GitHub concurrency queue](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency)
- actionlint 1.7.12 predates the `queue` schema. Only its specific unknown
  `queue` key diagnostic was excluded; other workflow validation remains on.
