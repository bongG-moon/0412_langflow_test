# 00. Previous State JSON Input 상세 설명

대상 코드: `langflow/data_answer_flow/00_previous_state_json_input.py`

이 노드는 멀티턴 대화를 위해 이전 턴에서 반환된 state JSON을 사용자가 직접 붙여 넣을 수 있게 해주는 입력 노드다. 첫 질문에서는 비워 두고, 두 번째 질문부터 이전 결과의 state JSON을 넣으면 이전 조건과 데이터 상태를 이어받을 수 있다.

## 전체 역할

사용자가 입력한 이전 state JSON 문자열을 `Data` payload로 변환한다.

출력 구조는 다음과 같다.

```json
{
  "previous_state_json": "{...}",
  "state_json": "{...}",
  "is_empty": false,
  "valid_json": true
}
```

`previous_state_json`과 `state_json`은 같은 값을 담는다. 뒤 노드가 둘 중 어느 이름을 기대해도 처리할 수 있게 만든 호환용 구조다.

## import와 공통 fallback 구조

이 파일의 상단 구조는 `Domain JSON Input`과 거의 동일하다.

```python
from __future__ import annotations
import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict
```

`json`은 state 문자열이 정상 JSON인지 확인하는 데 사용한다. `dataclass`, `import_module`, `Any`, `Dict`는 Langflow 버전 호환 fallback 구조를 만들기 위해 사용한다.

```python
def _load_attr(module_names: list[str], attr_name: str, fallback: Any) -> Any:
```

여러 Langflow import 후보를 순서대로 확인하고, 실패하면 fallback 객체를 반환한다.

```python
class _FallbackComponent:
```

Langflow가 없는 환경에서도 코드 import가 가능하도록 하는 최소 Component 대체 클래스다.

```python
@dataclass
class _FallbackInput:
```

Langflow input 선언을 흉내 내는 fallback 클래스다.

```python
@dataclass
class _FallbackOutput:
```

Langflow output 선언을 흉내 내는 fallback 클래스다.

```python
class _FallbackData:
```

Langflow `Data` 객체를 흉내 내는 fallback 클래스다.

이 공통부의 목적은 실제 Langflow 환경과 일반 Python 테스트 환경 양쪽에서 파일이 최대한 깨지지 않게 하는 것이다.

## Langflow 클래스 로딩

```python
Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
```

Langflow의 `Component` 클래스를 가져온다. 실패하면 `_FallbackComponent`를 쓴다.

```python
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)
```

여러 줄 입력, 출력 선언, Data 객체를 Langflow에서 가져온다. 이 노드는 사용자가 긴 state JSON을 붙여 넣어야 하므로 `MultilineInput`을 사용한다.

## Data 생성 함수

```python
def _make_data(payload: Dict[str, Any]) -> Any:
```

payload dict를 Langflow `Data`로 바꾸는 helper다.

```python
try:
    return Data(data=payload)
```

먼저 최신 또는 일반적인 생성 방식을 시도한다.

```python
except TypeError:
    try:
        return Data(payload)
```

생성자 형태가 다른 버전을 대비해 두 번째 방식으로 시도한다.

```python
    except Exception:
        return _FallbackData(data=payload)
```

실패하면 fallback Data 객체를 반환한다.

## Component 선언

```python
class PreviousStateJsonInput(Component):
```

Langflow 노드 본체다.

```python
display_name = "Previous State JSON Input"
description = "Manual state_json input for multi-turn Langflow runs. Leave empty on the first turn."
icon = "History"
name = "PreviousStateJsonInput"
```

화면 이름, 설명, 아이콘, 내부 이름을 정의한다. `History` 아이콘은 이전 대화 상태를 의미한다.

## 입력 정의

```python
inputs = [
    MultilineInput(
        name="previous_state_json",
        display_name="Previous State JSON",
        info="Paste the state_json returned by the previous turn. Leave empty on the first turn.",
        value="",
    ),
]
```

이 노드는 입력창 하나만 가진다.

`name="previous_state_json"`이므로 실행 중에는 `self.previous_state_json`으로 읽힌다.

첫 턴에는 비워도 된다. 비어 있으면 뒤의 `Session State Loader`가 새 state를 만든다.

## 출력 정의

```python
outputs = [
    Output(name="previous_state_payload", display_name="Previous State Payload", method="build_payload", types=["Data"]),
]
```

출력은 `previous_state_payload` 하나다.

`method="build_payload"`이므로 output이 필요할 때 `build_payload()`가 호출된다.

## 실행 메서드

```python
def build_payload(self) -> Data:
```

state 입력을 payload로 만드는 메서드다.

```python
text = str(getattr(self, "previous_state_json", "") or "").strip()
```

입력값을 안전하게 문자열로 가져온다. 값이 없거나 `None`이어도 빈 문자열로 처리한다.

```python
valid_json = False
```

JSON 유효성 기본값이다.

```python
if text:
    try:
        json.loads(text)
        valid_json = True
    except Exception:
        valid_json = False
```

텍스트가 있으면 JSON 파싱을 시도한다. 성공하면 `valid_json=True`, 실패하면 `False`다.

이 노드는 JSON이 깨졌다고 바로 중단하지 않는다. state 복구는 다음 노드인 `Session State Loader`에서 최종 처리한다.

```python
payload = {
    "previous_state_json": text,
    "state_json": text,
    "is_empty": not bool(text),
    "valid_json": valid_json,
}
```

표준 payload를 만든다.

`previous_state_json`은 의미가 명확한 이름이고, `state_json`은 더 짧은 호환용 이름이다.

```python
return _make_data(payload)
```

payload를 Langflow `Data`로 감싸 반환한다.

## 다음 노드 연결

일반 연결은 다음과 같다.

```text
Previous State JSON Input.previous_state_payload -> Session State Loader.previous_state_payload
```

## 학습 포인트

이 노드는 `Domain JSON Input`과 구조가 거의 같다. 차이는 다루는 문자열의 의미뿐이다.

`Domain JSON Input`은 도메인 지식 JSON을 넘기고, `Previous State JSON Input`은 이전 대화 상태 JSON을 넘긴다. 둘 다 “사용자 입력 문자열을 Langflow Data payload로 포장하는 입력 노드” 패턴이다.
