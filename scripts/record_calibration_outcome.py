#!/usr/bin/env python3
"""Record one resolved run into a predictor's calibration store and recompute.

This is the decoupled calibrate step. OPE deliberately keeps resolution a pure
scoring write (``appendsCorpusEvidence`` stays false in the resolution runtime);
this separate, explicit step reads a *terminal* run state, appends its outcome
to the per-predictor calibration store, and recomputes the track-record /
calibration gate. Running it after every resolution — e.g. from the ticker — is
what makes calibration advance automatically per run.

Idempotent: re-recording the same resolved run is a no-op (dedup on rowKey).
A run that is not yet scored/ambiguous is left untouched (it reports a noop).

Usage:
    python3 scripts/record_calibration_outcome.py --run-state PATH [--run-source single|campaign]
    python3 scripts/record_calibration_outcome.py --gate --domain weather-transit-delays
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import calibration_store as cs


TERMINAL_STATUSES = {"resolved", "scored", "ambiguous"}


def now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def record_run_state(
    *,
    run_state_path: Path,
    run_source: str,
    store_path: Path | None,
    generated_at: str,
) -> dict:
    state = json.loads(run_state_path.read_text(encoding="utf-8"))
    run_status = state.get("runStatus", "")
    if run_status not in TERMINAL_STATUSES:
        return {
            "status": "noop_not_terminal",
            "runStatus": run_status or "unknown",
            "runStatePath": str(run_state_path),
        }
    horizon_bucket = state.get("forecastStage", {}).get("serviceWindow", "rolling-24h")
    row = cs.row_from_forward_run_state(state, run_source=run_source)
    result = cs.append_resolved_run(
        domain=state["domain"],
        row=row,
        store_path=store_path,
        horizon_bucket=horizon_bucket,
        generated_at=generated_at,
    )
    result["status"] = "recorded" if result["appended"] else "already_present"
    result["runStatus"] = run_status
    result["rowKind"] = row["rowKind"]
    return result


def record_campaign_ledger(*, ledger_path: Path, domain: str, store_path: Path | None, generated_at: str) -> dict:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    rows = cs.rows_from_campaign_ledger(ledger, domain)
    path = store_path or cs.store_path_for(domain)
    store = cs.load_store(path, domain)
    appended, already = cs.append_rows(store, rows)
    cs.save_store(path, store)
    gate = cs.recompute_gate(store, generated_at=generated_at)
    return {
        "status": "recorded" if appended else "already_present",
        "storePath": str(path),
        "ledgerPath": str(ledger_path),
        "appended": appended,
        "alreadyPresent": already,
        "gate": gate,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-state", help="path to a terminal forward-run-state.json")
    parser.add_argument("--campaign-ledger", help="path to a campaign evidence-ledger.json to project into the store")
    parser.add_argument("--run-source", choices=sorted(cs.RUN_SOURCES), default="single")
    parser.add_argument("--domain", help="predictor domain (for --gate, --campaign-ledger, or to override store location)")
    parser.add_argument("--store-path", help="override the calibration store path")
    parser.add_argument("--gate", action="store_true", help="just print the current recomputed gate for --domain")
    parser.add_argument("--now", default=None, help="UTC timestamp to stamp the recompute (default: now)")
    args = parser.parse_args(argv)

    generated_at = args.now or now_iso()
    store_path = Path(args.store_path) if args.store_path else None

    try:
        if args.gate:
            if not args.domain:
                parser.error("--gate requires --domain")
            path = store_path or cs.store_path_for(args.domain)
            gate = cs.recompute_gate(cs.load_store(path, args.domain), generated_at=generated_at)
            sys.stdout.write(json.dumps(gate, indent=2) + "\n")
            return 0
        if args.campaign_ledger:
            if not args.domain:
                parser.error("--campaign-ledger requires --domain")
            result = record_campaign_ledger(
                ledger_path=Path(args.campaign_ledger),
                domain=args.domain,
                store_path=store_path,
                generated_at=generated_at,
            )
            sys.stdout.write(json.dumps(result, indent=2) + "\n")
            return 0
        if not args.run_state:
            parser.error("--run-state, --campaign-ledger, or --gate is required")
        result = record_run_state(
            run_state_path=Path(args.run_state),
            run_source=args.run_source,
            store_path=store_path,
            generated_at=generated_at,
        )
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
        return 0
    except (OSError, json.JSONDecodeError, cs.CalibrationStoreError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
