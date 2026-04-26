# 09. Dummy Data Retriever

## 한 줄 역할

Oracle DB 없이도 flow를 테스트할 수 있도록 가짜 제조 데이터를 만들어 반환하는 노드입니다.

## 왜 필요한가

실제 DB 연결 전에도 Langflow 분기, pandas 분석, 최종 답변 흐름을 확인해야 합니다.
이 노드는 `production`, `target`, `wip` 같은 dataset을 dummy row로 만들어 줍니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Intent Route Router.single_retrieval` 또는 `multi_retrieval` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | 조회 결과처럼 생긴 source_results와 current_data를 담습니다. |

## 주요 함수 설명

- `_base_rows`: 날짜, 공정, MODE별 기본 row를 만듭니다.
- `_apply_filters`: intent plan에 있는 공정/제품 filter를 row에 적용합니다.
- `get_production_data`: 생산량 dummy 데이터를 만듭니다.
- `get_target_data`: 목표량 dummy 데이터를 만듭니다.
- `get_wip_status`: 재공량 dummy 데이터를 만듭니다.
- `_run_job`: retrieval job의 `tool_name`에 맞는 dummy 함수를 호출합니다.
- `retrieve_dummy_data`: 여러 job을 순서대로 실행하고 결과를 합칩니다.

## 출력 구조

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {
        "dataset_key": "production",
        "data": [],
        "summary": "total rows ..."
      }
    ],
    "current_data": {}
  }
}
```

## 초보자 포인트

dummy retriever는 SQL이나 DB 연결을 전혀 사용하지 않습니다.

실제 운영 연결 전에는 이 노드로 먼저 flow를 검증하는 것이 안전합니다.
`single`과 `multi` branch를 캔버스에서 따로 보려면 같은 파일을 두 번 올려 각각 연결합니다.

## 연결

```text
Intent Route Router.single_retrieval
-> Dummy Data Retriever (Single).intent_plan

Intent Route Router.multi_retrieval
-> Dummy Data Retriever (Multi).intent_plan

Dummy Data Retriever.retrieval_payload
-> Retrieval Payload Merger.single_retrieval 또는 multi_retrieval
```

