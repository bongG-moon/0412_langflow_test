# 03. Domain JSON Loader

## 한 줄 역할

MongoDB 대신 직접 붙여 넣은 domain JSON을 읽어 `domain_payload`로 만드는 노드입니다.

## 언제 쓰나?

처음 테스트할 때 MongoDB를 연결하지 않고도 flow를 확인하고 싶을 때 사용합니다.

운영에서는 `MongoDB Domain Loader`를 권장하지만, 개발/디버깅에서는 이 노드가 빠릅니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `domain_json` | domain JSON 문자열입니다. aggregate 형식과 item document 배열을 모두 받을 수 있습니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `domain_payload` | 정규화된 domain 정보입니다. |

## 주요 함수 설명

- `_parse_jsonish`: JSON 문자열, Python dict처럼 보이는 문자열을 최대한 안전하게 파싱합니다.
- `_empty_domain`: 기본 domain 틀을 만듭니다.
- `_merge_item`: item document를 aggregate domain 구조에 합칩니다.
- `_normalize_domain_payload`: 입력이 어떤 형식이든 뒤 노드가 읽을 수 있는 구조로 맞춥니다.

## 입력 가능 형식

aggregate domain:

```json
{
  "domain": {
    "process_groups": {},
    "terms": {},
    "datasets": {},
    "metrics": {},
    "join_rules": []
  }
}
```

item document 배열:

```json
[
  {
    "gbn": "process_groups",
    "key": "DA",
    "payload": {
      "display_name": "Die Attach",
      "aliases": ["DA", "D/A"],
      "processes": ["D/A1", "D/A2"]
    }
  }
]
```

## 초보자 포인트

`Domain JSON Loader`와 `MongoDB Domain Loader`는 둘 중 하나만 연결하면 됩니다.
둘 다 같은 `domain_payload`를 출력하기 때문입니다.

## 연결

```text
Domain JSON Loader.domain_payload
-> Build Intent Prompt.domain_payload

Domain JSON Loader.domain_payload
-> Build Pandas Prompt.domain_payload
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "metrics": {
    "achievement_rate": {
      "display_name": "Achievement Rate",
      "aliases": ["달성률"],
      "required_datasets": ["production", "wip"]
    }
  }
}
```

또는 MongoDB item 배열 형태도 받을 수 있습니다.

```json
[
  {
    "gbn": "metrics",
    "key": "achievement_rate",
    "payload": {
      "aliases": ["달성률"],
      "required_datasets": ["production", "wip"]
    }
  }
]
```

### 출력 예시

```json
{
  "domain_payload": {
    "domain": {
      "metrics": {
        "achievement_rate": {
          "aliases": ["달성률"],
          "required_datasets": ["production", "wip"]
        }
      }
    },
    "domain_source": "json",
    "domain_errors": []
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_parse_jsonish` | 코드블록 JSON 문자열 | `(dict 또는 list, errors)` | 사용자가 Langflow 입력창에 JSON을 붙여 넣을 때 코드블록까지 받아주기 위함입니다. |
| `_empty_domain` | 없음 | 빈 domain 기본 구조 | 입력이 일부만 있어도 뒤 노드가 key missing으로 실패하지 않게 합니다. |
| `_merge_item` | item document | domain dict에 반영 | MongoDB item document 형식을 일반 domain dict로 바꿉니다. |
| `_normalize_domain_payload` | dict, list, `{"domain_payload": ...}` | 표준 `domain_payload` | 직접 JSON, item 배열, 이미 감싼 payload를 모두 같은 출력 형태로 맞춥니다. |
| `build_payload` | `domain_json` | `Data(data=domain_payload)` | Langflow에서 실행되는 output method입니다. |

### 코드 흐름

```text
사용자 JSON 입력
-> JSON 파싱
-> domain dict 또는 item document 배열인지 판단
-> 표준 domain_payload로 정규화
-> MongoDB 없이도 Intent/Pandas Prompt에 연결
```

### 초보자 포인트

이 노드는 MongoDB가 준비되지 않았을 때 쓰는 fallback입니다. 운영에서는 `02 MongoDB Domain Loader`를 쓰고, 테스트나 빠른 수정에서는 이 노드에 JSON을 직접 넣으면 됩니다.

## 함수 코드 단위 해석: `_normalize_domain_payload`

