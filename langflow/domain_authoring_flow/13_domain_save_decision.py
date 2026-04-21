from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict


# NOTE FOR CONFIRMED LFX LANGFLOW RUNTIME:
# Compatibility scaffolding for local tests. In lfx Langflow this can be
# replaced with direct imports from lfx.custom, lfx.io, and lfx.schema.
def _load_attr(module_names: list[str], attr_name: str, fallback: Any) -> Any:
    for module_name in module_names:
        try:
            return getattr(import_module(module_name), attr_name)
        except Exception:
            continue
    return fallback


class _FallbackComponent:
    display_name = ""
    description = ""
    icon = ""
    name = ""
    inputs = []
    outputs = []
    status = ""


@dataclass
class _FallbackInput:
    name: str
    display_name: str
    info: str = ""
    value: Any = None
    advanced: bool = False
    tool_mode: bool = False
    input_types: list[str] | None = None


@dataclass
class _FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None


class _FallbackData:
    def __init__(self, data: Dict[str, Any] | None = None, text: str | None = None):
        self.data = data or {}
        self.text = text


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _payload_from_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data
    text = getattr(value, "text", None)
    if isinstance(text, str):
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _config_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    return payload.get("authoring_config") if isinstance(payload.get("authoring_config"), dict) else payload


def _semantic_review_from_value(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    review = payload.get("semantic_review") if isinstance(payload.get("semantic_review"), dict) else payload
    return review if isinstance(review, dict) else {}


def decide_domain_fragment_save(
    conflict_value: Any,
    validated_value: Any,
    semantic_review_value: Any = None,
    config_value: Any = None,
) -> Dict[str, Any]:
    conflict_payload = _payload_from_value(conflict_value)
    validated_payload = _payload_from_value(validated_value)
    semantic_review = _semantic_review_from_value(semantic_review_value)
    validation = validated_payload.get("validation") if isinstance(validated_payload.get("validation"), dict) else {}
    config = _config_from_value(config_value)
    authoring_mode = str(config.get("authoring_mode") or "append").lower()

    validation_errors = [str(item) for item in _as_list(validation.get("errors")) if str(item).strip()]
    validation_warnings = [str(item) for item in _as_list(validation.get("warnings")) if str(item).strip()]
    conflict_warnings = [str(item) for item in _as_list(conflict_payload.get("warnings")) if str(item).strip()]
    blocking_errors = [str(item) for item in _as_list(conflict_payload.get("blocking_errors")) if str(item).strip()]
    conflicts = [item for item in _as_list(conflict_payload.get("conflicts")) if item]
    semantic_conflicts = [item for item in _as_list(semantic_review.get("semantic_conflicts")) if item]
    semantic_warnings = [str(item) for item in _as_list(semantic_review.get("semantic_warnings")) if str(item).strip()]
    semantic_parse_errors = [str(item) for item in _as_list(semantic_review.get("parse_errors")) if str(item).strip()]
    semantic_status = str(semantic_review.get("recommended_status") or "active").strip().lower()
    all_errors = [*blocking_errors, *validation_errors]
    all_warnings = [*validation_warnings, *conflict_warnings, *semantic_warnings, *semantic_parse_errors]

    if authoring_mode == "validate_only":
        decision = {
            "should_save": False,
            "target_status": "draft",
            "needs_review": False,
            "reason": "authoring_mode is validate_only",
        }
    elif all_errors:
        decision = {
            "should_save": False,
            "target_status": "rejected",
            "needs_review": True,
            "reason": "blocking errors or validation errors found",
        }
    elif semantic_status == "rejected":
        decision = {
            "should_save": False,
            "target_status": "rejected",
            "needs_review": True,
            "reason": "semantic review recommended rejected",
        }
    elif conflicts or semantic_conflicts or semantic_status == "review_required":
        decision = {
            "should_save": True,
            "target_status": "review_required",
            "needs_review": True,
            "reason": "rule or semantic conflicts found; save fragment for review, but do not use in Main Flow",
        }
    else:
        decision = {
            "should_save": True,
            "target_status": str(config.get("target_status") or "active").strip() or "active",
            "needs_review": False,
            "reason": "no blocking conflicts",
        }

    decision["error_count"] = len(all_errors)
    decision["warning_count"] = len(all_warnings)
    decision["conflict_count"] = len(conflicts) + len(semantic_conflicts)
    decision["errors"] = all_errors
    decision["warnings"] = all_warnings
    decision["conflicts"] = conflicts
    decision["semantic_conflicts"] = semantic_conflicts
    decision["semantic_review"] = semantic_review
    return {"save_decision": decision}


class DomainSaveDecision(Component):
    display_name = "Domain Save Decision"
    description = "Decide whether a normalized domain patch should be saved as active, review_required, or blocked."
    icon = "GitBranch"
    name = "DomainSaveDecision"

    inputs = [
        DataInput(name="conflict_report", display_name="Conflict Report", info="Output from Domain Conflict Detector.", input_types=["Data", "JSON"]),
        DataInput(name="validated_domain", display_name="Validated Domain", info="Output from Domain Schema Validator.", input_types=["Data", "JSON"]),
        DataInput(name="semantic_review", display_name="Semantic Review", info="Output from Parse Domain Review JSON.", input_types=["Data", "JSON"]),
        DataInput(
            name="authoring_config",
            display_name="Authoring Config",
            info="Optional config. Leave disconnected to use defaults.",
            input_types=["Data", "JSON"],
            advanced=True,
        ),
    ]

    outputs = [
        Output(name="save_decision", display_name="Save Decision", method="build_save_decision", types=["Data"]),
    ]

    def build_save_decision(self) -> Data:
        return _make_data(
            decide_domain_fragment_save(
                getattr(self, "conflict_report", None),
                getattr(self, "validated_domain", None),
                getattr(self, "semantic_review", None),
                getattr(self, "authoring_config", None),
            )
        )
