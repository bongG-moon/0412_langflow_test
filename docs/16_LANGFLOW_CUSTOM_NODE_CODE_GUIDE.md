# Langflow Custom Node Code Guide

이 문서는 Langflow Custom Component, 즉 Custom Node 코드를 처음 작성하는 사람이 기본 구조를 이해할 수 있도록 정리한 학습 자료이다.

제조 데이터 분석 Agent 구현 문서와는 별개로, Langflow 커스텀 노드 자체의 코드 작성 방식, 입력과 출력 타입, 자주 쓰는 옵션, 실행 흐름, 실수하기 쉬운 지점을 설명한다.

기준 문서는 Langflow 공식 문서의 Custom Components, Components overview, Tool mode 설명이다. Langflow 버전에 따라 import path나 일부 input class 이름은 달라질 수 있다. 현재 공식 문서 기준으로는 Langflow 1.7 이후 `lfx` import path가 권장되고, 이전 `langflow` import path도 호환된다.

## 1. Custom Node의 기본 개념

Langflow에서 하나의 노드는 Python class 하나로 생각하면 된다.

보통 하나의 Custom Component는 다음 요소로 구성된다.

```text
Python class
  -> Component를 상속
  -> display_name, description, icon, name 같은 메타데이터 선언
  -> inputs 리스트로 화면 입력 필드와 입력 포트 선언
  -> outputs 리스트로 출력 포트 선언
  -> Output.method에 연결된 실제 함수 구현
```

Langflow는 이 class 정보를 읽어서 canvas에 노드를 보여준다.

사용자가 canvas에서 값을 입력하거나 노드를 연결하면, Langflow는 input 값을 `self.<input_name>` 형태로 component instance에 넣어준다. 이후 output이 실행될 때 `Output(method="...")`에 적힌 메서드를 호출한다.

## 2. 가장 작은 기본 코드

아래는 JSON 같은 구조화 데이터를 받아서 다시 `Data`로 내보내는 가장 작은 예시이다.

```python
from __future__ import annotations

from typing import Any

from lfx.custom import Component
from lfx.io import DataInput, MessageTextInput, Output
from lfx.schema import Data


class ExampleDataNode(Component):
    display_name = "Example Data Node"
    description = "Minimal custom component example."
    icon = "Box"
    name = "ExampleDataNode"

    inputs = [
        MessageTextInput(
            name="title",
            display_name="Title",
            info="Short label typed by the user.",
            value="hello",
        ),
        DataInput(
            name="payload",
            display_name="Payload",
            info="JSON/Data payload from another node.",
            input_types=["Data", "JSON"],
        ),
    ]

    outputs = [
        Output(
            name="result",
            display_name="Result",
            method="build_result",
        ),
    ]

    def build_result(self) -> Data:
        title = str(self.title or "")
        payload = self.payload
        return Data(data={"title": title, "payload": _payload_from_value(payload)})


def _payload_from_value(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data
    return {}
```

핵심은 다음 네 가지다.

- `class ExampleDataNode(Component)`: Langflow node class이다.
- `inputs = [...]`: 화면에 보일 입력 필드와 연결 가능한 입력 포트를 정의한다.
- `outputs = [...]`: 화면에 보일 출력 포트를 정의한다.
- `def build_result(self) -> Data`: output이 호출할 실제 실행 함수이다.

## 3. Import Path와 버전 호환

공식 문서 기준으로 새 Langflow에서는 보통 아래 import를 사용한다.

```python
from lfx.custom import Component
from lfx.io import DataInput, MessageTextInput, Output
from lfx.schema import Data
```

구버전 또는 일부 배포 환경에서는 아래 import가 쓰이기도 한다.

```python
from langflow.custom import Component
from langflow.io import DataInput, MessageTextInput, Output
from langflow.schema import Data
```

우리 프로젝트의 Stand Alone 노드들은 환경 차이를 줄이기 위해 `import_module`로 `lfx`와 `langflow` 양쪽을 시도하는 fallback 구조를 사용한다.

간단한 개인용 노드라면 공식 문서 스타일의 `lfx` import만 써도 된다. 여러 Langflow 버전에서 복사해서 돌릴 가능성이 있으면 fallback import를 고려한다.

## 4. Class 메타데이터

Custom Component class에는 보통 다음 class-level 속성을 둔다.

```python
class MyNode(Component):
    display_name = "My Node"
    description = "What this node does."
    icon = "Box"
    name = "MyNode"

    inputs = []
    outputs = []
```

각 속성의 의미는 다음과 같다.

| 속성 | 의미 |
| --- | --- |
| `display_name` | Langflow UI에 보이는 노드 이름 |
| `description` | 노드 설명 |
| `icon` | UI 아이콘 이름 |
| `name` | 내부 component 이름, 보통 class명과 비슷하게 둔다 |
| `inputs` | 입력 필드와 입력 포트 목록 |
| `outputs` | 출력 포트 목록 |
| `status` | 실행 중/실행 후 UI에 보여줄 상태 메시지 |

