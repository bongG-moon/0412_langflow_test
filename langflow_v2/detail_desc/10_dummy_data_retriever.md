# 10. Dummy Data Retriever

## 이 노드 역할

Oracle DB 없이도 flow를 테스트할 수 있도록 가짜 제조 데이터를 만들어 반환하는 노드입니다.

## 왜 필요한가

실제 DB 연결을 하기 전에 Langflow 분기, pandas 분석, 최종 답변 흐름이 맞는지 확인해야 합니다. 이 노드는 `production`, `target`, `wip`, `equipment` 같은 dataset을 dummy row로 만들어 줍니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `intent_plan` | `Intent Route Router.single_retrieval` 또는 `multi_retrieval` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | 실제 조회 결과처럼 생긴 `source_results`, `current_datasets`, `source_snapshots`를 담습니다. |

## 주요 함수 설명

- `_normalize_yyyymmdd`: 날짜 입력을 `YYYYMMDD`로 맞춥니다.
- `_stable_seed`: 같은 날짜 질문에서 같은 dummy 데이터가 나오도록 seed를 만듭니다.
- `_matches`: row 값이 필터 조건과 맞는지 비교합니다.
- `_apply_filters`: `process_name`, `mode`, `line`, `den`, `tech`, `mcp_no`, `product_name` 같은 필터를 row에 적용합니다.
- `_apply_column_filters`: `PKG_TYPE1`처럼 실제 컬럼 기준 조건을 적용합니다.
- `_base_rows`: 날짜, 공정, 제품 조합으로 기본 row를 만듭니다.
- `get_production_data`: 생산량 dummy 데이터를 만듭니다.
- `get_target_data`: 목표량 dummy 데이터를 만듭니다.
- `get_wip_status`: 재공 dummy 데이터를 만듭니다.
- `get_equipment_status`: 설비 가동률 dummy 데이터를 만듭니다.
- `_run_job`: retrieval job의 `tool_name`에 맞는 dummy 함수를 실행합니다.
- `retrieve_dummy_data`: 여러 retrieval job을 실행하고 `retrieval_payload`를 만듭니다.

## 출력 구조

```json
{
  "retrieval_payload": {
    "route": "single_retrieval",
    "source_results": [
      {
        "success": true,
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "data": [],
        "summary": "total rows 12, production 33,097"
      }
    ],
    "current_datasets": {},
    "source_snapshots": [],
    "intent_plan": {},
    "state": {},
    "used_dummy_data": true
  }
}
```

## 초보자 확인용

Dummy retriever는 SQL이나 DB 연결을 전혀 사용하지 않습니다. 실제 운영 연결 전에 flow 전체를 안전하게 검증하기 위한 가짜 데이터 노드입니다.

`single`과 `multi` branch를 Langflow 화면에서 따로 보고 싶으면 같은 파일의 컴포넌트를 두 번 올려 각각 연결하면 됩니다.

## 연결

```text
Intent Route Router.single_retrieval
-> Dummy Data Retriever (Single).intent_plan

Intent Route Router.multi_retrieval
-> Dummy Data Retriever (Multi).intent_plan

Dummy Data Retriever.retrieval_payload
-> Retrieval Payload Merger.single_retrieval 또는 multi_retrieval
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "intent_plan": {
    "route": "single_retrieval",
    "retrieval_jobs": [
      {
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "params": {
          "date": "20260425"
        },
        "filters": {
          "process_name": ["D/A1"],
          "mode": ["DDR5"]
        },
        "column_filters": {
          "PKG_TYPE1": ["PKG_A"]
        }
      }
    ]
  },
  "state": {
    "session_id": "abc"
  }
}
```

### 출력 예시

