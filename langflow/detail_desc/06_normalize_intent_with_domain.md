# 06. Normalize Intent With Domain 상세 설명

대상 코드: `langflow/data_answer_flow/06_normalize_intent_with_domain.py`

이 노드는 LLM이 추출한 raw intent를 domain 지식 기준으로 보정한다. LLM이 놓친 제품명, 공정명, metric alias, dataset keyword를 질문 원문과 domain index에서 다시 찾아 intent에 반영한다.

## 전체 역할

입력으로 raw intent, domain payload, domain index, agent state, user question을 받는다.

그리고 다음 작업을 한다.

- intent 기본 필드를 보정한다.
- 오늘/어제/명시 날짜를 실제 `YYYY-MM-DD`로 변환한다.
- 질문에 포함된 제품 alias를 찾아 filters에 반영한다.
- 질문에 포함된 공정 alias를 찾아 filters에 반영한다.
- 질문에 포함된 domain term alias를 찾아 filter expression에 반영한다.
- dataset keyword를 찾아 dataset_hints를 보완한다.
- metric alias를 찾아 metric_hints를 보완한다.
- metric에 필요한 required_datasets를 붙인다.
- 후속 질문으로 보이는 cue를 추출한다.
- request_type이 unknown이어도 데이터 질문으로 볼 근거가 있으면 data_question으로 보정한다.

## 출력 구조

```json
{
  "intent": {
    "request_type": "data_question",
    "dataset_hints": ["production"],
    "metric_hints": ["production_qty"],
    "required_params": {
      "date": "2026-04-19"
    },
    "filters": {
      "product": "A"
    },
    "required_datasets": ["production"],
    "normalization_notes": []
  }
}
```

## import 영역

```python
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from importlib import import_module
from typing import Any, Dict
```

`json`은 Data text 출력과 중복 제거 marker 생성에 사용한다.

`re`는 텍스트 정규화와 alias 검색에 사용한다.

`datetime`, `timedelta`는 오늘/어제 같은 날짜 표현을 실제 날짜로 바꾸는 데 사용한다.

나머지는 Langflow 호환 공통부와 타입 힌트용이다.

## payload 추출

```python
def _payload_from_value(value: Any) -> Dict[str, Any]:
```

Langflow input에서 dict payload를 꺼낸다.

이 파일의 특징은 `.text`가 JSON이 아닐 경우에도 `{"text": text}`를 반환한다는 점이다.

```python
if isinstance(text, str):
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {"text": text}
    except Exception:
        return {"text": text}
```

즉, JSON이면 dict로 쓰고, JSON이 아니면 text payload로 보존한다.

## 텍스트 정규화

```python
def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())
```

문자열을 비교하기 쉽게 정리한다. 현재 코드에서는 직접 사용되지는 않지만, alias 처리 확장 시 사용할 수 있는 helper다.

## list 변환

```python
def _as_list(value: Any) -> list[Any]:
```

값을 항상 list로 바꾼다. 단일 값, tuple, None을 안정적으로 처리하기 위한 helper다.

## 중복 제거

```python
def _unique(values: list[Any]) -> list[Any]:
```

list에서 중복을 제거하되 순서를 유지한다.

```python
result = []
seen = set()
```

결과 리스트와 이미 본 값을 저장할 set을 만든다.

```python
for value in values:
    marker = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
```

dict나 list는 바로 set에 넣을 수 없으므로 JSON 문자열로 바꿔 marker를 만든다. 일반 값은 문자열로 바꾼다.

```python
if marker in seen:
    continue
seen.add(marker)
result.append(value)
```

이미 본 값이면 건너뛰고, 처음 본 값이면 결과에 추가한다.

## alias 포함 여부 확인

```python
def _contains_alias(question: str, alias: str) -> bool:
```

질문에 특정 alias가 포함되어 있는지 확인한다.

```python
alias = str(alias or "").strip()
if not alias:
    return False
```

