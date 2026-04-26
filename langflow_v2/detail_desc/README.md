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