`display_name`은 사람이 읽는 이름이고, `name`은 내부 식별자에 가깝다. 보통 `name`에는 공백 없이 PascalCase를 쓴다.

## 5. 입력 선언 구조

입력은 `inputs` 리스트 안에 선언한다.

```python
inputs = [
    MessageTextInput(
        name="user_question",
        display_name="User Question",
        info="Current user question.",
    ),
    DataInput(
        name="agent_state",
        display_name="Agent State",
        info="State payload from previous node.",
        input_types=["Data", "JSON"],
    ),
]
```

Langflow가 실행될 때 `name` 값이 instance attribute가 된다.

위 예시에서는 코드 안에서 다음처럼 접근한다.

```python
question = self.user_question
state = self.agent_state
```

## 6. 자주 쓰는 Input 타입

아래는 Custom Component에서 자주 쓰는 입력 타입이다.

| Input class | 용도 | 예시 |
| --- | --- | --- |
| `MessageTextInput` | 짧은 텍스트, 질문, 이름, 모델명 | 사용자 질문, session id |
| `MultilineInput` | 긴 텍스트 | JSON 붙여넣기, prompt template |
| `DataInput` | 다른 노드의 `Data`/`JSON` payload | domain payload, agent state |
| `DataFrameInput` | 표 형태 데이터 | pandas table, CSV 결과 |
| `SecretStrInput` | 비밀값 | API key |
| `IntInput` | 정수 | top n, timeout seconds |
| `FloatInput` | 실수 | temperature |
| `BoolInput` | true/false | debug mode, approved |
| `DropdownInput` | 선택지 | mode, provider |
| `FileInput` | 파일 경로 또는 업로드 | CSV, JSON file |
| `CodeInput` | 코드 입력 | pandas code, python snippet |
| `HandleInput` | 특정 타입 객체 연결 | model, embedding, tool 같은 handle |

실제 사용 가능한 input class는 Langflow 버전에 따라 조금씩 다를 수 있다.

## 7. Input 공통 옵션

많은 input class에서 공통적으로 쓰는 옵션은 다음과 같다.

| 옵션 | 의미 |
| --- | --- |
| `name` | 코드에서 `self.<name>`으로 접근할 내부 이름 |
| `display_name` | UI에 보이는 라벨 |
| `info` | 입력 설명 |
| `value` | 기본값 |
| `advanced` | true면 고급 설정 영역에 숨김 |
| `required` | 필수 입력 여부 |
| `input_types` | 이 입력 포트가 받을 수 있는 연결 타입 |
| `is_list` | 여러 값을 리스트로 받을지 여부 |
| `tool_mode` | Agent tool로 노출할 때 사용할 입력인지 여부 |
| `dynamic` | 입력 필드가 동적으로 바뀔 수 있는지 여부 |
| `real_time_refresh` | 값 변경 시 `update_build_config`를 즉시 호출할지 여부 |
| `options` | `DropdownInput` 선택지 |

예시:

```python
DropdownInput(
    name="query_mode",
    display_name="Query Mode",
    options=["auto", "retrieval", "followup_transform"],
    value="auto",
)
```

```python
DataInput(
    name="domain_payload",
    display_name="Domain Payload",
    input_types=["Data", "JSON"],
    required=True,
)
```

## 8. DataInput의 input_types

`DataInput`은 다른 노드 output과 연결되는 경우가 많다. 연결 가능 여부는 UI에서 포트 타입으로 판단된다.

JSON처럼 구조화된 payload를 주고받는 노드는 보통 아래처럼 선언한다.

```python
DataInput(
    name="payload",
    display_name="Payload",
    input_types=["Data", "JSON"],
)
```

`Data`와 `JSON`을 같이 넣는 이유는 Langflow 버전이나 노드 종류에 따라 구조화 데이터 포트가 `Data` 또는 `JSON`으로 표시될 수 있기 때문이다.

우리 프로젝트에서는 custom node 간 dict payload 전달을 안정적으로 하기 위해 `input_types=["Data", "JSON"]`를 기본으로 사용한다.

## 9. Output 선언 구조

출력은 `outputs` 리스트 안에 선언한다.

```python
outputs = [
    Output(
        name="agent_state",
        display_name="Agent State",
        method="build_agent_state",
    ),
]
```

여기서 중요한 것은 `method`이다.

`method="build_agent_state"`라고 쓰면, class 안에 같은 이름의 메서드가 있어야 한다.

```python
def build_agent_state(self) -> Data:
    return Data(data={"state": {}})
```

메서드 이름이 틀리면 Langflow가 output 실행 시 해당 함수를 찾지 못한다.

## 10. Output 타입은 어떻게 정해지는가

Langflow에서 output 포트 타입은 주로 output 메서드의 반환 타입 annotation으로 판단된다.

권장 형태:

```python
def build_payload(self) -> Data:
    return Data(data={"key": "value"})
```

좋지 않은 형태:

