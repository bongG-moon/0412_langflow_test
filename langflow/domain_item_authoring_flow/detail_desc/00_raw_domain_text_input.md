# 00. Raw Domain Text Input

사용자가 도메인 설명을 입력하는 단일 입력 노드다.

입력 필드는 `MultilineInput`을 사용한다. Langflow 화면에서는 변수 선택형 입력이 아니라 긴 텍스트를 직접 붙여넣는 입력창으로 쓰면 된다.

출력:

```json
{
  "raw_text": "사용자 입력 원문",
  "source": "domain_item_authoring_flow",
  "is_empty": false
}
```

다음 연결:

```text
Raw Domain Text Input.raw_domain_payload -> Domain Text Splitter.raw_domain_payload
```
