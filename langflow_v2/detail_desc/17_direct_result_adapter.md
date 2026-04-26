# 17. Direct Result Adapter

## ??以???븷

pandas 遺꾩꽍???꾩슂 ?녿뒗 議고쉶 寃곌낵瑜?`analysis_result` ?뺥깭濡?諛붽씀???몃뱶?낅땲??

## ?몄젣 ?곕굹?

?덈? ?ㅼ뼱 ?⑥닚??`?ㅻ뒛 DA怨듭젙 ?앹궛???뚮젮以?泥섎읆 議고쉶??row? summary留뚯쑝濡??듯븷 ???덈뒗 寃쎌슦 ?ъ슜?⑸땲??

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `retrieval_payload` | `Retrieval Postprocess Router.direct_response` 異쒕젰?낅땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `analysis_result` | 理쒖쥌 ?듬? ?④퀎媛 ?쎌쓣 ?쒖? 寃곌낵?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_retrieval_payload`: ?낅젰?먯꽌 ?ㅼ젣 retrieval payload瑜?爰쇰깄?덈떎.
- `adapt_direct_result`: source_results, rows, summary瑜?final ?④퀎??analysis_result濡??뺣━?⑸땲??

## 珥덈낫???ъ씤??
???몃뱶???곗씠?곕? 怨꾩궛?섏? ?딆뒿?덈떎.
議고쉶 寃곌낵瑜?理쒖쥌 ?듬? ?몃뱶媛 ?쎄린 ?ъ슫 紐⑥뼇?쇰줈 諛붽씀??adapter?낅땲??

## ?곌껐

```text
Retrieval Postprocess Router.direct_response
-> Direct Result Adapter.retrieval_payload

Direct Result Adapter.analysis_result
-> Analysis Result Merger.direct_result
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {
        "dataset_key": "production",
        "data": [
          {"MODE": "A", "production": 10}
        ],
        "summary": "total rows 1"
      }
    ]
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "analysis_result": {
    "success": true,
    "result_type": "direct_response",
    "source_results": [
      {
        "dataset_key": "production",
        "data": [
          {"MODE": "A", "production": 10}
        ]
      }
    ],
    "final_rows": [
      {"MODE": "A", "production": 10}
    ],
    "summary": "total rows 1"
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_retrieval_payload` | `{"retrieval_payload": {...}}` | retrieval dict | ??router output?먯꽌 ?ㅼ젣 議고쉶 寃곌낵瑜?爰쇰깄?덈떎. |
| `adapt_direct_result` | retrieval payload | analysis result | pandas ?놁씠 諛붾줈 理쒖쥌 ?듬??쇰줈 媛????덇쾶 議고쉶 寃곌낵瑜?analysis_result ?뺤떇?쇰줈 諛붽퓠?덈떎. |
| `build_result` | Langflow input | `Data(data=analysis_result)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
direct_response branch ?낅젰
-> 泥?source_result??data瑜?final_rows濡??ъ슜
-> source_results? summary ?좎?
-> Analysis Result Merger濡??꾨떖
```

### 珥덈낫???ъ씤??
議고쉶 寃곌낵瑜?洹몃?濡?蹂댁뿬以섎룄 ?섎뒗 吏덈Ц?대씪硫?pandas瑜?嫄곗튂吏 ?딆뒿?덈떎. 洹몃옒?????몃뱶? 紐⑥뼇??留욎텛湲??꾪빐 `analysis_result`濡?蹂?섑빀?덈떎.

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `adapt_direct_result`

???⑥닔??retrieval payload瑜?final answer媛 ?쎌쓣 ???덈뒗 analysis result濡?諛붽퓠?덈떎.

### ?⑥닔 input

```json
{
  "retrieval_payload": {
    "source_results": [
      {
        "dataset_key": "production",
        "data": [
          {"MODE": "A", "production": 10}
        ],
        "summary": "total rows 1"
      }
    ],
    "intent_plan": {"route": "single_retrieval"}
  }
}
```

### ?⑥닔 output

```json
{
  "analysis_result": {
    "success": true,
    "tool_name": "direct_response",
    "data": [
      {"MODE": "A", "production": 10}
    ],
    "summary": "total rows 1",
    "analysis_logic": "direct_response"
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
retrieval = _retrieval_payload(retrieval_payload_value)
```

???몃뱶?먯꽌 ?섏뼱??媛믪쓣 retrieval payload dict濡?爰쇰깄?덈떎.

```python
source_results = retrieval.get("source_results") if isinstance(retrieval.get("source_results"), list) else []
first = source_results[0] if source_results and isinstance(source_results[0], dict) else {}
```

吏곸젒 ?듬?? 蹂댄넻 泥?踰덉㎏ 議고쉶 寃곌낵瑜?湲곗??쇰줈 ?⑸땲??

```python
rows = first.get("data") if isinstance(first.get("data"), list) else []
```

泥?source result ?덉쓽 ?ㅼ젣 row list瑜?爰쇰깄?덈떎.

```python
result = {
    "success": bool(first.get("success", retrieval.get("success", True))),
    "data": rows,
    "summary": first.get("summary", retrieval.get("summary", "")),
    ...
}
```

pandas 寃곌낵? 媛숈? 紐⑥뼇?쇰줈 留욎텛湲??꾪빐 `success`, `data`, `summary`, `source_results`, `intent_plan` ?깆쓣 梨꾩썎?덈떎.