alias가 비어 있으면 false다.

```python
if re.fullmatch(r"[A-Za-z0-9_]+", alias):
```

alias가 영문, 숫자, underscore로만 되어 있으면 단어 경계를 고려한다.

```python
return re.search(rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])", question, re.I) is not None
```

예를 들어 `A`가 `AUTO` 안에 들어 있다는 이유로 매칭되지 않도록 앞뒤 경계를 본다.

```python
return alias.lower() in question.lower()
```

한글이나 특수문자가 포함된 alias는 단순 포함 여부로 판단한다.

## 오늘 날짜 계산

```python
def _today(reference_date: str = "") -> datetime:
```

오늘 기준 날짜를 만든다.

```python
if reference_date:
    try:
        return datetime.strptime(reference_date, "%Y-%m-%d")
    except Exception:
        pass
```

테스트나 재현성을 위해 reference_date가 주어지면 그것을 오늘로 본다.

```python
try:
    from zoneinfo import ZoneInfo as TimeZoneInfo
    return datetime.now(TimeZoneInfo("Asia/Seoul")).replace(tzinfo=None)
except Exception:
    pass
```

reference_date가 없으면 Asia/Seoul 기준 현재 날짜를 사용한다. timezone 정보는 제거해서 naive datetime으로 반환한다.

```python
return datetime.now()
```

zoneinfo 사용이 불가능하면 시스템 현재 시간을 사용한다.

## 날짜 표현 추출

```python
def _extract_date(question: str, reference_date: str = "") -> tuple[str | None, str | None]:
```

질문에서 날짜 표현을 찾아 실제 날짜 문자열로 바꾼다.

```python
base = _today(reference_date)
lowered = question.lower()
```

기준 날짜와 소문자 질문을 준비한다.

```python
if any(token in question for token in (...)) or "today" in lowered:
    return base.strftime("%Y-%m-%d"), "explicit"
```

질문에 오늘 표현이 있으면 기준 날짜를 반환한다.

현재 코드에는 일부 한글 token이 깨져 보이는 값이 포함되어 있다. 의도상 `"오늘"`, `"금일"` 같은 표현을 잡기 위한 부분이다.

```python
if any(token in question for token in (...)) or "yesterday" in lowered:
    return (base - timedelta(days=1)).strftime("%Y-%m-%d"), "explicit"
```

어제 표현이 있으면 기준 날짜에서 하루를 뺀다.

```python
match = re.search(r"(20\d{2})[-./]?(0[1-9]|1[0-2])[-./]?([0-2]\d|3[01])", question)
if match:
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}", "explicit"
```

`20260419`, `2026-04-19`, `2026.04.19`, `2026/04/19` 같은 날짜를 찾아 `YYYY-MM-DD`로 반환한다.

```python
return None, None
```

날짜를 찾지 못하면 둘 다 None이다.

## 입력 payload별 추출 함수

```python
def _get_intent(value: Any) -> Dict[str, Any]:
```

`Parse Intent JSON` 출력에서 `intent_raw`를 꺼낸다. 없으면 payload 자체를 intent로 본다.

```python
def _get_domain(value: Any) -> Dict[str, Any]:
```

`Domain JSON Loader.domain_payload`에서 `domain`을 꺼낸다.

```python
def _get_index(domain_payload: Any) -> Dict[str, Any]:
```

`domain_payload` 안의 `domain_index`를 꺼낸다. 별도 domain index output 포트는 더 이상 사용하지 않는다.

```python
def _get_state(value: Any) -> Dict[str, Any]:
```

`Session State Loader` 출력에서 `agent_state` 또는 `state`를 꺼낸다.

## 핵심 함수: normalize_intent_with_domain

```python
def normalize_intent_with_domain(
    intent_raw: Any,
    domain_payload: Any,
    agent_state_payload: Any,
    user_question: str,
    reference_date: str = "",
) -> Dict[str, Any]:
```

