# 00. Raw Domain Input

## 역할

사용자가 입력한 도메인 원문을 Langflow 연결용 `Data` payload로 포장한다.

이 노드는 자연어, 표 형태 텍스트, markdown table, 부분 JSON을 그대로 받는다. 아직 LLM 정리는 하지 않고, 뒤 노드가 원문을 안정적으로 읽을 수 있도록 key를 붙인다.

## 입력

- `raw_domain_text`: 사용자가 작성한 도메인 설명 원문

## 출력

`raw_domain_payload`

```json
{
  "raw_domain_text": "생산 달성율은 생산량 / 목표량 * 100..."
}
```

## 주요 구현

- LLM prompt에 실제로 필요한 원문만 넘기기 위해 `raw_domain_text`만 생성한다.
- 입력 종류, hash, title 같은 추적용 정보는 현재 flow에서 쓰지 않으므로 생성하지 않는다.
- `.text`는 사용하지 않고 모든 결과를 `.data`에 넣는다.

## 다음 연결

```text
Raw Domain Input.raw_domain_payload -> Build Domain Structuring Prompt.raw_domain_payload
```
