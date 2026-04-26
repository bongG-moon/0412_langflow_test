# Langflow Custom Node Code Guide

이 문서는 특정 프로젝트에 묶이지 않는 Langflow Custom Component 작성 가이드이다.

목표는 Python을 많이 써보지 않은 사람도 다음 내용을 이해할 수 있게 하는 것이다.

- Custom Component 파일은 어떤 구조로 작성하는지
- Input, Output, Data, Message를 어떻게 연결하는지
- 분기, 멀티턴, ReAct 같은 흐름을 Langflow에서 어떻게 설계하면 좋은지
- 다른 프로젝트에서도 재사용 가능한 노드 작성 습관은 무엇인지

프로젝트별 도메인, MongoDB collection, 데이터 조회 규칙, 세션 state 구조처럼 특정 업무에만 맞는 내용은 별도 프로젝트 문서에 두는 편이 좋다.

## 1. Custom Component란?

Langflow의 기본 컴포넌트만으로 표현하기 어려운 로직을 Python class로 만든 것이 Custom Component이다.

예를 들어 다음 작업은 Custom Component로 만들기 좋다.

- 입력 JSON을 필요한 형태로 정리하기
- LLM 응답을 JSON으로 파싱하고 기본값을 채우기
- 조건에 따라 여러 Output 중 하나로만 보내기
- 외부 DB, API, 파일 저장소에서 데이터를 읽기
- 다음 턴에서 쓸 작은 state를 만들기

반대로 단순히 prompt 문장을 바꾸는 일은 Prompt Template 컴포넌트로 처리하는 편이 더 쉽다.

## 2. 가장 작은 예시

아래는 텍스트를 받아 앞뒤 공백을 제거하고 `Data`로 반환하는 가장 작은 형태의 노드이다.

```python
from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data


class TextCleaner(Component):
    display_name = "Text Cleaner"
    description = "Trim a text value and return it as Data."
    icon = "scissors"
    name = "TextCleaner"

    inputs = [
        MessageTextInput(
            name="text",
            display_name="Text",
            value="",
        ),
    ]

    outputs = [
        Output(
            name="cleaned",
            display_name="Cleaned",
            method="clean_text",
        ),
    ]

    def clean_text(self) -> Data:
        value = str(self.text or "").strip()
        self.status = f"{len(value)} chars"
        return Data(data={"text": value})
```

핵심은 세 가지다.

1. `inputs`에 Langflow 화면에서 받을 값을 선언한다.
2. `outputs`에 다음 노드로 내보낼 포트와 실행 method를 선언한다.
3. method 안에서 `Data`, `Message`, 또는 문자열을 반환한다.

## 3. Import Path와 버전 차이

Langflow 버전에 따라 import path가 조금씩 다를 수 있다. 최근 버전에서는 보통 다음 형태를 먼저 사용한다.

```python
from langflow.custom import Component
from langflow.io import MessageTextInput, MultilineInput, DataInput, Output
from langflow.schema import Data
from langflow.schema.message import Message
```

만약 특정 버전에서 import가 실패하면, 같은 컴포넌트가 어느 모듈로 이동했는지 Langflow의 Custom Component 예시 코드를 먼저 확인한다.

팀에서 여러 Langflow 버전을 섞어 쓰는 경우에는 노드 파일 상단에 호환 fallback을 둘 수도 있다.

```python
try:
    from langflow.custom import Component
    from langflow.io import MessageTextInput, Output
    from langflow.schema import Data
except Exception:
    from langflow.custom.custom_component.component import Component
    from langflow.inputs import MessageTextInput
    from langflow.template.field.base import Output
    from langflow.schema import Data
```

단, fallback이 너무 많아지면 초보자가 읽기 어려워진다. 운영 환경의 Langflow 버전이 정해졌다면 그 버전에 맞춰 단순하게 유지하는 편이 좋다.

## 4. Class 메타데이터

Custom Component class에는 화면에 표시될 정보를 넣는다.

```python
class MyComponent(Component):
    display_name = "My Component"
    description = "Short description shown in Langflow."
    icon = "box"
    name = "MyComponent"
```

자주 쓰는 항목:

| 항목 | 의미 |
| --- | --- |
| `display_name` | Langflow 화면에 보이는 이름 |
| `description` | 노드 설명 |
| `icon` | 노드 아이콘 이름 |
| `name` | 내부 식별 이름 |
| `documentation` | 문서 URL을 연결할 때 사용 |

