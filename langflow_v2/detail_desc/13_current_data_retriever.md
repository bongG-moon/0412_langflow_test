# 13. Current Data Retriever

## ??以???븷

?꾩냽 吏덈Ц?먯꽌 ?댁쟾 寃곌낵??`state.current_data`瑜???議고쉶 寃곌낵泥섎읆 ?ㅼ떆 爰쇰궡???몃뱶?낅땲??

## ?몄젣 ?곕굹?

泥?吏덈Ц:

```text
?ㅻ뒛 DA怨듭젙 ?앹궛???뚮젮以?```

?꾩냽 吏덈Ц:

```text
?대븣 媛???앹궛?됱씠 留롮븯??MODE ?뚮젮以?```

??踰덉㎏ 吏덈Ц? DB瑜??덈줈 議고쉶???꾩슂媛 ?놁뒿?덈떎.
?댁쟾 寃곌낵瑜?pandas濡??ㅼ떆 遺꾩꽍?섎㈃ ?⑸땲??

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `intent_plan` | `Intent Route Router.followup_transform` 異쒕젰?낅땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `retrieval_payload` | ?댁쟾 current_data瑜?source_results泥섎읆 媛먯떬 payload?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_source_result_from_current_data`: current_data瑜?source_result ?뺥깭濡?諛붽퓠?덈떎.
- `_build_current_datasets`: ?꾩옱 ?곗씠?곗쓽 dataset ?붿빟??留뚮벊?덈떎.
- `retrieve_current_data`: ?꾩냽 遺꾩꽍???꾩슂??retrieval_payload瑜?留뚮벊?덈떎.

## 珥덈낫???ъ씤??
?대쫫? Retriever吏留?DB 議고쉶瑜??섏? ?딆뒿?덈떎.
?대? 媛吏怨??덈뒗 ?곗씠?곕? "議고쉶 寃곌낵泥섎읆" ?ъ옣?댁꽌 ???몃뱶?ㅼ씠 媛숈? 諛⑹떇?쇰줈 泥섎━?섍쾶 留뚮벊?덈떎.

## ?곌껐

```text
Intent Route Router.followup_transform
-> Current Data Retriever.intent_plan

Current Data Retriever.retrieval_payload
-> Retrieval Payload Merger.followup_retrieval
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "intent_plan": {
    "route": "followup_transform",
    "state": {
      "current_data": {
        "rows": [
          {"MODE": "A", "production": 10},
          {"MODE": "B", "production": 20}
        ],
        "summary": "previous production result"
      }
    }
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "retrieval_payload": {
    "success": true,
    "query_mode": "followup_transform",
    "source_results": [
      {
        "success": true,
        "dataset_key": "current_data",
        "tool_name": "current_data",
        "data": [
          {"MODE": "A", "production": 10},
          {"MODE": "B", "production": 20}
        ]
      }
    ],
    "current_data": {
      "rows": [
        {"MODE": "A", "production": 10},
        {"MODE": "B", "production": 20}
      ]
    }
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_rows_columns` | `[{"MODE": "A", "production": 10}]` | `["MODE", "production"]` | ?꾩옱 ?곗씠?곗쓽 而щ읆 ?뺣낫瑜??붿빟?⑸땲?? |
| `_build_current_datasets` | source_results | `{"current_data": {"rows": [...]}}` | ?꾩냽 吏덈Ц?먯꽌??current_data 援ъ“瑜??좎??⑸땲?? |
| `_source_result_from_current_data` | state.current_data | source result | ?댁쟾 寃곌낵瑜?retriever媛 議고쉶??寃껋쿂??媛숈? schema濡?媛먯뙃?덈떎. |
| `retrieve_current_data` | intent plan | retrieval payload | ?꾩냽 吏덈Ц branch?먯꽌 ?댁쟾 ?곗씠?곕? ?ㅼ떆 遺꾩꽍 媛?ν븳 payload濡?留뚮벊?덈떎. |
| `build_payload` | Langflow input | `Data(data=retrieval_payload)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
intent_plan.state.current_data ?뺤씤
-> rows ?먮뒗 datasets?먯꽌 湲곗〈 ?곗씠??異붿텧
-> source_results ?뺤떇?쇰줈 蹂??-> Retrieval Payload Merger???꾨떖
```

### 珥덈낫???ъ씤??
???몃뱶??DB瑜??덈줈 議고쉶?섏? ?딆뒿?덈떎. "?대븣", "??寃곌낵" 媛숈? ?꾩냽 吏덈Ц?먯꽌 ?댁쟾 寃곌낵瑜??ㅼ떆 議고쉶 寃곌낵泥섎읆 ?ъ옣???ㅼ쓬 遺꾩꽍 ?④퀎濡??섍퉩?덈떎.

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `retrieve_current_data`

???⑥닔??state ?덉쓽 `current_data`瑜?議고쉶 寃곌낵泥섎읆 諛붽퓭 以띾땲??

### ?⑥닔 input

```json
{
  "intent_plan": {
    "route": "followup_transform",
    "state": {
      "current_data": {
        "data": [
          {"MODE": "A", "production": 10}
        ],
        "summary": "previous result"
      }
    }
  }
}
```

### ?⑥닔 output

```json
{
  "retrieval_payload": {
    "route": "followup_transform",
    "source_results": [
      {
        "dataset_key": "current_data",
        "data": [
          {"MODE": "A", "production": 10}
        ]
      }
    ]
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
payload = _payload_from_value(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
```

router?먯꽌 ?섏뼱??媛믪쓣 dict濡?諛붽씀怨??ㅼ젣 intent plan??爰쇰깄?덈떎.

```python
state = payload.get("state") if isinstance(payload.get("state"), dict) else plan.get("state", {})
current_data = state.get("current_data") if isinstance(state.get("current_data"), dict) else {}
```

?꾩냽 遺꾩꽍??湲곗????섎뒗 `current_data`瑜?state?먯꽌 李얠뒿?덈떎.

```python
source_results = [_source_result_from_current_data(current_data)] if current_data else []
```

current_data媛 ?덉쑝硫?source result ?섎굹濡?媛먯뙃?덈떎. ?대젃寃??댁빞 ?ㅼ쓽 `Retrieval Payload Merger`? pandas ?몃뱶媛 ?좉퇋 議고쉶 寃곌낵? 媛숈? 諛⑹떇?쇰줈 泥섎━?????덉뒿?덈떎.

```python
return {"retrieval_payload": {...}}
```

?꾩냽 吏덈Ц branch??retrieval payload ?뺤떇?쇰줈 諛섑솚?⑸땲?? ???몃뱶???닿쾬??DB 議고쉶?몄? current data ?ъ궗?⑹씤吏 紐곕씪??媛숈? 援ъ“濡??쎌뒿?덈떎.