```python
def build_payload(self) -> Any:
    return Data(data={"key": "value"})
```

실제로 반환은 `Data`여도 annotation이 `Any`이면 UI에서 포트 타입을 제대로 판단하지 못해 연결이 막힐 수 있다.

자주 쓰는 반환 타입은 다음과 같다.

| 반환 타입 | Langflow 의미 | 연결 대상 |
| --- | --- | --- |
| `Data` | JSON-like 구조화 데이터 | `DataInput`, JSON/Data 포트 |
| `Message` | 채팅 메시지 | Chat Output, Message 입력 |
| `DataFrame` | 표 데이터 | `DataFrameInput`, Table 포트 |
| `str`, `int`, `bool` | primitive 값 | 단순 입력, 일부 포트 |

일반적으로 custom node 사이에서는 plain `dict`를 그대로 반환하기보다 `Data(data=...)`로 감싸는 것이 안전하다.

## 11. Data 객체 사용법

`Data`는 JSON-like dict를 담는 wrapper로 생각하면 된다.

```python
return Data(
    data={
        "query_mode": "retrieval",
        "required_params": {"date": "2026-04-18"},
    }
)
```

텍스트 표현도 같이 넣고 싶으면 버전에 따라 `text` 필드를 함께 사용할 수 있다.
다만 현재 프로젝트 노드들은 중복을 줄이기 위해 결과를 거의 모두 `data`에만 담는다.

```python
return Data(
    data={"answer": "오늘 생산량은 100입니다."},
    text="오늘 생산량은 100입니다.",
)
```

다음 노드에서 받을 때는 환경에 따라 값이 `Data`, `dict`, 문자열 중 하나처럼 들어올 수 있다. 그래서 robust parser를 두는 것이 좋다.

```python
import json
from typing import Any


def payload_from_value(value: Any) -> dict:
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

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    return {}
```

우리 프로젝트의 Langflow 노드들도 이 패턴을 사용한다.

## 12. 여러 Output과 group_outputs

한 노드가 여러 output을 가질 수 있다.

```python
outputs = [
    Output(name="success", display_name="Success", method="success_result"),
    Output(name="error", display_name="Error", method="error_result"),
]
```

하지만 기본값인 `group_outputs=False`에서는 Langflow UI가 output들을 하나의 선택형 output처럼 보여줄 수 있다. 즉, 모든 output 포트가 동시에 보이지 않을 수 있다.

여러 output을 동시에 연결해야 한다면 반드시 `group_outputs=True`를 넣는다.

```python
outputs = [
    Output(
        name="route_payload",
        display_name="Route Payload",
        method="build_route",
        group_outputs=True,
    ),
    Output(
        name="data_question",
        display_name="Data Question",
        method="data_question_branch",
        group_outputs=True,
    ),
]
```

구분 기준은 다음과 같다.

| 상황 | 권장 |
| --- | --- |
| 여러 output 중 사용자가 하나만 선택하면 됨 | `group_outputs=False` 또는 생략 |
| 여러 output을 동시에 다른 노드에 연결해야 함 | 각 `Output`에 `group_outputs=True` |
| 라우터처럼 branch output을 여러 개 노출해야 함 | 각 branch output에 `group_outputs=True` |

우리 프로젝트에서는 `Request Type Router`처럼 여러 branch를 동시에 보여야 하는 노드에서 이 설정을 사용한다.

## 13. 출력 메서드 안에서 self.status 사용

실행 결과를 UI에 간단히 표시하고 싶으면 `self.status`를 설정한다.

```python
def build_result(self) -> Data:
    rows = [{"a": 1}, {"a": 2}]
    self.status = f"Built {len(rows)} rows"
    return Data(data={"rows": rows})
```

긴 debug 정보는 `self.status`에 전부 넣기보다 output payload의 `debug` key에 넣는 편이 좋다.

## 14. _pre_run_setup과 ctx

노드 실행 전에 초기화가 필요하면 `_pre_run_setup`을 사용할 수 있다.

```python
def _pre_run_setup(self):
    if not hasattr(self, "_initialized"):
        self._initialized = True
        self.ctx["run_count"] = 0
```

`self.ctx`는 같은 component instance 안에서 output method 간 공유할 값을 둘 때 사용할 수 있다.

다만 초보 단계에서는 너무 많이 쓰지 않는 것이 좋다. 대부분의 flow에서는 input payload를 받아 output payload를 만드는 순수 함수형 구조가 더 이해하기 쉽다.

## 15. run, _run, output method 중 무엇을 써야 하나

일반적인 Custom Node는 `Output(method="...")`에 연결된 output method만 구현하면 충분하다.

권장:

```python
outputs = [
    Output(name="result", display_name="Result", method="build_result"),
]

def build_result(self) -> Data:
    return Data(data={})
```

`run` 또는 `_run` override는 전체 실행 흐름을 직접 제어해야 할 때 사용한다. 입문자나 유지보수성이 중요한 flow에서는 output method 방식이 더 명확하다.

