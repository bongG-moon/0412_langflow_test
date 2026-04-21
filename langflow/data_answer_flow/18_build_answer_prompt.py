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
    required: bool = False


@dataclass
class _FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None


class _FallbackData:
    def __init__(self, data: Dict[str, Any] | None = None):
        self.data = data or {}


class _FallbackMessage:
    def __init__(self, text: str | None = None, **kwargs: Any):
        self.text = text or str(kwargs.get("content") or "")
        self.content = self.text


def _make_input(**kwargs: Any) -> _FallbackInput:
    return _FallbackInput(**kwargs)


Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
PromptInput = _load_attr(["lfx.io", "langflow.io"], "PromptInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)
Message = _load_attr(["lfx.schema.message", "lfx.schema", "langflow.schema.message", "langflow.schema"], "Message", _FallbackMessage)


DEFAULT_TEMPLATE = """당신은 제조 데이터 분석 결과를 한국어로 간결하게 설명하는 어시스턴트입니다.

사용자 질문:
{user_question}

최근 대화:
{chat_history}

분석 성공 여부:
{success}

결과 요약:
{summary}

결과 행 수:
{row_count}

결과 미리보기:
{preview_rows}

조회/분석 범위:
{scope_info}

분석 계획:
{analysis_plan}

작성 규칙:
1. 현재 결과에서 확인되는 사실만 설명한다.
2. 중요한 수치와 기준을 함께 언급한다.
3. 표 전체를 반복하지 말고 핵심만 3~5문장으로 요약한다.
4. 실패 결과라면 무엇이 부족한지와 다음에 입력해야 할 조건을 짧게 말한다.
5. 한국어로 자연스럽게 작성한다.
"""


def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)


def _make_message(text: str) -> Any:
    try:
        return Message(text=text)
    except TypeError:
        try:
            return Message(content=text)
        except TypeError:
            try:
                return Message(text)
            except Exception:
                return _FallbackMessage(text=text)


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
            return parsed if isinstance(parsed, dict) else {"text": text}
        except Exception:
            return {"text": text}
    return {}


def _analysis_result(value: Any) -> Dict[str, Any]:
    payload = _payload_from_value(value)
    result = payload.get("analysis_result")
    return result if isinstance(result, dict) else payload


def _compact_json(value: Any, limit: int = 5000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... truncated ..."


def _preview_rows(rows: Any, max_rows: int = 8) -> list[Dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return [row for row in rows[:max_rows] if isinstance(row, dict)]


def build_answer_prompt(analysis_result_payload: Any, template_value: Any = None) -> str:
    result = _analysis_result(analysis_result_payload)
    agent_state = result.get("agent_state") if isinstance(result.get("agent_state"), dict) else {}
    chat_history = agent_state.get("chat_history") if isinstance(agent_state.get("chat_history"), list) else []
    rows = result.get("data") if isinstance(result.get("data"), list) else []
    scope_info = {
        "source_dataset_keys": result.get("source_dataset_keys", []),
        "retrieval_applied_params": result.get("retrieval_applied_params", {}),
        "followup_applied_params": result.get("followup_applied_params", {}),
        "filter_notes": result.get("filter_notes", []),
        "merge_notes": result.get("merge_notes", []),
    }
    template = str(template_value or DEFAULT_TEMPLATE).strip()
    values = {
        "user_question": result.get("user_question") or agent_state.get("pending_user_question", ""),
        "chat_history": _compact_json(chat_history[-6:], limit=3000),
        "success": result.get("success", False),
        "summary": result.get("summary") or result.get("error_message", ""),
        "row_count": len(rows),
        "preview_rows": _compact_json(_preview_rows(rows), limit=7000),
        "scope_info": _compact_json(scope_info, limit=4000),
        "analysis_plan": _compact_json(result.get("analysis_plan", {}), limit=4000),
    }
    try:
        return template.format(**values)
    except KeyError as exc:
        raise ValueError(f"Template placeholder error: {exc}") from exc


class BuildAnswerPrompt(Component):
    display_name = "Build Answer Prompt"
    description = "Build a Message prompt for a built-in LLM to summarize the analysis result in Korean."
    icon = "MessageCircle"
    name = "BuildAnswerPrompt"

    inputs = [
        PromptInput(
            name="template",
            display_name="Template",
            value=DEFAULT_TEMPLATE,
            required=True,
            info="Use {user_question}, {chat_history}, {success}, {summary}, {row_count}, {preview_rows}, {scope_info}, and {analysis_plan}.",
        ),
        DataInput(name="analysis_result", display_name="Analysis Result", info="Output from Execute Pandas Analysis.", input_types=["Data", "JSON"]),
    ]

    outputs = [
        Output(name="prompt", display_name="Prompt Message", method="build_prompt", group_outputs=True, types=["Message"]),
        Output(name="prompt_payload", display_name="Prompt Payload", method="build_prompt_payload", group_outputs=True, types=["Data"]),
    ]

    def build_prompt_text(self) -> str:
        prompt = build_answer_prompt(getattr(self, "analysis_result", None), getattr(self, "template", "") or DEFAULT_TEMPLATE)
        self.status = {"prompt_chars": len(prompt)}
        return prompt

    def build_prompt(self) -> Message:
        return _make_message(self.build_prompt_text())

    def build_prompt_payload(self) -> Data:
        return _make_data({"prompt": self.build_prompt_text()})