raw intent를 domain 기준으로 보정하는 핵심 함수다.

```python
intent = _get_intent(intent_raw)
domain = _get_domain(domain_payload)
domain_index = _get_index(domain_payload)
agent_state = _get_state(agent_state_payload)
question = str(user_question or agent_state.get("pending_user_question") or "")
notes: list[str] = []
```

각 입력에서 실제 dict를 꺼낸다. user_question이 비어 있으면 state의 `pending_user_question`을 사용한다. `notes`는 어떤 alias가 매칭되었는지 기록하는 용도다.

```python
intent.setdefault("request_type", "unknown")
intent.setdefault("dataset_hints", [])
...
```

intent에 필수 필드가 없으면 기본값을 넣는다.

```python
if not isinstance(intent["required_params"], dict):
    intent["required_params"] = {}
if not isinstance(intent["filters"], dict):
    intent["filters"] = {}
```

required_params와 filters는 dict로 보정한다.

```python
date_value, date_source = _extract_date(question, reference_date)
if date_value:
    intent["required_params"]["date"] = date_value
    intent["date_source"] = date_source
```

질문에서 날짜를 찾으면 required_params에 `date`를 넣는다.

## 제품 alias 보정

```python
for alias_norm, product_key in domain_index.get("product_alias_to_key", {}).items():
    if _contains_alias(question, alias_norm):
```

질문에 제품 alias가 있는지 확인한다.

```python
product = domain.get("products", {}).get(product_key, {})
filters = product.get("filters") if isinstance(product, dict) else None
```

해당 제품 정의를 domain에서 찾는다.

```python
if isinstance(filters, dict):
    intent["filters"].update(filters)
else:
    intent["filters"]["product"] = product_key
```

제품 정의에 filters가 있으면 그대로 반영한다. 없으면 `product=product_key` 형태로 넣는다.

```python
notes.append(f"product alias '{alias_norm}' -> {product_key}")
```

매칭 이력을 남긴다.

## 공정 alias 보정

```python
for alias_norm, group_key in domain_index.get("process_alias_to_group", {}).items():
```

공정 alias를 순회한다.

```python
group = domain.get("process_groups", {}).get(group_key, {})
processes = group.get("processes") if isinstance(group, dict) else None
```

공정 그룹에 속한 실제 process 목록을 가져온다.

```python
if processes:
    intent["filters"]["process"] = list(processes)
else:
    intent["filters"]["process"] = [group_key]
```

process 목록이 있으면 그것을 filter에 넣고, 없으면 group_key를 list로 넣는다.

## term alias 보정

```python
filter_expressions = list(intent.get("filter_expressions") or [])
```

기존 filter expression을 가져온다.

```python
for alias_norm, term_key in domain_index.get("term_alias_to_key", {}).items():
    if _contains_alias(question, alias_norm):
```

질문에 domain term alias가 있는지 확인한다.

```python
term = domain.get("terms", {}).get(term_key, {})
filter_expr = term.get("filter") if isinstance(term, dict) else None
```

term 정의 안의 filter rule을 가져온다.

```python
if isinstance(filter_expr, dict):
    enriched = dict(filter_expr)
    enriched["term_key"] = term_key
    filter_expressions.append(enriched)
```

filter rule이 있으면 term_key를 붙여 filter_expressions에 추가한다.

```python
if filter_expressions:
    intent["filter_expressions"] = _unique(filter_expressions)
```

중복 제거 후 intent에 반영한다.

## dataset과 metric 보완

```python
dataset_hints = list(intent.get("dataset_hints") or [])
for keyword_norm, dataset_key in domain_index.get("dataset_keyword_to_key", {}).items():
    if _contains_alias(question, keyword_norm):
        dataset_hints.append(dataset_key)
```

질문에 dataset keyword가 있으면 dataset_hints에 추가한다.

