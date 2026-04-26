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
          "date": "20260425",
          "process": "DA"
        }
      }
    ],
    "state": {
      "session_id": "abc"
    }
  }
}
```

### 출력 예시

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {
        "success": true,
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "data": [
          {"WORK_DT": "20260425", "OPER_NAME": "D/A1", "MODE": "DDR5", "production": 1200}
        ],
        "summary": "total rows 12, production 33097"
      }
    ],
    "current_data": {
      "datasets": {
        "production": {
          "rows": []
        }
      }
    }
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_normalize_yyyymmdd` | `"2026-04-25"` | `"20260425"` | 날짜 입력 형식이 달라도 dummy row의 `WORK_DT`와 비교할 수 있게 맞춥니다. |
| `_stable_seed` | `"20260425"` | 정수 seed | 같은 날짜 질문은 같은 dummy 데이터가 나오게 해 테스트 재현성을 만듭니다. |
| `_apply_filters` | rows, `{"process": "DA"}` | 필터링된 rows | LLM이 만든 filter 조건을 dummy 데이터에도 적용합니다. |
| `_base_rows` | params | 생산/공정/모드 컬럼이 있는 row list | 실제 DB가 없어도 Langflow 흐름을 테스트할 수 있는 기본 row를 만듭니다. |
| `_result` | tool 이름, rows, summary | source result dict | 모든 dummy tool 함수가 같은 output schema를 반환하게 합니다. |
| `get_production_data` 등 | `{"date": "20260425"}` | dataset별 source result | 실제 tool처럼 보이는 dummy 조회 함수입니다. |
| `_run_job` | retrieval job | source result | `tool_name`에 맞는 dummy 함수를 찾아 실행합니다. |
| `retrieve_dummy_data` | intent plan | retrieval payload | 여러 retrieval job을 실행해 `source_results`와 `current_data`를 만듭니다. |
| `build_payload` | Langflow input | `Data(data=retrieval_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
Intent Route Router에서 active branch 수신
-> retrieval_jobs 반복
-> job.tool_name에 맞는 get_xxx_data 함수 실행
-> source_results 배열 생성
-> 후속 질문용 current_data 생성
-> Retrieval Payload Merger로 전달
```

### 초보자 포인트

dummy 함수들은 실제 DB 조회처럼 생겼지만 DB에 접속하지 않습니다. Langflow 선 연결, 분기, pandas, 최종 답변을 먼저 테스트하기 위한 안전한 가짜 데이터입니다.

## 함수 코드 단위 해석: `_apply_filters`

이 함수는 dummy row 목록에서 사용자가 질문한 조건에 맞는 row만 남기는 함수입니다.

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

`rows`는 조회된 데이터 행 목록입니다. 각 행은 dict입니다.

```json
[
  {
    "OPER_NAME": "D/A1",
    "OPER_NUM": "DA10",
    "LINE": "DA-L1",
    "MODE": "DDR5",
    "DEN": "512G",
    "TECH": "V7",
    "MCP_NO": "MCP-001",
    "PKG_TYPE1": "PKG-A",
    "PKG_TYPE2": "PKG-B"
  },
  {
    "OPER_NAME": "W/B1",
    "OPER_NUM": "WB10",
    "LINE": "WB-L1",
    "MODE": "HBM3",
    "DEN": "1024G",
    "TECH": "V9",
    "MCP_NO": "MCP-009",
    "PKG_TYPE1": "PKG-X",
    "PKG_TYPE2": "PKG-Y"
  }
]
```

`params`는 사용자의 질문에서 추출된 필터 조건입니다.

```json
{
  "process": "D/A1",
  "mode": "DDR5",
  "den": "512G"
}
```

### 함수 output

조건에 맞는 row만 남긴 list를 반환합니다.

```json
[
  {
    "OPER_NAME": "D/A1",
    "OPER_NUM": "DA10",
    "LINE": "DA-L1",
    "MODE": "DDR5",
    "DEN": "512G",
    "TECH": "V7",
    "MCP_NO": "MCP-001",
    "PKG_TYPE1": "PKG-A",
    "PKG_TYPE2": "PKG-B"
  }
]
```

### 코드 블록별 해석

```python
filtered = []
```

조건을 통과한 row를 담을 빈 list를 만듭니다. 처음에는 아무 row도 선택되지 않은 상태입니다.

```python
for row in rows:
```

입력으로 들어온 모든 row를 하나씩 검사합니다. row가 12개라면 이 반복문은 12번 실행됩니다.

```python
if not _matches(row.get("OPER_NAME"), params.get("process_name") or params.get("process")):
    continue
```

현재 row의 공정명 `OPER_NAME`이 사용자가 요청한 공정 조건과 맞는지 확인합니다.

