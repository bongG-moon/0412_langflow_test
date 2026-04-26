# 02. MongoDB Domain Loader

## 한 줄 역할

MongoDB에 저장된 도메인 규칙을 읽어 `domain_payload`로 만드는 노드입니다.

## 도메인 규칙이란?

도메인 규칙은 Agent가 질문을 이해하도록 돕는 업무 지식입니다.

예를 들면 다음과 같습니다.

- `WB`, `W/B`는 어떤 공정 그룹인가?
- `생산달성율`은 어떤 수식인가?
- 그 수식을 계산하려면 어떤 dataset이 필요한가?
- `mode별`이라고 하면 어떤 컬럼으로 그룹핑해야 하는가?

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `mongo_uri` | MongoDB 접속 URI입니다. |
| `db_name` | MongoDB database 이름입니다. 기본값은 `datagov`입니다. |
| `collection_name` | domain item document가 저장된 collection 이름입니다. |
| `status` | 보통 `active`를 사용합니다. |
| `limit` | 최대 몇 건까지 읽을지 정합니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `domain_payload` | Build Intent Prompt와 Build Pandas Prompt에서 사용할 domain 정보입니다. |

## 주요 함수 설명

- `_empty_domain`: 비어 있는 기본 domain 구조를 만듭니다.
- `_merge_item`: MongoDB item document 한 건을 전체 domain 구조에 합칩니다.
- `_load_domain_from_mongo`: MongoDB에 연결하고 item들을 읽습니다.

## MongoDB item document 예시

```json
{
  "gbn": "metrics",
  "key": "achievement_rate",
  "status": "active",
  "payload": {
    "display_name": "Achievement Rate",
    "aliases": ["달성률", "달성율"],
    "required_datasets": ["production", "target"],
    "formula": "sum(production) / sum(target) * 100",
    "output_column": "achievement_rate"
  }
}
```

## 초보자 포인트

이 노드는 실제 생산 데이터를 조회하지 않습니다.
질문을 이해하기 위한 "사전"만 읽습니다.

실제 테이블/DB 조회 정보는 `Table Catalog Loader`와 retriever 노드에서 다룹니다.

## 연결

```text
MongoDB Domain Loader.domain_payload
-> Build Intent Prompt.domain_payload

MongoDB Domain Loader.domain_payload
-> Build Pandas Prompt.domain_payload
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "mongo_uri": "mongodb://localhost:27017",
  "db_name": "datagov",
  "collection_name": "manufacturing_domain_items",
  "status": "active",
  "limit": 1000
}
```

MongoDB document 예시:

```json
{
  "gbn": "metrics",
  "key": "achievement_rate",
  "status": "active",
  "payload": {
    "display_name": "Achievement Rate",
    "aliases": ["달성률"],
    "required_datasets": ["production", "wip"]
  }
}
```

### 출력 예시

```json
{
  "domain_payload": {
    "domain": {
      "metrics": {
        "achievement_rate": {
          "display_name": "Achievement Rate",
          "aliases": ["달성률"],
          "required_datasets": ["production", "wip"]
        }
      }
    },
    "domain_source": "mongodb",
    "domain_errors": []
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_empty_domain` | 없음 | `{"products": {}, "metrics": {}, ...}` | MongoDB가 비어 있어도 뒤 노드가 항상 같은 구조를 받게 합니다. |
| `_json_safe` | `ObjectId(...)`, `datetime(...)` | 문자열 | MongoDB document 안의 특수 타입을 JSON으로 넘길 수 있게 바꿉니다. |
| `_merge_item` | `domain`, `{"gbn": "metrics", "key": "x", "payload": {...}}` | `domain["metrics"]["x"] = payload` | item document를 main flow가 읽기 쉬운 domain dict로 조립합니다. |
| `_load_domain_from_mongo` | Mongo 연결 정보 | `domain_payload` | MongoDB에서 `status=active` item만 읽고 domain payload를 만듭니다. |
| `build_payload` | Langflow 입력값 | `Data(data=domain_payload)` | Langflow output method입니다. Mongo 연결 실패도 `domain_errors`로 담아 반환합니다. |

### 코드 흐름

```text
MongoDB 연결
-> collection에서 status 조건으로 item 조회
-> gbn/key 기준으로 domain dict에 merge
-> Intent Prompt와 Pandas Prompt가 쓰는 domain_payload 반환
```

### 초보자 포인트

이 노드는 "도메인 규칙을 조회"하는 노드입니다. 사용자 질문을 판단하거나 계산하지 않습니다. 판단은 `05 Build Intent Prompt`, `07 Normalize Intent Plan`, `17 Build Pandas Prompt`에서 이 domain을 참고해 진행됩니다.

## 함수 코드 단위 해석: `_merge_item`

이 함수는 MongoDB item document 하나를 main flow가 쓰는 domain dict 안에 넣습니다.

### 함수 input

```json
{
  "domain": {"metrics": {}, "datasets": {}, "process_groups": {}},
  "doc": {
    "gbn": "metrics",
    "key": "achievement_rate",
    "payload": {
      "aliases": ["달성률"],
      "required_datasets": ["production", "wip"]
    }
  }
}
```

### 함수 output

이 함수는 `return`으로 새 값을 돌려주기보다, 입력으로 받은 `domain` dict를 직접 수정합니다.

```json
{
  "metrics": {
    "achievement_rate": {
      "aliases": ["달성률"],
      "required_datasets": ["production", "wip"]
    }
  }
}
```

### 핵심 코드 해석

```python
gbn = str(doc.get("gbn") or "").strip()
key = str(doc.get("key") or "").strip()
```

MongoDB document에서 item 종류와 item 이름을 꺼냅니다.

- `gbn`: `metrics`, `datasets`, `process_groups` 같은 분류
- `key`: `achievement_rate` 같은 항목 이름

```python
if not gbn or not key:
    return
```

분류나 key가 없으면 domain에 넣을 수 없으므로 조용히 건너뜁니다.

```python
payload = doc.get("payload") if isinstance(doc.get("payload"), dict) else {}
```

실제 도메인 내용은 `payload` 안에 있습니다. payload가 dict가 아니면 빈 dict로 처리합니다.

```python
domain.setdefault(gbn, {})[key] = _json_safe(payload)
```

`domain[gbn]` 위치에 `key` 이름으로 payload를 넣습니다.

예:

```python
domain["metrics"]["achievement_rate"] = {...}
```

`setdefault(gbn, {})`는 `domain`에 아직 `metrics` key가 없을 때 자동으로 빈 dict를 만들어 주는 코드입니다.
