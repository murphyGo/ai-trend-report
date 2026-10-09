# Shared runtime rename — 2026-10-09

The existing private repository is now `murphyGo/automation-runtime`. Its ID,
`codex-runtime` Environment and Secrets are unchanged. Current instructions
and requirements now use the new name; earlier session evidence is historical.

The report app pin remains `53037fc20e34a685f357c74c783e5dd4a39e47e4`; the
qualified Investo transport pin is `ca0ef610cdaafea7de188551f06d2107247e8472`,
a name-only source backport. Production report behavior is unchanged.

[Dry-run 37914423059](https://github.com/murphyGo/automation-runtime/actions/runs/37914423059)
succeeded under the new name, generating 20 articles with `gpt-6-astra`, exit 0
and unchanged auth. Publication and email steps were skipped. Production gate
`AI_REPORT_CODEX_ENABLED=1` and the private schedule were restored afterward;
public `daily-report.yml` remains disabled.
