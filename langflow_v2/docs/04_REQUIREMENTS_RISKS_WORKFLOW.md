# Langflow v2 Requirements, Risks, and Workflow

이 문서는 현재 구현된 Langflow v2 제조 데이터 분석 flow를 기능 관점에서 요약한 문서이다.

목적은 다음 세 가지다.

1. 이 프로젝트가 다른 일반 챗봇/데이터 조회 flow와 어떤 차별점을 가지는지 정리한다.
2. 현재 구조에서 예상되는 risk와 대응 방안을 미리 정리한다.
3. normalize, parser 같은 부속 노드를 제외하고 기능 단위 workflow를 한눈에 볼 수 있게 한다.

## 1. 개발 요건과 주요 기능

### 1.1 Domain/Table 기반 사용자 의도 추출

이 flow의 첫 번째 핵심 기능은 사용자의 자연어 질문을 제조 데이터 분석용 실행 계획으로 바꾸는 것이다.

사용자가 다음처럼 질문한다고 가정한다.

```text
어제 WB공정 생산달성률을 mode별로 알려줘
```

flow는 단순히 "생산달성률을 물었다" 정도만 판단하지 않는다. domain 정보와 table catalog를 함께 보고 다음을 구조화한다.

| 판단 항목 | 예시 결과 |
| --- | --- |
| 질문 유형 | 신규 데이터 조회 |
| 필요한 metric | 생산달성률 |
| 필요한 dataset | `production`, `wip` |
| 날짜 조건 | 어제 |
| 공정 조건 | WB 공정 그룹 |
| 집계 기준 | `MODE` |
| 후처리 필요 여부 | pandas 계산 필요 |

이 기능이 중요한 이유는 제조 현장 질문이 대부분 축약되어 있기 때문이다. 사용자는 "달성률"이라고만 말하지만, 시스템은 domain의 metric 정의를 보고 `생산량 / 재공 * 100` 같은 계산식과 필요한 dataset을 찾아야 한다.

### 1.2 Domain Metric 기반 복합 Dataset 확장

일반 데이터 조회 챗봇은 질문에 직접 나온 dataset만 조회하는 경우가 많다. 이 flow는 domain metric에 정의된 `required_datasets`를 기준으로 필요한 dataset을 자동 확장한다.

예시 domain item:

```json
{
  "gbn": "metrics",
  "key": "achievement_rate",
  "payload": {
    "aliases": ["달성률", "달성율", "생산달성률"],
    "required_datasets": ["production", "wip"],
    "formula": "sum(production) / sum(wip_qty) * 100",
    "grouping_hint": ["MODE", "OPER_NAME"]
  }
}
```

사용자 질문:

```text
어제 WB공정 생산달성률을 mode별로 알려줘
```

기대 동작:

```text
달성률 metric 매칭
-> required_datasets 확인
-> production + wip 조회 계획 생성
-> multi_retrieval branch로 이동
```

즉, LLM이 `production`만 반환하더라도 normalizer가 domain metric을 기준으로 `wip`을 추가해야 한다.

### 1.3 Table Catalog 기반 조회 Tool 선택

Table catalog는 사용자의 질문과 실제 데이터 조회 tool 사이를 연결하는 지도 역할을 한다.

예시:

```json
{
  "dataset_key": "production",
  "description": "Daily production rows by process, line, mode, density, package.",
  "keywords": ["생산", "생산량", "production"],
  "tool_name": "get_production_data",
  "required_params": ["date"],
  "common_group_by": ["OPER_NAME", "MODE", "LINE"]
}
```

flow는 table catalog를 보고 다음을 판단한다.

- "생산량"이라는 표현은 `production` dataset과 연결된다.
- `production` 조회에는 `date`가 필수다.
- 실제 조회 함수는 `get_production_data`다.
- mode별, 공정별 분석이 자주 쓰인다.