`display_name`은 사용자가 캔버스에서 읽는 이름이므로 역할이 바로 보이게 작성한다.

## 5. Input 선언

Input은 Langflow 화면에서 값을 받는 칸이다.

```python
inputs = [
    MessageTextInput(
        name="question",
        display_name="Question",
        value="",
        required=True,
    ),
]
```

method 안에서는 `self.question`처럼 `name`으로 접근한다.

자주 쓰는 Input 종류:

| Input | 용도 |
| --- | --- |
| `MessageTextInput` | 짧은 텍스트, 질문, session id |
| `MultilineInput` | 긴 prompt, JSON, 문서 |
| `DataInput` | 앞 노드의 `Data` output 받기 |
| `BoolInput` | true/false 옵션 |
| `DropdownInput` | 정해진 선택지 중 하나 |
| `IntInput`, `FloatInput` | 숫자 설정 |
| `SecretStrInput` | API key, password |

버전에 따라 이름이 조금 다를 수 있으므로, 실제 Langflow에서 자동 생성되는 Custom Component 예시를 함께 확인하는 것이 좋다.

## 6. Input 공통 옵션

Input에는 보통 다음 옵션을 쓴다.

```python
MessageTextInput(
    name="session_id",
    display_name="Session ID",
    value="",
    required=False,
    info="Optional key for multi-turn memory.",
)
```

| 옵션 | 의미 |
| --- | --- |
| `name` | 코드에서 접근할 이름 |
| `display_name` | 화면에 표시될 이름 |
| `value` | 기본값 |
| `required` | 필수 입력 여부 |
| `info` | 마우스를 올렸을 때 보이는 설명 |
| `advanced` | 고급 설정 영역으로 숨길지 여부 |

초보자가 쓰는 flow라면 중요한 값은 `advanced=False`, 운영 튜닝용 값은 `advanced=True`로 두면 화면이 덜 복잡해진다.

## 7. Output 선언

Output은 다음 노드로 값을 넘기는 포트이다.

```python
outputs = [
    Output(
        name="result",
        display_name="Result",
        method="build_result",
    ),
]
```

`method`에는 실제 실행할 함수 이름을 넣는다.

```python
def build_result(self) -> Data:
    return Data(data={"ok": True})
```

Output이 여러 개여도 method는 각각 따로 둘 수 있다.

```python
outputs = [
    Output(name="success", display_name="Success", method="success_output"),
    Output(name="error", display_name="Error", method="error_output"),
]
```

## 8. Data, Message, Text

Langflow에서 가장 자주 다루는 반환 형태는 세 가지다.

| 형태 | 언제 쓰나 |
| --- | --- |
| `Data` | JSON처럼 구조화된 값을 다음 노드로 넘길 때 |
| `Message` | Chat Output에 표시할 대화 메시지를 만들 때 |
| `str` | 단순 텍스트를 넘길 때 |

구조화된 flow에서는 가능한 `Data(data={...})`를 쓰는 편이 좋다.

```python
return Data(data={
    "success": True,
    "rows": rows,
    "summary": "12 rows",
})
```

화면에 답변으로 보여줄 값은 `Message`가 잘 맞는다.

```python
return Message(text="처리가 완료되었습니다.")
```

## 9. JSON 입력 처리

사용자가 JSON을 직접 붙여 넣는 노드는 흔히 필요하다. 이때는 빈 값, 잘못된 JSON, 이미 `Data`인 값을 모두 받아줄 수 있게 만든다.

```python
import json
from langflow.schema import Data


def as_dict(value):
    if value is None:
        return {}
    if isinstance(value, Data):
        return value.data or {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        return json.loads(text)
    return {}
```

사용자 입력에는 종종 코드블록이 포함된다.

```text
```json
{"a": 1}
```
```

이런 경우에는 파싱 전에 코드블록 fence를 제거하는 helper를 두면 편하다.

```python
def strip_code_fence(text: str) -> str:
    value = str(text or "").strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    return value
```

## 10. Error 처리

Custom Component는 오류가 나면 Langflow 화면에서 어디가 문제인지 알 수 있어야 한다.

좋은 오류 메시지는 다음 조건을 만족한다.