- `row.get("OPER_NAME")`: 현재 row의 공정명입니다. 예: `"D/A1"`
- `params.get("process_name") or params.get("process")`: 사용자가 지정한 공정 조건입니다. 예: `"D/A1"`
- `_matches(...)`: 조건이 비어 있으면 통과시키고, 조건이 있으면 값이 맞는지 비교합니다.
- `not _matches(...)`: 조건과 맞지 않는다는 뜻입니다.
- `continue`: 이 row는 버리고 다음 row 검사로 넘어갑니다.

예를 들어 row가 `W/B1`인데 사용자가 `D/A1`을 물었다면 여기서 걸러집니다.

```python
if not _matches(row.get("OPER_NUM"), params.get("oper_num")):
    continue
```

공정 번호 조건을 확인합니다. 예를 들어 `oper_num`이 `"DA10"`이면 `OPER_NUM`이 `"DA10"`인 row만 남깁니다.

```python
if not _matches(row.get("LINE"), params.get("line_name") or params.get("line")):
    continue
```

라인 조건을 확인합니다.

- `line_name`과 `line` 둘 중 하나로 들어올 수 있어서 `or`를 사용합니다.
- `params.get("line_name")`이 있으면 그것을 쓰고, 없으면 `params.get("line")`을 씁니다.

```python
if not _matches(row.get("MODE"), params.get("mode")):
    continue
if not _matches(row.get("DEN"), params.get("den")):
    continue
if not _matches(row.get("TECH"), params.get("tech")):
    continue
if not _matches(row.get("MCP_NO"), params.get("mcp_no")):
    continue
```

제품 속성 조건을 차례로 확인합니다.

- `MODE`: DDR5, LPDDR5, HBM3 같은 mode
- `DEN`: 512G, 256G 같은 density
- `TECH`: 기술 세대
- `MCP_NO`: 제품 번호

각 조건 중 하나라도 맞지 않으면 `continue`로 현재 row를 버립니다.

```python
product_name = params.get("product_name") or params.get("product")
```

사용자가 제품명을 `product_name` 또는 `product`로 줄 수 있으므로 둘 중 있는 값을 선택합니다.

```python
if product_name and not any(_matches(row.get(column), product_name) for column in ("MODE", "DEN", "TECH", "MCP_NO", "PKG_TYPE1", "PKG_TYPE2")):
    continue
```

제품명 조건은 하나의 컬럼만 보는 것이 아니라 여러 제품 관련 컬럼을 함께 봅니다.

예를 들어 사용자가 `"HBM3"`라고 물었을 때 이 값은 `MODE`에 있을 수도 있고, 다른 제품 컬럼에 있을 수도 있습니다. 그래서 다음 컬럼들을 모두 검사합니다.

```text
MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2
```

`any(...)`는 이 중 하나라도 맞으면 true가 됩니다.

- 하나라도 맞으면 row를 통과시킵니다.
- 하나도 안 맞으면 `continue`로 버립니다.

```python
filtered.append(row)
```

여기까지 왔다는 것은 위의 모든 조건을 통과했다는 뜻입니다. 따라서 최종 결과 list에 현재 row를 추가합니다.

```python
return filtered
```

검사를 모두 끝낸 뒤 조건에 맞는 row 목록을 반환합니다.

### 실제 실행 예시

입력:

```json
{
  "rows": [
    {"OPER_NAME": "D/A1", "MODE": "DDR5", "DEN": "512G"},
    {"OPER_NAME": "D/A1", "MODE": "LPDDR5", "DEN": "128G"},
    {"OPER_NAME": "W/B1", "MODE": "DDR5", "DEN": "512G"}
  ],
  "params": {
    "process": "D/A1",
    "mode": "DDR5"
  }
}
```

처리 과정:

| row | 공정 조건 | mode 조건 | 결과 |
| --- | --- | --- | --- |
| `D/A1, DDR5` | 통과 | 통과 | 남김 |
| `D/A1, LPDDR5` | 통과 | 실패 | 버림 |
| `W/B1, DDR5` | 실패 | 확인할 필요 없음 | 버림 |

출력:

```json
[
  {"OPER_NAME": "D/A1", "MODE": "DDR5", "DEN": "512G"}
]
```

### 왜 이렇게 작성했나?

이 함수는 "필터 조건이 있으면 적용하고, 없으면 통과"시키는 구조입니다.

예를 들어 사용자가 mode를 말하지 않았다면 `params.get("mode")`는 비어 있습니다. 이때 `_matches(row.get("MODE"), None)`은 통과로 처리됩니다. 그래서 사용자가 말한 조건만 적용하고, 말하지 않은 조건으로 데이터를 잘못 줄이지 않습니다.

## 추가 함수 코드 단위 해석: `get_production_data`

이 함수는 dummy 생산 데이터를 만드는 tool 함수입니다.

### 함수 input

```json
{
  "date": "20260425",
  "process": "D/A1",
  "mode": "DDR5"
}
```

### 함수 output

```json
{
  "success": true,
  "tool_name": "get_production_data",
  "dataset_key": "production",
  "data": [
    {"WORK_DT": "20260425", "OPER_NAME": "D/A1", "MODE": "DDR5", "production": 2940}
  ],
  "summary": "total rows 1, production 2,940"
}
```

