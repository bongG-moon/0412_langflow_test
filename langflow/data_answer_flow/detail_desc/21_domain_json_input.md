# 21. Domain JSON Input 상세 설명

대상 코드: `langflow/data_answer_flow/00_domain_json_input.py`

이 노드는 Langflow 화면에서 사용자가 Domain JSON을 직접 붙여 넣을 수 있게 해주는 입력 전용 커스텀 노드다. 추후에는 Domain Authoring Flow 또는 MongoDB에서 도메인 정보를 가져오겠지만, 현재 Phase 1에서는 수동 JSON 입력이 필요하므로 이 노드가 그 입구 역할을 한다.

## 전체 역할

사용자가 입력한 긴 JSON 문자열을 받아 다음 노드가 처리하기 쉬운 `Data` 형태로 감싼다.

출력 payload는 다음 형태다.

```json
{
  "domain_json_text": "{...}",
  "is_empty": false,
  "valid_json": true
}
```

`domain_json_text`는 사용자가 붙여 넣은 원본 Domain JSON 문자열이다. 중복을 줄이기 위해 이 입력 노드는 표준 key로 `domain_json_text`만 출력한다.

뒤 노드인 `Domain JSON Loader`는 다른 flow와의 호환을 위해 `domain_json`, `text` key도 fallback으로 읽을 수 있지만, 이 노드에서는 만들지 않는다.

## import 영역

```python
from __future__ import annotations
```

타입 힌트를 지연 평가한다. `list[str]`, `Dict[str, Any] | None` 같은 타입 표현을 더 안정적으로 쓰기 위한 설정이다.

```python
import json
```

입력 문자열이 정상 JSON인지 확인할 때 사용한다.

```python
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict
```

`dataclass`는 fallback input/output 클래스를 단순하게 선언하기 위해 사용한다. `import_module`은 Langflow 버전에 따라 달라지는 import 경로를 동적으로 시도하기 위해 사용한다. `Any`, `Dict`는 타입 힌트다.

## Langflow 호환 로딩 함수

```python
def _load_attr(module_names: list[str], attr_name: str, fallback: Any) -> Any:
    for module_name in module_names:
        try:
            return getattr(import_module(module_name), attr_name)
        except Exception:
            continue
    return fallback
```

이 함수는 여러 모듈 후보에서 특정 클래스나 함수를 찾는다.

`module_names`에는 `"lfx.io"`, `"langflow.io"` 같은 후보 경로가 들어간다. Langflow 버전마다 실제 import 경로가 다를 수 있기 때문이다.

`attr_name`은 찾으려는 이름이다. 예를 들어 `"MultilineInput"`이면 해당 모듈 안의 `MultilineInput` 클래스를 찾는다.

`fallback`은 모든 import가 실패했을 때 대신 쓸 객체다.

`for module_name in module_names:`는 후보 모듈을 순서대로 확인한다.

`import_module(module_name)`은 문자열로 된 모듈명을 실제 Python 모듈로 import한다.

`getattr(..., attr_name)`은 import한 모듈 안에서 원하는 이름의 객체를 꺼낸다.

성공하면 즉시 `return`하므로 뒤 후보는 확인하지 않는다.

실패하면 `except Exception`에서 잡고 `continue`로 다음 후보를 시도한다.

모든 후보가 실패하면 마지막 줄에서 `fallback`을 반환한다.

## fallback 클래스들

```python
class _FallbackComponent:
    display_name = ""
    description = ""
    icon = ""
    name = ""
    inputs = []
    outputs = []
    status = ""
```

Langflow의 `Component` 클래스를 불러오지 못했을 때 대신 사용하는 최소 클래스다. 실제 Langflow 노드 기능을 완전히 흉내 내는 목적이 아니라, 로컬에서 파일을 import하거나 테스트할 때 에러를 줄이기 위한 안전장치다.

```python
@dataclass
class _FallbackInput:
    name: str
    display_name: str
    info: str = ""
    value: Any = None
    advanced: bool = False
    tool_mode: bool = False
    input_types: list[str] | None = None
```

Langflow input 클래스가 없을 때 대신 쓰는 구조다.

`name`은 코드에서 접근하는 내부 변수명이다. `display_name`은 Langflow 화면에 보이는 이름이다. `info`는 설명 문구다. `value`는 기본값이다. `advanced`는 고급 옵션 여부다. `tool_mode`는 Tool 모드 사용 여부다. `input_types`는 연결 가능한 데이터 타입 목록이다.

```python
@dataclass
class _FallbackOutput:
    name: str
    display_name: str
    method: str
    group_outputs: bool = False
    types: list[str] | None = None
    selected: str | None = None
```

Langflow output 클래스가 없을 때 대신 쓰는 구조다. `method`가 중요하다. 해당 output이 실행될 때 어떤 메서드를 호출할지 정한다.

```python
class _FallbackData:
    def __init__(self, data: Dict[str, Any] | None = None, text: str | None = None):
        self.data = data or {}
        self.text = text
```

