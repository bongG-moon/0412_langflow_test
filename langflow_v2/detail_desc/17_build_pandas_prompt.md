# 17. Build Pandas Prompt

## 한 줄 역할

조회된 데이터와 domain 정보를 바탕으로 pandas 코드 생성을 위한 prompt를 만드는 노드입니다.

## 왜 필요한가

LLM에게 그냥 "분석해줘"라고 하면 컬럼명을 잘못 쓰거나 불필요한 코드를 만들 수 있습니다.
이 노드는 실제 조회된 컬럼과 row 예시, metric 공식, grouping hint를 prompt에 넣어 pandas 계획을 더 정확하게 만듭니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `retrieval_payload` | pandas 분석이 필요한 조회 결과입니다. |
| `domain_payload` | metric 공식, grouping hint 등 분석에 필요한 domain 정보입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `prompt_payload` | `LLM JSON Caller (Pandas)`에 넘길 prompt입니다. |

## 주요 함수 설명

- `_source_results`: retrieval payload에서 source result 목록을 꺼냅니다.
- `_merge_sources`: 여러 dataset row를 분석용으로 합칠 준비를 합니다.
- `_domain_prompt`: domain metric과 alias 정보를 짧은 설명으로 만듭니다.
- `_build_prompt`: LLM에게 줄 pandas 코드 작성 지시문을 만듭니다.
- `build_pandas_prompt`: 전체 과정을 실행합니다.

## 초보자 포인트

이 노드는 pandas 코드를 실행하지 않습니다.
코드를 만들기 위한 prompt만 작성합니다.

실제 LLM 호출은 다음의 `LLM JSON Caller (Pandas)`가 하고, 실행은 `Pandas Analysis Executor`가 합니다.

## 연결

```text
Retrieval Postprocess Router.post_analysis
-> Build Pandas Prompt.retrieval_payload

Domain Loader.domain_payload
-> Build Pandas Prompt.domain_payload

Build Pandas Prompt.prompt_payload
-> LLM JSON Caller (Pandas).prompt_payload
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
        "data": [{"MODE": "A", "production": 100}]
      },
      {
        "dataset_key": "wip",
        "data": [{"MODE": "A", "wip_qty": 50}]
      }
    ]
  },
  "domain_payload": {
    "domain": {
      "metrics": {
        "achievement_rate": {
          "formula": "sum(production) / sum(wip_qty) * 100"
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
    "prompt": "Write pandas code that creates result_df...",
    "retrieval_payload": {"source_results": []},
    "plan": {
      "group_by": ["MODE"],
      "metrics": ["achievement_rate"]
    },
    "rows": [
      {"MODE": "A", "production": 100, "wip_qty": 50}
    ],
    "columns": ["MODE", "production", "wip_qty"]
  }
}
```

### 핵심 함수별 해석

| 함수 | 입력 예시 | 출력 예시 | 왜 이 코드가 필요한가 |
| --- | --- | --- | --- |
| `_pd` | 없음 | pandas module | pandas가 설치되어 있는지 확인하고 필요할 때 import합니다. |
| `_source_results` | retrieval payload | source result list | 조회 결과 배열만 꺼냅니다. |
| `_merge_sources` | production rows + wip rows | 합쳐진 rows/columns | 여러 dataset 결과를 pandas가 다룰 하나의 row 목록으로 준비합니다. |
| `_domain_from_payload` | domain payload | domain dict | formula, metric 설명을 prompt에 넣기 위해 꺼냅니다. |
| `_domain_prompt` | domain dict | 짧은 도메인 설명 문자열 | LLM이 컬럼 의미와 metric 계산식을 참고하도록 사람이 읽는 문장으로 바꿉니다. |
| `_build_prompt` | plan, rows, columns, domain | pandas code 작성 prompt | LLM에게 `result_df`를 만들라는 구체적 지시를 작성합니다. |
| `build_pandas_prompt` | retrieval payload, domain | prompt payload | pandas LLM 호출에 필요한 모든 재료를 하나로 묶습니다. |
| `build_prompt` | Langflow input | `Data(data=prompt_payload)` | Langflow output method입니다. |

### 코드 흐름