## 16. Dynamic Field와 update_build_config

입력 값에 따라 다른 입력 필드를 보이게 하거나 숨기고 싶을 때 dynamic field를 사용한다.

예를 들어 `mode`가 `api`일 때만 `api_key`를 보이게 할 수 있다.

개념 예시:

```python
inputs = [
    DropdownInput(
        name="mode",
        display_name="Mode",
        options=["manual", "api"],
        value="manual",
        real_time_refresh=True,
    ),
    SecretStrInput(
        name="api_key",
        display_name="API Key",
        advanced=True,
    ),
]

def update_build_config(self, build_config, field_value, field_name=None):
    if field_name == "mode":
        build_config["api_key"]["advanced"] = field_value != "api"
    return build_config
```

이 기능은 편리하지만 초보 단계에서는 flow를 복잡하게 만들 수 있다. 먼저 고정 input으로 구현하고, 실제로 UI 단순화가 필요할 때 도입하는 것을 권장한다.

## 17. Tool Mode

`tool_mode=True`를 input에 넣으면 해당 component를 Agent가 사용할 tool로 노출할 수 있다.

```python
MessageTextInput(
    name="input_text",
    display_name="Input Text",
    tool_mode=True,
)
```

공식 문서 기준으로 Tool Mode는 `DataInput`, `DataFrameInput`, `PromptInput`, `MessageTextInput`, `MultilineInput`, `DropdownInput` 같은 입력 타입에서 사용할 수 있다.

우리 제조 분석 flow의 Phase 1에서는 노드를 tool로 쓰기보다 canvas 단계별 흐름을 명확히 보여주는 것이 우선이므로, Tool Mode는 당장 필수는 아니다.

### 17.1 Tool Mode 예시

아래 예시는 Agent가 필요할 때 호출할 수 있는 간단한 dataset 설명 조회 도구이다.

핵심은 `dataset_key` 입력에 `tool_mode=True`가 붙어 있다는 점이다. 이렇게 하면 Agent가 tool call을 만들 때 `dataset_key` 값을 argument로 채울 수 있다.

```python
from __future__ import annotations

from lfx.custom import Component
from lfx.io import MessageTextInput, Output
from lfx.schema import Data


DATASET_CATALOG = {
    "production": {
        "display_name": "생산 데이터",
        "required_params": ["date"],
        "columns": ["date", "product", "process", "line", "qty"],
    },
    "target": {
        "display_name": "목표 데이터",
        "required_params": ["date"],
        "columns": ["date", "product", "process", "line", "target_qty"],
    },
}


class DatasetCatalogTool(Component):
    display_name = "Dataset Catalog Tool"
    description = "Return dataset metadata by dataset key."
    icon = "Database"
    name = "DatasetCatalogTool"

    inputs = [
        MessageTextInput(
            name="dataset_key",
            display_name="Dataset Key",
            info="Dataset key such as production or target.",
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(
            name="dataset_info",
            display_name="Dataset Info",
            method="lookup_dataset",
        ),
    ]

    def lookup_dataset(self) -> Data:
        dataset_key = str(self.dataset_key or "").strip()
        dataset = DATASET_CATALOG.get(dataset_key)
        if not dataset:
            return Data(
                data={
                    "found": False,
                    "dataset_key": dataset_key,
                    "available_dataset_keys": sorted(DATASET_CATALOG),
                }
            )

        return Data(
            data={
                "found": True,
                "dataset_key": dataset_key,
                "dataset": dataset,
            }
        )
```

Agent가 이 tool을 사용할 수 있는 상황은 다음과 같다.

```text
User: 생산량을 조회하려면 어떤 파라미터가 필요해?
Agent: Dataset Catalog Tool을 dataset_key=production으로 호출
Tool Result: production 데이터는 date 필수 파라미터와 qty 컬럼을 가진다.
```

Tool Mode를 쓸 때 주의할 점은 다음과 같다.

- tool argument로 받을 입력에만 `tool_mode=True`를 붙인다.
- API key, 내부 debug flag, 큰 JSON payload처럼 Agent가 직접 채우면 안 되는 값에는 붙이지 않는다.
- output method 반환 타입은 여전히 `-> Data`처럼 명확하게 적는다.
- tool 설명인 `description`, input의 `display_name`, `info`를 구체적으로 작성해야 Agent가 올바른 argument를 넣기 쉽다.
- 너무 큰 결과를 반환하면 Agent가 다음 reasoning에서 사용하기 어려우므로 필요한 정보만 반환한다.

## 18. Stand Alone 노드 작성 원칙

우리 Langflow 구현은 Stand Alone 방식을 목표로 한다.

즉, 하나의 custom component 파일을 복사해서 Langflow에 넣어도 동작해야 한다.

권장:

```text
one_node.py
  -> 필요한 helper 함수 포함
  -> Component class 포함
  -> 외부 프로젝트 모듈 import 없음
```

피해야 할 방식:

```python
from manufacturing_agent.services.runtime_service import run_something
```