Langflow의 `Data` 객체를 간단히 흉내 낸다. 실제 Langflow `Data`도 보통 `.data`와 `.text`를 가지고 있기 때문에, fallback도 같은 모양으로 맞춘다.

## Langflow 클래스 연결

```python
Component = _load_attr(
    ["lfx.custom.custom_component.component", "lfx.custom", "langflow.custom"],
    "Component",
    _FallbackComponent,
)
```

실제 Langflow `Component` 클래스를 찾는다. 최신 계열의 `lfx` 경로를 먼저 찾고, 구버전 계열의 `langflow` 경로를 나중에 찾는다. 실패하면 `_FallbackComponent`를 사용한다.

```python
MultilineInput = _load_attr(["lfx.io", "langflow.io"], "MultilineInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)
```

각각 Langflow의 입력 컴포넌트, 출력 컴포넌트, 데이터 객체를 불러온다. 실패하면 fallback을 사용한다.

## Data 생성 함수

```python
def _make_data(payload: Dict[str, Any]) -> Any:
    try:
        return Data(data=payload)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _FallbackData(data=payload)
```

payload dict를 Langflow `Data` 객체로 감싼다.

먼저 `Data(data=payload)` 방식으로 생성한다. Langflow 버전에 따라 이 생성자를 지원하지 않으면 `TypeError`가 날 수 있다.

그 경우 `Data(payload)` 방식으로 다시 시도한다.

그것도 실패하면 `_FallbackData`를 만들어 반환한다.

## Component 선언

```python
class DomainJsonInput(Component):
```

Langflow 커스텀 노드 클래스다. `Component`를 상속해야 Langflow가 이 클래스를 노드로 인식한다.

```python
display_name = "Domain JSON Input"
description = "Manual Domain JSON text input used before MongoDB domain loading is available."
icon = "Braces"
name = "DomainJsonInput"
```

`display_name`은 화면에 보이는 노드 이름이다. `description`은 노드 설명이다. `icon`은 Langflow UI 아이콘이다. `name`은 내부 식별자다.

## 입력 정의

```python
inputs = [
    MultilineInput(
        name="domain_json_text",
        display_name="Domain JSON Text",
        info="Paste the standard Domain JSON document or a bare domain object.",
        value="",
    ),
]
```

사용자에게 여러 줄 텍스트 입력창을 제공한다.

`name="domain_json_text"`이므로 실행 메서드에서는 `self.domain_json_text` 또는 `getattr(self, "domain_json_text", "")`로 값을 읽는다.

`value=""`는 기본값을 빈 문자열로 둔다는 뜻이다.

## 출력 정의

```python
outputs = [
    Output(name="domain_json_payload", display_name="Domain JSON Payload", method="build_payload", types=["Data"]),
]
```

출력 포트는 하나다.

`name="domain_json_payload"`는 뒤 노드에서 보이는 output 이름이다.

`method="build_payload"`는 이 output을 만들 때 `build_payload()` 메서드를 호출한다는 뜻이다.

`types=["Data"]`는 출력 타입이 Langflow `Data`임을 의미한다.

## 실행 메서드

```python
def build_payload(self) -> Data:
```

Langflow가 output을 요청하면 실행되는 메서드다.

```python
text = str(getattr(self, "domain_json_text", "") or "").strip()
```

입력창에 들어온 값을 가져온다. 값이 없으면 빈 문자열로 처리한다. `strip()`으로 앞뒤 공백을 제거한다.

```python
valid_json = False
```

입력값이 정상 JSON인지 여부를 저장할 기본값이다.

```python
if text:
    try:
        json.loads(text)
        valid_json = True
    except Exception:
        valid_json = False
```

입력 문자열이 비어 있지 않으면 JSON 파싱을 시도한다. 성공하면 `valid_json=True`, 실패하면 `False`다.

이 노드는 JSON이 깨졌다고 즉시 에러를 발생시키지 않는다. 대신 `valid_json` flag를 payload에 넣어 뒤 노드가 판단할 수 있게 한다.

```python
payload = {
    "domain_json_text": text,
    "is_empty": not bool(text),
    "valid_json": valid_json,
}
```

뒤 노드로 넘길 표준 payload를 만든다.

`domain_json_text`는 입력 원문이다. `is_empty`는 입력이 비어 있는지 여부다. `valid_json`은 JSON 파싱 가능 여부다.

```python
return _make_data(payload)
```

payload를 Langflow `Data`로 감싸 반환한다. `.data`에는 payload dict만 들어가며, 원본 JSON 문자열은 `domain_json_text` key로 확인한다.

## 다음 노드 연결

이 노드는 보통 다음처럼 연결한다.

```text
Domain JSON Input.domain_json_payload -> Domain JSON Loader.domain_json_payload
```

## 학습 포인트

이 노드는 Langflow custom node의 가장 단순한 입력 노드 패턴이다.

입력값을 읽고, 간단히 검증하고, 표준 payload dict로 만든 뒤, `_make_data()`로 감싸서 반환한다. 이후 복잡한 노드들도 이 기본 구조를 확장한 형태로 보면 된다.
