# 16. Retrieval Postprocess Router

## ??以???븷

議고쉶 寃곌낵瑜?諛붾줈 ?듯븷吏, pandas 遺꾩꽍??嫄곗튌吏 ?섎늻??遺꾧린 ?몃뱶?낅땲??

## ??媛吏 遺꾧린

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `direct_response` | 議고쉶 寃곌낵瑜?嫄곗쓽 洹몃?濡?理쒖쥌 ?듬??쇰줈 蹂대궪 ???덉뒿?덈떎. |
| `post_analysis` | group by, sort, metric 怨꾩궛, follow-up 遺꾩꽍 ??pandas 泥섎━媛 ?꾩슂?⑸땲?? |

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `retrieval_payload` | `Retrieval Payload Merger`??異쒕젰?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_select_postprocess_route`: pandas媛 ?꾩슂?쒖? ?먮떒?⑸땲??
- `route_retrieval_postprocess`: ?좏깮??branch?먮뒗 payload瑜?蹂대궡怨??섎㉧吏??skipped 泥섎━?⑸땲??

## pandas媛 ?꾩슂?????寃쎌슦

- `needs_pandas`媛 true
- ?щ윭 source_result媛 ?덉쓬
- ?꾩냽 吏덈Ц?대씪 current_data瑜??ㅼ떆 遺꾩꽍?댁빞 ??- top N, ?뺣젹, 洹몃９ 吏묎퀎, metric 怨꾩궛???꾩슂??
## 珥덈낫???ъ씤??
???몃뱶??遺꾩꽍??吏곸젒 ?섏? ?딆뒿?덈떎.
遺꾩꽍???꾩슂?쒖? ?먮떒?댁꽌 湲몄쓣 ?섎닃 肉먯엯?덈떎.

## ?곌껐

```text
Retrieval Payload Merger.retrieval_payload
-> Retrieval Postprocess Router.retrieval_payload

Retrieval Postprocess Router.direct_response
-> Direct Result Adapter.retrieval_payload

Retrieval Postprocess Router.post_analysis
-> Build Pandas Prompt.retrieval_payload
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "retrieval_payload": {
    "success": true,
    "intent_plan": {
      "needs_pandas": true,
      "query_mode": "retrieval"
    },
    "source_results": [
      {"dataset_key": "production"},
      {"dataset_key": "wip"}
    ]
  }
}
```

### 異쒕젰 ?덉떆

`post_analysis` output:

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {"dataset_key": "production"},
      {"dataset_key": "wip"}
    ]
  },
  "selected_postprocess_route": "post_analysis",
  "branch": "post_analysis"
}
```

`direct_response` output? ?좏깮?섏? ?딆븯?쇰?濡?

```json
{
  "skipped": true,
  "selected_postprocess_route": "post_analysis",
  "branch": "direct_response"
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_retrieval_payload` | `Data(data={"retrieval_payload": {...}})` | retrieval dict | merger 異쒕젰?먯꽌 ?ㅼ젣 payload瑜?爰쇰깄?덈떎. |
| `_select_postprocess_route` | retrieval payload | `"direct_response"` ?먮뒗 `"post_analysis"` | pandas 遺꾩꽍???꾩슂?쒖? 寃곗젙?⑸땲?? multi source, follow-up, `needs_pandas=true`硫?蹂댄넻 post_analysis?낅땲?? |
| `route_retrieval_postprocess` | retrieval payload, branch | active ?먮뒗 skipped payload | ?좏깮??branch留??ㅼ쓬 ?몃뱶媛 泥섎━?섍쾶 ?⑸땲?? |
| `_payload` | branch ?대쫫 | routed payload | class output method?ㅼ씠 怨듭쑀?섎뒗 ?대? ?⑥닔?낅땲?? |
| `build_direct_response`, `build_post_analysis` | ?놁쓬 | `Data(data=payload)` | Langflow canvas??蹂댁씠????output port?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
retrieval_payload ?낅젰
-> source_results 媛쒖닔? needs_pandas ?뺤씤
-> direct_response ?먮뒗 post_analysis ?좏깮
-> ?좏깮?섏? ?딆? output?먮뒗 skipped ?쒖떆
```

### 珥덈낫???ъ씤??
???몃뱶??"議고쉶???곗씠?곕? 洹몃?濡?留먰븷吏", "pandas濡?怨꾩궛????留먰븷吏"瑜??섎늻????踰덉㎏ 援먯감濡쒖엯?덈떎.

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_select_postprocess_route`

???⑥닔??議고쉶 寃곌낵瑜?諛붾줈 ?듬??좎?, pandas 遺꾩꽍?쇰줈 蹂대궪吏 寃곗젙?⑸땲??

### ?⑥닔 input

```json
{
  "intent_plan": {
    "needs_pandas": true,
    "query_mode": "retrieval"
  },
  "source_results": [
    {"dataset_key": "production"},
    {"dataset_key": "wip"}
  ]
}
```

### ?⑥닔 output

```text
post_analysis
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
plan = retrieval.get("intent_plan") if isinstance(retrieval.get("intent_plan"), dict) else {}
```

retrieval payload ?덉뿉??intent plan??爰쇰깄?덈떎.

```python
source_results = retrieval.get("source_results") if isinstance(retrieval.get("source_results"), list) else []
```

議고쉶 寃곌낵媛 紐?媛?source?먯꽌 ?붾뒗吏 ?뺤씤?⑸땲??

```python
if plan.get("needs_pandas") or plan.get("query_mode") == "followup_transform" or len(source_results) > 1:
    return "post_analysis"
```

?꾨옒 以??섎굹?쇰룄 ?대떦?섎㈃ pandas 遺꾩꽍?쇰줈 蹂대깄?덈떎.

- intent plan?먯꽌 pandas ?꾩슂?섎떎怨??먮떒??- ?꾩냽 吏덈Ц??- ?щ윭 dataset??議고쉶??
```python
return "direct_response"
```

洹??몄뿉??議고쉶 寃곌낵瑜?諛붾줈 ?듬????ъ슜?⑸땲??