이 방식은 기존 LangGraph 구조에 의존하게 되어 Langflow flow를 독립적으로 배포하거나 이해하기 어렵다.

대신 작은 helper는 노드 파일 내부에 둔다.

```python
def _normalize_text(text: str) -> str:
    return " ".join(str(text or "").split()).lower()
```

단, 완전히 같은 helper가 너무 많이 반복되면 장기적으로는 Langflow용 공통 패키지를 만들 수 있다. 하지만 현재 요구사항은 Stand Alone이므로 파일 간 import는 피한다.

## 19. 좋은 Custom Node의 기준

좋은 노드는 다음 특징을 가진다.

- 하나의 명확한 역할만 가진다.
- input과 output payload key가 문서화되어 있다.
- output method 반환 타입이 `-> Data`, `-> Message`, `-> DataFrame`처럼 명확하다.
- 다른 노드와 연결할 input type이 명확하다.
- LLM prompt 생성, LLM 호출, JSON parsing, validation을 한 노드에 몰아넣지 않는다.
- 에러가 발생해도 downstream이 이해할 수 있는 payload를 반환한다.
- `self.status` 또는 `debug` payload로 최소한의 상태를 보여준다.

좋지 않은 노드는 다음과 같다.

- 하나의 노드가 prompt 생성, LLM 호출, 데이터 조회, pandas 실행, 답변 생성을 모두 처리한다.
- output method가 `-> Any`로 되어 있어 Langflow UI가 포트 타입을 판단하기 어렵다.
- 여러 output을 동시에 연결해야 하는데 `group_outputs=True`가 없다.
- downstream에서 필요한 key 이름이 매번 다르다.
- 기존 repo 코드를 import해서 Langflow 환경에서만 깨진다.

## 20. 우리 프로젝트에서 쓰는 기본 패턴

현재 `langflow/data_answer_flow` 노드는 다음 패턴을 기본으로 한다.

```text
Input Node
  -> Data(data={...})

Loader Node
  -> DataInput(input_types=["Data", "JSON"])
  -> payload normalize
  -> Data(data={standard_payload})

Prompt Builder
  -> DataInput several payloads
  -> prompt string 생성
  -> Data(data={"prompt": prompt})

LLM Caller
  -> prompt payload
  -> per-node api key/model/provider settings
  -> Data(data={"llm_text": "...", "parsed": maybe})

Parser/Normalizer
  -> LLM output
  -> schema 보정
  -> Data(data={standard_payload})

Router/Decider
  -> standard payload
  -> branch or decision payload
```

이 구조를 유지하면 Langflow canvas에서 각 노드의 역할을 눈으로 따라가기 쉽다.

아래는 같은 내용을 조금 더 쉽게 풀어쓴 설명이다.

### 20.1 Input Node

Input Node는 사용자가 직접 넣는 값을 Langflow 연결용 `Data`로 포장하는 노드이다.

예를 들어 `Previous State JSON Input`은 사용자가 이전 턴의 상태 JSON을 붙여넣으면, 다음 노드가 읽기 쉬운 이름을 붙여서 내보낸다.

입력 예시:

```text
{"session_id":"default","turn_id":1,"chat_history":[]}
```

출력 예시:

```python
Data(
    data={
        "previous_state_json": "{\"session_id\":\"default\",\"turn_id\":1}",
        "state_json": "{\"session_id\":\"default\",\"turn_id\":1}",
        "is_empty": False,
        "valid_json": True,
    }
)
```

쉽게 말하면 Input Node는 "사용자가 넣은 원문을 다음 노드가 받을 수 있는 택배 상자에 담는 역할"이다.

### 20.2 Loader Node

Loader Node는 원문 또는 이전 노드 payload를 받아서 표준 구조로 정리한다.

예를 들어 `Session State Loader`는 `previous_state_json` 문자열을 받아서 실제 dict state로 바꾼다.

받는 정보 예시:

```python
{
    "previous_state_json": "{\"session_id\":\"default\",\"turn_id\":1}",
    "state_json": "{\"session_id\":\"default\",\"turn_id\":1}",
}
```

반환 정보 예시:

```python
Data(
    data={
        "agent_state": {
            "session_id": "default",
            "turn_id": 2,
            "chat_history": [],
            "context": {},
            "source_snapshots": {},
            "current_data": None,
            "pending_user_question": "오늘 A제품 생산량 알려줘",
            "state_errors": [],
        },
        "state": {
            "session_id": "default",
            "turn_id": 2,
            "chat_history": [],
            "context": {},
            "source_snapshots": {},
            "current_data": None,
            "pending_user_question": "오늘 A제품 생산량 알려줘",
            "state_errors": [],
        },
    }
)
```

Loader Node는 보통 다음 일을 한다.

- JSON 문자열을 dict로 바꾼다.
- 빠진 필드에 기본값을 채운다.
- 다음 노드들이 항상 같은 key를 볼 수 있게 표준 이름을 만든다.