이 기능 덕분에 dataset이나 table이 늘어나도, 질문 분류 prompt와 조회 계획이 catalog 기반으로 확장될 수 있다.

### 1.4 신규 조회와 후속 분석 구분

flow는 모든 질문을 새 조회로 처리하지 않는다. 이전 결과가 있는 상태에서 사용자가 후속 질문을 하면 현재 데이터를 재사용한다.

예시 흐름:

```text
1차 질문: 오늘 DA공정 생산량 알려줘
-> production 조회
-> current_data 저장

2차 질문: 이때 가장 생산량이 많았던 mode 알려줘
-> followup_transform
-> current_data 재사용
-> mode별 최대 생산량 계산
```

이 기능이 없으면 두 번째 질문도 다시 DB 조회로 가거나, "이때"가 무엇인지 몰라 잘못된 답변을 만들 수 있다.

후속 분석 판단에 필요한 상태:

| 상태 값 | 역할 |
| --- | --- |
| `chat_history` | 이전 질문/답변 흐름 확인 |
| `context` | 이전 조회 조건과 intent 확인 |
| `current_data` | 후속 분석에 사용할 현재 결과 |
| `data_ref` | current_data가 클 때 MongoDB에서 다시 불러올 주소 |

### 1.5 단일/복합 데이터 조회 분기

의도 분석 결과에 따라 조회 flow는 단일 조회와 복합 조회로 나뉜다.

| 분기 | 사용 상황 | 예시 |
| --- | --- | --- |
| `single_retrieval` | 하나의 dataset만 필요 | "오늘 DA공정 생산량 알려줘" |
| `multi_retrieval` | 여러 dataset이 필요 | "생산달성률 알려줘", "생산과 목표를 비교해줘" |
| `followup_transform` | 이전 결과를 분석 | "이때 mode별로 정리해줘" |
| `finish` | 조회 전 조건 부족 또는 조회 불필요 | "생산량 알려줘"처럼 날짜가 없는 경우 |

복합 조회에서는 여러 retriever 결과가 `source_results`로 모이고, 이후 pandas 전처리 단계에서 병합/계산된다.

### 1.6 Source별 데이터 조회 구조

실제 사용에서는 Oracle DB를 조회하지만, 같은 구조로 dummy 데이터나 MongoDB reference 데이터도 사용할 수 있다.

| 조회 방식 | 역할 |
| --- | --- |
| Dummy Data Retriever | DB 없이 flow 연결과 분기 테스트 |
| Oracle Data Retriever | 실제 Oracle DB에서 dataset 조회 |
| MongoDB Data Loader | `data_ref`로 저장된 큰 데이터 재조회 |
| Current Data Retriever | 후속 질문에서 이전 결과 재사용 |

중요한 점은 source가 달라도 output schema를 최대한 통일한다는 것이다.

```json
{
  "success": true,
  "dataset_key": "production",
  "tool_name": "get_production_data",
  "data": [],
  "summary": "total rows 12",
  "errors": []
}
```

이렇게 해야 뒤의 pandas 분석과 최종 답변 노드가 데이터 출처를 몰라도 같은 방식으로 처리할 수 있다.

### 1.7 Pandas 기반 답변용 데이터 후처리

조회된 원본 데이터를 그대로 답변에 쓰기 어려운 질문은 pandas 전처리로 넘어간다.

예시 질문:

```text
어제 WB공정 생산달성률을 mode별로 알려줘
```

필요한 처리:

```text
production dataset 조회
wip dataset 조회
MODE 기준 병합 또는 group by
sum(production) / sum(wip_qty) * 100 계산
achievement_rate 컬럼 생성
MODE별 최종 결과 생성
```

이 flow에서 LLM은 계산 결과를 직접 만들지 않는다. LLM은 pandas 계획 또는 코드를 만들고, 실제 숫자 계산은 pandas executor가 수행한다.

이 방식의 장점:

