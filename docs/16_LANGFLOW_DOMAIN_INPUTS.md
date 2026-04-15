# Langflow Domain Input Guide

이 문서는 Langflow 캔버스에서 `Domain Rules` 노드와 `Domain Registry` 노드에 어떤 값을 넣어야 하는지 정리한 문서입니다.

핵심만 먼저 정리하면 아래와 같습니다.

- `Domain Rules`: 자유 텍스트 메모
- `Domain Registry`: 구조화된 JSON
- 아무 커스텀 규칙이 없으면 `Domain Rules`는 비워도 되고, `Domain Registry`에는 `{}`만 넣어도 됩니다.

## 1. 언제 어떤 노드를 쓰면 되나

### `Domain Rules`

짧은 도메인 메모를 넣는 칸입니다.

- 한두 줄 설명
- 예외 규칙
- 사용자 조직 내부 표현
- 아직 JSON으로 정리할 정도는 아닌 임시 메모

이 값은 런타임 프롬프트에 그대로 붙습니다. 그래서 길게 넣기보다, 짧고 명확한 문장으로 넣는 편이 좋습니다.

예시:

```text
DDR5 제품이라고 말하면 기본적으로 MODE=DDR5로 우선 해석한다.
DA 세부 공정은 D/A1, D/A2, D/A3, D/A4, D/A5, D/A6 범위를 의미한다.
HBM과 3DS는 TSV 계열 질문으로 함께 보는 경우가 많다.
```

### `Domain Registry`

반복해서 재사용할 구조화 규칙을 넣는 칸입니다.

- dataset 키워드 별칭
- 값 그룹 정의
- 사용자 정의 파생 지표
- 사용자 정의 조인 규칙
- 저장형 노트

즉, 추출/계획/분석 단계에서 계속 재사용해야 하는 규칙은 `Domain Registry`에 넣는 것이 맞습니다.

## 2. 가장 쉬운 시작 방법

처음에는 아래처럼 시작하시면 됩니다.

### `Domain Rules` 시작값

비워두거나, 정말 필요한 메모만 1~3줄 입력

```text
DDR5 제품은 우선 MODE 기준으로 해석한다.
```

### `Domain Registry` 시작값

```json
{}
```

이 상태에서도 built-in 규칙은 그대로 동작합니다. 현재 런타임에는 기본적으로 아래 성격의 내장 규칙이 이미 있습니다.

- 기본 dataset keyword
- 기본 value group
- 기본 analysis rule
  - `achievement_rate`
  - `yield_rate`
  - `production_saturation_rate`
- 기본 join rule

즉, 정말 커스텀한 부분만 추가하면 됩니다.

## 3. `Domain Rules`에 넣는 값 예시

### 예시 1. 아주 짧은 메모

```text
DDR5 제품은 MODE로 우선 해석한다.
```

### 예시 2. 공정 해석 메모

```text
DA 세부 공정은 D/A1, D/A2, D/A3, D/A4, D/A5, D/A6을 의미한다.
WB 세부 공정은 W/B1, W/B2, W/B3을 의미한다.
```

### 예시 3. 조직 내부 용어 메모

```text
현업에서 "재공"은 기본적으로 WIP를 의미한다.
"생산 달성율"은 production과 target을 함께 봐야 한다.
```

### `Domain Rules` 작성 팁

- 규칙 하나당 한 줄로 쓰면 좋습니다.
- 긴 설명문보다 판단 규칙 위주로 적는 편이 좋습니다.
- 재사용성이 높고 구조가 명확한 규칙은 나중에 `Domain Registry`로 옮기는 편이 좋습니다.

## 4. `Domain Registry`에 넣는 JSON 기본 형태

가장 안전한 기본 형태는 아래입니다.

```json
{
  "entries": []
}
```

또는 더 간단하게 아래처럼 써도 됩니다.

```json
{}
```

실제로 지원되는 상위 키는 아래입니다.

- `entries`
- `dataset_keywords`
- `value_groups`
- `analysis_rules`
- `join_rules`
- `notes`
- `title`
- `raw_text`

가장 권장하는 방식은 `entries` 배열 안에 규칙을 묶는 방식입니다.

## 5. `Domain Registry` 전체 예시

아래 예시는 바로 붙여넣을 수 있는 샘플입니다.