### 20.3 Prompt Builder

Prompt Builder는 여러 payload를 모아서 LLM에게 보낼 질문지를 만든다.

예를 들어 `Build Intent Prompt`는 아래 정보를 받는다.

```text
사용자 질문: 오늘 A제품 생산량 알려줘
agent_state: 이전 대화 상태
domain_payload: 제품, 공정, 데이터셋, 지표 정의
domain_payload 안의 domain_index: alias 검색용 index
```

반환 정보 예시:

```python
Data(
    data={
        "intent_prompt": """
        You are extracting manufacturing data question intent.
        User question: 오늘 A제품 생산량 알려줘
        Available datasets: production, target
        Available products: A, B
        Return JSON only...
        """,
        "prompt": """
        You are extracting manufacturing data question intent.
        ...
        """,
    }
)
```

Prompt Builder가 중요한 이유는 LLM 호출 코드를 단순하게 만들기 위해서다. LLM Caller는 prompt를 어떻게 만들었는지 몰라도 되고, 그냥 `prompt` 문자열만 받아 호출하면 된다.

### 20.4 LLM Caller

LLM Caller는 prompt를 실제 모델에 보내고, 모델이 준 텍스트를 다시 `Data`로 포장한다.

받는 정보 예시:

```python
{
    "prompt": "User question: 오늘 A제품 생산량 알려줘\nReturn JSON only..."
}
```

노드 설정 예시:

```text
llm_api_key = ...
model_name = gemini-flash-latest
temperature = 0
```

반환 정보 예시:

```python
Data(
    data={
        "llm_text": """
        {
          "request_type": "data_question",
          "dataset_hints": ["production"],
          "metric_hints": ["production_qty"],
          "required_params": {"date": "2026-04-19"},
          "filters": {"product": "A"}
        }
        """,
        "llm_debug": {
            "provider": "langchain_google_genai",
            "model_name": "gemini-flash-latest",
            "prompt_chars": 1200,
            "ok": True,
        },
    }
)
```

LLM Caller는 가능하면 생각을 많이 하지 않는다.

- prompt를 읽는다.
- API key와 model name으로 LLM을 호출한다.
- 응답 텍스트를 반환한다.
- 실패하면 `llm_debug.error`에 이유를 넣는다.

### 20.5 Parser / Normalizer

Parser는 LLM이 준 문자열을 JSON dict로 바꾼다.

Normalizer는 LLM 결과를 도메인 규칙과 합쳐 더 정확한 표준 payload로 만든다.

예를 들어 `Parse Intent JSON`은 이런 문자열을 받는다.

```json
{
  "request_type": "data_question",
  "dataset_hints": ["production"],
  "filters": {"product": "A"}
}
```

그리고 이렇게 반환한다.

```python
Data(
    data={
        "intent_raw": {
            "request_type": "data_question",
            "dataset_hints": ["production"],
            "filters": {"product": "A"},
        },
        "parse_errors": [],
    }
)
```

그 다음 `Normalize Intent With Domain`은 사용자 질문과 `domain_payload` 안의 도메인 index를 다시 보고 보정한다.

받는 정보 예시:

```text
intent_raw: LLM이 만든 초안
domain_payload: 제품 A, 생산 데이터, 생산량 metric 정의
domain_payload.domain_index: "A제품" -> product A, "생산량" -> production_qty
agent_state: 이전 대화 상태
user_question: 오늘 A제품 생산량 알려줘
```

반환 정보 예시:

```python
Data(
    data={
        "intent": {
            "request_type": "data_question",
            "dataset_hints": ["production"],
            "metric_hints": ["production_qty"],
            "required_params": {"date": "2026-04-19"},
            "filters": {"product": "A"},
            "required_datasets": ["production"],
            "normalization_notes": [
                "product alias 'A제품' -> A",
                "metric alias '생산량' -> production_qty",
            ],
        }
    }
)
```

Parser / Normalizer는 LLM이 애매하게 준 결과를 실제 시스템이 쓰기 좋은 모양으로 다듬는 단계이다.

### 20.6 Router / Decider

Router 또는 Decider는 다음으로 어느 노드에 가야 하는지 결정한다.

예를 들어 `Request Type Router`는 `intent.request_type`을 보고 질문이 데이터 질문인지, 프로세스 실행 요청인지 나눈다.

받는 정보 예시:

```python
{
    "intent": {
        "request_type": "data_question",
        "dataset_hints": ["production"],
        "filters": {"product": "A"},
    }
}
```

반환 정보 예시:

```python
Data(
    data={
        "route": "data_question",
        "intent": {
            "request_type": "data_question",
            "dataset_hints": ["production"],
            "filters": {"product": "A"},
        },
        "agent_state": {...},
    }
)
```

`Query Mode Decider`는 데이터 질문 안에서도 새 조회가 필요한지, 기존 데이터를 재사용할 수 있는지 판단한다.

반환 정보 예시:

