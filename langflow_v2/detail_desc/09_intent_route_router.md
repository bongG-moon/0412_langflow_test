# 09. Intent Route Router

## ??以???븷

`intent_plan.route` 媛믪쓣 蹂닿퀬 flow瑜???媛덈옒濡??섎늻??遺꾧린 ?몃뱶?낅땲??

## ??媛吏 遺꾧린

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `single_retrieval` | dataset ?섎굹留?議고쉶?섎㈃ ?섎뒗 吏덈Ц?낅땲?? |
| `multi_retrieval` | ?щ윭 dataset??議고쉶?댁빞 ?섎뒗 吏덈Ц?낅땲?? |
| `followup_transform` | ?댁쟾 寃곌낵瑜??ㅼ떆 遺꾩꽍?섎뒗 ?꾩냽 吏덈Ц?낅땲?? |
| `finish` | 議곌굔 遺議? 議고쉶 遺덊븘???깆쑝濡?諛붾줈 醫낅즺?섍굅???덈궡?댁빞 ?섎뒗 寃쎌슦?낅땲?? |

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `intent_plan` | `Normalize Intent Plan`??異쒕젰?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_intent_payload`: ?낅젰?먯꽌 ?ㅼ젣 intent plan??爰쇰깄?덈떎.
- `_select_route`: route 媛믪쓣 ?쎄퀬 ?좏슚??遺꾧린 ?대쫫?쇰줈 ?뺣━?⑸땲??
- `route_intent`: ?좏깮??branch?먮뒗 ?ㅼ젣 payload瑜? ?섎㉧吏 branch?먮뒗 skipped payload瑜?蹂대깄?덈떎.

## skipped payload??

?좏깮?섏? ?딆? 異쒕젰??Langflow ?곌껐??downstream ?몃뱶??媛믪씠 ?ㅼ뼱媛????덉뒿?덈떎.
洹몃옒???좏깮?섏? ?딆? branch?먮뒗 ?ㅼ쓬泥섎읆 ?쒖떆?⑸땲??

```json
{
  "skipped": true,
  "skip_reason": "route is multi_retrieval"
}
```

???몃뱶?ㅼ? `skipped: true`瑜?蹂대㈃ ?꾨Т ?묒뾽???섏? ?딆뒿?덈떎.

## 珥덈낫???ъ씤??
???몃뱶媛 ?덉뼱??Langflow ?붾㈃?먯꽌 遺꾧린媛 ?덉뿉 蹂댁엯?덈떎.
利? `single`, `multi`, `follow-up`, `finish`瑜?罹붾쾭?ㅼ뿉??紐낇솗???뺤씤?섍린 ?꾪븳 ?몃뱶?낅땲??

## ?곌껐

```text
Normalize Intent Plan.intent_plan
-> Intent Route Router.intent_plan

Intent Route Router.single_retrieval
-> Dummy/Oracle Retriever (Single).intent_plan

Intent Route Router.multi_retrieval
-> Dummy/Oracle Retriever (Multi).intent_plan

Intent Route Router.followup_transform
-> Current Data Retriever.intent_plan

