# 09. Domain Item Conflict Checker

저장 전 충돌을 코드 기반으로 확인한다.

검증 항목:

```text
같은 batch 안 key 중복
기존 item과 key 동일 여부
alias가 다른 item에 이미 등록되었는지
dataset keyword가 다른 dataset에 이미 등록되었는지
```

error가 있으면 해당 item의 권장 상태를 `review_required`로 바꾼다.

다음 연결:

```text
Domain Item Conflict Checker.conflict_report -> MongoDB Domain Item Saver.conflict_report
```
