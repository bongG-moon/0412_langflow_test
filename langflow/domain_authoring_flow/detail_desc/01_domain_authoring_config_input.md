# 01. Domain Authoring Config Input

## 역할

도메인 생성/수정 방식을 설정한다.

예를 들어 신규 생성인지, 기존 도메인에 추가하는지, 결과 상태를 `active`로 둘지 정한다.

현재 MongoDB 저장 flow에서는 이 노드를 연결하지 않아도 된다. 연결하지 않으면 코드 기본값으로 `domain_id=manufacturing_default`, `authoring_mode=append`, `target_status=active`가 적용된다.

## 입력

- `domain_id`: 도메인 문서 ID. 기본값은 `manufacturing_default`
- `authoring_mode`: `create`, `append`, `update`, `validate_only`
- `target_status`: `draft` 또는 `active`. 기본값은 `active`
- `display_name`: 도메인 표시명
- `description`: 도메인 설명

## 출력

`authoring_config`

```json
{
  "authoring_config": {
    "domain_id": "manufacturing_default",
    "authoring_mode": "append",
    "target_status": "active",
    "metadata": {
      "display_name": "제조 분석 도메인",
      "description": "Domain Authoring Flow에서 생성한 제조 분석 도메인"
    }
  }
}
```

## 주요 구현

- `_normalize_choice()`는 허용되지 않은 mode/status가 들어오면 안전한 기본값으로 바꾼다.
- `metadata`는 최종 Domain JSON의 `metadata`에 병합된다.
- 최종 Main Flow에서 쓰지 않는 생성자 추적 정보는 payload에 넣지 않는다.

## 다음 연결

```text
Domain Authoring Config Input.authoring_config -> Build Domain Structuring Prompt.authoring_config
Domain Authoring Config Input.authoring_config -> MongoDB Active Domain Loader.authoring_config
Domain Authoring Config Input.authoring_config -> Domain Patch Merger.authoring_config
Domain Authoring Config Input.authoring_config -> Domain Save Decision.authoring_config
Domain Authoring Config Input.authoring_config -> MongoDB Domain Fragment Saver.authoring_config
```

위 연결은 모두 선택 사항이다. 기본 도메인으로 저장할 때는 이 노드 자체를 생략해도 된다.