- 어느 입력이 문제인지 알려준다.
- 다음에 뭘 고치면 되는지 알려준다.
- Python traceback만 그대로 보여주지 않는다.

```python
def build_result(self) -> Data:
    try:
        payload = json.loads(self.payload_text or "{}")
    except json.JSONDecodeError as exc:
        message = f"Invalid JSON in payload_text: {exc}"
        self.status = message
        return Data(data={"success": False, "errors": [message]})

    return Data(data={"success": True, "payload": payload})
```

운영에서 반드시 실패해야 하는 오류라면 `raise ValueError(...)`를 써도 된다. 하지만 초보자가 테스트하는 flow에서는 `Data`에 `success=False`와 `errors`를 담아 넘기는 방식이 디버깅하기 쉽다.

## 11. self.status

`self.status`는 Langflow 화면에서 노드 실행 결과를 짧게 보여주는 상태 문구이다.

```python
self.status = "Loaded 12 rows"
```

좋은 status 예시:

```text
Parsed 3 items
Routed to multi_retrieval
Saved 5 records
No data found
```

너무 긴 JSON 전체를 넣기보다는, 사람이 flow를 따라가며 확인할 수 있는 요약을 넣는다.

## 12. 여러 Output과 분기

분기 처리는 Langflow 캔버스에서 흐름을 명확히 보여줄 때 유용하다.

예를 들어 intent를 보고 `new_request`, `followup`, `no_retrieval` 중 하나로 보내고 싶다면 Output을 여러 개 만든다.

```python
outputs = [
    Output(name="new_request", display_name="New Request", method="new_request", group_outputs=True),
    Output(name="followup", display_name="Follow-up", method="followup", group_outputs=True),
    Output(name="no_retrieval", display_name="No Retrieval", method="no_retrieval", group_outputs=True),
]
```

각 method에서는 현재 route가 맞을 때만 payload를 반환하고, 아니면 빈 payload를 반환한다.

```python
def _route(self) -> str:
    payload = as_dict(self.intent)
    return payload.get("route") or "new_request"

def _output(self, route_name: str) -> Data:
    payload = as_dict(self.intent)
    if self._route() != route_name:
        return Data(data={"active": False, "route": self._route()})
    return Data(data={"active": True, **payload})

def new_request(self) -> Data:
    return self._output("new_request")

def followup(self) -> Data:
    return self._output("followup")

def no_retrieval(self) -> Data:
    return self._output("no_retrieval")
```

`group_outputs=True`를 쓰면 Langflow에서 여러 output이 서로 다른 가지처럼 보인다.

## 13. 노드 크기 나누기

한 노드가 너무 많은 일을 하면 고치기 어렵다. 다음 기준으로 나누면 flow가 읽기 쉬워진다.

| 작업 | 노드 분리 추천 |
| --- | --- |
| 입력을 모으기 | Context Builder |
| prompt 문장을 만들기 | Prompt Builder |
| LLM 호출하기 | LLM Caller |
| LLM 응답 파싱하기 | Parser |
| schema와 기본값 맞추기 | Normalizer |
| 분기 결정하기 | Router |
| 외부 데이터 읽기 | Retriever |
| 최종 답변 만들기 | Answer Builder |
| 다음 턴 state 만들기 | State Builder |
| memory 저장하기 | Memory Writer |

초보자에게는 노드 수가 조금 늘어나더라도 "어디서 문제가 생겼는지" 보이는 구조가 더 편하다.

## 14. LLM 호출 노드 패턴

LLM 호출 노드는 보통 prompt를 입력받고 text를 반환한다.

```python
from langflow.custom import Component
from langflow.io import MultilineInput, MessageTextInput, SecretStrInput, Output
from langflow.schema import Data


class GenericLLMCaller(Component):
    display_name = "Generic LLM Caller"
    icon = "bot"
    name = "GenericLLMCaller"

    inputs = [
        MultilineInput(name="prompt", display_name="Prompt"),
        MessageTextInput(name="model_name", display_name="Model Name", value="gpt-4o-mini"),
        SecretStrInput(name="llm_api_key", display_name="LLM API Key", required=True),
    ]

    outputs = [
        Output(name="llm_response", display_name="LLM Response", method="call_llm"),
    ]

    def call_llm(self) -> Data:
        prompt = str(self.prompt or "")

        # Example with ChatOpenAI.
        # from langchain_openai import ChatOpenAI
        # llm = ChatOpenAI(model=str(self.model_name), api_key=str(self.llm_api_key))
        # response = llm.invoke(prompt)
        # text = getattr(response, "content", str(response))

        text = ""
        self.status = f"Prompt {len(prompt)} chars"
        return Data(data={"text": text, "model_name": str(self.model_name or "")})
```

