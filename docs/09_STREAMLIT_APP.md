# Streamlit 실행 가이드

이 프로젝트는 Langflow 커스텀 노드 외에도 Streamlit UI로 바로 실행할 수 있습니다.

## 실행 파일

- [app.py](/C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/app.py)

## 실행 명령

프로젝트 루트에서 아래 명령으로 실행합니다.

```powershell
streamlit run app.py
```

또는 Python 모듈 방식으로 실행할 수도 있습니다.

```powershell
python -m streamlit run app.py
```

## 화면 구성

- `채팅 분석`
  - 제조 질문을 대화형으로 입력
  - 조회 결과와 후처리 결과를 함께 확인
  - 이전 질문 맥락을 이어서 follow-up 질문 가능
- `도메인 관리`
  - 사용자 도메인 규칙 메모 등록/미리보기/삭제

## 내부 연결

Streamlit 앱은 Langflow 노드를 거치지 않고 현재 프로젝트의 LangGraph 로직을 직접 호출합니다.

- 입력 진입점:
  - [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/manufacturing_agent/agent.py:1)
- UI 렌더링 헬퍼:
  - [manufacturing_agent/app/ui_renderer.py](/C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/manufacturing_agent/app/ui_renderer.py:1)
  - [manufacturing_agent/app/ui_domain_knowledge.py](/C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/manufacturing_agent/app/ui_domain_knowledge.py:1)

즉, Langflow 전환용 어댑터와 별개로 Streamlit에서는 기존 LangGraph 흐름을 그대로 사용합니다.

## 주의사항

- `.env` 또는 환경 변수에 LLM API 키가 필요합니다.
- `requirements.txt` 설치가 먼저 되어 있어야 합니다.
- Langflow용 세션 저장소와는 별개로, Streamlit은 `st.session_state` 기반으로 대화 문맥을 유지합니다.
