# 21. MongoDB Data Store

## 한 줄 역할

큰 row list를 MongoDB에 저장하고, flow payload에는 작은 preview와 `data_ref`만 남기는 노드입니다.

## 왜 필요한가

조회 결과가 수천 row가 되면 모든 데이터를 LLM prompt나 Langflow state에 계속 들고 있기 어렵습니다.

이 노드를 사용하면 다음처럼 바뀝니다.

```json
{
  "data": [{"preview": "rows"}],
  "data_ref": {
    "store": "mongodb",
    "ref_id": "...",
    "row_count": 1234
  },
  "data_is_reference": true
}
```

즉, 전체 데이터는 MongoDB에 있고 state에는 주소만 남습니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `payload` | row list가 포함된 payload입니다. 보통 Analysis Result Merger 출력입니다. |
| `mongo_uri` | MongoDB URI입니다. |
| `db_name` | database 이름입니다. |
| `collection_name` | row 저장 collection 이름입니다. |
| `enabled` | `true`이면 저장하고, `false`이면 통과시킵니다. |
| `preview_row_limit` | payload에 남길 미리보기 row 수입니다. |
| `min_rows` | 몇 row 이상일 때 MongoDB에 저장할지 정합니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `stored_payload` | 큰 row list가 preview + data_ref 형태로 압축된 payload입니다. |

## 주요 함수 설명

- `_is_row_list`: 값이 row list인지 확인합니다.
- `_find_session_id`: payload 안에서 session_id를 찾아 저장 문서에 넣습니다.
- `_store_rows`: MongoDB에 실제 rows를 저장합니다.
- `_compact_with_refs`: payload 안을 돌며 큰 row list를 data_ref로 바꿉니다.
- `store_payload_in_mongo`: 전체 저장과 압축을 실행합니다.

## 초보자 포인트

이 노드는 선택 사항입니다.
처음 테스트할 때는 연결하지 않아도 됩니다.

데이터가 커지고 후속 질문까지 지원하려면 다음 노드와 세트로 사용합니다.

- 저장: `MongoDB Data Store`
- 다시 불러오기: `MongoDB Data Loader`

## 연결

```text
Analysis Result Merger.analysis_result
-> MongoDB Data Store.payload

MongoDB Data Store.stored_payload
-> Build Final Answer Prompt.analysis_result

MongoDB Data Store.stored_payload
-> Final Answer Builder.analysis_result
```

