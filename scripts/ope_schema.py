"""Reusable OPE JSON Schema subset validation helpers."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec"


class SchemaError(Exception):
    """Raised when a schema uses unsupported local validator features."""


class Validator:
    """Validate records against the JSON Schema subset used by OPE contracts."""

    def __init__(self) -> None:
        self.cache: dict[Path, dict[str, Any]] = {}

    def load_schema(self, path: Path) -> dict[str, Any]:
        path = path.resolve()
        if path not in self.cache:
            self.cache[path] = json.loads(path.read_text(encoding="utf-8"))
        return self.cache[path]

    def resolve_ref(
        self,
        ref: str,
        current_file: Path,
        root_schema: dict[str, Any],
    ) -> tuple[dict[str, Any], Path, dict[str, Any]]:
        if "#" in ref:
            file_part, pointer = ref.split("#", 1)
        else:
            file_part, pointer = ref, ""
        if file_part:
            target_file = (current_file.parent / file_part).resolve()
            target_root = self.load_schema(target_file)
        else:
            target_file = current_file
            target_root = root_schema
        target: Any = target_root
        if pointer:
            if not pointer.startswith("/"):
                raise SchemaError(f"unsupported JSON pointer {ref!r}")
            for part in pointer.lstrip("/").split("/"):
                part = part.replace("~1", "/").replace("~0", "~")
                target = target[part]
        return target, target_file, target_root

    def validate(
        self,
        data: Any,
        schema: dict[str, Any],
        schema_file: Path,
        root_schema: dict[str, Any],
        path: str = "$",
    ) -> list[str]:
        errors: list[str] = []

        if "$ref" in schema:
            target, target_file, target_root = self.resolve_ref(schema["$ref"], schema_file, root_schema)
            return self.validate(data, target, target_file, target_root, path)

        if "allOf" in schema:
            for index, subschema in enumerate(schema["allOf"]):
                errors.extend(self.validate(data, subschema, schema_file, root_schema, f"{path}.allOf[{index}]"))

        if "oneOf" in schema:
            matches = [
                not self.validate(data, subschema, schema_file, root_schema, path)
                for subschema in schema["oneOf"]
            ]
            if sum(1 for item in matches if item) != 1:
                errors.append(f"{path}: expected exactly one matching schema, got {sum(matches)}")

        if "if" in schema:
            if_matches = not self.validate(data, schema["if"], schema_file, root_schema, path)
            if if_matches and "then" in schema:
                errors.extend(self.validate(data, schema["then"], schema_file, root_schema, path))

        if "const" in schema and data != schema["const"]:
            errors.append(f"{path}: expected const {schema['const']!r}, got {data!r}")

        if "enum" in schema and data not in schema["enum"]:
            errors.append(f"{path}: expected one of {schema['enum']!r}, got {data!r}")

        expected_type = schema.get("type")
        if expected_type and not self.is_type(data, expected_type):
            errors.append(f"{path}: expected type {expected_type}, got {type(data).__name__}")
            return errors

        if isinstance(data, dict):
            errors.extend(self.validate_object(data, schema, schema_file, root_schema, path))
        elif isinstance(data, list):
            errors.extend(self.validate_array(data, schema, schema_file, root_schema, path))
        elif isinstance(data, str):
            errors.extend(self.validate_string(data, schema, path))
        elif self.is_number(data):
            errors.extend(self.validate_number(data, schema, path))

        return errors

    def validate_object(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
        schema_file: Path,
        root_schema: dict[str, Any],
        path: str,
    ) -> list[str]:
        errors: list[str] = []
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            allowed = set(properties)
            for key in data:
                if key not in allowed:
                    errors.append(f"{path}: unexpected property {key!r}")
        for key, subschema in properties.items():
            if key in data:
                errors.extend(
                    self.validate(data[key], subschema, schema_file, root_schema, f"{path}.{key}")
                )
        return errors

    def validate_array(
        self,
        data: list[Any],
        schema: dict[str, Any],
        schema_file: Path,
        root_schema: dict[str, Any],
        path: str,
    ) -> list[str]:
        errors: list[str] = []
        if "minItems" in schema and len(data) < schema["minItems"]:
            errors.append(f"{path}: expected at least {schema['minItems']} items")
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            errors.append(f"{path}: expected at most {schema['maxItems']} items")
        if "items" in schema:
            for index, item in enumerate(data):
                errors.extend(
                    self.validate(item, schema["items"], schema_file, root_schema, f"{path}[{index}]")
                )
        return errors

    def validate_string(self, data: str, schema: dict[str, Any], path: str) -> list[str]:
        errors: list[str] = []
        if "minLength" in schema and len(data) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], data):
            errors.append(f"{path}: does not match pattern {schema['pattern']!r}")
        if "format" in schema:
            fmt = schema["format"]
            if fmt == "date-time":
                try:
                    datetime.fromisoformat(data.replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"{path}: invalid date-time")
            elif fmt == "date":
                try:
                    date.fromisoformat(data)
                except ValueError:
                    errors.append(f"{path}: invalid date")
            elif fmt == "uri":
                parsed = urlparse(data)
                if not parsed.scheme:
                    errors.append(f"{path}: invalid uri")
        return errors

    def validate_number(self, data: int | float, schema: dict[str, Any], path: str) -> list[str]:
        errors: list[str] = []
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(f"{path}: above maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and data <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: not greater than {schema['exclusiveMinimum']}")
        if "exclusiveMaximum" in schema and data >= schema["exclusiveMaximum"]:
            errors.append(f"{path}: not less than {schema['exclusiveMaximum']}")
        return errors

    @staticmethod
    def is_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def is_type(self, data: Any, expected: str) -> bool:
        if expected == "object":
            return isinstance(data, dict)
        if expected == "array":
            return isinstance(data, list)
        if expected == "string":
            return isinstance(data, str)
        if expected == "boolean":
            return isinstance(data, bool)
        if expected == "number":
            return self.is_number(data)
        if expected == "integer":
            return isinstance(data, int) and not isinstance(data, bool)
        if expected == "null":
            return data is None
        raise SchemaError(f"unsupported schema type {expected!r}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# Generated fixtures that are intentionally schema-less intermediates: computed
# feature snapshots, normalized source dumps, and human-readable run/outcome
# summaries that are not contract records. Every *other* file under
# spec/fixtures/generated/ must resolve to a schema via schema_for(); the
# schema-contract check enforces that so a renamed fixture or a stale
# endswith() rule cannot silently drop out of validation.
SCHEMALESS_GENERATED_SUFFIXES = (
    "-feature-snapshot.generated.json",
    "-normalized-sources.generated.json",
    "-outcome-summary.generated.json",
    "-run-summary.generated.json",
)


def schema_for(path: Path, spec_root: Path = SPEC) -> Path | None:
    name = path.name
    parts = path.parts
    if "invalid" in parts or "source" in parts or "live" in parts:
        return None
    if "benchmark" in parts:
        return spec_root / "benchmark-run.schema.json"
    if name.endswith("-method-registry.json"):
        return spec_root / "method-registry.schema.json"
    if name.endswith("-method-comparison.generated.json"):
        return spec_root / "method-comparison.schema.json"
    if name.endswith("-method-selection.generated.json"):
        return spec_root / "method-selection.schema.json"
    if name.endswith("-source-connector-registry.generated.json"):
        return spec_root / "source-connector-registry.schema.json"
    if name.endswith("-source-connector-results.generated.json"):
        return spec_root / "source-connector-result-set.schema.json"
    if name.endswith("-live-readiness.generated.json"):
        return spec_root / "live-connector-readiness.schema.json"
    if name.endswith("-transit-api-connector.generated.json"):
        return spec_root / "transit-api-connector.schema.json"
    if name.endswith("-transit-delays-forward-run.generated.json"):
        return spec_root / "transit-delay-forward-run.schema.json"
    if name.endswith("transit-forward-run-corpus.generated.json"):
        return spec_root / "transit-forward-run-corpus.schema.json"
    if name.endswith("transit-corpus-growth-loop.generated.json"):
        return spec_root / "transit-corpus-growth-loop.schema.json"
    if name.endswith("transit-baseline-track-record-gate.generated.json"):
        return spec_root / "transit-baseline-track-record-gate.schema.json"
    if name.endswith("transit-method-options.generated.json"):
        return spec_root / "transit-method-options.schema.json"
    if name.endswith("transit-live-evidence-promotion.generated.json"):
        return spec_root / "transit-live-evidence-promotion.schema.json"
    if name.endswith("resolve-due-forward-runs.generated.json"):
        return spec_root / "transit-forward-run-resolver.schema.json"
    if name.endswith("resolution-jobs.generated.json") or name.endswith("resolution-jobs-campaign.generated.json"):
        return spec_root / "resolution-job-registry.schema.json"
    if name.endswith("resolution-scheduler-run.generated.json") or name.endswith("resolution-scheduler-campaign-run.generated.json"):
        return spec_root / "resolution-scheduler-run.schema.json"
    if name.endswith("resolution-runtime-reliability.generated.json"):
        return spec_root / "resolution-runtime-reliability.schema.json"
    if name.endswith("internal-api.generated.json"):
        return spec_root / "internal-api.schema.json"
    if name.endswith("prediction-workspace-registry.generated.json"):
        return spec_root / "prediction-workspace-registry.schema.json"
    if name.endswith("background-worker-runtime.generated.json"):
        return spec_root / "background-worker-runtime.schema.json"
    if name.endswith("runtime-security.generated.json"):
        return spec_root / "runtime-security.schema.json"
    if name.endswith("agent-implementation-kit.generated.json"):
        return spec_root / "agent-implementation-kit.schema.json"
    if name.endswith("prediction-agent-adoption.generated.json"):
        return spec_root / "prediction-agent-adoption.schema.json"
    if name.endswith("prediction-goal-catalog.generated.json"):
        return spec_root / "prediction-goal-catalog.schema.json"
    if name.endswith("setup-engine.generated.json"):
        return spec_root / "setup-engine.schema.json"
    if "setup-engine-requests" in parts and name.endswith("-request.json"):
        return spec_root / "setup-engine-request.schema.json"
    if name.endswith("agent-integration.generated.json"):
        return spec_root / "agent-integration.schema.json"
    if name.endswith("prediction-feature-setup.generated.json"):
        return spec_root / "prediction-feature-setup.schema.json"
    if name.endswith("agent-guidance.generated.json"):
        return spec_root / "agent-guidance.schema.json"
    if name.endswith("mcp-adoption-path.generated.json"):
        return spec_root / "mcp-adoption-path.schema.json"
    if name.endswith("pilot-findings.generated.json"):
        return spec_root / "pilot-findings.schema.json"
    if name.endswith("pilot-supervision-status.generated.json"):
        return spec_root / "pilot-supervision-status.schema.json"
    if name.endswith("pilot-session-brief.generated.json"):
        return spec_root / "pilot-session-brief.schema.json"
    if name.endswith("pilot-summary-review.generated.json"):
        return spec_root / "pilot-summary-review.schema.json"
    if name.endswith("simulated-agent-pilot.generated.json"):
        return spec_root / "simulated-agent-pilot.schema.json"
    if name.endswith("generated-runtime-types-decision.generated.json"):
        return spec_root / "generated-runtime-types-decision.schema.json"
    if name.endswith("postgres-compatibility.generated.json"):
        return spec_root / "postgres-compatibility.schema.json"
    if name.endswith("database-source-adapter-runtime.generated.json"):
        return spec_root / "database-source-adapter-runtime.schema.json"
    if name.endswith("opp-provider-adapter.generated.json"):
        return spec_root / "opp-provider-adapter.schema.json"
    if name.endswith("persistent-sqlite-policy.generated.json"):
        return spec_root / "persistent-sqlite-policy.schema.json"
    if name.endswith("lifecycle-lease-policy.generated.json"):
        return spec_root / "lifecycle-lease-policy.schema.json"
    if name.endswith("runtime-transport-readiness.generated.json"):
        return spec_root / "runtime-transport-readiness.schema.json"
    if name.endswith("workspace-tenant-isolation.generated.json"):
        return spec_root / "workspace-tenant-isolation.schema.json"
    if name.endswith("domain-source-field-policy.generated.json"):
        return spec_root / "domain-source-field-policy.schema.json"
    if name.endswith("credential-reference-policy.generated.json"):
        return spec_root / "credential-reference-policy.schema.json"
    if name.endswith("retention-redaction-policy.generated.json"):
        return spec_root / "retention-redaction-policy.schema.json"
    if name.endswith("private-auto-evidence-policy.generated.json"):
        return spec_root / "private-auto-evidence-policy.schema.json"
    if name.endswith("lifecycle-operation-store.generated.json"):
        return spec_root / "lifecycle-operation.schema.json"
    if name.endswith("-domain-config.generated.json"):
        return spec_root / "domain-config.schema.json"
    if name.endswith("-source-binding.generated.json"):
        return spec_root / "source-binding.schema.json"
    if name.endswith("-domain-setup.generated.json"):
        return spec_root / "domain-setup.schema.json"
    if name.endswith("-source-manifest-build.generated.json"):
        return spec_root / "source-manifest-build.schema.json"
    if name.endswith("-source-adapter-output.generated.json"):
        return spec_root / "source-adapter-output.schema.json"
    if name.endswith("-source-adapter-intake.generated.json"):
        return spec_root / "source-adapter-intake.schema.json"
    if name.endswith("-source-intake-handoff.generated.json"):
        return spec_root / "source-intake-handoff.schema.json"
    if name.endswith("-source-handoff-method-gate.generated.json"):
        return spec_root / "source-handoff-method-gate.schema.json"
    if name.endswith("-source-manifest.json"):
        return spec_root / "source-manifest.schema.json"
    if name.endswith("-field-mapping.json"):
        return spec_root / "field-mapping.schema.json"
    if name.endswith("-source-intake-report.generated.json"):
        return spec_root / "source-intake-report.schema.json"
    if name.endswith("source-quality-mapping-confidence.generated.json"):
        return spec_root / "source-quality-mapping-confidence.schema.json"
    if name.endswith("local-source-runtime.generated.json"):
        return spec_root / "local-source-runtime.schema.json"
    if name.endswith("developer-adoption-surface.generated.json"):
        return spec_root / "developer-adoption-surface.schema.json"
    if name.endswith("expansion-readiness-gate.generated.json"):
        return spec_root / "expansion-readiness-gate.schema.json"
    if name.endswith("repeating-prediction-setup.generated.json"):
        return spec_root / "repeating-prediction-setup.schema.json"
    if name.endswith("-campaign-manifest.generated.json"):
        return spec_root / "prediction-campaign-manifest.schema.json"
    if name.endswith("-campaign-runner.generated.json"):
        return spec_root / "prediction-campaign-runner.schema.json"
    if name.endswith("campaign-forecast-creation.generated.json"):
        return spec_root / "prediction-campaign-forecast-creation.schema.json"
    if name.endswith("campaign-forecast-write.generated.json"):
        return spec_root / "prediction-campaign-forecast-write.schema.json"
    if name.endswith("campaign-resolution-attempt.generated.json"):
        return spec_root / "prediction-campaign-resolution-attempt.schema.json"
    if name.endswith("campaign-doctor.generated.json"):
        return spec_root / "prediction-campaign-doctor.schema.json"
    if name.endswith("campaign-resume.generated.json"):
        return spec_root / "prediction-campaign-resume.schema.json"
    if name.endswith("campaign-evidence-ledger.generated.json"):
        return spec_root / "prediction-campaign-evidence-ledger.schema.json"
    if name.endswith("campaign-pre-calibration.generated.json"):
        return spec_root / "prediction-campaign-pre-calibration.schema.json"
    if name.endswith("campaign-calibration-status.generated.json"):
        return spec_root / "prediction-campaign-calibration-status.schema.json"
    if name.endswith("campaign-method-update-gate.generated.json"):
        return spec_root / "prediction-campaign-method-update-gate.schema.json"
    if name.endswith("campaign-method-update-plan.generated.json"):
        return spec_root / "prediction-campaign-method-update-plan.schema.json"
    if name.endswith("campaign-method-update-action.generated.json"):
        return spec_root / "prediction-campaign-method-update-action.schema.json"
    if name.endswith("campaign-explain.generated.json"):
        return spec_root / "prediction-campaign-explain.schema.json"
    if name.endswith("helsinki-traffic-disturbance-pilot-runbook.generated.json"):
        return spec_root / "helsinki-traffic-disturbance-pilot-runbook.schema.json"
    if name.endswith("helsinki-traffic-pilot-readiness.generated.json"):
        return spec_root / "helsinki-traffic-pilot-readiness.schema.json"
    if name.endswith("-setup-benchmark-gate.generated.json"):
        return spec_root / "setup-benchmark-gate.schema.json"
    if name.endswith("-setup-method-decision.generated.json"):
        return spec_root / "setup-method-decision.schema.json"
    if name.endswith("-setup-forecast-run.generated.json"):
        return spec_root / "setup-forecast-run.schema.json"
    if name.endswith("-recalculation-trigger.generated.json") or name.endswith("-recalculation-rejected-trigger.generated.json"):
        return spec_root / "recalculation-trigger.schema.json"
    if name.endswith("-recalculation-run.generated.json") or name.endswith("-recalculation-rejected-run.generated.json"):
        return spec_root / "recalculation-run.schema.json"
    if name.endswith("-envelope.generated.json"):
        return spec_root / "agent-envelope.schema.json"
    if name.endswith("-protocol-map.generated.json"):
        return spec_root / "agent-adapter-protocol-map.schema.json"
    if "requests" in parts:
        return spec_root / "forecast-request.schema.json"
    if name.endswith("-question.json") or name.endswith("-question.generated.json"):
        return spec_root / "forecast-question.schema.json"
    if name.endswith("-history.json") or name.endswith("-history.generated.json"):
        return spec_root / "forecast-history.schema.json"
    if name.endswith("-evidence.json") or name.endswith("-evidence.generated.json"):
        return spec_root / "evidence-packet.schema.json"
    if name.endswith("-evidence-plan.generated.json"):
        return spec_root / "evidence-gathering-plan.schema.json"
    if name.endswith("-source-set.generated.json"):
        return spec_root / "evidence-source-set.schema.json"
    if name.endswith("-artifact.json") or name.endswith("-artifact.generated.json"):
        return spec_root / "forecast-artifact.schema.json"
    if name.endswith("-resolution.json") or name.endswith("-resolution.generated.json"):
        return spec_root / "resolution-record.schema.json"
    if name.endswith("-scoring.json") or name.endswith("-scoring.generated.json"):
        return spec_root / "scoring-report.schema.json"
    if name.endswith("-track-record.json") or name.endswith("-track-record.generated.json"):
        return spec_root / "track-record-report.schema.json"
    if name.endswith("-calibration.generated.json"):
        return spec_root / "calibration-summary.schema.json"
    if name.endswith("-pipeline-run.generated.json"):
        return spec_root / "pipeline-run.schema.json"
    if name.endswith("-source-handoff-setup-runbook.generated.json"):
        return spec_root / "source-handoff-setup-runbook.schema.json"
    if name.endswith("-private-setup-workflow.generated.json"):
        return spec_root / "private-setup-workflow.schema.json"
    if name.endswith("-private-source-adapter-capabilities.generated.json"):
        return spec_root / "private-source-adapter-capability.schema.json"
    if name.endswith("-private-source-adapter-outcome-matrix.generated.json"):
        return spec_root / "private-source-adapter-outcome-matrix.schema.json"
    if name.endswith("-private-source-adapter-intake-bridge.generated.json"):
        return spec_root / "private-source-adapter-intake-bridge.schema.json"
    if name.endswith("-private-source-kind-selection-examples.generated.json"):
        return spec_root / "private-source-kind-selection-examples.schema.json"
    if name.endswith("-private-source-kind-query-matrix.generated.json"):
        return spec_root / "private-source-kind-query-matrix.schema.json"
    if name.endswith("-private-setup-requests.generated.json"):
        return spec_root / "private-setup-request.schema.json"
    if name.endswith("-private-setup-first-action-runbook.generated.json"):
        return spec_root / "private-setup-first-action-runbook.schema.json"
    if name.endswith("-private-setup-adapter-chain-runbook.generated.json"):
        return spec_root / "private-setup-adapter-chain-runbook.schema.json"
    if name.endswith("-private-setup-adapter-conformance-matrix.generated.json"):
        return spec_root / "private-setup-adapter-conformance-matrix.schema.json"
    if name.endswith("-private-setup-adapter-conformance-summary.generated.json"):
        return spec_root / "private-setup-adapter-conformance-summary.schema.json"
    if name.endswith("-private-setup-orchestrator.generated.json"):
        return spec_root / "private-setup-orchestrator.schema.json"
    if name.endswith("-agent-pilot-validation.generated.json"):
        return spec_root / "agent-pilot-validation.schema.json"
    if name.endswith("-pilot-evidence-ledger.generated.json"):
        return spec_root / "pilot-evidence-ledger.schema.json"
    if name.endswith("-pilot-session-packet.generated.json"):
        return spec_root / "pilot-session-packet.schema.json"
    if name.endswith("-pilot-summary-intake.generated.json"):
        return spec_root / "pilot-summary-intake.schema.json"
    if name.endswith("-pilot-summary-template.generated.json"):
        return spec_root / "pilot-summary-template.schema.json"
    if "pilot-summary-intake" in parts and name.endswith("-summary.json"):
        return spec_root / "pilot-summary-submission.schema.json"
    if name.endswith("-local-usage-trace.generated.json"):
        return spec_root / "local-usage-trace.schema.json"
    if "-private-setup-first-action-" in name and name.endswith(".generated.json"):
        return spec_root / "private-setup-first-action.schema.json"
    if "-private-setup-agent-bundle-" in name and name.endswith(".generated.json"):
        return spec_root / "private-setup-agent-bundle.schema.json"
    if name.endswith("-forecast-runbook.generated.json"):
        return spec_root / "agent-forecast-runbook.schema.json"
    if name.endswith("-forecast-run.generated.json"):
        return spec_root / "forecast-run-summary.schema.json"
    if name.endswith("-intake-matrix.generated.json"):
        return spec_root / "forecast-run-intake-matrix.schema.json"
    if name == "record-index.generated.json":
        return spec_root / "record-index.schema.json"
    if name == "release-manifest.generated.json":
        return spec_root / "release-manifest.schema.json"
    if name == "weather-logistics-aggregate-forecast.json":
        return spec_root / "aggregate-forecast.schema.json"
    return None


def iter_contract_records(fixtures_root: Path = SPEC / "fixtures", spec_root: Path = SPEC) -> list[tuple[Path, Path]]:
    records: list[tuple[Path, Path]] = []
    for path in sorted(fixtures_root.rglob("*.json")):
        schema = schema_for(path, spec_root)
        if schema is not None:
            records.append((path, schema))
    return records


def iter_generated_fixtures(generated_root: Path = SPEC / "fixtures" / "generated") -> list[Path]:
    return sorted(generated_root.rglob("*.json"))


def validate_record(
    data: Any,
    schema_path: Path,
    validator: Validator | None = None,
) -> list[str]:
    validator = validator or Validator()
    schema = validator.load_schema(schema_path)
    return validator.validate(data, schema, schema_path, schema)


def validate_file(
    record_path: Path,
    schema_path: Path | None = None,
    validator: Validator | None = None,
) -> tuple[Path, list[str]]:
    schema_path = schema_path or schema_for(record_path)
    if schema_path is None:
        raise SchemaError(f"no schema could be inferred for {record_path}")
    return schema_path, validate_record(load_json(record_path), schema_path, validator)