- 계산 결과의 재현성이 높다.
- LLM이 숫자를 지어내는 risk를 줄인다.
- 최종 답변에 사용한 데이터가 `final_rows`로 남는다.

### 1.8 최종 답변 생성과 최종 데이터 동시 제공

최종 출력은 자연어 답변만 반환하지 않는다.

반드시 다음을 함께 제공하는 것이 목표다.

| 출력 | 의미 |
| --- | --- |
| `response` | 사용자가 읽는 자연어 답변 |
| `final_data.rows` | 답변을 만들 때 실제 사용한 최종 가공 데이터 |
| `final_result` | API나 저장소에서 읽을 수 있는 구조화 결과 |
| `next_state` | 다음 후속 질문을 위한 state |

예시 출력:

```text
WB공정의 mode별 생산달성률은 DDR5가 82.1%, HBM3가 76.4%입니다.

### 최종 데이터
총 2건

| MODE | production | wip_qty | achievement_rate |
| --- | --- | --- | --- |
| DDR5 | 1200 | 1462 | 82.1 |
| HBM3 | 980 | 1283 | 76.4 |
```

이 구조는 사용자가 답변의 근거 데이터를 함께 확인할 수 있게 해준다.

### 1.9 큰 데이터 Reference 관리

조회 결과 전체를 매번 LLM prompt나 memory에 넣으면 token 비용과 latency가 커진다. 그래서 큰 row list는 MongoDB에 저장하고 flow에는 reference만 유지한다.

권장 흐름:

```text
원본 row 또는 큰 중간 결과
-> MongoDB 저장
-> flow에는 data_ref, row_count, columns, preview, summary만 전달
-> 실제 계산이 필요할 때 data_ref로 다시 로드
```

이 기능은 특히 후속 질문에서 중요하다. 이전 결과가 매우 클 때도 `current_data`에 전체 row를 들고 다니지 않고, 필요 시 MongoDB에서 다시 불러올 수 있다.

### 1.10 도메인/테이블 정보 등록 및 확장

도메인 지식과 테이블 카탈로그는 코드 안에 고정하지 않는다.

지원 방식:

- MongoDB에 저장된 domain item document 로딩
- Langflow 입력창에 직접 넣는 JSON domain fallback
- Table catalog JSON 입력
- 등록 웹에서 자연어를 LLM으로 변환해 MongoDB에 저장

등록 웹을 통해 사용자는 다음처럼 자연어로 지식을 넣을 수 있다.

```text
생산달성률은 생산량 / 재공 * 100으로 계산한다.
WB는 W/B1, W/B2 공정 그룹을 의미한다.
mode별로 자주 확인한다.
```

시스템은 이를 metric, process group, dataset 설명 같은 item document로 변환해 저장하고, main flow는 저장된 item을 읽어 의도 추출과 pandas 후처리에 활용한다.

### 1.11 기능 단위로 보이는 분기형 Flow

v2에서는 Langflow canvas에서 주요 기능 분기가 보이도록 구성한다.

핵심 분기:

| 분기 | 의미 |
| --- | --- |
| `finish` | 데이터 조회 없이 바로 답변하거나 필수 조건 부족을 안내 |
| `single_retrieval` | 하나의 dataset만 조회 |
| `multi_retrieval` | 여러 dataset을 조회해서 병합 또는 계산 |
| `followup_transform` | 이전 결과를 기준으로 후속 분석 |
| `direct_response` | 조회 결과를 바로 답변에 사용 |
| `post_analysis` | pandas 전처리/집계/계산 후 답변 |

이 구조는 단순히 내부 코드에서 if문으로 처리하는 것보다, Langflow 화면에서 어떤 경로로 실행됐는지 확인하기 쉽다.

### 1.12 기능 안정성을 위한 보조 설계

아래 항목은 사용자가 직접 보는 기능은 아니지만, 위 기능들이 일관되게 동작하도록 받쳐주는 설계 요건이다.