실제 프로젝트에서는 provider별 구현을 노드 안에 직접 많이 넣기보다, 입력 이름을 `llm_api_key`, `model_name`, `base_url`처럼 범용적으로 두는 것이 좋다.

## 15. Parser와 Normalizer

LLM에게 JSON을 요청해도 실제 응답에는 설명 문장이나 코드블록이 섞일 수 있다.

따라서 보통은 두 단계를 둔다.

1. Parser: LLM raw text에서 JSON을 꺼낸다.
2. Normalizer: 누락된 필드 기본값, alias, route 이름 등을 표준 형태로 맞춘다.

Parser 예시:

```python
def parse_json_text(text: str) -> dict:
    cleaned = strip_code_fence(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise
```

Normalizer 예시:

```python
def normalize(payload: dict) -> dict:
    route = str(payload.get("route") or "finish").strip().lower()
    if route not in {"finish", "single", "multi"}:
        route = "finish"
    return {
        "route": route,
        "filters": payload.get("filters") or {},
        "warnings": payload.get("warnings") or [],
    }
```

Normalizer는 "복잡한 추론"을 하기보다 "형태를 안전하게 맞추는 일"에 집중하는 것이 좋다.

## 16. 멀티턴 Flow 설계

멀티턴은 이전 턴의 정보를 다음 질문에서 다시 쓰는 구조이다.

Langflow에서는 보통 세 가지를 분리해서 생각한다.

| 정보 | 예시 | 저장 방식 |
| --- | --- | --- |
| 대화 기록 | 사용자 질문, assistant 답변 | Chat memory, Message History |
| 작업 state | 이전 intent, 선택된 dataset, 현재 분석 결과 요약 | JSON state |
| 큰 데이터 | 조회 row 전체, 파일, 긴 계산 결과 | 외부 저장소에 저장하고 reference id만 유지 |

일반적인 연결 구조:

```text
Chat Input
-> Memory Loader
-> Context Builder
-> Prompt Builder
-> LLM Caller
-> Parser / Normalizer
-> Router
-> Work Nodes
-> Final Answer Builder
-> Memory Writer
-> Chat Output
```

멀티턴에서 중요한 점은 session id이다. 같은 session id로 이전 state를 읽고, 답변 후 같은 session id에 새 state를 저장해야 한다.

Langflow 자체의 Message History 컴포넌트를 사용할 수 있으면 먼저 사용한다. 더 오래 보존하거나 데이터가 큰 경우에는 MongoDB, Redis, SQL DB 같은 외부 저장소를 붙이는 편이 안정적이다.

## 17. 멀티턴 state 작성 기준

state에는 다음 턴 판단에 필요한 최소 정보만 넣는다.

좋은 state 예시:

```json
{
  "last_route": "single_retrieval",
  "last_user_question": "show this week's sales by region",
  "current_data_ref": "mongo://analysis_results/abc123",
  "current_data_summary": {
    "row_count": 12,
    "columns": ["region", "sales_amount"]
  },
  "filters": {
    "date": "2026-04-26",
    "process": "DA"
  }
}
```

피해야 할 state 예시:

```json
{
  "all_rows": [{ "...": "..." }, { "...": "..." }]
}
```

전체 row를 계속 들고 다니면 토큰과 화면 출력이 커진다. 다음 판단에는 summary와 reference id만 쓰고, 실제 계산이 필요할 때만 저장소에서 다시 읽는 구조가 좋다.

## 18. ReAct Flow 설계

ReAct는 LLM이 다음 행동을 고르고, 도구를 실행한 결과를 다시 관찰한 뒤, 필요한 만큼 반복해서 답을 만드는 방식이다.

기본 반복 구조:

```text
Question
-> Think / Plan
-> Action 선택
-> Tool 실행
-> Observation 정리
-> 다시 Think / Plan
-> Final Answer
```