```python
Data(
    data={
        "query_mode": "retrieval",
        "reason": "date required parameter is new or missing in current source snapshot",
        "reuse_source_snapshot": False,
        "required_params": {"date": "2026-04-19"},
    }
)
```

Router / Decider는 데이터를 크게 바꾸는 노드가 아니라 "다음 길을 고르는 노드"라고 이해하면 된다.

### 20.7 한 질문이 지나가는 전체 예시

사용자 질문:

```text
오늘 A제품 생산량 알려줘
```

노드를 지나며 정보는 대략 이렇게 바뀐다.

```text
Chat Input
  -> "오늘 A제품 생산량 알려줘"

Session State Loader
  -> {"agent_state": {"pending_user_question": "오늘 A제품 생산량 알려줘", ...}}

Domain JSON Loader
  -> {"domain": {...}, "domain_index": {...}}

Build Intent Prompt
  -> Message("질문과 도메인 정보를 보고 intent JSON을 만들어라...")

built-in LLM node
  -> Message("{\"request_type\":\"data_question\", ...}")

Parse Intent JSON
  -> {"intent_raw": {"request_type": "data_question", ...}}

Normalize Intent With Domain
  -> {"intent": {"required_params": {"date": "2026-04-19"}, "filters": {"product": "A"}, ...}}

Request Type Router
  -> {"route": "data_question", "intent": {...}}

Query Mode Decider
  -> {"query_mode": "retrieval", "reason": "새 원본 데이터 조회 필요"}
```

이렇게 보면 각 노드는 "완성된 답변"을 만들기보다, 다음 노드가 더 쉽게 일하도록 정보를 조금씩 정리해 넘기는 역할을 한다.

## 21. 연결이 안 될 때 확인할 체크리스트

Langflow에서 output과 input이 연결되지 않을 때는 아래를 순서대로 본다.

1. output method의 반환 타입이 `-> Data`, `-> Message`, `-> DataFrame`처럼 명확한가?
2. input이 `DataInput(input_types=["Data", "JSON"])`처럼 받을 타입을 열어두었는가?
3. 여러 output을 동시에 보여야 하는데 `group_outputs=True`가 빠지지 않았는가?
4. `Output(method="...")` 이름과 실제 메서드 이름이 정확히 같은가?
5. 기존 노드가 canvas에 캐시되어 있지는 않은가?
6. Langflow를 재시작하거나 custom components reload 후 노드를 새로 추가했는가?
7. `Data`를 반환해야 하는데 plain `dict` 또는 plain `str`를 반환하고 있지는 않은가?
8. input이 advanced로 숨겨져 있어 화면에서 안 보이는 것은 아닌가?
9. node file이 Langflow가 스캔하는 custom components 경로에 있는가?

## 22. 작성 후 검증 방법

코드를 작성한 뒤에는 최소한 아래를 확인한다.

```bash
python -m compileall langflow
```

그리고 로컬에서 import가 되는지 확인한다.

```python
from pathlib import Path
import importlib.util
import sys

root = Path("langflow/data_answer_flow")
for path in sorted(root.glob("*.py")):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    print(f"OK {path.name}")
```

Git whitespace 검사도 유용하다.

```bash
git diff --check -- langflow
```

Langflow UI에서는 다음을 확인한다.

- 노드가 원하는 이름으로 보이는가?
- input 필드가 expected 위치에 보이는가?
- output 포트가 expected 개수만큼 보이는가?
- 포트 색상이 예상 타입과 맞는가?
- 연결하려는 input/output이 실제로 연결되는가?
- 실행 후 output payload가 downstream에서 읽히는가?

## 23. 최소 템플릿

새 노드를 만들 때 아래 템플릿에서 시작하면 된다.

```python
from __future__ import annotations

import json
from typing import Any

from lfx.custom import Component
from lfx.io import DataInput, MessageTextInput, Output
from lfx.schema import Data


def _payload_from_value(value: Any) -> dict:
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


class MyCustomNode(Component):
    display_name = "My Custom Node"
    description = "Explain this node in one sentence."
    icon = "Box"
    name = "MyCustomNode"

    inputs = [
        MessageTextInput(
            name="user_text",
            display_name="User Text",
            value="",
        ),
        DataInput(
            name="input_payload",
            display_name="Input Payload",
            input_types=["Data", "JSON"],
        ),
    ]

    outputs = [
        Output(
            name="output_payload",
            display_name="Output Payload",
            method="build_output",
        ),
    ]

    def build_output(self) -> Data:
        payload = _payload_from_value(self.input_payload)
        result = {
            "user_text": str(self.user_text or ""),
            "input_payload": payload,
        }
        self.status = "Output payload built"
        return Data(data=result)
```

이 템플릿을 기반으로 input과 output payload만 바꿔도 대부분의 단순 Langflow 노드를 만들 수 있다.

## 24. 프로젝트 적용 예시: Domain Item Authoring Flow