- Prompt Builder, LLM Caller, Parser/Normalizer, Router/Executor를 분리해 디버깅 가능성을 높인다.
- LLM 호출 지점은 Intent, Pandas Plan, Final Answer로 역할을 분리한다.
- source별 retriever는 같은 output schema를 유지한다.
- 오류는 예외로만 중단하지 않고 `success`, `errors`, `summary` 형태로 downstream에 전달한다.

## 2. Risk 및 대응 방안

### 2.1 LLM이 의도나 Dataset을 잘못 분류할 Risk

예상 문제:

- 후속 질문을 신규 조회로 판단한다.
- metric 계산에 필요한 dataset을 일부만 선택한다.
- filter 조건을 누락하거나 잘못 해석한다.
- pandas가 필요한 질문인데 direct response로 보낸다.

대응 방안:

- Intent prompt에 route 기준과 예시를 명확히 넣는다.
- domain metric의 `required_datasets`를 normalizer에서 강제 반영한다.
- table catalog에 dataset 용도, keyword, 날짜 기준, 대표 group by를 명확히 넣는다.
- 회귀 질문 세트를 유지한다.
- LLM 결과를 그대로 쓰지 않고 schema 정규화와 route 검증을 거친다.

### 2.2 잘못된 최종 답변 Risk

예상 문제:

- LLM이 최종 데이터와 다른 내용을 말한다.
- 단위, 합계, 최대/최소 값이 틀린다.
- 데이터가 비어 있는데 분석 결과가 있는 것처럼 답한다.

대응 방안:

- 계산은 LLM이 아니라 pandas executor에서 수행한다.
- Final Answer LLM에는 최종 가공 데이터와 요약값을 함께 제공한다.
- Final Answer Builder가 답변과 최종 데이터를 함께 출력한다.
- 데이터가 없거나 errors가 있으면 답변에 그 상태를 명확히 반영한다.
- 숫자 결과는 가능하면 analysis_result의 계산값을 우선 사용하고 LLM은 문장화만 담당하게 한다.

### 2.3 Token, Latency, Cost Risk

예상 문제:

- 조회 row 전체가 prompt에 들어가 token이 커진다.
- 후속 질문마다 이전 데이터가 반복 주입된다.
- domain/table 정보가 커지면서 prompt가 느려진다.

대응 방안:

- 큰 데이터는 MongoDB에 저장하고 `data_ref`만 flow에 유지한다.
- LLM에는 preview, row_count, columns, summary 중심으로 전달한다.
- domain item은 active 상태만 읽고, prompt에 필요한 범위로 압축한다.
- table catalog도 dataset 선택에 필요한 설명 중심으로 유지한다.
- preview row limit, fetch limit, answer row limit을 설정한다.

### 2.4 Multi-turn Memory 연결 실패 Risk

예상 문제:

- Playground에서 이전 state를 읽지 못한다.
- session id가 달라져 후속 질문이 이어지지 않는다.
- `current_data`가 사라져 follow-up 분석이 불가능하다.

대응 방안:

- Langflow Message History retrieve/store 연결을 필수 연결로 문서화한다.
- State Memory Message에 marker를 넣어 일반 대화 메시지와 구분한다.
- 다음 턴에 필요한 최소 state만 저장한다.
- `current_data` 원본이 클 경우 `data_ref`와 summary를 함께 저장한다.
- 디버깅 시 State Memory Extractor 출력의 `memory_loaded`, `memory_record_count`를 먼저 확인한다.

### 2.5 Domain Registry 관리 어려움 Risk

예상 문제:

- 같은 alias가 여러 item에 중복 저장된다.
- metric formula가 dataset schema와 맞지 않는다.
- 오래된 domain item이 계속 prompt에 들어간다.

대응 방안:

- `gbn + key` 기준으로 item을 관리한다.
- alias, dataset keyword 중복 검사를 둔다.
- `status=active` item만 main flow에서 사용한다.
- 검토가 필요한 item은 `review_required` 상태로 저장한다.
- 등록 웹에서 항목별 조회/삭제/검토 기능을 제공한다.