Langflow에서 ReAct를 만드는 방법은 두 가지가 있다.

첫 번째는 Langflow의 Agent 계열 컴포넌트와 Tool Mode를 쓰는 방식이다.

- 도구가 될 Custom Component에 `tool_mode=True`를 설정한다.
- Agent 컴포넌트에 LLM과 tools를 연결한다.
- Agent가 필요한 tool을 골라 호출한다.

두 번째는 loop를 직접 보이는 방식이다.

```text
Planner LLM
-> Action Parser
-> Action Router
-> Tool A / Tool B / Tool C
-> Observation Builder
-> Stop Checker
-> Planner LLM 또는 Final Answer
```

반복 횟수는 반드시 제한한다.

```text
max_steps = 3 또는 5
```

업무 시스템에서는 모든 요청을 ReAct로 만들 필요가 없다. 데이터 조회 순서가 명확하고 재현성이 중요한 flow는 고정 DAG가 더 좋고, 도구 선택이 자유로워야 하는 탐색형 작업은 ReAct가 더 잘 맞는다.

## 19. Tool Mode

Custom Component를 Agent의 tool로 쓰려면 tool mode를 켠다.

```python
class SearchTool(Component):
    display_name = "Search Tool"
    name = "SearchTool"
    tool_mode = True
```

Tool로 쓸 노드는 설명이 특히 중요하다. Agent는 tool 설명을 보고 어떤 도구를 사용할지 판단한다.

```python
description = "Search documents by keyword and return short matching snippets."
```

좋은 tool 설명에는 다음이 들어간다.

- 이 tool이 해결하는 일
- 필요한 입력
- 반환하는 값
- 쓰면 안 되는 상황

## 20. 외부 데이터 조회 노드

DB나 API를 호출하는 노드는 연결 정보와 실행 로직을 분리해서 생각한다.

일반 구조:

```text
Input: connection config, query params
Process: connect -> execute -> fetch -> close
Output: success, rows, summary, errors
```

반환 payload 예시:

```json
{
  "success": true,
  "source_name": "orders",
  "rows": [],
  "row_count": 0,
  "summary": "0 rows",
  "errors": []
}
```

DB 연결 문자열, API key, password는 가능한 `SecretStrInput`이나 Langflow variable로 받는다. 코드 안에 고정하지 않는다.

### 20.1 외부 HTTP API에서 데이터 가져오기

외부 API를 호출하는 노드는 DB 조회 노드와 거의 같은 구조로 생각하면 된다.

```text
Input: api_url, api_key, query params, timeout
Process: request -> status check -> json parse -> schema normalize
Output: success, rows 또는 response, summary, errors
```

예를 들어 REST API에서 JSON 데이터를 가져오는 custom node는 다음처럼 만들 수 있다.

```python
import json
from typing import Any, Dict

import requests

from langflow.custom import Component
from langflow.io import MessageTextInput, MultilineInput, SecretStrInput, Output
from langflow.schema import Data


class ExternalApiRetriever(Component):
    display_name = "External API Retriever"
    description = "Call an external HTTP API and return normalized Data."
    icon = "cloud"
    name = "ExternalApiRetriever"

    inputs = [
        MessageTextInput(name="api_url", display_name="API URL", required=True),
        SecretStrInput(name="api_key", display_name="API Key", required=False),
        MultilineInput(name="params_json", display_name="Params JSON", value="{}"),
        MessageTextInput(name="timeout_seconds", display_name="Timeout Seconds", value="15"),
    ]

    outputs = [
        Output(name="api_payload", display_name="API Payload", method="call_api"),
    ]

    def call_api(self) -> Data:
        errors = []
        try:
            params = json.loads(str(self.params_json or "{}"))
        except json.JSONDecodeError as exc:
            message = f"Invalid params_json: {exc}"
            self.status = message
            return Data(data={"success": False, "rows": [], "errors": [message]})

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            timeout = float(self.timeout_seconds or 15)
            response = requests.get(
                str(self.api_url),
                params=params,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            message = f"API request failed: {exc}"
            self.status = message
            return Data(data={"success": False, "rows": [], "errors": [message]})

        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = payload.get("data") or payload.get("rows") or []
        else:
            rows = []

        result = {
            "success": True,
            "source_name": "external_api",
            "rows": rows,
            "row_count": len(rows) if isinstance(rows, list) else 0,
            "raw_response": payload,
            "summary": f"{len(rows) if isinstance(rows, list) else 0} rows",
            "errors": errors,
        }
        self.status = result["summary"]
        return Data(data=result)
```

