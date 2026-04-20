# 02. Domain JSON Loader 상세 설명

대상 코드: `langflow/data_answer_flow/02_domain_json_loader.py`

이 노드는 Domain JSON을 실제 분석 flow에서 사용할 수 있는 표준 구조로 정리한다. 특히 사람이 읽기 좋은 `domain_payload`와 코드가 빠르게 alias를 찾기 위한 `domain_index`를 분리해서 출력한다.

## 전체 역할

입력으로 Domain JSON payload를 받는다.

그리고 다음 작업을 한다.

- JSON 문자열을 dict로 파싱한다.
- 표준 domain document 형태로 정리한다.
- `products`, `process_groups`, `terms`, `datasets`, `metrics`, `join_rules` 기본 구조를 보정한다.
- dataset과 metric의 주요 필드를 검증하고 list 형태로 정리한다.
- 제품명, 공정명, 용어, 지표명, dataset keyword 검색용 alias index를 만든다.
- `domain_payload`와 `domain_index`를 별도 output으로 반환한다.

## 출력 구조

`domain_payload`는 다음 구조다.

```json
{
  "domain_document": {},
  "domain": {},
  "domain_index": {},
  "domain_errors": []
}
```

`domain_index` is intentionally included here as a fallback for Langflow
versions that may drop a custom component multi-output edge after execution.

`domain_index`는 다음 구조다.

```json
{
  "domain_index": {
    "term_alias_to_key": {},
    "product_alias_to_key": {},
    "process_alias_to_group": {},
    "metric_alias_to_key": {},
    "dataset_keyword_to_key": {}
  },
  "domain_errors": []
}
```

## import 영역

```python
from __future__ import annotations
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict
```

`json`은 JSON 파싱과 문자열 변환에 사용한다.

`re`는 alias 공백 정규화에 사용한다.

`deepcopy`는 입력 원본을 직접 수정하지 않기 위해 사용한다.

`dataclass`, `import_module`, `Any`, `Dict`는 Langflow 호환 fallback과 타입 힌트에 사용한다.

## Langflow 호환 공통부

`_load_attr`, `_FallbackComponent`, `_FallbackInput`, `_FallbackOutput`, `_FallbackData`, `_make_input`, `_make_data`는 다른 노드와 같은 패턴이다.

핵심은 다음이다.

```python
Component = _load_attr(..., "Component", _FallbackComponent)
DataInput = _load_attr(["lfx.io", "langflow.io"], "DataInput", _make_input)
Output = _load_attr(["lfx.io", "langflow.io"], "Output", _FallbackOutput)
Data = _load_attr(["lfx.schema.data", "lfx.schema", "langflow.schema"], "Data", _FallbackData)
```

Langflow 실제 클래스가 있으면 그것을 쓰고, 없으면 fallback으로 대체한다.

## 상수 정의

```python
ROOT_KEYS = ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")
```

domain 안에서 관리하는 핵심 root key 목록이다.

```python
VALID_COLUMN_TYPES = {"string", "number", "date", "datetime", "boolean"}
```

dataset column type으로 허용하는 값들이다.

## payload 추출

```python
def _payload_from_value(value: Any) -> Dict[str, Any]:
```

입력값을 dict로 바꿔준다.

`None`이면 `{}`를 반환한다.

이미 dict면 그대로 반환한다.

Langflow `Data` 객체면 `.data`를 확인한다.

`.text`가 JSON 문자열이면 `json.loads`로 파싱한다.

실패하면 `{}`를 반환한다.

이 함수 덕분에 앞 노드가 `Data`, `JSON`, 문자열 중 어떤 형태를 주더라도 어느 정도 흡수할 수 있다.

## alias 정규화

```python
def _normalize_alias(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text
```

alias를 비교 가능한 형태로 바꾼다.

예를 들어 `"  A제품   생산량 "`은 `"a제품 생산량"`으로 정리된다.

앞뒤 공백 제거, 소문자 변환, 여러 공백을 하나로 줄이는 작업을 한다.

## list 변환

```python
def _as_list(value: Any) -> list[Any]:
```

어떤 값이든 list로 통일한다.

