# 08. Normalize Intent Plan

## ??以???븷

LLM??intent ?묐떟???ㅼ젣 flow媛 ?ъ슜?????덈뒗 `intent_plan`?쇰줈 ?뺣━?섍퀬 蹂댁젙?섎뒗 ?몃뱶?낅땲??

## ??以묒슂?쒓?

LLM? 媛??dataset???섎굹留?留먰븯嫄곕굹, ?좎쭨瑜?鍮쇰㉨嫄곕굹, ?꾩냽 吏덈Ц????議고쉶泥섎읆 ?댁꽍?????덉뒿?덈떎.
???몃뱶??domain怨?table catalog瑜??ㅼ떆 ?뺤씤?댁꽌 洹몃윴 ?ㅼ닔瑜?以꾩엯?덈떎.

?뱁엳 metric??`required_datasets`媛 ?덉쑝硫? LLM???섎굹留?留먰빐???꾩슂??dataset??紐⑤몢 retrieval plan??異붽??⑸땲??

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `llm_result` | `LLM JSON Caller (Intent)`??異쒕젰?낅땲?? |
| `reference_date` | ?뚯뒪?몄슜 湲곗? ?좎쭨?낅땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `intent_plan` | route, retrieval_jobs, filters, group_by ?깆쓣 ?ы븿???ㅽ뻾 怨꾪쉷?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_extract_json_object`: LLM ?묐떟?먯꽌 JSON object瑜?李얠뒿?덈떎.
- `_extract_date`: `?ㅻ뒛`, `?댁젣` 媛숈? ?쒗쁽???좎쭨濡?諛붽퓠?덈떎.
- `_dataset_hints`: 吏덈Ц怨?table/domain ?뺣낫瑜?蹂닿퀬 ?꾩슂??dataset ?꾨낫瑜?李얠뒿?덈떎.
- `_matched_metrics`: 吏덈Ц??留욌뒗 metric 洹쒖튃??domain?먯꽌 李얠뒿?덈떎.
- `_filters_from_question`: 怨듭젙, ?쒗뭹, 議곌굔 ?쒗쁽??filter濡?諛붽퓠?덈떎.
- `_build_job`: dataset ?섎굹瑜?議고쉶?섍린 ?꾪븳 retrieval job??留뚮벊?덈떎.
- `_normalize_plan`: ?꾩껜 intent plan??route 媛?ν븳 ?뺥깭濡??꾩꽦?⑸땲??

## 異쒕젰 ?덉떆

```json
{
  "intent_plan": {
    "route": "multi_retrieval",
    "query_mode": "retrieval",
    "dataset_hints": ["production", "target"],
    "required_params": {"date": "20260426"},
    "needs_pandas": true
  },
  "retrieval_jobs": []
}
```

## 珥덈낫???ъ씤??
???몃뱶??LLM 寃곌낵瑜?洹몃?濡?誘우? ?딆뒿?덈떎.
洹쒖튃 湲곕컲 蹂댁젙???④퍡 ?⑸땲??

?덈? ?ㅼ뼱 `?앹궛?ъ꽦????domain?먯꽌 `production`, `target`???붽뎄?쒕떎硫? LLM??`production`留?諛섑솚?대룄 ???몃뱶媛 `target`??異붽??⑸땲??

## ?곌껐

