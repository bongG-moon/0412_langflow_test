# 01. Session State Loader 상세 설명

대상 코드: `langflow/data_answer_flow/01_session_state_loader.py`

이 노드는 이전 턴의 state JSON을 읽어서 이번 턴에서 사용할 `agent_state`를 준비한다. 멀티턴 분석에서 “이전 질문의 조건과 현재 데이터 상태를 이어받는 기반”이 되는 노드다.

## 전체 역할

입력으로 이전 state와 현재 사용자 질문을 받는다.

그리고 다음 작업을 한다.

- 이전 state JSON을 dict로 복원한다.
- 이전 state가 없거나 깨져 있으면 새 state를 만든다.
- `turn_id`를 1 증가시킨다.
- 현재 질문을 `pending_user_question`에 넣는다.
- 아직 `chat_history`에는 현재 질문을 추가하지 않는다.

출력 구조는 다음과 같다.

```json
{
  "agent_state": {
    "session_id": "default",
    "turn_id": 1,
    "chat_history": [],
    "context": {},
    "source_snapshots": {},
    "current_data": null,
    "pending_user_question": "오늘 A제품 생산량 알려줘",
    "state_errors": []
  },
  "state": {
    "...": "agent_state와 동일"
  }
}
```

`agent_state`와 `state`는 같은 내용을 담는다. 뒤 노드가 어느 이름을 기대해도 쓸 수 있게 하기 위한 호환 구조다.

## import 영역

```python
from __future__ import annotations
import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict
```

`json`은 state JSON 문자열 파싱에 사용한다. 나머지는 Langflow import 호환과 타입 힌트용이다.

## Langflow 호환 공통부

이 파일도 `_load_attr`, `_FallbackComponent`, `_FallbackInput`, `_FallbackOutput`, `_FallbackData`, `_make_input`, `_make_data` 구조를 사용한다.

이 공통부는 다음 목적을 가진다.

- Langflow 버전별 import 경로 차이를 흡수한다.
- 실제 Langflow 없이도 파일 import와 단위 테스트가 가능하게 한다.
- 출력은 항상 Langflow `Data`와 비슷한 형태로 맞춘다.

```python
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
MessageTextInput = _load_attr(["lfx.io", "langflow.io"], "MessageTextInput", _make_input)
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
```

이 노드는 세 종류의 input을 사용한다.

`DataInput`은 앞 노드의 `Data` 출력을 연결받기 위해 사용한다.

`MessageTextInput`은 짧은 문자열 입력에 사용한다. 여기서는 `session_id`, `user_question`에 사용된다.

`MultilineInput`은 긴 state JSON을 직접 붙여 넣는 예비 입력으로 사용된다.

## payload 추출 함수

```python
def _payload_from_value(value: Any) -> Dict[str, Any]:
```

Langflow input으로 들어온 값을 dict payload로 바꿔준다.

```python
if value is None:
    return {}
```

입력이 없으면 빈 dict다.

```python
if isinstance(value, dict):
    return value
```

이미 dict면 그대로 사용한다.

```python
data = getattr(value, "data", None)
if isinstance(data, dict):
    return data
```

Langflow `Data` 객체라면 `.data`에 실제 payload가 있으므로 그것을 반환한다.

```python
text = getattr(value, "text", None)
if isinstance(text, str):
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}
```

`.text`가 JSON 문자열이면 파싱해서 dict로 반환한다. 파싱 실패 시 빈 dict를 반환한다.

```python
return {}
```

그 외 형태는 처리하지 않는다.

## state 파싱 함수

```python
def _parse_state_text(value: Any) -> Dict[str, Any]:
```

이 함수는 여러 형태로 들어올 수 있는 previous state를 최종 state dict로 복원한다.

```python
if value is None:
    return {}
```

입력이 없으면 빈 dict다.

```python
if isinstance(value, dict):
    return value
```

이미 dict면 그대로 state로 사용한다.

```python
payload = _payload_from_value(value)
```

Langflow `Data` 또는 JSON text에서 payload를 추출한다.

```python
if payload:
    state = payload.get("state")
    if isinstance(state, dict):
        return state
```

payload 안에 `state` dict가 있으면 그것을 최종 state로 사용한다.

```python
if isinstance(payload.get("state_json"), str):
    return _parse_state_text(payload["state_json"])
```

payload 안에 `state_json` 문자열이 있으면 재귀적으로 다시 파싱한다.

```python
return payload
```

특별한 key가 없으면 payload 자체를 state로 본다.

```python
text = str(value or "").strip()
if not text:
    return {}
```

payload로 처리되지 않은 값은 문자열로 보고, 비어 있으면 빈 dict를 반환한다.

```python
try:
    parsed = json.loads(text)
except Exception:
    return {}
```

JSON 문자열로 파싱한다. 실패하면 빈 dict다.

```python
if isinstance(parsed, dict):
    if isinstance(parsed.get("state"), dict):
        return parsed["state"]
    if isinstance(parsed.get("state_json"), str):
        return _parse_state_text(parsed["state_json"])
    return parsed
```

파싱 결과가 dict라면 `state`, `state_json`, dict 자체 순서로 처리한다.

```python
return {}
```

dict가 아니면 state로 인정하지 않는다.

## 기본 state 생성 함수

```python
def _default_state(session_id: str) -> Dict[str, Any]:
```

이전 state가 없을 때 새 state를 만든다.

```python
return {
    "session_id": session_id or "default",
    "turn_id": 0,
    "chat_history": [],
    "context": {},
    "source_snapshots": {},
    "current_data": None,
}
```

`session_id`는 대화 세션 구분용이다.

