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