Intent Route Router.finish
-> Early Result Adapter.intent_plan
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "intent_plan": {
    "route": "multi_retrieval",
    "query_mode": "retrieval",
    "retrieval_jobs": [
      {"dataset_key": "production"},
      {"dataset_key": "wip"}
    ]
  },
  "state": {
    "session_id": "abc"
  }
}
```

### 異쒕젰 ?덉떆

`multi_retrieval` output?먮뒗 ?ㅼ젣 payload媛 ?섍컩?덈떎.

```json
{
  "intent_plan": {
    "route": "multi_retrieval",
    "retrieval_jobs": [
      {"dataset_key": "production"},
      {"dataset_key": "wip"}
    ]
  },
  "selected_route": "multi_retrieval",
  "branch": "multi_retrieval"
}
```

?좏깮?섏? ?딆? `single_retrieval` output?먮뒗 skipped payload媛 ?섍컩?덈떎.

```json
{
  "skipped": true,
  "skip_reason": "selected route is multi_retrieval",
  "selected_route": "multi_retrieval",
  "branch": "single_retrieval"
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_intent_payload` | `{"intent_plan": {...}}` ?먮뒗 plan ?먯껜 | ?쒖? payload | ???몃뱶媛 ?대뼡 媛먯떥湲??뺥깭濡?二쇰뱺 `intent_plan` key媛 ?덈뒗 ?뺥깭濡?留욎땅?덈떎. |
| `_select_route` | `{"route": "multi_retrieval"}` | `"multi_retrieval"` | route, query_mode, retrieval_jobs 媛쒖닔瑜?蹂닿퀬 ?ㅼ젣 ?좏깮 branch瑜??뺥빀?덈떎. |
| `route_intent` | intent payload, `"single_retrieval"` | active ?먮뒗 skipped payload | ?좏깮 branch留??ㅼ젣 泥섎━?섍퀬 ?섎㉧吏??嫄대꼫?곌쾶 留뚮벊?덈떎. |
| `_payload` | branch ?대쫫 | routed payload | class method?ㅼ씠 怨듯넻?쇰줈 ?곕뒗 ?대? ?⑥닔?낅땲?? status???ш린??媛깆떊?⑸땲?? |
| `build_single_retrieval` ??| ?놁쓬 | `Data(data=payload)` | Langflow canvas??蹂댁씠??媛?output port?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
Normalize Intent Plan 寃곌낵 ?낅젰
-> route 寃곗젙
-> 媛?output method媛 ?먭린 branch? 鍮꾧탳
-> 留욌뒗 branch??active payload
-> ?꾨땶 branch??skipped payload
```

### 珥덈낫???ъ씤??
???몃뱶???ㅼ젣 議고쉶瑜??섏? ?딆뒿?덈떎. Langflow ?붾㈃?먯꽌 "?대뒓 湲몃줈 媛붾뒗吏"瑜?蹂댁씠寃??섍린 ?꾪븳 援먯감濡???븷?낅땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `route_intent`

???⑥닔???꾩옱 branch媛 ?좏깮??branch?몄? ?뺤씤?섍퀬, 留욎쑝硫?payload瑜??듦낵?쒗궎怨??꾨땲硫?`skipped` payload瑜?諛섑솚?⑸땲??

### ?⑥닔 input

```json
{
  "intent_plan_value": {
    "intent_plan": {
      "route": "multi_retrieval",
      "retrieval_jobs": [{"dataset_key": "production"}, {"dataset_key": "wip"}]
    }
  },
  "branch": "single_retrieval"
}
```

### ?⑥닔 output

?좏깮 branch? ?ㅻⅤ硫?

```json
{
  "skipped": true,
  "skip_reason": "selected route is multi_retrieval",
  "selected_route": "multi_retrieval",
  "branch": "single_retrieval"
}
```

?좏깮 branch? 媛숈쑝硫?

```json
{
  "intent_plan": {"route": "multi_retrieval"},
  "selected_route": "multi_retrieval",
  "branch": "multi_retrieval"
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
payload = _intent_payload(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else {}
```

?낅젰媛믪뿉???ㅼ젣 intent plan??爰쇰깄?덈떎.

```python
selected = _select_route(plan)
```

plan??route, query_mode, retrieval_jobs 媛쒖닔瑜?蹂닿퀬 ?ㅼ젣 ?좏깮 route瑜?怨꾩궛?⑸땲??

```python
if selected != branch:
    return {
        "skipped": True,
        "skip_reason": f"selected route is {selected}",
        ...
    }
```

?꾩옱 output port媛 ?좏깮??branch媛 ?꾨땲硫?`skipped=True`濡?諛섑솚?⑸땲?? ???몃뱶????媛믪쓣 蹂닿퀬 ?ㅼ젣 泥섎━瑜??섏? ?딆뒿?덈떎.

```python
routed = deepcopy(payload)
routed["selected_route"] = selected
routed["branch"] = branch
return routed
```

?꾩옱 output port媛 ?좏깮??branch?쇰㈃ ?먮옒 payload瑜?蹂듭궗?댁꽌 ?듦낵?쒗궢?덈떎. ?먮낯??吏곸젒 ?섏젙?섏? ?딆쑝?ㅺ퀬 `deepcopy`瑜??ъ슜?⑸땲??