### 2.6 DB 조회 안정성 Risk

예상 문제:

- Oracle 연결 정보 입력 형식이 깨진다.
- TNS/DSN 문자열 줄바꿈 때문에 JSON 파싱이 실패한다.
- 잘못된 dataset key로 의도하지 않은 query가 실행된다.
- 조회량이 너무 많아 응답이 느려진다.

대응 방안:

- DB config 입력에서 따옴표 1개/3개 문자열을 모두 정리해 받는다.
- dataset key와 query template은 table catalog 기반 whitelist로 관리한다.
- 날짜, 공정, mode 같은 filter는 정규화 후 query에 반영한다.
- fetch limit과 row count summary를 둔다.
- 연결 실패와 query 실패를 `errors` payload로 명확히 반환한다.

### 2.7 Pandas 실행 Risk

예상 문제:

- LLM이 생성한 pandas code가 실패한다.
- 예상과 다른 컬럼명을 사용한다.
- 위험한 Python 코드가 실행될 수 있다.

대응 방안:

- Pandas plan normalizer에서 허용 schema를 검증한다.
- executor에서 사용 가능한 namespace를 제한한다.
- 원본 rows와 columns를 기준으로 존재하지 않는 컬럼을 사전 검증한다.
- 실패 시 fallback summary 또는 오류 메시지를 반환한다.
- 운영 환경에서는 timeout, row limit, 허용 함수 whitelist를 강화한다.

### 2.8 노드 수 증가로 인한 관리 Risk

예상 문제:

- 노드가 많아져 연결 순서가 헷갈린다.
- 같은 LLM Caller를 여러 번 쓰면서 어떤 caller인지 혼동한다.
- 수정 위치를 찾기 어렵다.

대응 방안:

- 파일명 번호를 실제 연결 순서와 맞춘다.
- README의 Exact Connection Map을 유지한다.
- `detail_desc/`에 노드별 설명을 둔다.
- LLM Caller는 canvas에서 `(Intent)`, `(Pandas)`, `(Answer)`처럼 instance 이름을 구분한다.
- 노드 status에 핵심 실행 결과를 남긴다.

### 2.9 Encoding 및 한글 출력 Risk

예상 문제:

- Windows/PowerShell/DB/웹 출력 과정에서 한글이 깨진다.
- Langflow component 출력이 mojibake 형태로 보인다.

대응 방안:

- 문서와 JSON 예시는 UTF-8 기준으로 저장한다.
- Python 문자열 처리에서 불필요한 encode/decode 변환을 피한다.
- DB client와 웹 출력의 charset 설정을 확인한다.
- 깨진 문자열을 후처리로 보정하기보다, 입력/저장/출력 경로의 encoding을 먼저 점검한다.

## 3. 시스템 구상도

아래 workflow는 기능 단위 흐름만 나타낸다. Parser, normalizer, adapter 같은 부속 노드는 생략했다.

```mermaid
flowchart TD
    A["사용자 질문<br/>Chat Input"] --> B["세션/이전 상태 로드<br/>Message History + State"]
    B --> C["도메인/테이블 정보 로드<br/>MongoDB Domain 또는 JSON + Table Catalog"]
    C --> D["의도 및 조회 계획 판단<br/>Intent LLM"]

    D --> E{"질문 유형/조회 계획"}

    E -->|필수 조건 부족 또는 조회 불필요| F["즉시 응답 준비"]
    E -->|이전 결과 후속 분석| G["현재 데이터 재사용<br/>current_data 또는 data_ref 로드"]
    E -->|단일 데이터 조회| H["단일 Dataset 조회<br/>Dummy 또는 Oracle"]
    E -->|복합 데이터 조회| I["여러 Dataset 조회<br/>Dummy 또는 Oracle"]

    H --> J["조회 결과 병합"]
    I --> J
    G --> J

    J --> K{"후처리 필요 여부"}
    K -->|불필요| L["조회 결과 기반 직접 답변 데이터 구성"]
    K -->|필요| M["Pandas 분석 계획 생성<br/>Pandas Plan LLM"]
    M --> N["Pandas 전처리/집계/계산 실행"]

    F --> O["분석 결과 통합"]
    L --> O
    N --> O

    O --> P["큰 데이터 저장 및 참조화<br/>MongoDB data_ref"]
    P --> Q["최종 답변 생성<br/>Final Answer LLM"]
    Q --> R["답변 + 최종 데이터 + final_result 구성"]
    R --> S["다음 턴 state 저장<br/>Message History"]
    R --> T["사용자에게 출력<br/>Chat Output"]
```