`None`은 `[]`가 된다.

이미 list면 그대로 둔다.

tuple이면 list로 바꾼다.

단일 문자열이나 숫자는 `[value]`로 감싼다.

JSON 작성자가 `aliases`를 실수로 문자열 하나로 넣어도 내부 처리를 안정적으로 하기 위한 helper다.

## JSON 텍스트 추출

```python
def _extract_json_text(value: Any) -> str:
```

입력값에서 실제 Domain JSON 문자열을 꺼낸다.

```python
if value is None:
    return ""
```

입력이 없으면 빈 문자열이다.

```python
if isinstance(value, str):
    return value.strip()
```

문자열이 직접 들어오면 그대로 사용한다.

```python
payload = _payload_from_value(value)
```

Data 객체라면 payload를 추출한다.

```python
if isinstance(payload.get("domain_json_text"), str):
    return payload["domain_json_text"].strip()
```

payload 안에서 표준 key인 `domain_json_text`를 찾는다.

현재 flow에서는 `Domain JSON Input`이 이 key만 출력한다. 다른 flow가 이미 dict 형태의 domain document를 넘기는 경우에는 아래의 `json.dumps(payload, ensure_ascii=False)` 경로로 처리된다.

```python
return json.dumps(payload, ensure_ascii=False)
```

payload 자체가 이미 dict 형태의 domain이면 다시 JSON 문자열로 만든다.

```python
return str(value or "").strip()
```

마지막 fallback이다.

## Domain JSON 파싱

```python
def _parse_domain_json(domain_json_text: Any) -> tuple[Dict[str, Any], list[str]]:
```

입력값을 JSON dict로 파싱하고, 에러 목록을 함께 반환한다.

```python
errors: list[str] = []
text = _extract_json_text(domain_json_text)
```

에러 리스트를 만들고 실제 JSON 문자열을 추출한다.

```python
if not text:
    errors.append("domain_json_payload is empty.")
    return {}, errors
```

비어 있으면 빈 dict와 에러를 반환한다.

```python
try:
    parsed = json.loads(text)
except Exception as exc:
    errors.append(f"Domain JSON parse failed: {exc}")
    return {}, errors
```

JSON 파싱을 시도한다. 실패하면 에러 메시지를 담는다.

```python
if not isinstance(parsed, dict):
    errors.append("Domain JSON root must be an object.")
    return {}, errors
```

최상위 JSON은 object여야 한다. list나 문자열이면 domain 문서로 인정하지 않는다.

```python
return parsed, errors
```

파싱 결과와 에러 목록을 반환한다.

## Domain 문서 표준화

```python
def _normalize_domain_document(parsed: Dict[str, Any]) -> tuple[Dict[str, Any], list[str]]:
```

입력 domain을 표준 document 형태로 바꾼다.

```python
source = deepcopy(parsed)
```

입력 원본을 보호하기 위해 깊은 복사한다.

```python
metadata = source.get("metadata") if isinstance(source.get("metadata"), dict) else {}
```

metadata가 dict면 사용하고, 아니면 빈 dict로 둔다. 도메인 JSON에서는 timezone을 넣지 않는 것을 기본 방향으로 두며, 이 노드가 별도로 timezone key를 제거하지는 않는다.

```python
if isinstance(source.get("domain"), dict):
```

입력이 이미 표준 구조인지 확인한다.

```python
domain = deepcopy(source["domain"])
document = {
    "domain_id": source.get("domain_id") or "manufacturing_default",
    "status": source.get("status") or "active",
    "metadata": metadata,
    "domain": domain,
}
```

표준 구조라면 `domain` 안쪽을 복사하고, `domain_id`, `status`, `metadata`를 포함한 document를 만든다.

```python
else:
    domain = {key: deepcopy(source.get(key)) for key in ROOT_KEYS if key in source}
```

표준 구조가 아니라 root에 바로 `products`, `datasets` 등이 있는 bare domain 형태라면 필요한 key만 골라 `domain`으로 묶는다.

```python
domain = document["domain"]
for key in ("products", "process_groups", "terms", "datasets", "metrics"):
    if not isinstance(domain.get(key), dict):
        domain[key] = {}
```