이 문서는 Langflow Custom Node 코드 작성법을 설명하는 일반 가이드다. 현재 프로젝트에서 이 패턴이 실제로 적용된 큰 예시는 새 도메인 정리 flow인 `domain_item_authoring_flow`다.

상세한 연결 순서, 각 노드의 입출력 payload, 여러 줄 입력이 MongoDB item 여러 건으로 저장되는 방식, built-in LLM 연결 방법은 아래 문서에 따로 정리했다.

```text
docs/17_LANGFLOW_DOMAIN_ITEM_FLOW_GUIDE.md
```

핵심 연결 흐름은 다음과 같다.

```text
Raw Domain Text Input
  -> Domain Text Splitter
  -> Domain Item Router
  -> MongoDB Existing Domain Item Loader
  -> Domain Item Prompt Context Builder
  -> Domain Item Prompt Template
  -> built-in LLM node
  -> Parse Domain Item JSON
  -> Normalize Domain Item
  -> Domain Item Conflict Checker
  -> MongoDB Domain Item Saver
```

이 flow에서 특히 확인할 custom node 작성 패턴은 다음이다.

- 긴 사용자 입력에는 `MultilineInput`을 사용한다.
- custom node 사이의 구조화 데이터는 `Data(data={...})`로 주고받는다.
- built-in LLM에 연결할 prompt는 `Message` 타입 output으로 내보낸다.
- LLM 결과 파싱, 정규화, 검증, 저장은 각각 별도 노드로 분리한다.
- MongoDB 저장은 `gbn + key` 단위 item document로 한다.

## 25. 프로젝트 적용 예시: Main Data Answer Flow

이 문서는 custom node를 어떻게 작성하는지 설명하는 문서이므로, Main Flow의 모든 연결선을 이 문서 안에 길게 반복하지는 않는다.

실제 Langflow canvas에서 어떤 노드를 어떤 순서로 연결해야 하는지는 아래 문서에 정리되어 있다.

```text
langflow/data_answer_flow/README.md
```

이 문서에서 특히 확인해야 하는 내용은 다음이다.

- `Query Mode Decider` 이후 11~19번 노드 연결 순서
- `Dummy Data Retriever`와 `OracleDB Data Retriever` 중 하나를 선택해서 연결하는 방법
- built-in LLM 노드를 어디에 넣어야 하는지
- `Build Intent Prompt.prompt -> built-in LLM -> Parse Intent JSON.llm_result` 연결
- `Build Pandas Analysis Prompt.prompt -> built-in LLM -> Parse Pandas Analysis JSON.llm_output` 연결
- `Build Answer Prompt.prompt -> built-in LLM -> Final Answer Builder.answer_llm_output` 연결
- `Final Answer Builder.next_state`를 다음 턴 state로 재사용하는 방법

핵심 연결 흐름은 다음과 같다.

```text
Build Intent Prompt
  -> built-in LLM node
  -> Parse Intent JSON
  -> Normalize Intent With Domain
  -> Request Type Router
  -> Query Mode Decider
  -> Retrieval Plan Builder
  -> Dummy Data Retriever 또는 OracleDB Data Retriever
  -> Analysis Base Builder
  -> Build Pandas Analysis Prompt
  -> built-in LLM node
  -> Parse Pandas Analysis JSON
  -> Execute Pandas Analysis
  -> Build Answer Prompt
  -> built-in LLM node
  -> Final Answer Builder
```

각 노드의 세부 역할은 아래 폴더에 노드 번호별 문서로 정리되어 있다.

```text
langflow/data_answer_flow/detail_desc/
```

예를 들어 `17_execute_pandas_analysis.md`는 LLM이 만든 pandas 코드를 어떤 기준으로 검증하고 실행하는지 설명하고, `19_final_answer_builder.md`는 최종 응답과 다음 턴 state를 어떻게 만드는지 설명한다.

Main Flow에서 특히 확인할 custom node 작성 패턴은 다음이다.

- 조회 계획, 조회 실행, 분석 테이블 구성, pandas prompt 생성, pandas 실행, 답변 prompt 생성, state 저장을 서로 다른 노드로 분리한다.
- built-in LLM을 쓰는 구간 앞에는 `Message` 타입 prompt output을 만든다. 현재 `Build Intent Prompt`, `Build Pandas Analysis Prompt`, `Build Answer Prompt`가 이 패턴을 따른다.
- LLM output은 바로 실행하지 않고 JSON parser 노드를 거친다.
- 데이터 조회 노드는 더미 조회와 Oracle 조회가 같은 `retrieval_result` output shape을 반환하도록 맞춘다.
- 최종 노드는 `response`, `tool_results`, `current_data`, `extracted_params`, `state_json`을 함께 반환해서 후속 질문을 지원한다.

## 26. 공식 참고 문서

- [Create custom Python components](https://docs.langflow.org/components-custom-components)
- [Components overview](https://docs.langflow.org/concepts-components)
- [Configure tools for agents](https://docs.langflow.org/agents-tools)
- [Dynamic Create Data](https://docs.langflow.org/dynamic-create-data)