### 3.1 기능 단위 Workflow 설명

| 단계 | 기능 | 핵심 결과 |
| --- | --- | --- |
| 사용자 질문 입력 | 사용자가 자연어로 질문한다. | `user_question` |
| 세션/이전 상태 로드 | 이전 대화, context, current data를 읽는다. | `state` |
| 도메인/테이블 정보 로드 | metric, alias, dataset 설명을 불러온다. | `domain_payload`, `table_catalog_payload` |
| 의도 및 조회 계획 판단 | 후속 분석/신규 조회/필터/dataset/pandas 필요 여부를 판단한다. | `intent_plan` |
| 분기 처리 | finish, follow-up, single, multi로 나눈다. | selected route |
| 데이터 조회 또는 재사용 | 필요한 데이터를 가져오거나 이전 데이터를 재사용한다. | `source_results` |
| 후처리 판단 | direct response인지 pandas 분석인지 나눈다. | postprocess route |
| pandas 분석 | 집계, 계산, 정렬, 필터링을 수행한다. | `final_data` |
| 큰 데이터 참조화 | 큰 row list를 MongoDB에 저장하고 reference만 유지한다. | `data_ref`, preview |
| 최종 답변 생성 | 최종 데이터를 기반으로 자연어 답변을 만든다. | `response` |
| 최종 출력 | 답변과 최종 데이터를 함께 보여준다. | `answer_message`, `final_result` |
| 다음 state 저장 | 후속 질문을 위해 state를 저장한다. | `next_state` |

### 3.2 대표 실행 시나리오

#### 단일 데이터 조회

```text
"오늘 DA공정 생산량 알려줘"
-> retrieval
-> single_retrieval
-> production 조회
-> direct_response 또는 post_analysis
-> 답변 + 최종 데이터 출력
```

#### 복합 데이터 조회

```text
"어제 WB공정 생산달성률을 mode별로 알려줘"
-> retrieval
-> metric required_datasets 확인
-> production + wip 조회
-> post_analysis
-> 생산달성률 계산
-> 답변 + mode별 최종 데이터 출력
```

#### 후속 분석

```text
"이때 가장 생산량이 많았던 mode를 알려줘"
-> followup_transform
-> current_data 또는 data_ref 로드
-> post_analysis
-> mode별 최대 생산량 계산
-> 답변 + 최종 데이터 출력
```

## 4. 운영 시 우선 확인할 체크리스트

- Message History retrieve/store가 연결되어 있는가
- `State Memory Extractor.memory_loaded`가 true로 나오는가
- domain item 중 필요한 metric이 `status=active`인가
- metric의 `required_datasets`가 정확한가
- table catalog에 dataset keyword와 date filter 기준이 들어 있는가
- Intent LLM 결과가 route와 retrieval jobs를 올바르게 반환하는가
- multi dataset 질문이 `multi_retrieval`로 가는가
- follow-up 질문이 `followup_transform`으로 가는가
- pandas 결과의 최종 데이터가 답변과 함께 출력되는가
- 큰 데이터가 prompt/memory에 그대로 들어가지 않고 `data_ref`로 줄어드는가