실제 운영용 노드에서는 다음을 추가로 고려한다.

- `timeout`을 반드시 둔다.
- API 응답이 실패했을 때 `success=False`, `errors=[]` 형태로 다음 노드가 읽을 수 있게 한다.
- API 응답 원문 전체를 LLM prompt에 바로 넣지 않는다.
- 필요한 경우 `rows`, `summary`, `data_ref` 형태로 한 번 더 정리한다.
- 인증정보는 `SecretStrInput`, Langflow variable, 환경변수 중 하나로 받는다.

### 20.2 외부 API 응답을 답변 생성에 쓰는 패턴

외부 API가 꼭 row data만 반환하는 것은 아니다. 검색 API, 사내 지식 API, 티켓 시스템 API처럼 이미 자연어 응답이나 문서 조각을 반환하는 경우도 있다.

이때도 Langflow 안에서는 표준 payload로 감싸는 편이 좋다.

```json
{
  "success": true,
  "source_name": "knowledge_api",
  "response_text": "요약된 API 응답",
  "documents": [
    {
      "title": "문서 제목",
      "url": "https://example.com/doc/1",
      "content": "짧은 근거 문단"
    }
  ],
  "summary": "3 documents found",
  "errors": []
}
```

이 payload는 다음 두 방식 중 하나로 쓸 수 있다.

```text
API Retriever
-> Final Answer Prompt Builder
-> LLM Caller
-> Final Answer
```

또는 API 결과를 추가 분석해야 한다면:

```text
API Retriever
-> Postprocess Router
-> Analysis Node
-> Final Answer Prompt Builder
```

핵심은 "API 응답 원문"과 "LLM에게 줄 요약/근거"를 구분하는 것이다.

### 20.3 MCP를 활용하는 방식

MCP는 외부 도구와 데이터를 LLM 애플리케이션에 연결하기 위한 프로토콜이다. 파일 검색, 문서 저장소, 업무 시스템, DB 조회, 사내 API 같은 기능을 MCP tool 형태로 노출할 수 있다.

Langflow에서 MCP를 활용하는 방식은 보통 세 가지다.

| 방식 | 설명 | 적합한 경우 |
| --- | --- | --- |
| Langflow의 MCP 관련 기본 컴포넌트 사용 | Langflow가 제공하는 MCP 연결 컴포넌트를 사용한다. | 설치한 Langflow 버전에서 MCP 컴포넌트를 지원할 때 |
| MCP Gateway를 HTTP API로 감싸기 | 별도 Python/FastAPI 서비스가 MCP server와 통신하고, Langflow custom node는 HTTP로 gateway만 호출한다. | 운영 안정성과 배포 관리가 중요할 때 |
| Custom Component에서 MCP client 직접 사용 | custom node 안에서 MCP client SDK로 server에 직접 연결한다. | 작은 실험, 내부 PoC |

운영에서는 두 번째 방식인 MCP Gateway 패턴이 가장 단순하게 관리되는 경우가 많다.

```text
Langflow Custom Component
-> HTTP request
-> MCP Gateway API
-> MCP Server / Tool
-> 외부 시스템
```

이렇게 하면 Langflow 노드는 일반 외부 API 호출 노드처럼 유지할 수 있고, MCP server 실행 방식이나 tool 목록 관리는 gateway 쪽에서 담당한다.

### 20.4 MCP Gateway 호출 노드 예시

아래 예시는 MCP tool을 직접 실행하는 코드가 아니라, MCP gateway HTTP API를 호출하는 Langflow custom node 예시다.

