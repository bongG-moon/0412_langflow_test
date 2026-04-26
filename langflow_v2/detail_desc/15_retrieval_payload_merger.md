# 15. Retrieval Payload Merger

## ??以???븷

single, multi, follow-up retrieval branch 以??ㅼ젣濡??ㅽ뻾??payload ?섎굹瑜?怨⑤씪 ?ㅼ쓬 ?몃뱶濡??섍퉩?덈떎.

## ???꾩슂?쒓?

Langflow?먯꽌??branch媛 ?щ윭 媛쒕줈 媛덈씪?몃룄 ?ㅼ떆 ?섎굹濡??⑹퀜????泥섎━瑜?怨듯넻?쇰줈 ?????덉뒿?덈떎.

???몃뱶???ㅼ쓬 ??branch瑜??섎굹濡?紐⑥쓭?덈떎.

- single retrieval
- multi retrieval
- follow-up retrieval

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `single_retrieval` | ?⑥씪 議고쉶 branch 寃곌낵?낅땲?? |
| `multi_retrieval` | 蹂듯빀 議고쉶 branch 寃곌낵?낅땲?? |
| `followup_retrieval` | ?댁쟾 current_data ?ъ궗??branch 寃곌낵?낅땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `retrieval_payload` | ?ㅼ젣 ?좏깮??retrieval 寃곌낵?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_retrieval_payload`: ?낅젰?먯꽌 ?ㅼ젣 retrieval_payload瑜?爰쇰깄?덈떎.
- `merge_retrieval_payloads`: skipped媛 ?꾨땶 泥?踰덉㎏ ?좏슚 payload瑜??좏깮?⑸땲??

## 珥덈낫???ъ씤??
???몃뱶???곗씠?곕? ?⑹궛?섍굅??join?섏? ?딆뒿?덈떎.
"?щ윭 branch 異쒕젰 以??대뼡 branch媛 吏꾩쭨?멸?"瑜?怨좊Ⅴ????븷?낅땲??

?곗씠??join?대굹 怨꾩궛? ?섏쨷??pandas ?④퀎?먯꽌 ?⑸땲??

## ?곌껐

```text
Dummy/Oracle Retriever (Single).retrieval_payload
-> Retrieval Payload Merger.single_retrieval

Dummy/Oracle Retriever (Multi).retrieval_payload
-> Retrieval Payload Merger.multi_retrieval

Current Data Retriever.retrieval_payload
-> Retrieval Payload Merger.followup_retrieval

Retrieval Payload Merger.retrieval_payload
-> Retrieval Postprocess Router.retrieval_payload
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "single_retrieval": {
    "skipped": true
  },
  "multi_retrieval": {
    "retrieval_payload": {
      "success": true,
      "source_results": [
        {"dataset_key": "production"},
        {"dataset_key": "wip"}
      ]
    }
  },
  "followup_retrieval": {
    "skipped": true
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {"dataset_key": "production"},
      {"dataset_key": "wip"}
    ],
    "selected_retrieval_branch": "multi_retrieval"
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_retrieval_payload` | `{"retrieval_payload": {...}}` | `{...}` | retriever 異쒕젰????寃?媛먯떥???덉뼱???ㅼ젣 retrieval payload瑜?爰쇰깄?덈떎. |
| `merge_retrieval_payloads` | single/multi/followup ?낅젰 | active retrieval payload | ?щ윭 branch 以?skipped媛 ?꾨땶 泥?踰덉㎏ ?ㅼ젣 寃곌낵瑜??좏깮?⑸땲?? |
| `build_payload` | Langflow inputs | `Data(data=retrieval_payload)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
single branch ?뺤씤
-> multi branch ?뺤씤
-> followup branch ?뺤씤
-> skipped媛 ?꾨땶 payload ?좏깮
-> selected_retrieval_branch ?쒖떆
```

### 珥덈낫???ъ씤??
Langflow?먯꽌???щ윭 branch output???숈떆???ㅼ쓬 ?몃뱶???곌껐?????덉뒿?덈떎. 洹몃옒??媛?branch媛 `skipped`?몄? ?뺤씤?섍퀬 ?ㅼ젣 ?ㅽ뻾??branch留?怨좊Ⅴ???⑸쪟 吏?먯씠 ?꾩슂?⑸땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `merge_retrieval_payloads`

???⑥닔??single, multi, follow-up ???낅젰 以??ㅼ젣 ?ㅽ뻾??retrieval payload ?섎굹瑜?怨좊쫭?덈떎.

### ?⑥닔 input

```json
{
  "single_retrieval_value": {"skipped": true},
  "multi_retrieval_value": {
    "retrieval_payload": {
      "route": "multi_retrieval",
      "source_results": [{"dataset_key": "production"}]
    }
  },
  "followup_retrieval_value": {"skipped": true}
}
```

### ?⑥닔 output

```json
{
  "retrieval_payload": {
    "route": "multi_retrieval",
    "source_results": [{"dataset_key": "production"}],
    "selected_retrieval_branch": "multi_retrieval"
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
for branch, value in candidates:
```

single, multi, followup ?꾨낫瑜??쒖꽌?濡?寃?ы빀?덈떎.

```python
payload = _retrieval_payload(value)
```

媛??꾨낫?먯꽌 ?ㅼ젣 retrieval payload瑜?爰쇰깄?덈떎.

```python
if not payload or payload.get("skipped"):
    continue
```

媛믪씠 鍮꾩뼱 ?덇굅??skipped branch?대㈃ 嫄대꼫?곷땲??

```python
merged = deepcopy(payload)
merged["selected_retrieval_branch"] = branch
return {"retrieval_payload": merged}
```

?ㅼ젣 branch瑜?李얠쑝硫?蹂듭궗蹂몄쓣 留뚮뱾怨??대뼡 branch??붿? ?쒖떆????諛섑솚?⑸땲??

```python
return {"retrieval_payload": {"skipped": True, ...}}
```

?대뒓 branch???ㅽ뻾?섏? ?딆븯?쇰㈃ skipped payload瑜?諛섑솚?⑸땲?? ???몃뱶媛 ?ㅽ뙣 ?먯씤???????덇쾶 ?섍린 ?꾪븿?낅땲??
