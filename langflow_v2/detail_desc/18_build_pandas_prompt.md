# 18. Build Pandas Prompt

## 최근 변경: domain 기반 source 병합

여러 retrieval source를 pandas 분석용 table로 합칠 때 더 이상 `WORK_DT`, `OPER_NAME`, `MCP_NO` 같은 제조 컬럼 우선순위를 코드에 직접 두지 않습니다.

병합 기준은 먼저 `domain.join_rules`에서 찾습니다. 예를 들어 `actual`과 `goal`을 `DAY`, `PRODUCT_CODE`로 합쳐야 한다면 domain에 아래처럼 등록합니다.

```json
{
  "join_rules": [
    {
      "left_dataset": "actual",
      "right_dataset": "goal",
      "keys": ["DAY", "PRODUCT_CODE"]
    }
  ]
}
```

등록된 rule이 없으면 공통 컬럼 중 수치형 measure가 아닌 컬럼을 일반 fallback join key로 사용합니다. 이 fallback은 특정 사내 컬럼명을 가정하지 않기 때문에, 테이블별 컬럼명이 달라도 domain/table catalog에서 관리할 수 있습니다.

## 이 노드 역할

조회된 데이터와 domain 정보를 바탕으로 pandas 분석 코드를 생성할 LLM prompt를 만드는 노드입니다.

이 노드는 코드를 실행하지 않습니다. "어떤 pandas 코드를 만들면 되는지"를 LLM에게 잘 설명하는 prompt payload만 구성합니다.

## 왜 필요한가

LLM에게 단순히 "분석해줘"라고만 전달하면 실제 컬럼명, 예시 row, metric 공식, 데이터셋 관계를 모른 채 코드를 만들 수 있습니다.

이 노드는 실제 조회 결과의 컬럼과 샘플 row, domain에 정의된 metric/formula를 prompt에 넣어 LLM이 실행 가능한 pandas 코드를 만들 확률을 높입니다.

## 입력

| 입력 포트 | 설명 |
| --- | --- |
| `retrieval_payload` | pandas 분석이 필요한 조회 결과입니다. |
| `domain_payload` | metric 공식, 분석 규칙, dataset 설명 등이 들어 있는 domain 정보입니다. |

## 출력

| 출력 포트 | 설명 |
| --- | --- |
| `prompt_payload` | `LLM JSON Caller`에 전달할 pandas 코드 생성 prompt입니다. |

## 주요 함수 설명

| 함수 | 역할 |
| --- | --- |
| `_merge_sources` | 여러 source result를 pandas 분석용 하나의 table로 병합합니다. |
| `_domain_prompt` | domain 정보를 LLM이 읽기 쉬운 설명 문장으로 바꿉니다. |
| `_build_prompt` | columns, sample rows, intent plan, domain hint를 포함한 prompt 문자열을 만듭니다. |
| `build_pandas_prompt` | 전체 prompt payload를 구성합니다. |

## 초보자 확인용

이 노드는 pandas를 실행하지 않습니다. 다음 노드인 `LLM JSON Caller`가 이 prompt를 보고 pandas 코드를 만들고, 실제 실행은 `Pandas Analysis Executor`에서 합니다.

여러 데이터셋이 조회된 경우 `_merge_sources`가 공통 컬럼을 기준으로 분석용 table을 준비합니다.

## 연결

```text
Retrieval Postprocess Router.post_analysis
-> Build Pandas Prompt.retrieval_payload

MongoDB Domain Loader.domain_payload
-> Build Pandas Prompt.domain_payload

Build Pandas Prompt.prompt_payload
-> LLM JSON Caller.prompt_payload
```

## Python 코드 상세 해석

### 입력 예시

```json
{
  "retrieval_payload": {
    "intent_plan": {
      "group_by": ["MODE"],
      "metrics": ["achievement_rate"]
    },
    "source_results": [
      {
        "dataset_key": "production",
        "success": true,
        "data": [{"MODE": "DDR5", "production": 100, "target": 120}]
      }
    ]
  },
  "domain_payload": {
    "domain": {
      "metrics": {
        "achievement_rate": {
          "formula": "production / target * 100"
        }
      }
    }
  }
}
```

### 출력 예시

