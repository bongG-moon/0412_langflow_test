# Manufacturing Registration Web

Streamlit 기반 등록 웹이다. 사용자가 도메인 지식과 테이블 정보를 편하게 붙여넣고, 검증한 뒤 MongoDB에 저장하거나 Main Flow용 JSON으로 사용할 수 있게 한다.

## 실행

```powershell
streamlit run C:\Users\qkekt\Desktop\langflow_local_manufacturing_project\langflow\registration_web\app.py
```

## 설정 위치

MongoDB와 LLM 설정은 웹 화면에서 입력하지 않는다. 아래 파일의 값을 사용한다.

```text
langflow/registration_web/services/config.py
```

주요 설정:

```python
MONGO_URI
DEFAULT_DB_NAME
DOMAIN_ITEMS_COLLECTION
TABLE_CATALOG_ITEMS_COLLECTION
LLM_API_KEY
LLM_MODEL_NAME
LLM_TEMPERATURE
```

API Key는 화면에 표시하지 않는다.

기본 모델은 `gemini-2.5-flash`로 설정되어 있다. 다른 모델을 쓰려면 `.env`에 `LLM_MODEL_NAME`을 추가하거나 `services/config.py`의 기본값을 바꾸면 된다.

## 메뉴

### 1. 도메인 정보 등록

자연어 도메인 설명을 입력하면 다음 순서로 처리한다.

```text
Raw Text
-> note 분리
-> 자동/수동 gbn 분류
-> LLM JSON 추출
-> normalized domain item 변환
-> 기존 MongoDB 항목과 충돌 검증
-> MongoDB 저장
```

저장 컬렉션 기본값:

```text
datagov.manufacturing_domain_items
```

저장되는 document는 Main Flow의 `MongoDB Domain Item Payload Loader`가 바로 읽을 수 있는 item 구조다.

```json
{
  "gbn": "process_groups",
  "key": "dp",
  "status": "active",
  "payload": {
    "display_name": "DP",
    "aliases": ["DP", "D/P"],
    "processes": ["WET1", "WET2"]
  },
  "normalized_aliases": ["dp", "d/p"],
  "normalized_keywords": [],
  "source_text": "DP,D/P는 WET1, WET2 공정 그룹을 의미한다."
}
```

### 2. 테이블 정보 등록

SQL, DDL, 자연어 설명 또는 Table Catalog JSON을 입력하면 Main Flow의 `Table Catalog Loader`가 사용하는 JSON으로 변환한다.

처리 방식:

- JSON이면 LLM 없이 바로 검증
- SQL/DDL/자연어면 LLM으로 Table Catalog JSON 생성
- 생성된 JSON은 화면에서 복사해 Main Flow의 `Table Catalog JSON Input`에 붙여넣을 수 있음
- 선택적으로 MongoDB에도 item 단위로 저장 가능

저장 컬렉션 기본값:

```text
datagov.manufacturing_table_catalog_items
```

### 3. 도메인 정보 조회

MongoDB에 저장된 domain item을 유형별로 조회한다. 목록에서 항목을 선택하면 payload, source text, normalized alias/keyword, 전체 document를 상세 확인할 수 있다.
상세 화면의 삭제 기능은 물리 삭제가 아니라 `status=deleted`로 바꾸는 soft delete 방식이다. Main Flow는 `status=active` 항목만 읽으므로 삭제 즉시 사용 대상에서 제외된다.

### 4. 테이블 정보 조회

MongoDB에 저장된 table catalog item을 조회한다. 목록에서 항목을 선택하면 SQL, bind params, columns, keywords, question examples, 전체 document를 상세 확인할 수 있다.
상세 화면의 삭제 기능은 `status=deleted`로 바꾸는 soft delete 방식이다.

## Main Flow와의 관계

현재 Main Flow는 도메인 정보를 MongoDB에서 읽는다.

```text
registration_web domain save
-> datagov.manufacturing_domain_items
-> data_answer_flow / MongoDB Domain Item Payload Loader
```

테이블 정보는 현재 JSON 붙여넣기 방식과 MongoDB 저장 방식을 모두 지원하도록 웹을 만들었다. Main Flow에서 자동 조회까지 연결하려면 다음 단계에서 `MongoDB Table Catalog Payload Loader` 노드를 추가하면 된다.

## 입력 예시

- `examples/domain_input_example.txt`
- `examples/table_input_example.txt`