```python
intent["dataset_hints"] = _unique([str(item) for item in dataset_hints if str(item).strip()])
```

문자열 list로 정리하고 중복 제거한다.

```python
metric_hints = list(intent.get("metric_hints") or [])
for alias_norm, metric_key in domain_index.get("metric_alias_to_key", {}).items():
    if _contains_alias(question, alias_norm):
        metric_hints.append(metric_key)
```

질문에 metric alias가 있으면 metric_hints에 추가한다.

```python
intent["metric_hints"] = _unique([str(item) for item in metric_hints if str(item).strip()])
```

metric_hints를 정리한다.

## required_datasets 계산

```python
required_datasets: list[str] = []
for dataset_key in intent["dataset_hints"]:
    if dataset_key in domain.get("datasets", {}):
        required_datasets.append(dataset_key)
```

dataset_hints에 있는 dataset을 required_datasets 후보로 넣는다.

```python
for metric_key in intent["metric_hints"]:
    metric = domain.get("metrics", {}).get(metric_key, {})
    if isinstance(metric, dict):
        required_datasets.extend([str(item) for item in _as_list(metric.get("required_datasets"))])
```

metric이 필요로 하는 dataset도 추가한다. 예를 들어 생산 달성율이면 production과 target이 들어갈 수 있다.

```python
intent["required_datasets"] = _unique([item for item in required_datasets if item])
```

중복 제거 후 intent에 반영한다.

## 후속 질문 cue

```python
followup_tokens = [...]
cues = list(intent.get("followup_cues") or [])
for token in followup_tokens:
    if token.lower() in question.lower():
        cues.append(token)
```

질문에 “이때”, “그중”, “top”, “공정별” 같은 후속 분석 표현이 있으면 followup_cues에 추가하는 의도다.

현재 코드에는 일부 한글 token이 깨져 보인다. 실제 동작 품질을 위해서는 추후 이 문자열들을 정상 한글로 정리하는 것이 좋다.

## request_type 보정

```python
if intent.get("request_type") == "unknown":
    if intent["dataset_hints"] or intent["metric_hints"] or intent["filters"] or intent.get("group_by"):
        intent["request_type"] = "data_question"
```

LLM이 unknown이라고 했더라도 dataset, metric, filter, group_by 근거가 있으면 data_question으로 보정한다.

```python
elif any(word in question for word in (...)):
    intent["request_type"] = "process_execution"
```

프로세스 실행 관련 표현이 있으면 process_execution으로 보정한다.

## 마무리

```python
intent["raw_terms"] = _unique(intent.get("raw_terms", []) + notes)
intent["normalization_notes"] = notes
return {"intent": intent}
```

매칭된 alias 정보를 raw_terms와 normalization_notes에 기록하고 최종 intent를 반환한다.

## Component 입력

```python
intent_raw
domain_payload
domain_index
agent_state
user_question
reference_date
```

`reference_date`는 advanced 입력이다. 테스트할 때 오늘 날짜를 고정하기 위해 사용할 수 있다.

## Component 출력

```python
Output(name="intent", display_name="Intent", method="build_intent", types=["Data"])
```

정규화된 intent를 출력한다.

## 실행 메서드

```python
def build_intent(self) -> Data:
```

Component input을 읽어 `normalize_intent_with_domain()`에 전달한다.

```python
return _make_data(payload)
```

payload 전체는 `.data`에 넣는다. 정규화된 intent도 `.data["intent"]`에서 확인한다.

## 다음 노드 연결

```text
Normalize Intent With Domain.intent -> Request Type Router.intent
```

## 학습 포인트

이 노드는 “LLM 결과를 그대로 믿지 않고 domain index로 다시 보정하는 노드”다.

LLM은 질문의 의도를 잘 잡는 역할이고, 이 노드는 프로젝트가 가진 확정 domain 지식으로 제품, 공정, metric, dataset을 안정적으로 매핑하는 역할이다.