```json
{
  "entries": [
    {
      "title": "Manufacturing custom rules",
      "notes": [
        "DDR5 제품은 우리 조직에서는 MODE 기준으로 해석한다.",
        "DA 묶음은 세부 공정 전체를 의미한다."
      ],
      "dataset_keywords": [
        {
          "dataset_key": "production",
          "keywords": ["생산", "output", "prod"]
        },
        {
          "dataset_key": "wip",
          "keywords": ["재공", "wip", "in progress"]
        },
        {
          "dataset_key": "target",
          "keywords": ["목표", "plan", "target qty"]
        }
      ],
      "value_groups": [
        {
          "field": "process_name",
          "canonical": "DA",
          "synonyms": ["DA", "D/A", "다이 어태치"],
          "values": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
          "description": "DA라고 하면 DA 세부 공정 전체를 의미한다."
        },
        {
          "field": "mode",
          "canonical": "DDR5",
          "synonyms": ["DDR5", "DDR5 제품"],
          "values": ["DDR5"],
          "description": "DDR5는 MODE 값으로 관리된다."
        }
      ],
      "analysis_rules": [
        {
          "name": "backlog_gap",
          "display_name": "backlog gap",
          "synonyms": ["backlog gap", "생산 부족분", "목표 대비 부족분"],
          "required_datasets": ["target", "production"],
          "required_columns": ["target", "production"],
          "source_columns": [
            {
              "dataset_key": "target",
              "column": "target",
              "role": "numerator"
            },
            {
              "dataset_key": "production",
              "column": "production",
              "role": "denominator"
            }
          ],
          "calculation_mode": "difference",
          "output_column": "backlog_gap",
          "default_group_by": ["OPER_NAME"],
          "condition": "",
          "decision_rule": "",
          "formula": "target - production",
          "pandas_hint": "group by OPER_NAME and calculate target minus production",
          "description": "목표 대비 부족 생산량을 계산한다."
        }
      ],
      "join_rules": [
        {
          "name": "production_target_join_custom",
          "base_dataset": "production",
          "join_dataset": "target",
          "join_type": "left",
          "join_keys": ["WORK_DT", "OPER_NAME", "MODE", "DEN"],
          "description": "생산과 목표를 주요 제조 차원으로 결합한다."
        }
      ]
    }
  ]
}
```

## 6. 항목별 상세 설명

### `dataset_keywords`

질문에 어떤 단어가 나오면 어떤 dataset을 우선 떠올릴지 정하는 규칙입니다.

형식:

```json
{
  "dataset_key": "production",
  "keywords": ["생산", "output", "prod"]
}
```

언제 쓰면 좋나:

- 현업에서 쓰는 dataset 별칭이 built-in에 없는 경우
- 영어/약어/팀 내부 용어를 같이 지원하고 싶은 경우

주의:

- `dataset_key`는 실제 런타임이 아는 dataset key여야 합니다.
- 다른 dataset에서 이미 쓰는 키워드와 충돌하면 검증 이슈가 날 수 있습니다.

### `value_groups`

하나의 표현이 여러 실제 값 묶음을 의미할 때 쓰는 규칙입니다.

형식:

```json
{
  "field": "process_name",
  "canonical": "DA",
  "synonyms": ["DA", "D/A"],
  "values": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
  "description": "DA는 세부 공정 전체를 의미한다."
}
```

지원되는 `field` 값:

- `process_name`
- `mode`
- `den`
- `tech`
- `pkg_type1`
- `pkg_type2`
- `product_name`
- `line_name`
- `oper_num`
- `mcp_no`

중요:

- `DDR5`가 실제 데이터에서 `MODE` 컬럼이라면 `field`는 `mode`로 넣어야 합니다.
- `DDR5`가 실제 데이터에서 제품 컬럼이라면 그때 `product_name`을 써야 합니다.

### `analysis_rules`

질문이 특정 파생 지표를 요구할 때 어떤 dataset 조합과 계산 방식을 쓸지 정의하는 규칙입니다.

형식:

```json
{
  "name": "backlog_gap",
  "display_name": "backlog gap",
  "synonyms": ["생산 부족분", "목표 대비 부족분"],
  "required_datasets": ["target", "production"],
  "required_columns": ["target", "production"],
  "source_columns": [
    {
      "dataset_key": "target",
      "column": "target",
      "role": "numerator"
    },
    {
      "dataset_key": "production",
      "column": "production",
      "role": "denominator"
    }
  ],
  "calculation_mode": "difference",
  "output_column": "backlog_gap",
  "default_group_by": ["OPER_NAME"],
  "formula": "target - production",
  "pandas_hint": "group by OPER_NAME and calculate target minus production",
  "description": "목표 대비 부족 생산량"
}
```

지원되는 `calculation_mode`:

- `ratio`
- `difference`
- `sum`
- `mean`
- `count`
- `condition_flag`
- `threshold_flag`
- `count_if`
- `sum_if`
- `mean_if`
- `custom`

참고:

- `achievement_rate`, `yield_rate`, `production_saturation_rate`는 이미 built-in으로 있습니다.
- built-in과 완전히 같은 의미라면 새로 넣지 않아도 됩니다.
- 조직 내부 정의가 다를 때만 커스텀 규칙을 추가하는 편이 좋습니다.

### `join_rules`

여러 dataset을 어떤 키로 붙일지 정하는 규칙입니다.

