# 21. Analysis Result Merger

## ??以???븷

early, direct, pandas branch 以??ㅼ젣 寃곌낵 ?섎굹瑜?怨⑤씪 `analysis_result`濡??듯빀?섎뒗 ?몃뱶?낅땲??

## ???꾩슂?쒓?

???먮쫫? ?щ윭 branch濡??섎돥?덈떎.

- 議곌굔 遺議깆쑝濡?鍮⑤━ ?앸궃 寃곌낵
- 議고쉶留??섍퀬 諛붾줈 ?듯븯??寃곌낵
- pandas 遺꾩꽍??嫄곗튇 寃곌낵

理쒖쥌 ?듬? ?④퀎???섎굹???낅젰留?諛쏅뒗 寃껋씠 ?명븯誘濡????몃뱶媛 branch瑜??ㅼ떆 ?⑹묩?덈떎.

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `early_result` | `Early Result Adapter` 異쒕젰?낅땲?? |
| `direct_result` | `Direct Result Adapter` 異쒕젰?낅땲?? |
| `pandas_result` | `Pandas Analysis Executor` 異쒕젰?낅땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `analysis_result` | ?좏깮??理쒖쥌 遺꾩꽍 寃곌낵?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_analysis_result`: ?낅젰?먯꽌 ?ㅼ젣 result payload瑜?爰쇰깄?덈떎.
- `merge_analysis_results`: skipped媛 ?꾨땶 ?좏슚 寃곌낵瑜??곗꽑?쒖쐞?濡??좏깮?⑸땲??

## 珥덈낫???ъ씤??
???몃뱶???곗씠?곕? 怨꾩궛?섏? ?딆뒿?덈떎.
"?대쾲 ?댁뿉???댁븘?⑥? branch 寃곌낵媛 臾댁뾿?멸?"瑜?怨좊쫭?덈떎.

## ?곌껐

```text
Early Result Adapter.analysis_result
-> Analysis Result Merger.early_result

Direct Result Adapter.analysis_result
-> Analysis Result Merger.direct_result

Pandas Analysis Executor.analysis_result
-> Analysis Result Merger.pandas_result

Analysis Result Merger.analysis_result
-> Build Final Answer Prompt.analysis_result
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "early_result": {"skipped": true},
  "direct_result": {"skipped": true},
  "pandas_result": {
    "analysis_result": {
      "success": true,
      "result_type": "pandas_analysis",
      "final_rows": [
        {"MODE": "A", "production": 150}
      ]
    }
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "analysis_result": {
    "success": true,
    "result_type": "pandas_analysis",
    "selected_analysis_branch": "pandas_result",
    "final_rows": [
      {"MODE": "A", "production": 150}
    ]
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_analysis_result` | `{"analysis_result": {...}}` | `{...}` | branch output?먯꽌 ?ㅼ젣 analysis result瑜?爰쇰깄?덈떎. |
| `merge_analysis_results` | early/direct/pandas | active analysis result | ??branch 以?skipped媛 ?꾨땶 ?ㅼ젣 寃곌낵瑜??섎굹 ?좏깮?⑸땲?? |
| `build_result` | Langflow inputs | `Data(data=analysis_result)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
early_result ?뺤씤
-> direct_result ?뺤씤
-> pandas_result ?뺤씤
-> ?ㅼ젣 寃곌낵 branch ?좏깮
-> selected_analysis_branch ?쒖떆
```

### 珥덈낫???ъ씤??
?욎뿉???щ윭 媛덈옒濡??섎돇?덈뜕 flow瑜??ㅼ떆 ?섎굹濡??⑹튂??吏?먯엯?덈떎. ?ㅼ쓽 理쒖쥌 ?듬? ?몃뱶??branch 醫낅쪟瑜?紐곕씪??`analysis_result` ?섎굹留??쎌쑝硫??⑸땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `merge_analysis_results`

???⑥닔??early/direct/pandas ??寃곌낵 以??ㅼ젣 ?ㅽ뻾??analysis result ?섎굹瑜?怨좊쫭?덈떎.

### ?⑥닔 input

```json
{
  "early_result_value": {"skipped": true},
  "direct_result_value": {"skipped": true},
  "pandas_result_value": {
    "analysis_result": {
      "success": true,
      "data": [{"MODE": "A", "production": 150}]
    }
  }
}
```

### ?⑥닔 output

```json
{
  "analysis_result": {
    "success": true,
    "data": [{"MODE": "A", "production": 150}],
    "selected_analysis_branch": "pandas_result"
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
candidates = [
    ("early_result", early_result_value),
    ("direct_result", direct_result_value),
    ("pandas_result", pandas_result_value),
]
```

??branch瑜??쒖꽌?濡??꾨낫 list???ｌ뒿?덈떎.

```python
for branch, value in candidates:
    result = _analysis_result(value)
```

媛?branch?먯꽌 ?ㅼ젣 analysis result瑜?爰쇰깄?덈떎.

```python
if not result or result.get("skipped"):
    continue
```

鍮꾩뼱 ?덇굅??skipped??branch??嫄대꼫?곷땲??

```python
merged = deepcopy(result)
merged["selected_analysis_branch"] = branch
return {"analysis_result": merged}
```

?ㅼ젣 寃곌낵瑜?李얠쑝硫?蹂듭궗?????대뼡 branch??붿? ?쒖떆?섍퀬 諛섑솚?⑸땲??