이 함수는 사용자가 입력한 여러 형태의 domain JSON을 v2 표준 `domain_payload` 형태로 바꿉니다.

### 함수 input 예시 1: 이미 domain 형태

```json
{
  "metrics": {
    "achievement_rate": {
      "aliases": ["달성률"]
    }
  }
}
```

### 함수 input 예시 2: item document 배열

```json
[
  {
    "gbn": "metrics",
    "key": "achievement_rate",
    "payload": {"aliases": ["달성률"]}
  }
]
```

### 함수 output

```json
{
  "domain_payload": {
    "domain": {
      "metrics": {
        "achievement_rate": {"aliases": ["달성률"]}
      }
    },
    "domain_source": "json",
    "domain_errors": []
  }
}
```

### 핵심 코드 해석

```python
raw, errors = _parse_jsonish(raw_value)
```

입력값을 JSON으로 파싱합니다. 문자열, 코드블록, dict/list 입력을 모두 처리합니다. 파싱 실패 메시지는 `errors`에 담습니다.

```python
domain = _empty_domain()
```

먼저 빈 domain 기본 구조를 만듭니다. 그래야 일부 항목만 입력해도 뒤 노드가 안정적으로 읽을 수 있습니다.

```python
if isinstance(raw, dict) and isinstance(raw.get("domain_payload"), dict):
    return raw
```

이미 `domain_payload`로 감싸진 입력이면 다시 바꿀 필요가 없습니다. 그대로 반환합니다.

```python
if isinstance(raw, list):
    for doc in raw:
        if isinstance(doc, dict):
            _merge_item(domain, doc)
```

입력이 item document 배열이면 각 item을 `_merge_item`으로 domain dict에 넣습니다.

```python
elif isinstance(raw, dict):
    for key, value in raw.items():
        if key in domain and isinstance(value, dict):
            domain[key] = value
```

입력이 이미 `{"metrics": {...}}` 같은 domain 형태이면 해당 section을 그대로 복사합니다.

## 추가 함수 코드 단위 해석: `_parse_jsonish`

이 함수는 사용자가 넣은 domain JSON을 최대한 유연하게 해석합니다.

```python
if isinstance(text, (dict, list)):
    return deepcopy(text), []
```

이미 dict나 list로 들어온 값은 다시 파싱하지 않고 복사해서 반환합니다.

```python
raw = str(text or "").strip()
if not raw:
    return {}, []
```

입력이 비어 있으면 빈 dict와 빈 오류 목록을 반환합니다. 빈 설정도 flow가 깨지지 않도록 처리합니다.

```python
for parser in (json.loads, ast.literal_eval):
    try:
        return parser(raw), []
    except Exception as exc:
        errors.append(str(exc))
```

표준 JSON을 먼저 시도하고, Python dict처럼 작은따옴표가 들어간 형태도 `ast.literal_eval`로 한 번 더 시도합니다.

```python
return {}, errors
```

두 파서가 모두 실패하면 빈 dict와 파싱 오류 목록을 반환합니다.

## 추가 함수 코드 단위 해석: `_merge_item`

MongoDB Domain Loader와 같은 item 형식도 JSON 입력으로 받을 수 있게 해주는 병합 함수입니다.

```python
if isinstance(doc.get("domain"), dict):
    for key, value in doc["domain"].items():
```

입력이 완성된 domain 문서라면 `domain` 내부의 key를 그대로 병합합니다.

```python
if key == "join_rules" and isinstance(value, list):
    domain.setdefault("join_rules", []).extend(deepcopy(value))
elif isinstance(value, dict):
    domain.setdefault(key, {}).update(deepcopy(value))
```

`join_rules`는 list라서 append/extend 방식으로 합치고, `metrics`, `terms`, `process_groups` 같은 dict 계열은 key 기준으로 update합니다.

```python
gbn = str(doc.get("gbn") or doc.get("category") or "").strip()
key = str(doc.get("key") or doc.get("name") or "").strip()
payload = doc.get("payload") if isinstance(doc.get("payload"), dict) else {}
```

item 문서라면 `gbn/key/payload` 형식으로 분해합니다.

```python
if gbn == "join_rules":
    item = deepcopy(payload)
    if key:
        item.setdefault("name", key)
    domain.setdefault("join_rules", []).append(item)
```

join rule item은 이름을 보존해 list에 추가합니다.