```python
import json
from typing import Any, Dict

import requests

from langflow.custom import Component
from langflow.io import MessageTextInput, MultilineInput, SecretStrInput, Output
from langflow.schema import Data


class McpGatewayToolCaller(Component):
    display_name = "MCP Gateway Tool Caller"
    description = "Call an MCP gateway API and return normalized tool results."
    icon = "plug"
    name = "McpGatewayToolCaller"

    inputs = [
        MessageTextInput(name="gateway_url", display_name="Gateway URL", required=True),
        MessageTextInput(name="tool_name", display_name="Tool Name", required=True),
        MultilineInput(name="arguments_json", display_name="Arguments JSON", value="{}"),
        SecretStrInput(name="gateway_api_key", display_name="Gateway API Key", required=False),
        MessageTextInput(name="timeout_seconds", display_name="Timeout Seconds", value="30"),
    ]

    outputs = [
        Output(name="tool_result", display_name="Tool Result", method="call_tool"),
    ]

    def call_tool(self) -> Data:
        try:
            arguments = json.loads(str(self.arguments_json or "{}"))
        except json.JSONDecodeError as exc:
            message = f"Invalid arguments_json: {exc}"
            self.status = message
            return Data(data={"success": False, "errors": [message]})

        headers = {"Content-Type": "application/json"}
        if self.gateway_api_key:
            headers["Authorization"] = f"Bearer {self.gateway_api_key}"

        request_body = {
            "tool_name": str(self.tool_name or "").strip(),
            "arguments": arguments,
        }

        try:
            response = requests.post(
                str(self.gateway_url),
                headers=headers,
                json=request_body,
                timeout=float(self.timeout_seconds or 30),
            )
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            message = f"MCP gateway call failed: {exc}"
            self.status = message
            return Data(data={"success": False, "errors": [message]})

        result = {
            "success": bool(payload.get("success", True)) if isinstance(payload, dict) else True,
            "source_name": "mcp_gateway",
            "tool_name": request_body["tool_name"],
            "arguments": arguments,
            "result": payload.get("result", payload) if isinstance(payload, dict) else payload,
            "documents": payload.get("documents", []) if isinstance(payload, dict) else [],
            "rows": payload.get("rows", []) if isinstance(payload, dict) else [],
            "summary": payload.get("summary", "MCP tool call completed") if isinstance(payload, dict) else "MCP tool call completed",
            "errors": payload.get("errors", []) if isinstance(payload, dict) else [],
        }
        self.status = result["summary"]
        return Data(data=result)
```

Gateway 쪽 API는 다음처럼 단순한 형태로 맞추면 Langflow 노드가 다루기 쉽다.

```json
{
  "tool_name": "search_documents",
  "arguments": {
    "query": "monthly sales policy",
    "limit": 5
  }
}
```

응답도 다음처럼 표준화한다.

```json
{
  "success": true,
  "result": {},
  "documents": [],
  "rows": [],
  "summary": "5 documents found",
  "errors": []
}
```

### 20.5 MCP를 ReAct Agent와 연결할 때

MCP tool을 ReAct 방식으로 쓰고 싶다면 구조는 다음처럼 잡을 수 있다.

```text
User Question
-> Planner / Agent LLM
-> Tool Selection
-> MCP Gateway Tool Caller
-> Observation Builder
-> Planner / Agent LLM
-> Final Answer
```

주의할 점:

- tool 호출 횟수는 `max_steps`로 제한한다.
- 같은 tool을 반복 호출할 때는 중복 query를 막는다.
- tool result 전체를 LLM에 넣지 않고 observation 요약을 만든다.
- MCP tool 실패 시 다음 action을 계속할지, 사용자에게 실패를 알릴지 route를 명확히 둔다.

고정된 업무 flow에서는 모든 단계를 ReAct로 만들 필요가 없다. 어떤 데이터셋을 조회해야 하는지 명확하고 재현성이 중요하면 고정 DAG가 낫고, 사용 가능한 tool이 많고 탐색이 필요한 경우에 ReAct + MCP 구조가 잘 맞는다.

### 20.6 외부 API/MCP 노드 체크리스트

외부 시스템을 호출하는 노드는 아래 항목을 확인한다.

- 인증정보를 코드에 하드코딩하지 않았는가
- timeout이 설정되어 있는가
- 실패 응답이 `success=False`, `errors`로 정리되는가
- API/MCP 원문 응답과 LLM용 요약을 분리했는가
- 다음 노드가 기대하는 key 이름으로 normalize했는가
- 큰 응답은 `data_ref`나 `documents` preview로 줄였는가
- retry가 필요하다면 최대 횟수와 backoff를 제한했는가
- 외부 tool 호출 로그에 민감정보가 남지 않는가
- ReAct와 연결할 경우 tool 호출 최대 횟수를 제한했는가