주요 domain 항목은 dict여야 한다. 없거나 타입이 잘못되면 빈 dict로 보정한다.

```python
if not isinstance(domain.get("join_rules"), list):
    domain["join_rules"] = []
```

join_rules는 list여야 하므로 아니면 빈 list로 보정한다.

## dataset 검증

```python
for dataset_key, dataset in list(domain["datasets"].items()):
```

모든 dataset 정의를 순회한다. 반복 중 삭제가 가능하도록 `list(...)`로 복사해서 순회한다.

```python
if not isinstance(dataset, dict):
    errors.append(...)
    domain["datasets"].pop(dataset_key, None)
    continue
```

dataset 값이 dict가 아니면 잘못된 정의로 보고 제거한다.

```python
dataset.setdefault("display_name", dataset_key)
```

display_name이 없으면 dataset key를 기본 표시명으로 넣는다.

```python
dataset["keywords"] = [str(item) for item in _as_list(dataset.get("keywords")) if str(item).strip()]
```

keywords를 문자열 list로 정리하고 빈 값은 제거한다.

```python
dataset["required_params"] = [
    str(item) for item in _as_list(dataset.get("required_params")) if str(item).strip()
]
```

required_params도 문자열 list로 정리한다.

```python
columns = dataset.get("columns")
if not isinstance(columns, list):
    dataset["columns"] = []
    continue
```

columns는 list여야 한다. 아니면 빈 list로 처리한다.

```python
for column in columns:
    if not isinstance(column, dict) or not column.get("name"):
        errors.append(...)
        continue
```

column은 dict여야 하고 `name`이 있어야 한다. 아니면 스킵한다.

```python
column = dict(column)
column.setdefault("type", "string")
```

column을 복사하고 type이 없으면 `"string"`으로 둔다.

```python
if column["type"] not in VALID_COLUMN_TYPES:
    errors.append(...)
```

허용되지 않은 type이면 에러에 기록한다. 다만 column 자체는 유지한다.

## metric 검증

```python
for metric_key, metric in list(domain["metrics"].items()):
```

metric 정의를 순회한다.

```python
if not isinstance(metric, dict):
    errors.append(...)
    domain["metrics"].pop(metric_key, None)
    continue
```

metric이 dict가 아니면 제거한다.

```python
metric.setdefault("display_name", metric_key)
```

display_name이 없으면 metric key를 사용한다.

```python
metric["aliases"] = [str(item) for item in _as_list(metric.get("aliases")) if str(item).strip()]
```

aliases를 문자열 list로 정리한다.

```python
if "required_datasets" not in metric:
    errors.append(...)
```

metric은 어떤 dataset이 필요한지 알아야 하므로 `required_datasets`가 없으면 에러에 기록한다.

```python
metric["required_datasets"] = [
    str(item) for item in _as_list(metric.get("required_datasets")) if str(item).strip()
]
```

required_datasets를 문자열 list로 정리한다.

## alias 추가 함수

```python
def _add_alias(index: Dict[str, Dict[str, str]], bucket: str, alias: Any, key: str, errors: list[str]) -> None:
```

index의 특정 bucket에 alias를 등록한다.

```python
normalized = _normalize_alias(alias)
if not normalized:
    return
```

alias를 정규화하고, 빈 값이면 등록하지 않는다.

```python
existing = index[bucket].get(normalized)
if existing and existing != key:
    errors.append(...)
    return
```

같은 alias가 이미 다른 key에 연결되어 있으면 충돌로 본다. 예를 들어 `"A제품"`이 `PRODUCT_A`와 `PRODUCT_B`에 동시에 매핑되면 안 된다.

```python
index[bucket][normalized] = key
```

정상 alias를 등록한다.

## domain_index 생성

```python
def _build_domain_index(domain: Dict[str, Any], errors: list[str]) -> Dict[str, Dict[str, str]]:
```

domain에서 검색용 alias index를 만든다.

```python
index = {
    "term_alias_to_key": {},
    "product_alias_to_key": {},
    "process_alias_to_group": {},
    "metric_alias_to_key": {},
    "dataset_keyword_to_key": {},
}
```