`turn_id`는 이후 `load_session_state`에서 증가되므로 여기서는 0으로 시작한다.

`chat_history`는 이전 대화 이력이다.

`context`는 이전 질문의 조건, 마지막 required param 같은 요약 상태를 담을 수 있다.

`source_snapshots`는 조회된 원본 데이터의 dataset별 snapshot 정보를 저장하기 위한 공간이다.

`current_data`는 현재 사용 가능한 전처리 또는 분석 결과를 가리키기 위한 공간이다.

## 핵심 함수: load_session_state

```python
def load_session_state(previous_state_json: Any, session_id: str, user_question: str) -> Dict[str, Any]:
```

이 노드의 핵심 로직이다. 이전 state와 현재 질문을 받아 이번 턴 state를 만든다.

```python
state = _parse_state_text(previous_state_json)
```

입력된 previous state를 dict로 복원한다.

```python
if not state:
    state = _default_state(session_id)
```

복원 실패 또는 빈 입력이면 새 state를 만든다.

```python
state = dict(state)
```

원본 state를 직접 수정하지 않도록 얕은 복사한다.

```python
state["session_id"] = str(session_id or state.get("session_id") or "default")
```

현재 입력된 `session_id`를 우선 사용한다. 없으면 기존 state의 session_id를 사용하고, 그것도 없으면 `"default"`를 사용한다.

```python
try:
    state["turn_id"] = int(state.get("turn_id") or 0) + 1
except Exception:
    state["turn_id"] = 1
```

이전 turn_id를 숫자로 바꿔 1 증가시킨다. 값이 이상하면 이번 턴을 1로 둔다.

```python
chat_history = state.get("chat_history")
state["chat_history"] = chat_history if isinstance(chat_history, list) else []
```

chat_history가 list인지 확인한다. 아니면 빈 list로 보정한다.

```python
state["context"] = state.get("context") if isinstance(state.get("context"), dict) else {}
```

context는 dict여야 하므로 아니면 빈 dict로 보정한다.

```python
source_snapshots = state.get("source_snapshots")
state["source_snapshots"] = source_snapshots if isinstance(source_snapshots, dict) else {}
```

source_snapshots도 dict여야 하므로 아니면 빈 dict로 보정한다.

```python
if "current_data" not in state:
    state["current_data"] = None
```

current_data key가 없으면 `None`으로 추가한다.

```python
state["pending_user_question"] = str(user_question or "")
```

현재 사용자 질문을 임시 필드에 저장한다. 아직 chat_history에 넣지는 않는다.

```python
state["state_errors"] = []
```

state 처리 중 에러를 담을 자리를 만든다. 현재 구현에서는 파싱 실패를 조용히 기본 state로 대체하므로 빈 리스트다.

```python
return state
```

이번 턴에서 사용할 agent_state를 반환한다.

## Component 입력 정의

```python
DataInput(
    name="previous_state_payload",
    display_name="Previous State Payload",
    input_types=["Data", "JSON"],
)
```

`Previous State JSON Input` 노드의 출력을 연결받는 입력이다.

```python
MultilineInput(
    name="previous_state_json",
    display_name="Previous State JSON",
    value="",
)
```

앞 노드 없이 직접 state JSON을 붙여 넣을 수 있는 예비 입력이다.

```python
MessageTextInput(
    name="session_id",
    display_name="Session ID",
    value="default",
)
```

세션 구분자다. 현재는 기본값 `"default"`를 주로 사용하면 된다.

```python
MessageTextInput(
    name="user_question",
    display_name="User Question",
)
```

현재 사용자 질문이다. 보통 Chat Input의 텍스트를 연결한다.

## Component 출력 정의

```python
Output(name="agent_state", display_name="Agent State", method="build_agent_state", types=["Data"])
```

출력은 `agent_state` 하나다. 이 출력은 `build_agent_state()` 메서드를 호출한다.

## 실행 메서드

```python
def build_agent_state(self) -> Data:
```

Langflow output 요청 시 실행된다.

```python
previous_state_source = getattr(self, "previous_state_payload", None) or getattr(self, "previous_state_json", "")
```

앞 노드에서 연결된 payload가 있으면 그것을 우선 사용한다. 없으면 직접 입력된 multiline JSON을 사용한다.

```python
state = load_session_state(
    previous_state_source,
    getattr(self, "session_id", "default"),
    getattr(self, "user_question", ""),
)
```

핵심 함수로 이번 턴 state를 생성한다.

```python
return _make_data({"agent_state": state, "state": state}, text=json.dumps(state, ensure_ascii=False))
```

`agent_state`와 `state` 두 이름으로 같은 state를 담아 반환한다. `.text`에는 사람이 확인하기 좋은 JSON 문자열을 넣는다.

## 다음 노드 연결

일반 연결은 다음과 같다.

```text
Previous State JSON Input.previous_state_payload -> Session State Loader.previous_state_payload
Chat Input.message/text -> Session State Loader.user_question
Session State Loader.agent_state -> Build Intent Prompt.agent_state
Session State Loader.agent_state -> Normalize Intent With Domain.agent_state
Session State Loader.agent_state -> Request Type Router.agent_state
```

## 학습 포인트

이 노드는 “state를 안전하게 복원하고 이번 턴용으로 정리하는 노드”다.

중요한 점은 현재 질문을 바로 history에 넣지 않는다는 것이다. 현재 질문은 먼저 intent 추출, domain 정규화, query mode 판단 등에 쓰이고, 최종 응답이 만들어진 뒤에 history로 확정되는 흐름을 염두에 둔 구조다.
