# Local Live Capture Workspace

Status: implemented as an ignored developer workspace for explicit Open-Meteo integration checks.

The local live capture workspace lets a developer intentionally save one sanitized live connector result under `.ope/live/` without turning it into committed forecast evidence. The saved file validates against the same `source-connector-result-set.schema.json` boundary used by public connector results, but it is ignored by git and excluded from normal checks, public read indexes, track records, calibration, and release claims.

## Commands

Run and save an explicit live connector check:

```bash
python3 scripts/ope.py live-readiness --live --save-local --service-date YYYY-MM-DD
```

Validate a saved local capture:

```bash
python3 scripts/ope.py live-capture --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json --check
```

Convert a successful saved connector result into a local evidence source-set draft:

```bash
python3 scripts/ope.py live-capture \
  --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json \
  --draft-source-set \
  --write
```

The draft is also written under `.ope/live/` by default. It validates against `evidence-source-set.schema.json` with `executionMode: live_fetch`, but remains a draft until an explicit promotion or forecast command consumes and binds it. The checked transit promotion boundary is documented in `spec/transit-live-evidence-promotion.md`.

## Guardrails

- `.ope/live/` is git ignored.
- `--save-local` requires the explicit `--live` flag.
- Saved captures keep `networkAccess: true` and `liveFetch: true` so agents cannot confuse them with committed fixtures.
- Saved captures store no raw previews, raw diagnostics, raw stack traces, or prompt-visible credentials.
- Failed live captures may be saved as sanitized connector results, but cannot become evidence source-set drafts.
- Local drafts do not create forecast artifacts, evidence traces, forecast histories, resolutions, scoring reports, track records, or calibration summaries.
- Local drafts are not included in `python3 scripts/run_checks.py`, `python3 scripts/release_check.py`, or the public record index.

## Agent Use

An agent may inspect a local live capture only when the developer intentionally created it and provided access to `.ope/live/`. The agent should treat it as a development draft, not as committed forecast evidence. If the agent needs a forecast, it must use a future forecast command that explicitly accepts local live drafts and preserves the normal request, source-policy, evidence, forecast, resolution, and scoring bindings.
