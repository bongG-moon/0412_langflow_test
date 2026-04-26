# 03. Domain JSON Loader

## 한 줄 역할

MongoDB 대신 직접 붙여 넣은 domain JSON을 읽어 `domain_payload`로 만드는 노드입니다.

## 언제 쓰나?

처음 테스트할 때 MongoDB를 연결하지 않고도 flow를 확인하고 싶을 때 사용합니다.

운영에서는 `MongoDB Domain Loader`를 권장하지만, 개발/디버깅에서는 이 노드가 빠릅니다.

## 입력

| 입력 포트 | 의미 |
| --- | --- |
| `domain_json` | domain JSON 문자열입니다. aggregate 형식과 item document 배열을 모두 받을 수 있습니다. |

## 출력

| 출력 포트 | 의미 |
| --- | --- |
| `domain_payload` | 정규화된 domain 정보입니다. |

## 주요 함수 설명

- `_parse_jsonish`: JSON 문자열, Python dict처럼 보이는 문자열을 최대한 안전하게 파싱합니다.
- `_empty_domain`: 기본 domain 틀을 만듭니다.
- `_merge_item`: item document를 aggregate domain 구조에 합칩니다.
- `_normalize_domain_payload`: 입력이 어떤 형식이든 뒤 노드가 읽을 수 있는 구조로 맞춥니다.

## 입력 가능 형식

aggregate domain:

```json
{
  "domain": {
    "process_groups": {},
    "terms": {},
    "datasets": {},
    "metrics": {},
    "join_rules": []
  }
}
```

item document 배열:

```json
[
  {
    "gbn": "process_groups",
    "key": "DA",
    "payload": {
      "display_name": "Die Attach",
      "aliases": ["DA", "D/A"],
      "processes": ["D/A1", "D/A2"]
    }
  }
]
```

## 초보자 포인트

`Domain JSON Loader`와 `MongoDB Domain Loader`는 둘 중 하나만 연결하면 됩니다.
둘 다 같은 `domain_payload`를 출력하기 때문입니다.

## 연결

```text
Domain JSON Loader.domain_payload
-> Build Intent Prompt.domain_payload

Domain JSON Loader.domain_payload
-> Build Pandas Prompt.domain_payload
```