형식:

```json
{
  "name": "production_target_join_custom",
  "base_dataset": "production",
  "join_dataset": "target",
  "join_type": "left",
  "join_keys": ["WORK_DT", "OPER_NAME", "MODE", "DEN"],
  "description": "생산과 목표를 결합한다."
}
```

지원되는 `join_type`:

- `left`
- `inner`
- `right`
- `outer`

참고:

- `production` + `target`
- `production` + `wip`

같은 대표 조합은 built-in join rule이 이미 있습니다.

### `notes`

정형 규칙으로 만들지 않은 짧은 메모를 저장할 때 씁니다.

형식:

```json
{
  "notes": [
    "DDR5는 MODE 기준으로 관리된다.",
    "재공은 WIP와 같은 의미로 쓰인다."
  ]
}
```

## 7. 자주 쓰는 입력 패턴

### 패턴 1. 그냥 간단히 시작하고 싶다

- `Domain Rules`

```text
DDR5 제품은 MODE로 해석한다.
```

- `Domain Registry`

```json
{}
```

### 패턴 2. DA와 WB 같은 묶음 규칙을 명확히 주고 싶다

- `Domain Rules`

```text
DA는 DA 세부 공정 전체를 의미한다.
WB는 WB 세부 공정 전체를 의미한다.
```

- `Domain Registry`

```json
{
  "entries": [
    {
      "title": "Process groups",
      "value_groups": [
        {
          "field": "process_name",
          "canonical": "DA",
          "synonyms": ["DA", "D/A"],
          "values": ["D/A1", "D/A2", "D/A3", "D/A4", "D/A5", "D/A6"],
          "description": "DA process family"
        },
        {
          "field": "process_name",
          "canonical": "WB",
          "synonyms": ["WB", "W/B"],
          "values": ["W/B1", "W/B2", "W/B3"],
          "description": "WB process family"
        }
      ]
    }
  ]
}
```

### 패턴 3. 조직 내부 파생 지표를 추가하고 싶다

- `Domain Rules`

```text
목표 대비 부족분이라는 표현은 target - production 계산을 의미한다.
```

- `Domain Registry`

```json
{
  "entries": [
    {
      "title": "Custom metric",
      "analysis_rules": [
        {
          "name": "backlog_gap",
          "display_name": "backlog gap",
          "synonyms": ["목표 대비 부족분", "생산 부족분"],
          "required_datasets": ["target", "production"],
          "required_columns": ["target", "production"],
          "source_columns": [
            {
              "dataset_key": "target",
              "column": "target",
              "role": "numerator"
            },
            {
              "dataset_key": "production",
              "column": "production",
              "role": "denominator"
            }
          ],
          "calculation_mode": "difference",
          "output_column": "backlog_gap",
          "default_group_by": ["OPER_NAME"],
          "formula": "target - production",
          "pandas_hint": "group by OPER_NAME and calculate target minus production",
          "description": "목표 대비 부족 생산량"
        }
      ]
    }
  ]
}
```

## 8. 입력할 때 주의할 점

- `Domain Rules`는 JSON이 아닙니다. 그냥 일반 텍스트를 넣으면 됩니다.
- `Domain Registry`는 반드시 JSON이어야 합니다.
- JSON 안에 주석은 넣으면 안 됩니다.
- 마지막 쉼표가 있으면 안 됩니다.
- 값이 없으면 `Domain Registry`에는 그냥 `{}`를 넣는 편이 가장 안전합니다.
- 같은 의미의 규칙을 `Rules`와 `Registry`에 동시에 과하게 중복해서 넣으면 관리가 어려워질 수 있습니다.

## 9. 추천 운영 방식

가장 안정적인 순서는 아래입니다.

1. 처음에는 `Domain Rules`만 아주 짧게 사용
2. 반복해서 쓰는 별칭은 `Domain Registry.value_groups`로 이동
3. dataset 별칭은 `Domain Registry.dataset_keywords`에 추가
4. 파생 지표는 `Domain Registry.analysis_rules`에 추가
5. 정말 필요한 조합만 `Domain Registry.join_rules`에 추가

## 10. 빠른 체크리스트

`Domain Rules`에 넣기 전:

- 텍스트 메모인가
- 한두 줄로 설명 가능한가
- 구조화 JSON까지는 필요 없는가

`Domain Registry`에 넣기 전:

- 반복 재사용될 규칙인가
- JSON 문법이 맞는가
- `field`와 실제 데이터 컬럼 의미가 맞는가
- `dataset_key`가 실제 dataset 이름과 맞는가

## 11. 추천 기본값

바로 시작할 때는 아래 두 값이면 충분합니다.

### `Domain Rules`

```text
DDR5 제품은 MODE로 우선 해석한다.
```

### `Domain Registry`

```json
{}
```
