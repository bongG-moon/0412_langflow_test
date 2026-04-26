# Langflow v2 Node Detail Descriptions

이 폴더는 `langflow_v2`에 있는 Custom Component 노드들을 번호 순서대로 설명합니다.

목표는 Python 초보자도 다음 질문에 답할 수 있게 만드는 것입니다.

- 이 노드는 왜 필요한가?
- Langflow 화면에서 어떤 입력 포트를 연결해야 하는가?
- 출력에는 어떤 데이터가 들어가는가?
- 코드 안의 주요 함수는 어떤 순서로 실행되는가?
- 연결할 때 자주 실수하는 부분은 무엇인가?

## 읽는 순서

처음에는 전체 흐름을 한 번에 외우려고 하지 않아도 됩니다.

1. `00`-`08`: 질문을 상태로 만들고, LLM으로 의도와 분기 방향을 정하는 부분
2. `09`-`16`: 데이터를 조회하거나 기존 데이터를 다시 쓰고, pandas가 필요한지 나누는 부분
3. `17`-`20`: pandas 분석을 만들고 실행한 뒤 결과를 하나로 합치는 부분
4. `21`-`25`: 큰 데이터 저장, 최종 답변 생성, 다음 턴을 위한 메모리 저장 부분

## 큰 흐름

```text
질문 입력
-> 상태 구성
-> 도메인/테이블 정보 로드
-> intent prompt 생성
-> LLM 호출
-> intent 정규화
-> single/multi/follow-up/finish 분기
-> 데이터 조회 또는 기존 데이터 재사용
-> direct/post-analysis 분기
-> pandas 분석 또는 직접 결과
-> 최종 답변 LLM
-> 최종 메시지와 next_state 생성
-> Langflow Message History에 저장
```

## 중요한 약속

v2 노드는 Langflow standalone custom component 방식입니다.

따라서 각 Python 파일은 필요한 helper 함수를 자기 파일 안에 직접 가지고 있습니다.
겉으로 보면 중복 코드가 있어 보이지만, Langflow에 개별 노드 파일을 직접 등록하기 위해 의도적으로 이렇게 작성했습니다.

## 모든 노드에 반복해서 나오는 공통 코드 읽는 법

각 노드 파일을 열면 처음에 비슷한 helper 함수와 fallback class가 반복됩니다. 이 부분은 비즈니스 로직이 아니라 "Langflow 밖에서도 테스트가 되게 하기 위한 안전장치"입니다.

| 코드 이름 | 초보자용 설명 | 입력 예시 | 출력 예시 |
| --- | --- | --- | --- |
| `_load_attr` | Langflow 버전에 따라 import 위치가 달라도 필요한 class를 찾아옵니다. | `["langflow.schema"], "Data", _FallbackData` | 실제 `Data` class 또는 fallback class |
| `_FallbackComponent` | Langflow가 없는 테스트 환경에서도 class 선언이 깨지지 않게 하는 가짜 Component입니다. | 없음 | 테스트에서만 쓰이는 빈 parent class |
| `_FallbackInput` | `MessageTextInput`, `DataInput` 같은 입력 class를 대신하는 가짜 class입니다. | `name="payload"` | `name`, `display_name` 같은 속성을 가진 객체 |
| `_FallbackOutput` | `Output(...)` 선언을 테스트 환경에서도 보존합니다. | `name="result", method="build"` | output 설정 객체 |
| `_FallbackData` | Langflow의 `Data(data={...})`를 흉내 냅니다. | `{"success": true}` | `.data`에 dict가 들어 있는 객체 |
| `_make_input` | 실제 Langflow input class나 fallback input class를 만들어 줍니다. | `name="chat_input"` | Langflow 입력 포트 객체 |
| `_make_data` | 함수 결과 dict를 Langflow `Data` 형태로 감쌉니다. | `{"rows": []}` | `Data(data={"rows": []})` |
| `_payload_from_value` | 앞 노드에서 넘어온 값이 `Data`, dict, JSON 문자열 중 무엇이든 dict로 꺼냅니다. | `Data(data={"a": 1})` | `{"a": 1}` |
| `_parse_jsonish` | JSON 문자열, 코드블록 JSON, 이미 dict인 값을 최대한 안전하게 파싱합니다. | ````json {"a": 1} ```` | `({"a": 1}, [])` |
| `_json_safe` | datetime, ObjectId처럼 JSON 저장이 어려운 값을 문자열 등으로 바꿉니다. | `datetime(...)` | `"2026-04-26T..."` |

노드 설명 문서에서는 이런 반복 helper를 매번 길게 풀지 않고, 해당 노드의 실제 판단과 결과를 만드는 핵심 함수 중심으로 설명합니다.

## 함수 설명을 읽는 방법

각 노드별 문서의 `Python 코드 상세 해석` 섹션은 다음 순서로 읽으면 됩니다.

1. `입력 예시`를 보고 Langflow 앞 노드가 어떤 dict를 넘기는지 확인합니다.
2. `핵심 함수별 해석`에서 함수가 어떤 값을 꺼내고, 왜 그 처리를 하는지 봅니다.
3. `출력 예시`를 보고 다음 노드가 어떤 key를 기대하는지 확인합니다.
4. 코드 파일을 열어서 같은 함수 이름을 검색하면 문서와 실제 코드가 1:1로 이어집니다.

중요한 점은 Langflow custom node의 method 대부분이 마지막에 `Data(data=payload)`를 반환한다는 것입니다. 즉, Python 함수가 만든 `dict`가 그대로 다음 노드의 입력 재료가 됩니다.

## 코드 단위 해석의 기준

각 노드 문서에서 `함수 코드 단위 해석`은 다음 기준으로 작성합니다.

- 함수 전체 역할을 먼저 설명합니다.
- 함수 input이 실제로 어떤 dict/list/string 형태인지 예시를 둡니다.
- 함수 output이 다음 노드로 어떤 형태로 넘어가는지 예시를 둡니다.
- 중요한 코드 블록을 그대로 보여주고, 각 줄이 왜 필요한지 설명합니다.
- `continue`, `return`, `or`, list comprehension, dict merge처럼 Python 초보자가 헷갈리기 쉬운 문법은 문장으로 풀어씁니다.
- 모든 fallback/import helper를 길게 반복하지는 않고, 노드 동작을 바꾸는 핵심 함수 위주로 해석합니다.

예를 들어 `10_dummy_data_retriever.md`의 `_apply_filters` 설명은 이 기준의 대표 예시입니다.