```json
{
  "retrieval_payload": {
    "route": "single_retrieval",
    "source_results": [
      {
        "success": true,
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "data": [
          {
            "WORK_DT": "20260425",
            "OPER_NAME": "D/A1",
            "MODE": "DDR5",
            "production": 2940
          }
        ],
        "summary": "total rows 1, production 2,940"
      }
    ],
    "used_dummy_data": true
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 필요한가 |
| --- | --- | --- | --- |
| `_normalize_yyyymmdd` | `"2026-04-25"` | `"20260425"` | 날짜 형식을 dummy row의 `WORK_DT`와 비교 가능하게 맞춥니다. |
| `_stable_seed` | `"20260425"` | 정수 seed | 같은 날짜 질문에서 같은 dummy 데이터가 나오게 합니다. |
| `_matches` | `"D/A1"`, `["D/A1"]` | `true` | 단일 값과 list 필터를 같은 방식으로 비교합니다. |
| `_apply_filters` | rows, filters | 필터링된 rows | 표준 필터 조건을 dummy 데이터에 적용합니다. |
| `_apply_column_filters` | rows, `{"PKG_TYPE1": ["PKG_A"]}` | 필터링된 rows | 실제 컬럼 기준 조건을 적용합니다. |
| `_base_rows` | params | 공정/제품 조합 row list | 모든 dummy tool이 공통으로 쓰는 기본 제조 row를 만듭니다. |
| `_result` | tool name, rows, summary | source result dict | 모든 dummy tool이 같은 output schema를 반환하게 합니다. |
| `_run_job` | retrieval job | source result | `tool_name`에 맞는 dummy 함수를 찾아 실행합니다. |
| `retrieve_dummy_data` | routed intent plan | retrieval payload | 여러 job을 실행하고 source_results/current_datasets를 만듭니다. |
| `build_payload` | Langflow input | `Data(data=retrieval_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
Intent Route Router에서 active branch 수신
-> skipped이면 빈 retrieval_payload 반환
-> finish route면 early_result 형태로 반환
-> followup_transform이면 current_data를 source_result처럼 감싸 반환
-> retrieval_jobs 반복
-> job.tool_name에 맞는 get_xxx_data 함수 실행
-> column_filters 적용
-> source_results, current_datasets, source_snapshots 생성
-> Retrieval Payload Merger로 전달
```

## 함수 코드 단위 해석: `_apply_filters`

이 함수는 dummy row 목록에서 사용자의 표준 필터 조건에 맞는 row만 남깁니다.

### 함수 원문

```python
def _apply_filters(rows: list[Dict[str, Any]], params: Dict[str, Any]) -> list[Dict[str, Any]]:
    filtered = []
    for row in rows:
        if not _matches(row.get("OPER_NAME"), params.get("process_name") or params.get("process")):
            continue
        if not _matches(row.get("OPER_NUM"), params.get("oper_num")):
            continue
        if not _matches(row.get("LINE"), params.get("line_name") or params.get("line")):
            continue
        if not _matches(row.get("MODE"), params.get("mode")):
            continue
        if not _matches(row.get("DEN"), params.get("den")):
            continue
        if not _matches(row.get("TECH"), params.get("tech")):
            continue
        if not _matches(row.get("MCP_NO"), params.get("mcp_no")):
            continue
        product_name = params.get("product_name") or params.get("product")
        if product_name and not any(_matches(row.get(column), product_name) for column in ("MODE", "DEN", "TECH", "MCP_NO", "PKG_TYPE1", "PKG_TYPE2")):
            continue
        filtered.append(row)
    return filtered
```

### 함수 input

`rows`는 조회된 것처럼 만든 dummy row 목록입니다.

```json
[
  {
    "OPER_NAME": "D/A1",
    "OPER_NUM": "DA10",
    "LINE": "DA-L1",
    "MODE": "DDR5",
    "DEN": "512G",
    "TECH": "WB",
    "MCP_NO": "MCP-A1",
    "PKG_TYPE1": "PKG_A"
  },
  {
    "OPER_NAME": "W/B1",
    "OPER_NUM": "WB10",
    "LINE": "WB-L1",
    "MODE": "HBM3",
    "DEN": "1024G",
    "TECH": "TSV",
    "MCP_NO": "MCP-H1",
    "PKG_TYPE1": "PKG_H"
  }
]
```

`params`는 intent plan에서 넘어온 필터 조건입니다.

```json
{
  "process_name": ["D/A1"],
  "mode": ["DDR5"],
  "den": ["512G"]
}
```

### 함수 output

조건에 맞는 row만 남깁니다.

```json
[
  {
    "OPER_NAME": "D/A1",
    "OPER_NUM": "DA10",
    "LINE": "DA-L1",
    "MODE": "DDR5",
    "DEN": "512G",
    "TECH": "WB",
    "MCP_NO": "MCP-A1",
    "PKG_TYPE1": "PKG_A"
  }
]
```

### 코드 블록별 해석

```python
filtered = []
```

조건을 통과한 row를 담을 빈 list를 만듭니다.

```python
for row in rows:
```

모든 row를 하나씩 검사합니다.

```python
if not _matches(row.get("OPER_NAME"), params.get("process_name") or params.get("process")):
    continue
```

공정 조건을 검사합니다. 조건이 맞지 않으면 `continue`로 현재 row를 버리고 다음 row로 넘어갑니다.

```python
if not _matches(row.get("MODE"), params.get("mode")):
    continue
```

mode 조건을 검사합니다. `DDR5`만 요청했으면 `LPDDR5`, `HBM3` row는 제외됩니다.

```python
product_name = params.get("product_name") or params.get("product")
if product_name and not any(_matches(row.get(column), product_name) for column in ("MODE", "DEN", "TECH", "MCP_NO", "PKG_TYPE1", "PKG_TYPE2")):
    continue
```

제품명 조건은 특정 컬럼 하나로 고정하기 어렵습니다. 그래서 `MODE`, `DEN`, `TECH`, `MCP_NO`, `PKG_TYPE1`, `PKG_TYPE2` 중 하나라도 맞으면 제품 조건을 만족한 것으로 봅니다.

```python
filtered.append(row)
```

모든 조건을 통과한 row만 결과 list에 넣습니다.

## 함수 코드 단위 해석: `retrieve_dummy_data`

이 함수는 intent plan을 보고 실제 dummy retrieval payload를 만듭니다.

### 중요한 분기

```python
if payload.get("skipped"):
    return {"retrieval_payload": {"skipped": True, ...}}
```

Router에서 선택되지 않은 branch라면 아무 조회도 하지 않고 skipped payload를 반환합니다.

```python
if plan.get("route") == "followup_transform":
    current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
```

후속 분석 route라면 새 dummy row를 만들지 않고 이전 `current_data`를 source_result처럼 감쌉니다.

```python
jobs = plan.get("retrieval_jobs") if isinstance(plan.get("retrieval_jobs"), list) else []
source_results = [_run_job(job) for job in jobs if isinstance(job, dict)]
```

새 조회 route라면 retrieval job을 하나씩 실행합니다.

```python
"current_datasets": _build_current_datasets(source_results),
"source_snapshots": _build_source_snapshots(source_results, jobs),
```

후속 질문에서 다시 쓸 수 있도록 현재 조회 결과의 dataset별 요약과 snapshot을 함께 만듭니다.

## 추가 함수 코드 단위 해석: `_apply_column_filters`

이 함수는 `main_flow_filters`에 정의되지 않았지만 실제 테이블 컬럼으로 들어온 조건을 dummy row에 적용합니다.

```python
if not isinstance(column_filters, dict) or not column_filters:
    return rows
```

컬럼 필터가 없으면 원본 rows를 그대로 반환합니다.

```python
for row in rows:
    keep = True
    for column, expected in column_filters.items():
```

각 row마다 모든 column filter 조건을 검사합니다.

```python
if column in row and not _matches(row.get(column), expected):
    keep = False
    break
```

해당 컬럼이 row에 있고 값이 기대 조건과 맞지 않으면 row를 제외합니다. 컬럼이 없는 경우에는 dummy dataset마다 컬럼 구성이 다를 수 있으므로 강제로 실패 처리하지 않습니다.

```python
if keep:
    filtered.append(row)
```

모든 조건을 통과한 row만 결과에 남깁니다.

## 추가 함수 코드 단위 해석: `_base_rows`

dummy 데이터셋의 공통 기본 row를 만드는 함수입니다.

```python
work_date = _normalize_yyyymmdd(params.get("date"))
random.seed(_stable_seed(work_date, offset))
```

날짜를 `YYYYMMDD`로 맞추고, 날짜와 offset 기반 seed를 사용합니다. 같은 날짜와 dataset이면 매번 같은 dummy 값이 나오도록 하기 위한 구조입니다.

```python
rows = [{"WORK_DT": work_date, **process, **product} for process in PROCESSES for product in PRODUCTS]
```

공정 목록과 제품 목록을 조합해 제조 현장 데이터처럼 보이는 기본 row grid를 만듭니다.

```python
return _apply_filters(rows, params)
```

process, mode, line, den, tech, mcp_no 같은 표준 조건을 적용합니다.

## 추가 함수 코드 단위 해석: `_run_job`

```python
tool_name = str(job.get("tool_name") or job.get("dataset_key") or "")
tool = TOOL_REGISTRY.get(tool_name) or TOOL_REGISTRY.get(str(job.get("dataset_key") or ""))
```

retrieval job에서 실행할 dummy tool을 찾습니다. `tool_name`으로 못 찾으면 `dataset_key`로 한 번 더 찾습니다.

```python
params = deepcopy(job.get("params", {}))
params.update({key: value for key, value in (job.get("filters") or {}).items() if value not in (None, "", [])})
```

required params와 semantic filters를 하나의 params dict로 합칩니다. dummy tool 함수들은 이 params를 기준으로 row를 만듭니다.

```python
result = tool(params)
```

선택된 dummy 데이터 생성 함수를 실행합니다.

```python
result["data"] = _apply_column_filters(result.get("data", []), job.get("column_filters", {}))
```

semantic filter 이후 실제 컬럼명 기반 조건을 추가로 적용합니다.

```python
result["filter_plan"] = deepcopy(job.get("filter_plan", []))
```

후속 질문과 pandas executor가 어떤 필터가 적용됐는지 알 수 있도록 filter plan을 결과에 보존합니다.