## 21. 큰 데이터 처리

LLM flow에서 큰 데이터를 그대로 계속 넘기면 세 가지 문제가 생긴다.

- 토큰이 많이 든다.
- 화면이 느려진다.
- 후속 질문에서 prompt가 불필요하게 길어진다.

권장 패턴:

```text
Retriever
-> Large Data Store Writer
-> Summary Builder
-> LLM에는 summary + data_ref만 전달
-> 실제 계산 노드는 data_ref로 원본 재조회
```

예시 payload:

```json
{
  "data_ref": "mongo://analysis_results/abc123",
  "row_count": 12000,
  "columns": ["date", "category", "amount"],
  "preview_rows": [
    {"date": "2026-04-26", "category": "A", "amount": 10}
  ]
}
```

최종 사용자에게 보여줄 데이터는 "분석에 실제로 사용한 최종 가공 데이터"로 제한하는 편이 읽기 쉽다.

## 22. Dynamic Field

입력값에 따라 다른 field를 보여주고 싶으면 `update_build_config`를 사용할 수 있다.

대표 사례:

- provider가 `openai`일 때만 `base_url` 표시
- auth type이 `password`일 때만 password 표시
- mode가 `advanced`일 때만 고급 옵션 표시

개념 예시:

```python
def update_build_config(self, build_config, field_value, field_name=None):
    if field_name == "mode":
        build_config["advanced_option"]["show"] = field_value == "advanced"
    return build_config
```

너무 많은 dynamic field는 화면 이해를 어렵게 만들 수 있다. 필수 기능에만 사용한다.

## 23. 검증 체크리스트

Custom Component를 만든 뒤에는 다음을 확인한다.

- 노드가 Langflow에서 import되는가
- 모든 input 이름과 코드의 `self.xxx`가 일치하는가
- output method 이름이 실제 함수와 일치하는가
- 빈 입력을 넣어도 이해 가능한 오류가 나오는가
- 잘못된 JSON을 넣었을 때 어디가 문제인지 보이는가
- `self.status`가 핵심 결과를 보여주는가
- 다음 노드가 기대하는 payload key가 빠지지 않았는가
- 분기 output에서 inactive 가지가 실수로 실제 처리되지 않는가
- API key나 password가 코드에 하드코딩되어 있지 않은가
- 큰 데이터가 LLM prompt에 그대로 들어가지 않는가

## 24. 재사용 가능한 기본 템플릿

아래 템플릿은 새 노드를 만들 때 출발점으로 쓰기 좋다.

```python
import json
from typing import Any, Dict

from langflow.custom import Component
from langflow.io import DataInput, MessageTextInput, Output
from langflow.schema import Data


def as_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Data):
        return value.data or {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        return json.loads(text)
    return {}


class ExampleComponent(Component):
    display_name = "Example Component"
    description = "Explain what this component does."
    icon = "box"
    name = "ExampleComponent"

    inputs = [
        DataInput(name="payload", display_name="Payload", required=False),
        MessageTextInput(name="option", display_name="Option", value="default"),
    ]

    outputs = [
        Output(name="result", display_name="Result", method="build_result"),
    ]

    def build_result(self) -> Data:
        payload = as_dict(self.payload)
        option = str(self.option or "default").strip()

        result = {
            "success": True,
            "option": option,
            "payload": payload,
            "errors": [],
        }
        self.status = "OK"
        return Data(data=result)
```

## 25. 설계 원칙

좋은 Langflow Custom Component는 다음 성격을 가진다.

- 한 노드는 한 가지 책임에 집중한다.
- 입력과 출력 schema가 예측 가능하다.
- 오류 메시지가 사용자의 다음 행동을 알려준다.
- LLM 호출, prompt 생성, 파싱, 정규화를 한 함수에 몰아넣지 않는다.
- 외부 연결 정보는 코드에 고정하지 않는다.
- 큰 데이터는 저장소에 두고 reference와 summary만 흐르게 한다.
- 멀티턴에서는 session id, memory load, memory write 위치가 명확하다.
- ReAct는 필요한 경우에만 사용하고 반복 횟수를 제한한다.

이 원칙만 지켜도 Langflow canvas에서 flow를 읽고 수정하는 부담이 크게 줄어든다.