```json
{
  "prompt_payload": {
    "prompt": "You are writing pandas code...",
    "rows": [
      {"MODE": "DDR5", "production": 100, "target": 120}
    ],
    "columns": ["MODE", "production", "target"],
    "plan": {
      "group_by": ["MODE"],
      "metrics": ["achievement_rate"]
    }
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 설명 |
| --- | --- | --- | --- |
| `_merge_sources` | source result list | rows, columns, merge_notes | pandas 분석에 쓸 단일 table을 준비합니다. |
| `_domain_prompt` | domain dict | 설명 문자열 | metric과 규칙을 prompt에 넣기 쉬운 문장으로 만듭니다. |
| `_build_prompt` | plan, rows, columns | prompt string | LLM에게 코드 작성 규칙을 전달합니다. |
| `build_pandas_prompt` | retrieval/domain payload | prompt payload | LLM 호출에 필요한 정보를 하나로 묶습니다. |

### 코드 흐름

```text
retrieval_payload 입력
-> source_results 추출
-> 분석용 rows/columns 준비
-> domain metric/formula 설명 생성
-> pandas code 생성 prompt 작성
-> prompt_payload 출력
```

## 함수 코드 단위 해석: `_merge_sources`

### 함수 input

```json
[
  {
    "dataset_key": "production",
    "success": true,
    "data": [{"WORK_DT": "20260426", "MODE": "DDR5", "production": 100}]
  },
  {
    "dataset_key": "target",
    "success": true,
    "data": [{"WORK_DT": "20260426", "MODE": "DDR5", "target": 120}]
  }
]
```

### 함수 output

```json
{
  "success": true,
  "data": [
    {"WORK_DT": "20260426", "MODE": "DDR5", "production": 100, "target": 120}
  ],
  "columns": ["WORK_DT", "MODE", "production", "target"]
}
```

### 핵심 코드 해석

```python
valid = [item for item in source_results if item.get("success") and isinstance(item.get("data"), list)]
```

성공했고 row list를 가진 source만 병합 대상으로 사용합니다.

```python
if len(valid) == 1:
    rows = deepcopy(valid[0].get("data", []))
    return {"success": True, "data": rows, "columns": _rows_columns(rows), ...}
```

source가 하나뿐이면 별도 merge 없이 그대로 분석 table로 사용합니다.

```python
shared = set(str(column) for column in merged.columns) & set(str(column) for column in right.columns)
join_columns = _select_join_columns(domain, current_name, right_name, merged, right, shared)
```

source가 여러 개라면 공통 컬럼을 찾고, 날짜/공정/제품처럼 선호되는 join key를 우선 사용합니다.

```python
merged = merged.merge(right, how="inner", on=join_columns, suffixes=("", f"_{right_name}"))
```

공통 key를 기준으로 DataFrame을 병합합니다.

```python
return {"success": True, "data": rows, "columns": [str(column) for column in merged.columns], "merge_notes": notes}
```

병합 결과를 다시 list[dict] 형태로 바꿔 prompt payload에 넣습니다.

## 추가 함수 코드 단위 해석: `_build_prompt`

이 함수는 pandas code LLM에게 전달할 실제 prompt 문자열을 만듭니다.

```python
return f"""You are writing safe pandas code for a manufacturing data assistant.
Return JSON only.
```

LLM의 역할과 응답 형식을 먼저 고정합니다. 여기서는 자연어 설명이 아니라 JSON만 반환하도록 요구합니다.

```python
- A pandas DataFrame named df already exists.
- Use only existing columns.
- Assign the final DataFrame to a variable named result.
```

executor가 제공하는 실행 환경을 명확히 알려줍니다. 특히 최종 결과 변수 이름을 `result`로 고정해야 `Pandas Analysis Executor`가 결과를 꺼낼 수 있습니다.

```python
- Do not import modules, read files, open sockets, or use eval/exec.
```

LLM이 위험한 코드를 만들지 않도록 prompt 단계에서도 제한을 알려줍니다. 실제 실행 전에는 executor의 `_validate_code`가 한 번 더 막습니다.

```python
Intent plan:
{json.dumps(plan, ensure_ascii=False, default=str, indent=2)}
```

group_by, sort, top_n, filters 같은 분석 의도를 prompt에 넣습니다.

```python
Available columns:
{json.dumps(columns, ensure_ascii=False)}
```

LLM이 존재하지 않는 컬럼을 만들지 않도록 실제 사용 가능한 컬럼 목록을 제공합니다.

```python
Data preview:
{json.dumps(rows[:5], ensure_ascii=False, default=str, indent=2)}
```

전체 데이터를 넣지 않고 앞 5개 row만 보여줍니다. token을 줄이면서도 데이터 형태를 이해시키기 위한 선택입니다.

## 추가 함수 코드 단위 해석: `_domain_from_payload`

```python
if isinstance(payload.get("domain_payload"), dict):
    payload = payload["domain_payload"]
```

Domain Loader 출력처럼 감싸진 구조면 내부 payload로 들어갑니다.

```python
if isinstance(payload.get("domain"), dict):
    return deepcopy(payload["domain"])
```

정상 domain payload이면 실제 domain dict를 반환합니다.

```python
if any(key in payload for key in ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")):
    return deepcopy(payload)
```

domain dict 자체가 바로 들어온 경우도 허용합니다.

```python
return {"products": {}, "process_groups": {}, "terms": {}, "datasets": {}, "metrics": {}, "join_rules": []}
```

domain이 없더라도 뒤 prompt 생성이 실패하지 않도록 빈 domain 구조를 반환합니다.
