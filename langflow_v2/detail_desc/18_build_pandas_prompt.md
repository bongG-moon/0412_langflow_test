# 18. Build Pandas Prompt

## ??以???븷

議고쉶???곗씠?곗? domain ?뺣낫瑜?諛뷀깢?쇰줈 pandas 肄붾뱶 ?앹꽦???꾪븳 prompt瑜?留뚮뱶???몃뱶?낅땲??

## ???꾩슂?쒓?

LLM?먭쾶 洹몃깷 "遺꾩꽍?댁쨾"?쇨퀬 ?섎㈃ 而щ읆紐낆쓣 ?섎せ ?곌굅??遺덊븘?뷀븳 肄붾뱶瑜?留뚮뱾 ???덉뒿?덈떎.
???몃뱶???ㅼ젣 議고쉶??而щ읆怨?row ?덉떆, metric 怨듭떇, grouping hint瑜?prompt???ｌ뼱 pandas 怨꾪쉷?????뺥솗?섍쾶 留뚮벊?덈떎.

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `retrieval_payload` | pandas 遺꾩꽍???꾩슂??議고쉶 寃곌낵?낅땲?? |
| `domain_payload` | metric 怨듭떇, grouping hint ??遺꾩꽍???꾩슂??domain ?뺣낫?낅땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `prompt_payload` | `LLM JSON Caller (Pandas)`???섍만 prompt?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_source_results`: retrieval payload?먯꽌 source result 紐⑸줉??爰쇰깄?덈떎.
- `_merge_sources`: ?щ윭 dataset row瑜?遺꾩꽍?⑹쑝濡??⑹튌 以鍮꾨? ?⑸땲??
- `_domain_prompt`: domain metric怨?alias ?뺣낫瑜?吏㏃? ?ㅻ챸?쇰줈 留뚮벊?덈떎.
- `_build_prompt`: LLM?먭쾶 以?pandas 肄붾뱶 ?묒꽦 吏?쒕Ц??留뚮벊?덈떎.
- `build_pandas_prompt`: ?꾩껜 怨쇱젙???ㅽ뻾?⑸땲??

## 珥덈낫???ъ씤??
???몃뱶??pandas 肄붾뱶瑜??ㅽ뻾?섏? ?딆뒿?덈떎.
肄붾뱶瑜?留뚮뱾湲??꾪븳 prompt留??묒꽦?⑸땲??

?ㅼ젣 LLM ?몄텧? ?ㅼ쓬??`LLM JSON Caller (Pandas)`媛 ?섍퀬, ?ㅽ뻾? `Pandas Analysis Executor`媛 ?⑸땲??

## ?곌껐

```text
Retrieval Postprocess Router.post_analysis
-> Build Pandas Prompt.retrieval_payload

Domain Loader.domain_payload
-> Build Pandas Prompt.domain_payload

