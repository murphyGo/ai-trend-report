# Codex production activation — 2026-10-09 KST

The operator registered `AI_REPORT_PUBLISH_TOKEN` in the private
`murphyGo/investo-runtime` Environment `codex-runtime`; Secret metadata shows
2026-10-09 09:19:37 UTC. Only its name and metadata were inspected.

## Ownership and publisher verification

- Publisher preflight
  [37910592891](https://github.com/murphyGo/investo-runtime/actions/runs/37910592891)
  passed the destination-scoped Git handshake and Pages dispatch. The resulting
  [Pages run 37910613883](https://github.com/murphyGo/ai-trend-report/actions/runs/37910613883)
  succeeded against the existing public revision `02dfae6bcf65454fe336c1415fcf06b79f94fdbe`.
- The old public `daily-report.yml` was disabled (`disabled_manually`), with
  all previous daily runs completed, before the private gate was enabled.
- `AI_REPORT_CODEX_ENABLED=1` activates the private `ai-report.yml` at its
  existing daily 00:00 UTC / 09:00 KST schedule. GitHub can delay actual starts.
- Application pin remains `53037fc20e34a685f357c74c783e5dd4a39e47e4`;
  qualified Investo runner pin remains `056dd8a1b4a8e599f44519e54b5bf4f486275dbd`.
  No executable application changes followed the prior qualification.
- Investo's separate gate, event-preview workflow and shared authentication
  settings were preserved. The repository name remains `investo-runtime`.

## Actual generation, publication and notification

Manual production run
[37910674025](https://github.com/murphyGo/investo-runtime/actions/runs/37910674025)
at private revision `ce772cf53e734c267c5e08a30354b543be84661f` **succeeded** with
`dry_run=false`, `limit=0`. Job: 09:20:54–09:23:54 UTC (18:20:54–18:23:54 KST),
3 minutes.

- Collected 217 articles; recency retained 118, including 9 undated articles
  under the existing fallback rule; dedup removed 4, leaving 114 candidates.
- Codex `gpt-6-astra` selected and summarized **20 articles**. Native call
  127.360s; supervisor 127.649s; `auth=unchanged`, exit 0.
- Auth checkpoint, publication and notification steps all succeeded.
- Actual public commit
  [`44c11d75adb241deefe42e7084abe6a22e09be0b`](https://github.com/murphyGo/ai-trend-report/commit/44c11d75adb241deefe42e7084abe6a22e09be0b)
  changed only `data/report_2026-10-09.json`. Its 20 unique article IDs all have
  source URLs, summaries and audience tags.
- Existing SMTP settings sent the report to **2 recipients**. The application
  logged successful sending; this verifies SMTP submission, not inbox delivery.
  No manual test email or duplicate production replay was sent.
- [Pages run 37910995388](https://github.com/murphyGo/ai-trend-report/actions/runs/37910995388)
  **succeeded at that exact report commit**. The
  [published report](https://murphygo.github.io/ai-trend-report/reports/2026-10-09.html)
  was checked over HTTP.

## Validation and remaining debt

CI [37910995474](https://github.com/murphyGo/ai-trend-report/actions/runs/37910995474)
passed the Python 3.9, 3.10, 3.11 and 3.12 test jobs. Its lint job still fails
on the previously recorded baseline (DEBT-006). This is not an all-green CI
claim. The earlier local 311 tests and private 12 regression tests remain the
implementation qualification evidence. This activation changes operational
settings and documentation only; no additional local application tests were
needed. Documentation was checked with `git diff --check`.

## Rollback and scope

Disable `AI_REPORT_CODEX_ENABLED`, drain active private report runs, and inspect
the date's public commit and email history before re-enabling public
`daily-report.yml`. Never keep both schedule owners enabled. A replay can send
another email even if its report date already exists.

The unrelated local `.claude/settings.local.json` was preserved through a
separate worktree. No Secret values were read, printed, committed or copied to
chat. Crypto-master's Fly.io runtime and the shared repository rename are
outside this activation; no changes were made to either.