```text
LLM JSON Caller (Intent).llm_result
-> Normalize Intent Plan.llm_result

Normalize Intent Plan.intent_plan
-> Intent Route Router.intent_plan
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "llm_result": {
    "llm_text": "{\"query_mode\":\"retrieval\",\"datasets\":[\"production\"],\"filters\":{\"process\":\"WB\"},\"needs_pandas\":true}",
    "prompt_payload": {
      "state": {
        "pending_user_question": "?댁젣 WB怨듭젙 ?앹궛?ъ꽦瑜좎쓣 mode蹂꾨줈 ?뚮젮以?,
        "current_data": null
      },
      "domain": {
        "metrics": {
          "achievement_rate": {
            "aliases": ["?ъ꽦瑜?],
            "required_datasets": ["production", "wip"]
          }
        }
      },
      "table_catalog": {
        "datasets": {
          "production": {"tool_name": "get_production_data", "required_params": ["date"]},
          "wip": {"tool_name": "get_wip_status", "required_params": ["date"]}
        }
      }
    }
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "intent_plan": {
    "query_mode": "retrieval",
    "route": "multi_retrieval",
    "datasets": ["production", "wip"],
    "filters": {"process": "WB"},
    "group_by": ["MODE"],
    "needs_pandas": true,
    "retrieval_jobs": [
      {"dataset_key": "production", "tool_name": "get_production_data", "params": {"process": "WB", "date": "20260425"}},
      {"dataset_key": "wip", "tool_name": "get_wip_status", "params": {"process": "WB", "date": "20260425"}}
    ]
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_normalize_triple_quoted_json` | `{"dsn": """abc"""}` | ?좏슚??JSON 臾몄옄??| ?ъ슜?먭? `""" """`濡??ｌ? DB/JSON 臾몄옄?댁씠 ?뚯떛?섎룄濡?蹂댁젙?⑸땲?? |
| `_extract_json_object` | LLM ?ㅻ챸臾?+ JSON | JSON dict | LLM??JSON ?욌뮘濡?留먯쓣 遺숈뿬???ㅼ젣 JSON留?爰쇰깄?덈떎. |
| `_extract_date` | `"?댁젣 ?앹궛??`, 湲곗???`2026-04-26` | `"20260425"` | ?ㅻ뒛/?댁젣 媛숈? ?먯뿰???좎쭨瑜?議고쉶 ?뚮씪誘명꽣濡?諛붽퓠?덈떎. |
| `_dataset_hints` | 吏덈Ц, catalog, domain | `["production"]` | 吏덈Ц ??keyword瑜?蹂닿퀬 ?꾩슂??dataset ?꾨낫瑜?李얠뒿?덈떎. |
| `_matched_metrics` | `"?앹궛?ъ꽦瑜?` | `{"achievement_rate": {...}}` | domain metric alias? 吏덈Ц??留ㅼ묶?⑸땲?? |
| `_filters_from_question` | `"WB怨듭젙 mode蹂?` | `{"process": "WB"}` | 吏덈Ц?먯꽌 怨듭젙, ?쒗뭹援?媛숈? filter瑜?異붿텧?⑸땲?? |
| `_group_by_from_question` | `"mode蹂?` | `["MODE"]` | pandas 吏묎퀎 湲곗? 而щ읆??異붿젙?⑸땲?? |
| `_required_params` | 吏덈Ц, state | `{"date": "20260425"}` | dataset 議고쉶??瑗??꾩슂???좎쭨 媛숈? 媛믪쓣 梨꾩썎?덈떎. |
| `_build_job` | dataset config, params | retrieval job dict | retriever媛 諛붾줈 ?ㅽ뻾?????덈뒗 ?묒뾽 ?⑥쐞濡?留뚮벊?덈떎. |
| `_normalize_plan` | LLM plan + domain/catalog | ?쒖? intent plan | LLM 寃곌낵, domain required_datasets, fallback 異붾줎???⑹퀜 理쒖쥌 route瑜??뺥빀?덈떎. |
| `normalize_intent_plan` | `llm_result` | `intent_plan` payload | Langflow?먯꽌 諛쏆? LLM 寃곌낵瑜??ㅼ젣 flow媛 ?곕뒗 ?뺥깭濡?諛붽퓠?덈떎. |

### 肄붾뱶 ?먮쫫

```text
LLM raw text ?뚯떛
-> prompt_payload?먯꽌 question/state/domain/catalog 蹂듭썝
-> 吏덈Ц?먯꽌 ?좎쭨/filter/group_by 異붿텧
-> metric required_datasets 諛섏쁺
-> retrieval_jobs ?앹꽦
-> finish/single/multi/followup route 寃곗젙
```

