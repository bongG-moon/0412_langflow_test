# 10. Request Type Router

정규화된 intent를 보고 질문이 데이터 조회인지, process 실행 요청인지, 추가 확인이 필요한지 나누는 노드다.

## 입력

```text
intent
main_context    optional
agent_state     legacy optional
```

보통 `Normalize Intent With Domain.intent` output 안에 `main_context`가 같이 들어 있으므로 `main_context`와 `agent_state`를 따로 연결하지 않아도 된다.

## 출력

```text
route_result
data_question
process_execution
clarification
```

## 역할

- `intent.request_type`을 읽고 route를 결정한다.
- Phase 1에서는 `data_question`만 본 flow로 계속 진행한다.
- `process_execution`은 아직 실제 실행하지 않고 별도 branch로 분리한다.
- 판단 신뢰도가 낮고 dataset/metric 단서도 없으면 `clarification`으로 보낸다.

## 권장 연결

```text
Normalize Intent With Domain.intent
-> Request Type Router.intent

Request Type Router.data_question
-> Query Mode Decider.intent
```