Build Pandas Prompt.prompt_payload
-> LLM JSON Caller (Pandas).prompt_payload
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "retrieval_payload": {
    "intent_plan": {
      "group_by": ["MODE"],
      "metrics": ["achievement_rate"]
    },
    "source_results": [
      {
        "dataset_key": "production",
        "data": [{"MODE": "A", "production": 100}]
      },
      {
        "dataset_key": "wip",
        "data": [{"MODE": "A", "wip_qty": 50}]
      }
    ]
  },
  "domain_payload": {
    "domain": {
      "metrics": {
        "achievement_rate": {
          "formula": "sum(production) / sum(wip_qty) * 100"
        }
      }
    }
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "prompt_payload": {
    "prompt": "Write pandas code that creates result_df...",
    "retrieval_payload": {"source_results": []},
    "plan": {
      "group_by": ["MODE"],
      "metrics": ["achievement_rate"]
    },
    "rows": [
      {"MODE": "A", "production": 100, "wip_qty": 50}
    ],
    "columns": ["MODE", "production", "wip_qty"]
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_pd` | ?놁쓬 | pandas module | pandas媛 ?ㅼ튂?섏뼱 ?덈뒗吏 ?뺤씤?섍퀬 ?꾩슂????import?⑸땲?? |
| `_source_results` | retrieval payload | source result list | 議고쉶 寃곌낵 諛곗뿴留?爰쇰깄?덈떎. |
| `_merge_sources` | production rows + wip rows | ?⑹퀜吏?rows/columns | ?щ윭 dataset 寃곌낵瑜?pandas媛 ?ㅻ０ ?섎굹??row 紐⑸줉?쇰줈 以鍮꾪빀?덈떎. |
| `_domain_from_payload` | domain payload | domain dict | formula, metric ?ㅻ챸??prompt???ｊ린 ?꾪빐 爰쇰깄?덈떎. |
| `_domain_prompt` | domain dict | 吏㏃? ?꾨찓???ㅻ챸 臾몄옄??| LLM??而щ읆 ?섎?? metric 怨꾩궛?앹쓣 李멸퀬?섎룄濡??щ엺???쎈뒗 臾몄옣?쇰줈 諛붽퓠?덈떎. |
| `_build_prompt` | plan, rows, columns, domain | pandas code ?묒꽦 prompt | LLM?먭쾶 `result_df`瑜?留뚮뱾?쇰뒗 援ъ껜??吏?쒕? ?묒꽦?⑸땲?? |
| `build_pandas_prompt` | retrieval payload, domain | prompt payload | pandas LLM ?몄텧???꾩슂??紐⑤뱺 ?щ즺瑜??섎굹濡?臾띠뒿?덈떎. |
| `build_prompt` | Langflow input | `Data(data=prompt_payload)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
retrieval_payload?먯꽌 source_results 異붿텧
-> ?щ윭 source rows瑜?遺꾩꽍??rows濡?蹂묓빀
-> domain metric/formula ?ㅻ챸 ?앹꽦
-> LLM??pandas code瑜?諛섑솚?섎룄濡?prompt ?묒꽦
```

### 珥덈낫???ъ씤??
???몃뱶??pandas瑜??ㅽ뻾?섏? ?딆뒿?덈떎. "?대뼡 pandas 肄붾뱶瑜?留뚮뱾硫?醫뗭쓣吏" LLM?먭쾶 ?붿껌?섎뒗 prompt留?留뚮벊?덈떎.

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_merge_sources`

???⑥닔???щ윭 dataset?먯꽌 議고쉶??rows瑜?pandas媛 遺꾩꽍???섎굹??table ?뺥깭濡?以鍮꾪빀?덈떎.

### ?⑥닔 input

```json
[
  {
    "dataset_key": "production",
    "data": [{"MODE": "A", "production": 100}]
  },
  {
    "dataset_key": "wip",
    "data": [{"MODE": "A", "wip_qty": 50}]
  }
]
```

### ?⑥닔 output

```json
{
  "success": true,
  "data": [
    {"MODE": "A", "production": 100, "wip_qty": 50}
  ],
  "columns": ["MODE", "production", "wip_qty"]
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
frames = []
for source in source_results:
    rows = source.get("data") if isinstance(source.get("data"), list) else []
```

媛?source result?먯꽌 row list瑜?爰쇰깄?덈떎.

```python
frame = pd.DataFrame(rows)
frames.append(frame)
```

rows瑜?pandas DataFrame?쇰줈 諛붽씀怨?`frames`??紐⑥쓭?덈떎.

```python
if len(frames) == 1:
    merged = frames[0]
```

source媛 ?섎굹肉먯씠硫?join???꾩슂 ?놁씠 洹몃?濡??ъ슜?⑸땲??

```python
else:
    merged = ...
```

source媛 ?щ윭 媛쒖씠硫?怨듯넻 而щ읆??湲곗??쇰줈 蹂묓빀?⑸땲?? ?덈? ?ㅼ뼱 production怨?wip 紐⑤몢 `MODE`媛 ?덉쑝硫?`MODE` 湲곗??쇰줈 ?⑹퀜吏묐땲??

```python
return {"success": True, "data": merged.to_dict(orient="records"), "columns": list(merged.columns)}
```

理쒖쥌 DataFrame???ㅼ떆 list[dict]濡?諛붽퓭 prompt payload???ｌ뒿?덈떎.

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_build_prompt`

???⑥닔??Pandas LLM???쎌쓣 ?ㅼ젣 prompt 臾몄옄?댁쓣 留뚮벊?덈떎.

### ?⑥닔 input

```json
{
  "plan": {
    "group_by": ["MODE"],
    "metrics": ["achievement_rate"],
    "analysis_goal": "mode蹂??앹궛?ъ꽦瑜?怨꾩궛"
  },
  "rows": [
    {"MODE": "A", "production": 100, "wip_qty": 50}
  ],
  "columns": ["MODE", "production", "wip_qty"],
  "domain": {
    "metrics": {
      "achievement_rate": {
        "formula": "sum(production) / sum(wip_qty) * 100"
      }
    }
  }
}
```

### ?⑥닔 output

```text
You are writing pandas code...
Available columns: MODE, production, wip_qty
Return JSON only...
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
preview_rows = rows[:20]
```

LLM prompt???꾩껜 rows瑜????ｌ? ?딄퀬 ???쇰?留??ｌ뒿?덈떎. ?곗씠?곌? 留롮쓣?섎줉 token??而ㅼ?湲??뚮Ц?낅땲??

```python
domain_text = _domain_prompt(domain)
```

domain???ㅼ뼱 ?덈뒗 metric formula??column ?섎?瑜??щ엺???쎈뒗 ?ㅻ챸?쇰줈 諛붽퓠?덈떎.

```python
prompt = f"""..."""
```

LLM?먭쾶 ?ㅼ쓬 議곌굔??吏?쒗빀?덈떎.

- pandas DataFrame ?대쫫? `df`瑜??ъ슜??寃?- 理쒖쥌 寃곌낵??諛섎뱶??`result` 蹂?섏뿉 ?댁쓣 寃?- import???뚯씪 ?묎렐 媛숈? 肄붾뱶???곗? 留?寃?- JSON?쇰줈 `code`, `explanation`, `warnings`瑜?諛섑솚??寃?
```python
Available columns:
{json.dumps(columns, ensure_ascii=False)}
```

LLM???녿뒗 而щ읆紐낆쓣 吏?대궡吏 ?딅룄濡??ㅼ젣 ?ъ슜 媛?ν븳 而щ읆 紐⑸줉???ｌ뒿?덈떎.

```python
Sample rows:
{json.dumps(preview_rows, ensure_ascii=False, indent=2)}
```

LLM???곗씠???뺥깭瑜??댄빐?섎룄濡??쇰? row ?덉떆瑜??ｌ뒿?덈떎.

### ?????⑥닔媛 以묒슂?쒓??

Pandas code ?덉쭏? prompt媛 醫뚯슦?⑸땲?? ???⑥닔媛 而щ읆, ?덉떆 row, domain formula瑜????ｌ뼱以섏빞 LLM???ㅽ뻾 媛?ν븳 pandas 肄붾뱶瑜?留뚮뱾 媛?μ꽦???믪븘吏묐땲??
