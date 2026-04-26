# 11. MongoDB Data Loader

## 한 줄 역할

`data_ref`만 남아 있는 payload에서 MongoDB에 저장된 실제 row list를 다시 불러오는 노드입니다.

## 왜 필요한가

큰 데이터 전체를 Langflow state에 계속 들고 있으면 토큰과 메모리를 많이 씁니다.
그래서 `MongoDB Data Store`가 큰 row list를 MongoDB에 저장하고 state에는 주소만 남길 수 있습니다.

후속 질문에서 실제 row가 다시 필요하면 이 노드가 그 주소를 따라가 row를 복원합니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `payload` | `data_ref`가 포함된 payload입니다. 보통 follow-up branch에서 들어옵니다. |
| `mongo_uri` | row 저장소 MongoDB URI입니다. |
| `db_name` | database 이름입니다. |
| `collection_name` | row data ref collection 이름입니다. |
| `enabled` | `true`이면 로드하고, `false`이면 통과시킵니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `loaded_payload` | data_ref가 실제 data row로 복원된 payload입니다. |

## 주요 함수 설명

- `_connect_collection`: MongoDB collection에 연결합니다.
- `_load_rows`: data_ref에 있는 `ref_id`로 저장된 row를 찾습니다.
- `_hydrate_refs`: payload 안을 재귀적으로 돌며 data_ref를 실제 row로 바꿉니다.
- `load_payload_from_mongo`: 전체 로딩 작업을 실행합니다.

## 초보자 포인트

이 노드는 모든 질문에서 꼭 필요하지는 않습니다.

`MongoDB Data Store`를 사용해서 큰 데이터를 ref로 저장하는 구조를 쓸 때, 후속 분석 branch 앞에 연결합니다.

## 연결

```text
Intent Route Router.followup_transform
-> MongoDB Data Loader (Follow-up).payload

MongoDB Data Loader.loaded_payload
-> Current Data Retriever.intent_plan
```

