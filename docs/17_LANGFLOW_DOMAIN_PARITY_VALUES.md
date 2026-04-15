# Langflow Domain Parity Values

이 문서는 Langflow `Domain Rules` 노드와 `Domain Registry` 노드에 바로 붙여넣을 수 있는 추천값 위치를 정리한 문서입니다.

## 추천 파일

- `Domain Rules`에 붙여넣을 텍스트:
  [domain_rules_langgraph_parity.txt](/C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/reference_materials/langflow_domain_inputs/domain_rules_langgraph_parity.txt)
- `Domain Registry`에 붙여넣을 JSON:
  [domain_registry_langgraph_parity.json](/C:/Users/qkekt/Desktop/langflow_local_manufacturing_project/reference_materials/langflow_domain_inputs/domain_registry_langgraph_parity.json)

## 이 값들의 기준

- Langflow standalone 노드 안에 이미 들어간 built-in LangGraph 도메인 지식
- 저장소의 실제 저장 도메인 엔트리
  - `reference_materials/domain_registry/entries/*.json`
- 현재 프로젝트에서 자주 쓰는 커스텀 파생지표/별칭 규칙

즉, 위 두 파일을 그대로 붙여넣으면 현재 LangGraph 기준 동작에 가장 가깝게 맞출 수 있습니다.

## 붙여넣는 방법

### 1. `Domain Rules`

`reference_materials/langflow_domain_inputs/domain_rules_langgraph_parity.txt` 파일 내용을 전부 복사해서 `Domain Rules` 노드에 붙여넣습니다.

### 2. `Domain Registry`

`reference_materials/langflow_domain_inputs/domain_registry_langgraph_parity.json` 파일 내용을 전부 복사해서 `Domain Registry` 노드에 붙여넣습니다.

## 포함된 커스텀 규칙

- `hold_anomaly_check`
- `plan_gap_rate`
- `hold_load_index`
- `양품률 -> yield` dataset keyword 매핑
- `후공정A -> D/A1, D/A2` process group 매핑

## 참고

아래 built-in 지식은 이미 Langflow standalone 노드 코드 안에 들어 있습니다.

- 공정 그룹
  - `DA`, `WB`, `DP`, `PCO`, `DC`, `FCB` 등
- MODE 그룹
  - `DDR4`, `DDR5`, `LPDDR5`
- DEN 그룹
  - `256G`, `512G`, `1T`
- TECH 그룹
  - `LC`, `FO`, `FC`
- 기본 분석 규칙
  - `achievement_rate`
  - `yield_rate`
  - `production_saturation_rate`

그래서 이번 복붙용 파일은 built-in을 중복해서 다시 넣는 대신, 현재 프로젝트에서 의미 있는 커스텀 규칙 위주로 구성했습니다.