5개의 검색 bucket을 만든다.

제품은 `product_alias_to_key`에 등록된다. 제품 key, display_name, aliases가 모두 같은 product key로 연결된다.

공정은 `process_alias_to_group`에 등록된다. 공정 그룹 key, display_name, aliases, 실제 processes 값이 모두 group key로 연결된다.

용어는 `term_alias_to_key`에 등록된다.

metric은 `metric_alias_to_key`에 등록된다.

dataset은 `dataset_keyword_to_key`에 등록된다.

이 index 덕분에 뒤 노드는 질문에 `"생산 달성율"`, `"달성률"`, `"Achievement"` 중 어떤 표현이 있어도 동일 metric key를 찾을 수 있다.

## 최상위 실행 함수

```python
def load_domain_json(domain_json_text: Any) -> Dict[str, Any]:
```

이 파일의 핵심 진입점이다.

```python
parsed, errors = _parse_domain_json(domain_json_text)
```

먼저 JSON을 파싱한다.

```python
document, normalize_errors = _normalize_domain_document(parsed) if parsed else (...)
```

파싱 성공 시 표준화한다. 파싱 실패 시 빈 기본 domain document를 사용한다.

```python
errors.extend(normalize_errors)
```

파싱 에러와 정규화 에러를 합친다.

```python
domain = document["domain"]
domain_index = _build_domain_index(domain, errors)
```

domain을 꺼내고 alias index를 만든다.

```python
return {
    "domain_document": document,
    "domain": domain,
    "domain_index": domain_index,
    "domain_errors": errors,
}
```

최종 결과를 반환한다.

## Component 입력

```python
DataInput(
    name="domain_json_payload",
    display_name="Domain JSON Payload",
    input_types=["Data", "JSON"],
)
```

`Domain JSON Input` 또는 추후 `Domain Authoring Flow`에서 나온 JSON payload를 받는다.

## Component 출력

```python
Output(
    name="domain_payload",
    method="build_domain_payload",
    group_outputs=True,
    types=["Data"],
)
```

LLM prompt와 도메인 참조에 사용할 domain payload를 출력한다.

```python
Output(
    name="domain_index",
    method="build_domain_index",
    group_outputs=True,
    types=["Data"],
)
```

alias 검색과 정규화에 사용할 domain index를 출력한다.

`group_outputs=True`이므로 두 output이 Langflow에서 별도 포트로 보인다.

## 출력 메서드

```python
def build_domain_payload(self) -> Data:
```

입력을 읽고 `load_domain_json()`을 실행한 뒤 `domain_document`, `domain`, `domain_index`, `domain_errors`를 반환한다.
`domain_index`는 별도 output으로도 제공되지만, multi-output 연결이 풀리는 Langflow 환경을 대비한 fallback으로 `domain_payload`에도 같이 담는다.

```python
def build_domain_index(self) -> Data:
```

입력을 읽고 `load_domain_json()`을 실행한 뒤 `domain_index`, `domain_errors`만 반환한다.

```python
def build_domain(self) -> Data:
def build_domain_document(self) -> Data:
```

현재 outputs에는 연결되어 있지 않은 helper 메서드다. 디버깅이나 향후 output 추가 시 사용할 수 있다.

## 다음 노드 연결

```text
Domain JSON Loader.domain_payload -> Build Intent Prompt.domain_payload
Domain JSON Loader.domain_index   -> Build Intent Prompt.domain_index

Domain JSON Loader.domain_payload -> Normalize Intent With Domain.domain_payload
Domain JSON Loader.domain_index   -> Normalize Intent With Domain.domain_index

Domain JSON Loader.domain_payload -> Query Mode Decider.domain_payload
```

## 학습 포인트

이 노드는 “정리된 domain 본문”과 “검색용 index”를 분리하는 게 핵심이다.

`domain_payload`는 LLM prompt에 넣기 좋고, `domain_index`는 코드가 alias를 빠르게 찾기 좋다. 두 목적이 다르기 때문에 output을 나누는 편이 유지보수에 유리하다.
