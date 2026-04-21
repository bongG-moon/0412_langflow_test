# 07. Domain Conflict Detector

## 역할

기존 도메인과 새 patch 사이의 충돌 가능성을 찾는다.

## 입력

- `existing_domain`: MongoDB Active Domain Loader output
- `normalized_domain_patch`: Normalize Domain Patch output

## 출력

`conflict_report`

```json
{
  "conflicts": [],
  "warnings": [],
  "blocking_errors": [],
  "has_blocking_conflict": false
}
```

## 검사 내용

- 같은 alias가 기존 도메인과 새 patch에서 서로 다른 key를 가리키는지 확인한다.
- patch 내부에서 같은 alias가 서로 다른 key로 중복 등록되었는지 확인한다.
- 같은 metric key의 formula가 기존 정의와 달라지는지 확인한다.
- metric이나 join rule이 아직 정의되지 않은 dataset을 참조하면 warning을 남긴다.

## 다음 연결

```text
Domain Conflict Detector.conflict_report -> Domain Patch Merger.conflict_report
```