### 핵심 코드 해석

```python
rows = _base_rows(params, 100)
```

기본 공정/제품 조합 row를 만들고, `params` 조건으로 필터링합니다. `100`은 dummy 난수 seed를 dataset별로 다르게 만들기 위한 offset입니다.

```python
for row in rows:
```

필터링된 row 각각에 생산량 값을 넣기 위해 반복합니다.

```python
base = 3300 if row.get("family") == "DA" else 2200
row["production"] = int(base * random.uniform(0.6, 1.2))
```

DA 계열은 기본 생산량을 3300 근처로, 그 외는 2200 근처로 잡습니다. `random.uniform(0.6, 1.2)`는 기본값의 60%-120% 범위에서 값을 흔들어 dummy 데이터를 자연스럽게 만듭니다.

```python
if row.get("OPER_NAME") == "D/A3" and row.get("MODE") == "DDR5":
    row["production"] = 2940 if row.get("DEN") == "512G" else 2680
```

특정 테스트 케이스가 항상 같은 결과를 얻도록 일부 row는 고정값을 넣습니다. 이렇게 하면 회귀 테스트나 playground 확인이 쉬워집니다.

```python
total = sum(int(row["production"]) for row in rows)
```

전체 생산량 합계를 계산합니다.

```python
return _result("get_production_data", "production", rows, f"total rows {len(rows)}, production {_quantity(total)}", params)
```

다음 노드가 읽기 쉬운 표준 source result 형식으로 감싸서 반환합니다.

## 추가 함수 코드 단위 해석: `_run_job`

이 함수는 retrieval job 하나를 실제 dummy tool 함수 하나로 실행합니다.

### 함수 input

```json
{
  "dataset_key": "production",
  "tool_name": "get_production_data",
  "params": {"date": "20260425"},
  "filters": {"process": "D/A1"}
}
```

### 함수 output

```json
{
  "success": true,
  "dataset_key": "production",
  "tool_name": "get_production_data",
  "data": []
}
```

### 핵심 코드 해석

```python
tool_name = str(job.get("tool_name") or job.get("dataset_key") or "")
tool = TOOL_REGISTRY.get(tool_name) or TOOL_REGISTRY.get(str(job.get("dataset_key") or ""))
```

job에서 tool 이름을 꺼낸 뒤, `TOOL_REGISTRY`에서 실제 Python 함수를 찾습니다. tool name이 없으면 dataset key로도 한 번 더 찾습니다.

```python
if tool is None:
    return _error_result(job, f"Unsupported dummy retrieval tool: {tool_name}", "unsupported_tool")
```

등록되지 않은 tool이면 실패 payload를 반환합니다. 예외를 터뜨리기보다 `source_results` 안에 실패 결과를 담아 flow가 계속 설명할 수 있게 합니다.

```python
params = deepcopy(job.get("params", {}))
params.update({key: value for key, value in (job.get("filters") or {}).items() if value not in (None, "", [])})
```

조회 파라미터와 filter를 합칩니다. `deepcopy`는 원래 job을 수정하지 않기 위한 복사입니다.

```python
result = tool(params)
```

드디어 실제 dummy 함수가 실행됩니다. 예를 들어 `get_production_data(params)`가 호출됩니다.

```python
result["dataset_key"] = job.get("dataset_key", result.get("dataset_key"))
result["dataset_label"] = job.get("dataset_label", result.get("dataset_label", result.get("dataset_key")))
```

결과에 dataset key/label을 확실히 채웁니다. 뒤 노드가 어떤 dataset 결과인지 알아야 하기 때문입니다.

## 추가 함수 코드 단위 해석: `retrieve_dummy_data`

이 함수는 active branch payload 전체를 받아 여러 retrieval job을 실행합니다.

### 핵심 코드 해석

```python
payload = _payload_from_value(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
```

router에서 넘어온 payload에서 intent plan과 state를 꺼냅니다.

```python
if payload.get("skipped"):
    return {"retrieval_payload": {"skipped": True, ...}}
```

선택되지 않은 branch라면 실제 조회를 하지 않고 skipped payload를 반환합니다.

```python
jobs = plan.get("retrieval_jobs") if isinstance(plan.get("retrieval_jobs"), list) else []
source_results = [_run_job(job) for job in jobs if isinstance(job, dict)]
```

retrieval job 목록을 하나씩 `_run_job`으로 실행합니다. list comprehension은 반복문을 짧게 쓴 Python 문법입니다.

```python
return {
    "retrieval_payload": {
        "route": plan.get("route", "single_retrieval"),
        "source_results": source_results,
        "current_datasets": _build_current_datasets(source_results),
        "source_snapshots": _build_source_snapshots(source_results, jobs),
        ...
    }
}
```

여러 tool 결과를 `source_results`로 묶고, 후속 질문에서 쓸 `current_datasets`와 `source_snapshots`도 함께 만듭니다.
