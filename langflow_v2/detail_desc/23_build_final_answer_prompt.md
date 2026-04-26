# 23. Build Final Answer Prompt

## ??以???븷

遺꾩꽍 寃곌낵瑜?蹂닿퀬 理쒖쥌 ?먯뿰???듬???留뚮뱾湲??꾪븳 LLM prompt瑜??묒꽦?섎뒗 ?몃뱶?낅땲??

## ???꾩슂?쒓?

`analysis_result`?먮뒗 row, summary, source_results, error ?깆씠 ?ㅼ뼱 ?덉뒿?덈떎.
LLM?먭쾶 ???꾩껜瑜?臾댁옉??蹂대궡硫??덈Т 湲멸굅??遺덈챸?뺥븷 ???덉뒿?덈떎.

???몃뱶???꾩슂???뺣낫留??뺣━?댁꽌 "?ъ슜?먯뿉寃??대뼸寃??듯븷吏"瑜?臾삳뒗 prompt瑜?留뚮벊?덈떎.

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `analysis_result` | `Analysis Result Merger` ?먮뒗 `MongoDB Data Store` 異쒕젰?낅땲?? |
| `preview_row_limit` | LLM prompt???ｌ쓣 row ?섏엯?덈떎. ?꾩껜 final data ?쒖떆 ?섏????ㅻ쫭?덈떎. |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `prompt_payload` | `LLM JSON Caller (Answer)`???섍만 prompt?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_analysis_result`: ?낅젰?먯꽌 ?ㅼ젣 analysis_result瑜?爰쇰깄?덈떎.
- `_safe_rows`: prompt???ｌ쓣 row ?섎? ?쒗븳?⑸땲??
- `_row_count_from_result`: ?꾩껜 row count瑜?怨꾩궛?⑸땲??
- `_source_summaries`: 議고쉶 source蹂?summary瑜?留뚮벊?덈떎.
- `build_final_answer_prompt`: 理쒖쥌 ?듬???prompt瑜?留뚮벊?덈떎.

## 珥덈낫???ъ씤??
???몃뱶??理쒖쥌 ?듬???吏곸젒 留뚮뱾吏 ?딆뒿?덈떎.
理쒖쥌 ?듬? LLM??李멸퀬???뺣━???먮즺瑜?留뚮벊?덈떎.

`preview_row_limit`? LLM 鍮꾩슜??以꾩씠湲??꾪븳 媛믪엯?덈떎.
?ъ슜?먯뿉寃?蹂댁뿬以?理쒖쥌 ?곗씠?곕뒗 `Final Answer Builder`媛 ?곕줈 泥섎━?⑸땲??

## ?곌껐

```text
Analysis Result Merger.analysis_result
?먮뒗 MongoDB Data Store.stored_payload
-> Build Final Answer Prompt.analysis_result

Build Final Answer Prompt.prompt_payload
-> LLM JSON Caller (Answer).prompt_payload
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "analysis_result": {
    "success": true,
    "final_rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "summary": "mode蹂??앹궛??
  },
  "preview_row_limit": "20"
}
```

### 異쒕젰 ?덉떆

```json
{
  "prompt_payload": {
    "prompt": "Write a Korean answer using this final data...",
    "analysis_result": {
      "success": true,
      "final_rows": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ]
    },
    "preview_rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "row_count": 2
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_analysis_result` | `{"analysis_result": {...}}` | result dict | ??merger/store 異쒕젰?먯꽌 ?ㅼ젣 遺꾩꽍 寃곌낵瑜?爰쇰깄?덈떎. |
| `_safe_rows` | rows, limit 20 | 理쒕? 20媛?rows | prompt???덈Т 留롮? row媛 ?ㅼ뼱媛吏 ?딄쾶 ?쒗븳?⑸땲?? |
| `_row_count_from_result` | result, preview rows | ?꾩껜 row count | preview蹂대떎 ?꾩껜 寃곌낵媛 紐?嫄댁씤吏 ?듬????뚮젮二쇨린 ?꾪빐 怨꾩궛?⑸땲?? |
| `_source_summaries` | analysis result | source ?붿빟 諛곗뿴 | 理쒖쥌 ?듬? LLM???대뼡 ?곗씠?곗뿉????寃곌낵?몄? ?????덇쾶 ?⑸땲?? |
| `build_final_answer_prompt` | analysis result | prompt payload | 理쒖쥌 ?듬? LLM???ｌ쓣 臾몄옣, preview, ?붿빟??留뚮벊?덈떎. |
| `build_prompt` | Langflow input | `Data(data=prompt_payload)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
analysis_result ?낅젰
-> final_rows preview ?앹꽦
-> row_count/source summary 怨꾩궛
-> 理쒖쥌 ?듬? LLM??吏耳쒖빞 ??洹쒖튃怨?JSON schema ?묒꽦
```

### 珥덈낫???ъ씤??
???몃뱶??LLM???몄텧?섏? ?딆뒿?덈떎. 理쒖쥌 ?듬? LLM??"理쒖쥌 ?곗씠?곗뿉 洹쇨굅???듯븯??怨??쎌쓣 prompt瑜?留뚮뱶????븷?낅땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `build_final_answer_prompt`

???⑥닔??理쒖쥌 ?듬? LLM?먭쾶 以?prompt? preview data瑜?留뚮벊?덈떎.

### ?⑥닔 input

```json
{
  "analysis_result_value": {
    "analysis_result": {
      "success": true,
      "data": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ],
      "summary": "data analysis complete: 2 rows"
    }
  },
  "preview_row_limit_value": "20"
}
```

### ?⑥닔 output

```json
{
  "prompt_payload": {
    "prompt": "You are a manufacturing data analyst...",
    "preview_rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "row_count": 2
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
result = _analysis_result(analysis_result_value)
```

???몃뱶?먯꽌 ??媛믪쓣 ?ㅼ젣 analysis result dict濡?爰쇰깄?덈떎.

```python
rows = result.get("data") if isinstance(result.get("data"), list) else []
preview_rows = _safe_rows(rows, preview_limit)
```

理쒖쥌 ?곗씠??rows瑜?爰쇰궡怨? prompt???ｌ쓣 留뚰겮留??쒗븳?⑸땲??

```python
row_count = _row_count_from_result(result, preview_rows)
```

?꾩껜 寃곌낵 嫄댁닔瑜?怨꾩궛?⑸땲?? preview媛 20嫄댁씠?대룄 ?ㅼ젣 row_count媛 200嫄댁씠硫??듬????꾩껜 嫄댁닔瑜??뚮젮以????덉뒿?덈떎.

```python
source_summaries = _source_summaries(result)
```

寃곌낵媛 ?대뼡 source dataset?먯꽌 ?붾뒗吏 ?붿빟?⑸땲??

```python
prompt = f"""..."""
```

LLM?먭쾶 ?ㅼ쓬 洹쒖튃??吏?쒗빀?덈떎.

- final data???녿뒗 ?댁슜??吏?대궡吏 留?寃?- ?レ옄??final data 湲곗??쇰줈 留먰븷 寃?- ?쒓뎅?대줈 ?듯븷 寃?- JSON ?뺥깭濡?`response`瑜?諛섑솚??寃?
```python
return {"prompt_payload": {...}}
```

LLM Caller媛 prompt瑜??쎄퀬, ??normalizer媛 ?먮옒 analysis_result??李멸퀬?????덇쾶 context瑜?媛숈씠 諛섑솚?⑸땲??
