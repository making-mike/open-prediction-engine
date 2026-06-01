#!/usr/bin/env python3
"""Generate, check, or execute guarded campaign method-update actions."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

from generate_prediction_campaign_method_update_gate import build_prediction_campaign_method_update_gate
from generate_prediction_campaign_method_update_plan import (
    DEFAULT_CASE as DEFAULT_PLAN_CASE,
    METHOD_UPDATE_PLAN_CASES,
    build_prediction_campaign_method_update_plan,
    gate_case_for,
)
from generate_transit_method_options import BASELINE_METHOD_ID, WEATHER_ADJUSTMENT_METHOD_ID
from ope_fixtures import compact_json, render_json, validate_and_emit
from ope_schema import SPEC, validate_record
from prediction_campaign_forecast_write_runtime import ensure_safe_local_path, read_json


ROOT = Path(__file__).resolve().parents[1]
LOCAL_WORKSPACE_ROOT = ROOT
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-method-update-action"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-method-update-action.generated.json"
SCHEMA = SPEC / "prediction-campaign-method-update-action.schema.json"
GENERATED_AT = "2026-05-31T05:00:00Z"
OPERATIONS = ["apply", "rollback"]
MINIMUM_COMPARABLE_FOR_UPDATE = 100


class PredictionCampaignMethodUpdateError(Exception):
    pass


def now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def content_hash(data: dict[str, Any]) -> str:
    return hashlib.sha256(render_json(data).encode("utf-8")).hexdigest()


def method_update_paths(plan: dict[str, Any]) -> dict[str, str]:
    campaign_id = plan["bindings"]["campaignId"]
    root = f".ope/live/prediction-campaigns/{campaign_id}"
    return {
        "campaignStatePath": f"{root}/campaign-manifest.json",
        "methodUpdateDirectory": f"{root}/method-updates",
        "methodUpdateArtifactPath": f"{root}/method-updates/predictioncampaignmethodupdateaction-001.json",
        "methodBindingPath": f"{root}/method-binding.json",
        "rollbackArtifactPath": f"{root}/method-updates/predictioncampaignmethodupdaterollback-001.json",
    }


def action_status_for(operation: str, plan: dict[str, Any], method_update_plan_id: str) -> str:
    if method_update_plan_id != plan["predictionCampaignMethodUpdatePlanId"]:
        return "blocked_plan_id_mismatch"
    status = plan["planStatus"]
    if status == "blocked_by_method_update_gate":
        return "blocked_by_method_update_plan"
    if status == "blocked_regression_risk":
        return "blocked_candidate_regression_risk"
    if status == "blocked_missing_approval_artifact":
        return "blocked_missing_approval_artifact"
    if status == "blocked_missing_rollback_record":
        return "blocked_missing_rollback_record"
    if operation == "rollback":
        return "ready_for_explicit_local_rollback"
    return "ready_for_explicit_local_apply"


def preflight_check(
    index: int,
    *,
    status: str,
    required: bool,
    blocks: bool,
    message: str,
) -> dict[str, Any]:
    return {
        "checkId": f"methodupdateactioncheck-{index:03d}",
        "checkStatus": status,
        "requiredBeforeWrite": required,
        "blocksWrite": blocks,
        "message": message,
    }


def build_preflight_checks(
    *,
    operation: str,
    plan: dict[str, Any],
    gate: dict[str, Any],
    action_status: str,
) -> list[dict[str, Any]]:
    plan_ready = plan["decision"]["methodUpdatePlanReady"]
    approval_ready = plan["approvalArtifact"]["approvalStatus"] == "approved"
    rollback_ready = plan["rollbackRecord"]["rollbackStatus"] == "present"
    evidence_favorable = (
        gate["evidenceReadback"]["candidateBaselineLift"] > 0
        and gate["evidenceReadback"]["cleanAntiLeakageEvidence"]
        and gate["evidenceReadback"]["comparableEvidenceReady"]
    )
    plan_id_ok = action_status != "blocked_plan_id_mismatch"
    target_ok = plan["bindings"]["candidateMethodId"] == WEATHER_ADJUSTMENT_METHOD_ID
    return [
        preflight_check(
            1,
            status="pass" if plan_id_ok else "block",
            required=True,
            blocks=not plan_id_ok,
            message="The requested method-update plan id must match the checked plan readback.",
        ),
        preflight_check(
            2,
            status="pass" if plan_ready else "block",
            required=True,
            blocks=not plan_ready,
            message="The method-update plan must be plan-ready before any local method binding can change.",
        ),
        preflight_check(
            3,
            status="pass" if approval_ready else "block",
            required=True,
            blocks=not approval_ready,
            message="Method-owner, calibration-review, and source-policy approvals must be present.",
        ),
        preflight_check(
            4,
            status="pass" if rollback_ready else "block",
            required=True,
            blocks=not rollback_ready,
            message="A rollback record must be present before apply or rollback commands are eligible.",
        ),
        preflight_check(
            5,
            status="pass" if evidence_favorable else "block",
            required=True,
            blocks=not evidence_favorable,
            message="Candidate benchmark lift, comparable calibration evidence, and anti-leakage evidence must remain favorable.",
        ),
        preflight_check(
            6,
            status="pass" if target_ok else "block",
            required=True,
            blocks=not target_ok,
            message="The first non-baseline candidate is limited to the transparent weather-adjustment method.",
        ),
        preflight_check(
            7,
            status="pass",
            required=True,
            blocks=False,
            message="Method changes are prospective-only and never rewrite prior forecast histories or probabilities.",
        ),
        preflight_check(
            8,
            status="pass" if operation == "apply" else "warn",
            required=operation == "rollback",
            blocks=False,
            message="Rollback restores the prior baseline method binding without deleting the original apply artifact.",
        ),
    ]


def candidate_evidence(gate: dict[str, Any]) -> dict[str, Any]:
    evidence = gate["evidenceReadback"]
    return {
        "candidateBenchmarkStatus": evidence["candidateBenchmarkStatus"],
        "candidateBaselineLift": evidence["candidateBaselineLift"],
        "cleanAntiLeakageEvidence": evidence["cleanAntiLeakageEvidence"],
        "comparableEvidenceReady": evidence["comparableEvidenceReady"],
        "approvalStatus": evidence["approvalStatus"],
        "evidenceSupportsCandidate": (
            evidence["candidateBaselineLift"] > 0
            and evidence["cleanAntiLeakageEvidence"]
            and evidence["comparableEvidenceReady"]
        ),
    }


def write_result_empty() -> dict[str, Any]:
    return {
        "writeStatus": "not_run",
        "artifactWrites": [],
        "stateWrites": [],
        "newFileWriteCount": 0,
        "alreadyPresentCount": 0,
        "sanitizedDiagnostics": "Dry-run readback only; add --write-local after the plan is ready to mutate ignored local state.",
    }


def build_prediction_campaign_method_update_action(
    *,
    operation: str = "apply",
    method_update_plan_case: str = DEFAULT_PLAN_CASE,
    method_update_plan_id: str | None = None,
    write_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if operation not in OPERATIONS:
        raise ValueError(f"unknown method-update operation: {operation}")
    if method_update_plan_case not in METHOD_UPDATE_PLAN_CASES:
        raise ValueError(f"unknown method update plan case: {method_update_plan_case}")
    plan = build_prediction_campaign_method_update_plan(method_update_plan_case=method_update_plan_case)
    gate = build_prediction_campaign_method_update_gate(method_update_case=gate_case_for(method_update_plan_case))
    requested_plan_id = method_update_plan_id or plan["predictionCampaignMethodUpdatePlanId"]
    action_status = action_status_for(operation, plan, requested_plan_id)
    result = write_result or write_result_empty()
    if result["writeStatus"] != "not_run":
        action_status = result["writeStatus"]
    paths = method_update_paths(plan)
    local_write_eligible = action_status in {
        "ready_for_explicit_local_apply",
        "ready_for_explicit_local_rollback",
        "local_apply_completed",
        "local_apply_already_present",
        "local_rollback_completed",
        "local_rollback_already_present",
    }
    target_method_id = (
        plan["bindings"]["currentMethodId"] if operation == "rollback" else plan["bindings"]["candidateMethodId"]
    )
    return {
        "predictionCampaignMethodUpdateActionId": "predictioncampaignmethodupdateaction-001",
        "generatedAt": result.get("writtenAt", GENERATED_AT),
        "operation": operation,
        "actionStatus": action_status,
        "domain": plan["domain"],
        "bindings": {
            "predictionCampaignMethodUpdatePlanId": plan["predictionCampaignMethodUpdatePlanId"],
            "predictionCampaignMethodUpdateGateId": plan["bindings"]["predictionCampaignMethodUpdateGateId"],
            "campaignId": plan["bindings"]["campaignId"],
            "cycleId": plan["bindings"]["cycleId"],
            "sourcePolicyId": plan["bindings"]["sourcePolicyId"],
            "currentMethodId": plan["bindings"]["currentMethodId"],
            "candidateMethodId": plan["bindings"]["candidateMethodId"],
            "requestedMethodUpdatePlanId": requested_plan_id,
        },
        "planReadback": {
            "planCase": plan["planCase"],
            "planStatus": plan["planStatus"],
            "gateStatus": gate["gateStatus"],
            "methodUpdatePlanReady": plan["decision"]["methodUpdatePlanReady"],
            "blockingReasons": plan["preflightChecks"]["blockingReasons"],
        },
        "approvalArtifact": plan["approvalArtifact"],
        "rollbackRecord": plan["rollbackRecord"],
        "candidateEvidence": candidate_evidence(gate),
        "methodBinding": {
            "currentMethodId": plan["bindings"]["currentMethodId"],
            "candidateMethodId": plan["bindings"]["candidateMethodId"],
            "targetMethodId": target_method_id,
            "methodBindingPath": paths["methodBindingPath"],
            "methodUpdateArtifactPath": paths["methodUpdateArtifactPath"],
            "rollbackArtifactPath": paths["rollbackArtifactPath"],
            "effectiveScope": "future_campaign_forecasts_only",
            "runnerCanUseAfterWrite": True,
            "normalChecksReadLocalBinding": False,
            "priorForecastHistoryRewriteAllowed": False,
            "priorForecastProbabilityRewriteAllowed": False,
        },
        "preflightChecks": build_preflight_checks(
            operation=operation,
            plan=plan,
            gate=gate,
            action_status=action_status,
        ),
        "writePlan": {
            "campaignStatePath": paths["campaignStatePath"],
            "methodUpdateDirectory": paths["methodUpdateDirectory"],
            "requiresWriteLocal": True,
            "writeLocalRequested": result["writeStatus"] != "not_run",
            "minimumComparableResolvedForApply": MINIMUM_COMPARABLE_FOR_UPDATE,
            "idempotent": True,
            "normalChecksWriteLocal": False,
            "preservesForecastHistory": True,
        },
        "writeResult": result,
        "decision": {
            "localWriteEligible": local_write_eligible,
            "effectfulUpdateAllowedNow": False,
            "automaticUpdateAllowed": False,
            "qualityClaimAllowed": False,
            "recommendedNextAction": recommended_next_action(operation, action_status),
        },
        "commandSurface": {
            "command": f"python3 scripts/ope.py prediction-campaign {operation}-method-update",
            "acceptedFlags": [
                "--method-update-plan-id",
                "--method-update-plan-case",
                "--write-local",
                "--output-format",
                "--view",
            ],
            "defaultMode": "checked_method_update_action_readback",
            "capturedStdoutMode": "json",
            "explicitWriteFlagRequired": True,
            "normalChecksMutateState": False,
        },
        "executionBoundary": {
            "readsIgnoredLiveState": result["writeStatus"] != "not_run",
            "writesIgnoredLiveState": result["writeStatus"] != "not_run",
            "writesCampaignState": result["writeStatus"] != "not_run",
            "fetchesLiveData": False,
            "executesResolvers": False,
            "createsForecastArtifacts": False,
            "updatesForecastProbabilities": False,
            "changesForecastMethod": result["writeStatus"] != "not_run",
            "changesMethodWeights": False,
            "writesMethodRegistry": False,
            "writesMethodBinding": result["writeStatus"] != "not_run",
            "rewritesPriorForecastHistories": False,
            "startsNextCycle": False,
            "normalChecksMutateState": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "Normal checks never apply or roll back a campaign method update.",
            "The baseline remains the default unless an approved local method binding is written explicitly.",
            "Apply and rollback preserve prior forecast histories and never rewrite old probabilities.",
        ],
    }


def recommended_next_action(operation: str, action_status: str) -> str:
    if action_status == "blocked_by_method_update_plan":
        return "Keep the baseline method until the method-update plan is ready."
    if action_status == "blocked_candidate_regression_risk":
        return "Keep the pilot on transitmethod-100 because candidate benchmark evidence is unfavorable."
    if action_status == "blocked_missing_approval_artifact":
        return "Collect method-owner, calibration-review, and source-policy approvals before applying a method update."
    if action_status == "blocked_missing_rollback_record":
        return "Create the rollback record before applying a method update."
    if action_status == "blocked_plan_id_mismatch":
        return "Use the method-update plan id from the checked plan readback."
    if action_status == "ready_for_explicit_local_apply":
        return "Run the same command with --write-local only after reviewing the local campaign state and approvals."
    if action_status == "ready_for_explicit_local_rollback":
        return "Run rollback with --write-local only after confirming the applied method binding should be restored."
    if action_status.startswith("local_apply"):
        return "Future campaign forecasts may read the local method binding; prior forecasts remain unchanged."
    if action_status.startswith("local_rollback"):
        return "Future campaign forecasts should use the restored baseline binding; prior forecasts remain unchanged."
    return f"Inspect the {operation} method-update action status."


def safe_path(path_value: str) -> Path:
    return ensure_safe_local_path(path_value, workspace_root=LOCAL_WORKSPACE_ROOT)


def require_campaign_state(path_value: str, campaign_id: str, *, require_threshold: bool) -> dict[str, Any]:
    path = safe_path(path_value)
    if not path.exists():
        raise PredictionCampaignMethodUpdateError(f"Local campaign state is missing: {path_value}")
    state = read_json(path)
    if state.get("campaignId") != campaign_id:
        raise PredictionCampaignMethodUpdateError(f"Local campaign state campaignId mismatch: {path_value}")
    comparable = int(state.get("resolvedComparableOutcomes", 0))
    if require_threshold and comparable < MINIMUM_COMPARABLE_FOR_UPDATE:
        raise PredictionCampaignMethodUpdateError(
            f"Method update requires at least {MINIMUM_COMPARABLE_FOR_UPDATE} resolved comparable outcomes"
        )
    return state


def write_audit_artifact(path_value: str, artifact: dict[str, Any]) -> dict[str, Any]:
    path = safe_path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = read_json(path)
        if (
            existing.get("operation") != artifact["operation"]
            or existing.get("campaignId") != artifact["campaignId"]
            or existing.get("targetMethodId") != artifact["targetMethodId"]
        ):
            raise PredictionCampaignMethodUpdateError(f"Refusing to overwrite different method-update artifact: {path_value}")
        return {
            "recordType": "method_update_audit",
            "targetPath": path_value,
            "writeStatus": "already_present",
            "contentHash": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    path.write_text(render_json(artifact), encoding="utf-8")
    return {
        "recordType": "method_update_audit",
        "targetPath": path_value,
        "writeStatus": "written",
        "contentHash": content_hash(artifact),
    }


def write_method_binding(
    *,
    path_value: str,
    binding: dict[str, Any],
    operation: str,
    current_method_id: str,
    candidate_method_id: str,
) -> dict[str, Any]:
    path = safe_path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    if operation == "rollback" and not existed:
        raise PredictionCampaignMethodUpdateError("Rollback requires an existing applied method binding")
    if path.exists():
        existing = read_json(path)
        active = existing.get("activeMethodId")
        if operation == "apply":
            if active == candidate_method_id:
                return {"stateType": "prediction_campaign_method_binding", "targetPath": path_value, "writeStatus": "already_present"}
            if active != current_method_id:
                raise PredictionCampaignMethodUpdateError(f"Refusing to replace unexpected active method binding: {active}")
        elif active == current_method_id:
            return {"stateType": "prediction_campaign_method_binding", "targetPath": path_value, "writeStatus": "already_present"}
        elif active != candidate_method_id:
            raise PredictionCampaignMethodUpdateError(f"Refusing to roll back unexpected active method binding: {active}")
    path.write_text(render_json(binding), encoding="utf-8")
    return {
        "stateType": "prediction_campaign_method_binding",
        "targetPath": path_value,
        "writeStatus": "updated" if existed else "written",
    }


def update_campaign_state(
    *,
    path_value: str,
    state: dict[str, Any],
    operation: str,
    written_at: str,
    method_binding_path: str,
    artifact_path: str,
    current_method_id: str,
    candidate_method_id: str,
) -> dict[str, Any]:
    path = safe_path(path_value)
    updated = dict(state)
    update_paths = list(updated.get("methodUpdateArtifactPaths", []))
    rollback_paths = list(updated.get("methodRollbackArtifactPaths", []))
    if operation == "apply":
        if (
            updated.get("activeMethodId") == candidate_method_id
            and updated.get("methodBindingPath") == method_binding_path
            and artifact_path in update_paths
        ):
            return {"stateType": "prediction_campaign_state", "targetPath": path_value, "writeStatus": "already_present"}
        if artifact_path not in update_paths:
            update_paths.append(artifact_path)
        active_method_id = candidate_method_id
        status = "applied_weather_adjustment"
    else:
        if (
            updated.get("activeMethodId") == current_method_id
            and updated.get("methodBindingPath") == method_binding_path
            and artifact_path in rollback_paths
        ):
            return {"stateType": "prediction_campaign_state", "targetPath": path_value, "writeStatus": "already_present"}
        if artifact_path not in rollback_paths:
            rollback_paths.append(artifact_path)
        active_method_id = current_method_id
        status = "rolled_back_to_baseline"
    updated.update(
        {
            "writtenAt": written_at,
            "activeMethodId": active_method_id,
            "methodBindingPath": method_binding_path,
            "methodUpdateStatus": status,
            "methodUpdateArtifactPaths": update_paths,
            "methodRollbackArtifactPaths": rollback_paths,
        }
    )
    boundary = dict(updated.get("executionBoundary", {}))
    boundary.update(
        {
            "changesForecastMethod": True,
            "rewritesPriorForecastHistories": False,
            "updatesForecastProbabilities": False,
            "writesMethodRegistry": False,
            "qualityClaimAllowed": False,
        }
    )
    updated["executionBoundary"] = boundary
    if path.read_text(encoding="utf-8") == render_json(updated):
        status_out = "already_present"
    else:
        path.write_text(render_json(updated), encoding="utf-8")
        status_out = "updated"
    return {"stateType": "prediction_campaign_state", "targetPath": path_value, "writeStatus": status_out}


def execute_local_method_update(action: dict[str, Any]) -> dict[str, Any]:
    blocking = [check for check in action["preflightChecks"] if check["blocksWrite"]]
    if blocking:
        ids = ", ".join(check["checkId"] for check in blocking)
        raise PredictionCampaignMethodUpdateError(f"Method update blocked by preflight checks: {ids}")
    operation = action["operation"]
    bindings = action["bindings"]
    paths = {
        "campaignStatePath": action["writePlan"]["campaignStatePath"],
        "methodUpdateArtifactPath": action["methodBinding"]["methodUpdateArtifactPath"],
        "methodBindingPath": action["methodBinding"]["methodBindingPath"],
        "rollbackArtifactPath": action["methodBinding"]["rollbackArtifactPath"],
    }
    campaign_state = require_campaign_state(
        paths["campaignStatePath"],
        bindings["campaignId"],
        require_threshold=operation == "apply",
    )
    written_at = now_timestamp()
    target_method_id = action["methodBinding"]["targetMethodId"]
    artifact_path = paths["rollbackArtifactPath"] if operation == "rollback" else paths["methodUpdateArtifactPath"]
    artifact = {
        "artifactType": "prediction_campaign_method_update_action",
        "artifactVersion": 1,
        "methodUpdateActionId": action["predictionCampaignMethodUpdateActionId"],
        "writtenAt": written_at,
        "operation": operation,
        "campaignId": bindings["campaignId"],
        "cycleId": bindings["cycleId"],
        "methodUpdatePlanId": bindings["predictionCampaignMethodUpdatePlanId"],
        "currentMethodId": bindings["currentMethodId"],
        "candidateMethodId": bindings["candidateMethodId"],
        "targetMethodId": target_method_id,
        "sourcePolicyId": bindings["sourcePolicyId"],
        "resolvedComparableOutcomes": int(campaign_state.get("resolvedComparableOutcomes", 0)),
        "effectiveScope": "future_campaign_forecasts_only",
        "priorForecastHistoryRewriteAllowed": False,
        "priorForecastProbabilityRewriteAllowed": False,
    }
    binding = {
        "stateType": "prediction_campaign_method_binding",
        "stateVersion": 1,
        "writtenAt": written_at,
        "campaignId": bindings["campaignId"],
        "cycleId": bindings["cycleId"],
        "activeMethodId": target_method_id,
        "previousMethodId": bindings["candidateMethodId"] if operation == "rollback" else bindings["currentMethodId"],
        "sourceMethodUpdateArtifactPath": artifact_path,
        "effectiveScope": "future_campaign_forecasts_only",
        "prospectiveOnly": True,
        "priorForecastHistoryRewriteAllowed": False,
        "priorForecastProbabilityRewriteAllowed": False,
        "writesMethodRegistry": False,
    }
    artifact_write = write_audit_artifact(artifact_path, artifact)
    binding_write = write_method_binding(
        path_value=paths["methodBindingPath"],
        binding=binding,
        operation=operation,
        current_method_id=bindings["currentMethodId"],
        candidate_method_id=bindings["candidateMethodId"],
    )
    campaign_write = update_campaign_state(
        path_value=paths["campaignStatePath"],
        state=campaign_state,
        operation=operation,
        written_at=written_at,
        method_binding_path=paths["methodBindingPath"],
        artifact_path=artifact_path,
        current_method_id=bindings["currentMethodId"],
        candidate_method_id=bindings["candidateMethodId"],
    )
    rows = [artifact_write, binding_write, campaign_write]
    new_count = len([row for row in rows if row["writeStatus"] in {"written", "updated"}])
    already_count = len([row for row in rows if row["writeStatus"] == "already_present"])
    status = f"local_{operation}_completed" if new_count else f"local_{operation}_already_present"
    return {
        "writtenAt": written_at,
        "writeStatus": status,
        "artifactWrites": [artifact_write],
        "stateWrites": [binding_write, campaign_write],
        "newFileWriteCount": new_count,
        "alreadyPresentCount": already_count,
        "sanitizedDiagnostics": "Method update action wrote only ignored local campaign state and preserved prior histories.",
    }


def print_view(record: dict[str, Any], view: str, output_format: str) -> None:
    views = {
        "plan": record,
        "approval": record["approvalArtifact"],
        "command": record["commandSurface"],
        "rollback": record["rollbackRecord"],
        "preflight": record["preflightChecks"],
        "decision": record["decision"],
        "summary": {
            "operation": record["operation"],
            "actionStatus": record["actionStatus"],
            "localWriteEligible": record["decision"]["localWriteEligible"],
            "targetMethodId": record["methodBinding"]["targetMethodId"],
            "writeStatus": record["writeResult"]["writeStatus"],
            "recommendedNextAction": record["decision"]["recommendedNextAction"],
        },
        "boundary": record["executionBoundary"],
    }
    data = views[view]
    if output_format == "human":
        print(f"{record['operation']} {record['actionStatus']} target={record['methodBinding']['targetMethodId']}")
        return
    if output_format == "jsonl":
        print(compact_json(data), end="")
        return
    print(render_json(data), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(
        data,
        SCHEMA,
        OUTPUT_PATH,
        write=write,
        label="prediction campaign method update action",
        regen="python3 scripts/generate_prediction_campaign_method_update_action.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated method-update action")
    parser.add_argument("--check", action="store_true", help="check generated method-update action drift")
    parser.add_argument("--write-local", action="store_true", help="execute the ignored local method-update action")
    parser.add_argument("--operation", choices=OPERATIONS, default="apply", help="method-update action operation")
    parser.add_argument("--method-update-plan-id", help="checked method-update plan id to apply or roll back")
    parser.add_argument(
        "--method-update-plan-case",
        choices=METHOD_UPDATE_PLAN_CASES,
        default=DEFAULT_PLAN_CASE,
        help="checked method-update plan case",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for command output",
    )
    parser.add_argument(
        "--view",
        choices=["plan", "approval", "command", "rollback", "preflight", "decision", "summary", "boundary"],
        default="plan",
        help="print one prediction campaign method-update action view",
    )
    args = parser.parse_args()
    if (args.write or args.check) and (
        args.operation != "apply"
        or args.method_update_plan_case != DEFAULT_PLAN_CASE
        or args.method_update_plan_id is not None
        or args.write_local
    ):
        raise SystemExit("custom method-update action cases cannot be combined with --write or --check")
    record = build_prediction_campaign_method_update_action(
        operation=args.operation,
        method_update_plan_case=args.method_update_plan_case,
        method_update_plan_id=args.method_update_plan_id,
    )
    if args.write or args.check:
        check_or_write(record, write=args.write)
        return
    if args.write_local:
        try:
            result = execute_local_method_update(record)
        except PredictionCampaignMethodUpdateError as exc:
            raise SystemExit(str(exc)) from exc
        record = build_prediction_campaign_method_update_action(
            operation=args.operation,
            method_update_plan_case=args.method_update_plan_case,
            method_update_plan_id=args.method_update_plan_id,
            write_result=result,
        )
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(record, args.view, args.output_format)


if __name__ == "__main__":
    main()
