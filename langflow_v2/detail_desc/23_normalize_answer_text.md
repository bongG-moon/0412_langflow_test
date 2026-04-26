# 23. Normalize Answer Text

## 한 줄 역할

최종 답변 LLM 응답을 파싱해서 `answer_text`로 정리하는 노드입니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `llm_result` | `LLM JSON Caller (Answer)` 출력입니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `answer_text` | 자연어 답변, 하이라이트, warnings 등을 담습니다. |

## 주요 함수 설명

- `_extract_json_object`: LLM 응답에서 JSON을 찾습니다.
- `_fallback_answer`: LLM 응답이 없거나 파싱 실패했을 때 규칙 기반 답변을 만듭니다.
- `_fallback_success_answer`: 성공 결과를 사람이 읽을 수 있는 문장으로 만듭니다.
- `normalize_answer_text`: LLM 응답과 fallback을 합쳐 최종 answer_text를 만듭니다.

## 기대 JSON 예시

```json
{
  "answer": "오늘 DA공정 생산량은 총 33,097입니다.",
  "highlights": ["총 12건 기준입니다."]
}
```

## 초보자 포인트

이 노드는 사용자에게 바로 출력하지 않습니다.
문장만 정리하고, 실제 화면용 메시지와 final_result는 `Final Answer Builder`가 만듭니다.

LLM 호출이 실패해도 fallback 답변이 있으므로 테스트가 가능합니다.

## 연결

```text
LLM JSON Caller (Answer).llm_result
-> Normalize Answer Text.llm_result

Normalize Answer Text.answer_text
-> Final Answer Builder.answer_text
```