```text
retrieval_payload에서 source_results 추출
-> 여러 source rows를 분석용 rows로 병합
-> domain metric/formula 설명 생성
-> LLM이 pandas code를 반환하도록 prompt 작성
```

### 초보자 포인트

이 노드는 pandas를 실행하지 않습니다. "어떤 pandas 코드를 만들면 좋을지" LLM에게 요청하는 prompt만 만듭니다.

## 함수 코드 단위 해석: `_merge_sources`

이 함수는 여러 dataset에서 조회된 rows를 pandas가 분석할 하나의 table 형태로 준비합니다.

### 함수 input

```json
[
  {
    "dataset_key": "production",
    "data": [{"MODE": "A", "production": 100}]
  },
  {
    "dataset_key": "wip",
    "data": [{"MODE": "A", "wip_qty": 50}]
  }
]
```

### 함수 output

```json
{
  "success": true,
  "data": [
    {"MODE": "A", "production": 100, "wip_qty": 50}
  ],
  "columns": ["MODE", "production", "wip_qty"]
}
```

### 핵심 코드 해석

```python
frames = []
for source in source_results:
    rows = source.get("data") if isinstance(source.get("data"), list) else []
```

각 source result에서 row list를 꺼냅니다.

```python
frame = pd.DataFrame(rows)
frames.append(frame)
```

rows를 pandas DataFrame으로 바꾸고 `frames`에 모읍니다.

```python
if len(frames) == 1:
    merged = frames[0]
```

source가 하나뿐이면 join할 필요 없이 그대로 사용합니다.

```python
else:
    merged = ...
```

source가 여러 개이면 공통 컬럼을 기준으로 병합합니다. 예를 들어 production과 wip 모두 `MODE`가 있으면 `MODE` 기준으로 합쳐집니다.

```python
return {"success": True, "data": merged.to_dict(orient="records"), "columns": list(merged.columns)}
```

최종 DataFrame을 다시 list[dict]로 바꿔 prompt payload에 넣습니다.

## 추가 함수 코드 단위 해석: `_build_prompt`

이 함수는 Pandas LLM이 읽을 실제 prompt 문자열을 만듭니다.

### 함수 input

```json
{
  "plan": {
    "group_by": ["MODE"],
    "metrics": ["achievement_rate"],
    "analysis_goal": "mode별 생산달성률 계산"
  },
  "rows": [
    {"MODE": "A", "production": 100, "wip_qty": 50}
  ],
  "columns": ["MODE", "production", "wip_qty"],
  "domain": {
    "metrics": {
      "achievement_rate": {
        "formula": "sum(production) / sum(wip_qty) * 100"
      }
    }
  }
}
```

### 함수 output

```text
You are writing pandas code...
Available columns: MODE, production, wip_qty
Return JSON only...
```

### 핵심 코드 해석

```python
preview_rows = rows[:20]
```

LLM prompt에 전체 rows를 다 넣지 않고 앞 일부만 넣습니다. 데이터가 많을수록 token이 커지기 때문입니다.

```python
domain_text = _domain_prompt(domain)
```

domain에 들어 있는 metric formula나 column 의미를 사람이 읽는 설명으로 바꿉니다.

```python
prompt = f"""..."""
```

LLM에게 다음 조건을 지시합니다.

- pandas DataFrame 이름은 `df`를 사용할 것
- 최종 결과는 반드시 `result` 변수에 담을 것
- import나 파일 접근 같은 코드는 쓰지 말 것
- JSON으로 `code`, `explanation`, `warnings`를 반환할 것

```python
Available columns:
{json.dumps(columns, ensure_ascii=False)}
```

LLM이 없는 컬럼명을 지어내지 않도록 실제 사용 가능한 컬럼 목록을 넣습니다.

```python
Sample rows:
{json.dumps(preview_rows, ensure_ascii=False, indent=2)}
```

LLM이 데이터 형태를 이해하도록 일부 row 예시를 넣습니다.

### 왜 이 함수가 중요한가?

Pandas code 품질은 prompt가 좌우합니다. 이 함수가 컬럼, 예시 row, domain formula를 잘 넣어줘야 LLM이 실행 가능한 pandas 코드를 만들 가능성이 높아집니다.