### 珥덈낫???ъ씤??
???몃뱶??v2 flow???듭떖 ?덉쟾?μ튂?낅땲?? LLM??dataset???섎굹留?留먰빐?? domain metric??`required_datasets`媛 ?덉쑝硫??ш린???щ윭 dataset?쇰줈 ?뺤옣?⑸땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_normalize_plan`

???⑥닔??LLM??諛섑솚??raw plan???ㅼ젣 Langflow route? retrieval job?쇰줈 諛붽씀???듭떖 ?⑥닔?낅땲??

### ?⑥닔 input

```json
{
  "raw_plan": {
    "query_mode": "retrieval",
    "datasets": ["production"],
    "filters": {"process": "WB"},
    "needs_pandas": true
  },
  "question": "?댁젣 WB怨듭젙 ?앹궛?ъ꽦瑜좎쓣 mode蹂꾨줈 ?뚮젮以?,
  "state": {"current_data": null},
  "domain": {
    "metrics": {
      "achievement_rate": {
        "aliases": ["?ъ꽦瑜?],
        "required_datasets": ["production", "wip"]
      }
    }
  },
  "table_catalog": {
    "datasets": {
      "production": {"tool_name": "get_production_data", "required_params": ["date"]},
      "wip": {"tool_name": "get_wip_status", "required_params": ["date"]}
    }
  }
}
```

### ?⑥닔 output

```json
{
  "query_mode": "retrieval",
  "route": "multi_retrieval",
  "needed_datasets": ["production", "wip"],
  "filters": {"process": "WB", "process_name": ["W/B1", "W/B2"]},
  "group_by": ["MODE"],
  "needs_pandas": true,
  "retrieval_jobs": [
    {"dataset_key": "production", "tool_name": "get_production_data", "params": {"date": "20260425"}},
    {"dataset_key": "wip", "tool_name": "get_wip_status", "params": {"date": "20260425"}}
  ]
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
configs = _dataset_configs(table_catalog)
matched_metrics = _matched_metrics(question, domain)
```

- `configs`: table catalog?먯꽌 dataset ?ㅼ젙留?爰쇰궦 dict?낅땲??
- `matched_metrics`: 吏덈Ц ?덉뿉 `"?ъ꽦瑜?` 媛숈? metric alias媛 ?덈뒗吏 domain?먯꽌 李얠? 寃곌낵?낅땲??

```python
needed_datasets = _unique_strings([
    *_as_list(raw_plan.get("needed_datasets")),
    *_as_list(raw_plan.get("dataset_keys")),
    *_as_list(raw_plan.get("datasets")),
])
```

LLM??dataset???대뼡 key ?대쫫?쇰줈 諛섑솚?좎? ?꾩쟾??怨좎젙?섍린 ?대졄湲??뚮Ц???щ윭 ?꾨낫 key瑜?紐⑤몢 ?쎌뒿?덈떎.

- `needed_datasets`
- `dataset_keys`
- `datasets`

`*_as_list(...)`??媛믪씠 臾몄옄???섎굹?щ룄 list泥섎읆 ?⑹튂湲??꾪븳 肄붾뱶?낅땲??

```python
if str(raw_plan.get("query_mode") or "").strip() != "followup_transform":
    for metric in matched_metrics.values():
        needed_datasets.extend(str(item) for item in _as_list(metric.get("required_datasets")))
```

?꾩냽 遺꾩꽍???꾨땲???좉퇋 議고쉶?쇰㈃, metric???붽뎄?섎뒗 dataset??媛뺤젣濡?異붽??⑸땲??

?덈? ?ㅼ뼱 LLM??`production`留?怨⑤옄?붾씪??`achievement_rate.required_datasets`媛 `["production", "wip"]`?대㈃ `wip`??異붽??⑸땲??

```python
if not needed_datasets:
    needed_datasets = _dataset_hints(question, table_catalog, domain)
```

LLM??dataset??紐?怨⑤옄???뚮뒗 吏덈Ц ?ㅼ썙?쒖? catalog/domain??蹂닿퀬 fallback?쇰줈 李얠뒿?덈떎.

```python
needed_datasets = [key for key in _unique_strings(needed_datasets) if key in configs]
```

以묐났???쒓굅?섍퀬, table catalog???ㅼ젣濡?議댁옱?섎뒗 dataset留??④퉩?덈떎. 紐⑤Ⅴ??dataset ?대쫫???ㅼ뼱?ㅻ㈃ ?ш린???쒓굅?⑸땲??

```python
raw_filters = raw_plan.get("filters") if isinstance(raw_plan.get("filters"), dict) else {}
filters = {**_filters_from_question(question, domain), **raw_filters}
```

?꾪꽣????異쒖쿂瑜??⑹묩?덈떎.

1. 吏덈Ц?먯꽌 rule 湲곕컲?쇰줈 異붿텧???꾪꽣
2. LLM??JSON?쇰줈 諛섑솚???꾪꽣

?ㅼ뿉 ?덈뒗 `raw_filters`媛 媛숈? key瑜???뼱?????덉뒿?덈떎.

```python
params = _normalize_param_values({
    **_required_params(question, state, reference_date),
    **_drop_empty_params(raw_params)
})
```

?좎쭨 媛숈? ?꾩닔 議고쉶 ?뚮씪誘명꽣瑜?留뚮벊?덈떎. `"?댁젣"` 媛숈? ?쒗쁽? `_required_params`?먯꽌 湲곗???湲곕컲 ?좎쭨濡?諛붾앸땲??

```python
if query_mode not in {"retrieval", "followup_transform", "finish", "clarification"}:
    query_mode = "followup_transform" if _has_current_data(state) and followup_like and not explicit_fresh else "retrieval"
```

LLM??query_mode瑜??댁긽?섍쾶 諛섑솚?덇굅??鍮꾩썙 ??寃쎌슦 fallback???뺥빀?덈떎.

- ?댁쟾 current data媛 ?덇퀬
- 吏덈Ц??`"?대븣"`, `"??寃곌낵"`泥섎읆 ?꾩냽 吏덈Ц泥섎읆 蹂댁씠怨?- ?ъ슜?먭? `"?덈줈 議고쉶"`?쇨퀬 ?섏? ?딆븯?ㅻ㈃

`followup_transform`?쇰줈 遊낅땲?? ?꾨땲硫??좉퇋 議고쉶 `retrieval`?낅땲??

```python
if query_mode == "followup_transform" and not _has_current_data(state):
    query_mode = "retrieval"
```

?꾩냽 吏덈Ц?대씪怨??먮떒?덈뜑?쇰룄 ?ㅼ젣 ?댁쟾 ?곗씠?곌? ?놁쑝硫?遺꾩꽍?????놁뒿?덈떎. 洹몃옒???좉퇋 議고쉶濡??섎룎由쎈땲??

```python
needs_pandas = bool(raw_plan.get("needs_pandas") or raw_plan.get("needs_post_processing") or group_by)
```

LLM??pandas媛 ?꾩슂?섎떎怨??덇굅?? group_by媛 ?덉쑝硫?pandas 遺꾩꽍???꾩슂?섎떎怨?遊낅땲??

```python
if _contains_any(question, ["蹂?, "湲곗?", "top", "?곸쐞", "?섏쐞", "?뺣젹", "鍮꾧탳", "?ъ꽦瑜?, "?ъ꽦??, "鍮꾩쑉", "rate", "ratio", "group", "by"]) or query_mode == "followup_transform" or len(needed_datasets) > 1 or bool(matched_metrics):
    needs_pandas = True
```

吏덈Ц??吏묎퀎/?뺣젹/鍮꾩쑉/metric 怨꾩궛 ?깃꺽?대㈃ pandas媛 ?꾩슂?섎떎怨?媛뺤젣?⑸땲?? ?뱁엳 ?щ윭 dataset???꾩슂??寃쎌슦?먮뒗 嫄곗쓽 ??긽 ?꾩쿂由ш? ?꾩슂?⑸땲??

```python
for dataset_key in needed_datasets:
    job = _build_job(dataset_key, configs.get(dataset_key, {}), params, filters)
    ...
    jobs.append(job)
```

dataset留덈떎 retriever媛 ?ㅽ뻾??job??留뚮벊?덈떎. ??job???ㅼ쓽 Dummy/Oracle Retriever?먯꽌 ?ㅼ젣 議고쉶 ?⑥쐞媛 ?⑸땲??

```python
route = "followup_transform" if query_mode == "followup_transform" else ("multi_retrieval" if len(jobs) > 1 else "single_retrieval")
```

理쒖쥌 route瑜?寃곗젙?⑸땲??

- ?꾩냽 遺꾩꽍?대㈃ `followup_transform`
- 議고쉶 job??2媛??댁긽?대㈃ `multi_retrieval`
- 議고쉶 job??1媛쒕㈃ `single_retrieval`

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_dataset_hints`

???⑥닔??LLM??dataset??紐낇솗??紐?怨⑤옄???? 吏덈Ц 臾몄옣怨?table catalog/domain ?뺣낫瑜?蹂닿퀬 dataset ?꾨낫瑜?李얠뒿?덈떎.

### ?⑥닔 input

```json
{
  "question": "?ㅻ뒛 DA怨듭젙 ?앹궛???뚮젮以?,
  "table_catalog": {
    "datasets": {
      "production": {
        "display_name": "Production",
        "keywords": ["?앹궛", "?앹궛??]
      },
      "wip": {
        "display_name": "WIP",
        "keywords": ["?ш났", "wip"]
      }
    }
  },
  "domain": {
    "metrics": {}
  }
}
```

### ?⑥닔 output

```json
["production"]
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
normalized_question = _normalize_text(question)
found: list[str] = []
```

吏덈Ц??鍮꾧탳?섍린 ?ъ슫 ?뺥깭濡??뺢퇋?뷀븯怨? 李얠? dataset key瑜??댁쓣 list瑜?留뚮벊?덈떎.

```python
for dataset_key, dataset in _dataset_configs(table_catalog).items():
```

table catalog ?덉쓽 dataset???섎굹???뺤씤?⑸땲?? ?덈? ?ㅼ뼱 `production`, `wip`, `target`??李⑤?濡?遊낅땲??

```python
candidates = [
    dataset_key,
    dataset.get("display_name", ""),
    dataset.get("description", ""),
    *DEFAULT_DATASET_KEYWORDS.get(str(dataset_key), []),
    *_as_list(dataset.get("keywords")),
    *_as_list(dataset.get("aliases")),
    *_as_list(dataset.get("question_examples")),
]
```

??dataset???삵븷 ???덈뒗 紐⑤뱺 ?⑥뼱 ?꾨낫瑜?紐⑥쓭?덈떎.

- dataset key: `production`
- ?쒖떆 ?대쫫: `Production`
- ?ㅻ챸 臾몄옣
- 湲곕낯 keyword
- catalog???깅줉??keywords/aliases/question_examples

```python
if any(_normalize_text(item) and _normalize_text(item) in normalized_question for item in candidates):
    found.append(dataset_key)
```

?꾨낫 ?⑥뼱 以??섎굹?쇰룄 吏덈Ц???ㅼ뼱 ?덉쑝硫??대떦 dataset??李얠? 寃껋쑝濡?遊낅땲?? ?덈? ?ㅼ뼱 `"?앹궛??`??吏덈Ц???덉쑝硫?`production`??異붽??⑸땲??

```python
for _metric_key, metric in _matched_metrics(question, domain).items():
    if isinstance(metric, dict):
        found.extend(str(item) for item in _as_list(metric.get("required_datasets")))
```

吏덈Ц??metric??留먰븯怨??덈떎硫? metric???깅줉??`required_datasets`??異붽??⑸땲?? ?앹궛?ъ꽦瑜좎쿂???щ윭 dataset???꾩슂??吏덈Ц???볦튂吏 ?딄린 ?꾪븳 肄붾뱶?낅땲??

```python
return _unique_strings(found)
```

以묐났???쒓굅?섍퀬 dataset 紐⑸줉??諛섑솚?⑸땲??

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_filters_from_question`

???⑥닔??吏덈Ц 臾몄옣?먯꽌 怨듭젙, 怨듭젙 洹몃９, mode 媛숈? filter 議곌굔??rule 湲곕컲?쇰줈 異붿텧?⑸땲??

### ?⑥닔 input

```json
{
  "question": "?댁젣 WB怨듭젙 DDR5 ?앹궛???뚮젮以?,
  "domain": {
    "process_groups": {
      "wb": {
        "aliases": ["WB怨듭젙", "W/B"],
        "processes": ["W/B1", "W/B2"]
      }
    }
  }
}
```

### ?⑥닔 output

```json
{
  "process_name": ["W/B1", "W/B2"],
  "mode": ["DDR5"]
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
filters: Dict[str, Any] = {}
```

異붿텧??filter瑜??댁쓣 鍮?dict瑜?留뚮벊?덈떎.

```python
process_matches = re.findall(r"\b(?:D/A|DA|W/B|WB)\s*-?\s*\d+\b", question, flags=re.IGNORECASE)
```

吏덈Ц?먯꽌 `D/A1`, `DA1`, `W/B2`, `WB2` 媛숈? 援ъ껜 怨듭젙紐낆쓣 ?뺢퇋?앹쑝濡?李얠뒿?덈떎.

```python
for item in process_matches:
    text = re.sub(r"\s+", "", item.upper())
    if text.startswith("DA"):
        text = text.replace("DA", "D/A", 1)
    if text.startswith("WB"):
        text = text.replace("WB", "W/B", 1)
    normalized_processes.append(text)
```

?ъ슜?먭? `DA1`泥섎읆 ?⑤룄 ?대? ?쒖???`D/A1`濡?諛붽퓠?덈떎. `WB1`??`W/B1`濡?諛붽퓠?덈떎.

```python
if normalized_processes:
    filters["process_name"] = _unique_strings(normalized_processes)
elif _contains_any(question, ["DA怨듭젙", "D/A怨듭젙", "DA process"]):
    filters["process_name"] = ["D/A1", "D/A2", "D/A3"]
elif _contains_any(question, ["WB怨듭젙", "W/B怨듭젙", "WB process"]):
    filters["process_name"] = ["W/B1", "W/B2"]
```

援ъ껜 怨듭젙紐낆씠 ?덉쑝硫?洹멸쾬???곌퀬, `DA怨듭젙`, `WB怨듭젙`泥섎읆 洹몃９留?留먰븯硫?洹몃９???랁븳 怨듭젙 紐⑸줉?쇰줈 ?뺤옣?⑸땲??

```python
groups = (domain or {}).get("process_groups") if isinstance((domain or {}).get("process_groups"), dict) else {}
```

MongoDB/domain JSON???깅줉??process group???뺤씤?⑸땲??

```python
if any(_normalize_text(item) and _normalize_text(item) in _normalize_text(question) for item in aliases):
    processes = [str(item) for item in _as_list(group.get("processes")) if str(item).strip()]
    if processes and not filters.get("process_name"):
        filters["process_name"] = processes
```

吏덈Ц??domain???깅줉??alias? 留ㅼ묶?섎㈃ ?대떦 group??processes瑜?filter濡??ｌ뒿?덈떎.

```python
modes = [token for token in ("DDR5", "LPDDR5", "HBM3", "HBM") if token.lower() in question.lower()]
if modes:
    filters["mode"] = _unique_strings(modes)
```

吏덈Ц??`DDR5`, `HBM3` 媛숈? mode ?⑥뼱媛 ?덉쑝硫?`mode` filter濡?異붽??⑸땲??
