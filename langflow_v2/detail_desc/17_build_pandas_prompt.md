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

