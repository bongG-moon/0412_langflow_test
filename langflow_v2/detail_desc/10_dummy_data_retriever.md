# 10. Dummy Data Retriever

## ??以???븷

Oracle DB ?놁씠??flow瑜??뚯뒪?명븷 ???덈룄濡?媛吏??쒖“ ?곗씠?곕? 留뚮뱾??諛섑솚?섎뒗 ?몃뱶?낅땲??

## ???꾩슂?쒓?

?ㅼ젣 DB ?곌껐 ?꾩뿉??Langflow 遺꾧린, pandas 遺꾩꽍, 理쒖쥌 ?듬? ?먮쫫???뺤씤?댁빞 ?⑸땲??
???몃뱶??`production`, `target`, `wip` 媛숈? dataset??dummy row濡?留뚮뱾??以띾땲??

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `intent_plan` | `Intent Route Router.single_retrieval` ?먮뒗 `multi_retrieval` 異쒕젰?낅땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `retrieval_payload` | 議고쉶 寃곌낵泥섎읆 ?앷릿 source_results? current_data瑜??댁뒿?덈떎. |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_base_rows`: ?좎쭨, 怨듭젙, MODE蹂?湲곕낯 row瑜?留뚮벊?덈떎.
- `_apply_filters`: intent plan???덈뒗 怨듭젙/?쒗뭹 filter瑜?row???곸슜?⑸땲??
- `get_production_data`: ?앹궛??dummy ?곗씠?곕? 留뚮벊?덈떎.
- `get_target_data`: 紐⑺몴??dummy ?곗씠?곕? 留뚮벊?덈떎.
- `get_wip_status`: ?ш났??dummy ?곗씠?곕? 留뚮벊?덈떎.
- `_run_job`: retrieval job??`tool_name`??留욌뒗 dummy ?⑥닔瑜??몄텧?⑸땲??
- `retrieve_dummy_data`: ?щ윭 job???쒖꽌?濡??ㅽ뻾?섍퀬 寃곌낵瑜??⑹묩?덈떎.

## 異쒕젰 援ъ“

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {
        "dataset_key": "production",
        "data": [],
        "summary": "total rows ..."
      }
    ],
    "current_data": {}
  }
}
```

## 珥덈낫???ъ씤??
dummy retriever??SQL?대굹 DB ?곌껐???꾪? ?ъ슜?섏? ?딆뒿?덈떎.

?ㅼ젣 ?댁쁺 ?곌껐 ?꾩뿉?????몃뱶濡?癒쇱? flow瑜?寃利앺븯??寃껋씠 ?덉쟾?⑸땲??
`single`怨?`multi` branch瑜?罹붾쾭?ㅼ뿉???곕줈 蹂대젮硫?媛숈? ?뚯씪????踰??щ젮 媛곴컖 ?곌껐?⑸땲??

## ?곌껐

```text
Intent Route Router.single_retrieval
-> Dummy Data Retriever (Single).intent_plan

Intent Route Router.multi_retrieval
-> Dummy Data Retriever (Multi).intent_plan

Dummy Data Retriever.retrieval_payload
-> Retrieval Payload Merger.single_retrieval ?먮뒗 multi_retrieval
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "intent_plan": {
    "route": "single_retrieval",
    "retrieval_jobs": [
      {
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "params": {
          "date": "20260425",
          "process": "DA"
        }
      }
    ],
    "state": {
      "session_id": "abc"
    }
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "retrieval_payload": {
    "success": true,
    "source_results": [
      {
        "success": true,
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "data": [
          {"WORK_DT": "20260425", "OPER_NAME": "D/A1", "MODE": "DDR5", "production": 1200}
        ],
        "summary": "total rows 12, production 33097"
      }
    ],
    "current_data": {
      "datasets": {
        "production": {
          "rows": []
        }
      }
    }
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_normalize_yyyymmdd` | `"2026-04-25"` | `"20260425"` | ?좎쭨 ?낅젰 ?뺤떇???щ씪??dummy row??`WORK_DT`? 鍮꾧탳?????덇쾶 留욎땅?덈떎. |
| `_stable_seed` | `"20260425"` | ?뺤닔 seed | 媛숈? ?좎쭨 吏덈Ц? 媛숈? dummy ?곗씠?곌? ?섏삤寃????뚯뒪???ы쁽?깆쓣 留뚮벊?덈떎. |
| `_apply_filters` | rows, `{"process": "DA"}` | ?꾪꽣留곷맂 rows | LLM??留뚮뱺 filter 議곌굔??dummy ?곗씠?곗뿉???곸슜?⑸땲?? |
| `_base_rows` | params | ?앹궛/怨듭젙/紐⑤뱶 而щ읆???덈뒗 row list | ?ㅼ젣 DB媛 ?놁뼱??Langflow ?먮쫫???뚯뒪?명븷 ???덈뒗 湲곕낯 row瑜?留뚮벊?덈떎. |
| `_result` | tool ?대쫫, rows, summary | source result dict | 紐⑤뱺 dummy tool ?⑥닔媛 媛숈? output schema瑜?諛섑솚?섍쾶 ?⑸땲?? |
| `get_production_data` ??| `{"date": "20260425"}` | dataset蹂?source result | ?ㅼ젣 tool泥섎읆 蹂댁씠??dummy 議고쉶 ?⑥닔?낅땲?? |
| `_run_job` | retrieval job | source result | `tool_name`??留욌뒗 dummy ?⑥닔瑜?李얠븘 ?ㅽ뻾?⑸땲?? |
| `retrieve_dummy_data` | intent plan | retrieval payload | ?щ윭 retrieval job???ㅽ뻾??`source_results`? `current_data`瑜?留뚮벊?덈떎. |
| `build_payload` | Langflow input | `Data(data=retrieval_payload)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
Intent Route Router?먯꽌 active branch ?섏떊
-> retrieval_jobs 諛섎났
-> job.tool_name??留욌뒗 get_xxx_data ?⑥닔 ?ㅽ뻾
-> source_results 諛곗뿴 ?앹꽦
-> ?꾩냽 吏덈Ц??current_data ?앹꽦
-> Retrieval Payload Merger濡??꾨떖
```

### 珥덈낫???ъ씤??
dummy ?⑥닔?ㅼ? ?ㅼ젣 DB 議고쉶泥섎읆 ?앷꼈吏留?DB???묒냽?섏? ?딆뒿?덈떎. Langflow ???곌껐, 遺꾧린, pandas, 理쒖쥌 ?듬???癒쇱? ?뚯뒪?명븯湲??꾪븳 ?덉쟾??媛吏??곗씠?곗엯?덈떎.

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_apply_filters`

???⑥닔??dummy row 紐⑸줉?먯꽌 ?ъ슜?먭? 吏덈Ц??議곌굔??留욌뒗 row留??④린???⑥닔?낅땲??

### ?⑥닔 ?먮Ц

```python
def _apply_filters(rows: list[Dict[str, Any]], params: Dict[str, Any]) -> list[Dict[str, Any]]:
    filtered = []
    for row in rows:
        if not _matches(row.get("OPER_NAME"), params.get("process_name") or params.get("process")):
            continue
        if not _matches(row.get("OPER_NUM"), params.get("oper_num")):
            continue
        if not _matches(row.get("LINE"), params.get("line_name") or params.get("line")):
            continue
        if not _matches(row.get("MODE"), params.get("mode")):
            continue
        if not _matches(row.get("DEN"), params.get("den")):
            continue
        if not _matches(row.get("TECH"), params.get("tech")):
            continue
        if not _matches(row.get("MCP_NO"), params.get("mcp_no")):
            continue
        product_name = params.get("product_name") or params.get("product")
        if product_name and not any(_matches(row.get(column), product_name) for column in ("MODE", "DEN", "TECH", "MCP_NO", "PKG_TYPE1", "PKG_TYPE2")):
            continue
        filtered.append(row)
    return filtered
```

### ?⑥닔 input

`rows`??議고쉶???곗씠????紐⑸줉?낅땲?? 媛??됱? dict?낅땲??

```json
[
  {
    "OPER_NAME": "D/A1",
    "OPER_NUM": "DA10",
    "LINE": "DA-L1",
    "MODE": "DDR5",
    "DEN": "512G",
    "TECH": "V7",
    "MCP_NO": "MCP-001",
    "PKG_TYPE1": "PKG-A",
    "PKG_TYPE2": "PKG-B"
  },
  {
    "OPER_NAME": "W/B1",
    "OPER_NUM": "WB10",
    "LINE": "WB-L1",
    "MODE": "HBM3",
    "DEN": "1024G",
    "TECH": "V9",
    "MCP_NO": "MCP-009",
    "PKG_TYPE1": "PKG-X",
    "PKG_TYPE2": "PKG-Y"
  }
]
```

`params`???ъ슜?먯쓽 吏덈Ц?먯꽌 異붿텧???꾪꽣 議곌굔?낅땲??

```json
{
  "process": "D/A1",
  "mode": "DDR5",
  "den": "512G"
}
```

### ?⑥닔 output

議곌굔??留욌뒗 row留??④릿 list瑜?諛섑솚?⑸땲??

```json
[
  {
    "OPER_NAME": "D/A1",
    "OPER_NUM": "DA10",
    "LINE": "DA-L1",
    "MODE": "DDR5",
    "DEN": "512G",
    "TECH": "V7",
    "MCP_NO": "MCP-001",
    "PKG_TYPE1": "PKG-A",
    "PKG_TYPE2": "PKG-B"
  }
]
```

### 肄붾뱶 釉붾줉蹂??댁꽍

```python
filtered = []
```

議곌굔???듦낵??row瑜??댁쓣 鍮?list瑜?留뚮벊?덈떎. 泥섏쓬?먮뒗 ?꾨Т row???좏깮?섏? ?딆? ?곹깭?낅땲??

```python
for row in rows:
```

?낅젰?쇰줈 ?ㅼ뼱??紐⑤뱺 row瑜??섎굹??寃?ы빀?덈떎. row媛 12媛쒕씪硫???諛섎났臾몄? 12踰??ㅽ뻾?⑸땲??

```python
if not _matches(row.get("OPER_NAME"), params.get("process_name") or params.get("process")):
    continue
```

?꾩옱 row??怨듭젙紐?`OPER_NAME`???ъ슜?먭? ?붿껌??怨듭젙 議곌굔怨?留욌뒗吏 ?뺤씤?⑸땲??

- `row.get("OPER_NAME")`: ?꾩옱 row??怨듭젙紐낆엯?덈떎. ?? `"D/A1"`
- `params.get("process_name") or params.get("process")`: ?ъ슜?먭? 吏?뺥븳 怨듭젙 議곌굔?낅땲?? ?? `"D/A1"`
- `_matches(...)`: 議곌굔??鍮꾩뼱 ?덉쑝硫??듦낵?쒗궎怨? 議곌굔???덉쑝硫?媛믪씠 留욌뒗吏 鍮꾧탳?⑸땲??
- `not _matches(...)`: 議곌굔怨?留욎? ?딅뒗?ㅻ뒗 ?살엯?덈떎.
- `continue`: ??row??踰꾨━怨??ㅼ쓬 row 寃?щ줈 ?섏뼱媛묐땲??

?덈? ?ㅼ뼱 row媛 `W/B1`?몃뜲 ?ъ슜?먭? `D/A1`??臾쇱뿀?ㅻ㈃ ?ш린??嫄몃윭吏묐땲??

```python
if not _matches(row.get("OPER_NUM"), params.get("oper_num")):
    continue
```

怨듭젙 踰덊샇 議곌굔???뺤씤?⑸땲?? ?덈? ?ㅼ뼱 `oper_num`??`"DA10"`?대㈃ `OPER_NUM`??`"DA10"`??row留??④퉩?덈떎.

```python
if not _matches(row.get("LINE"), params.get("line_name") or params.get("line")):
    continue
```

?쇱씤 議곌굔???뺤씤?⑸땲??

- `line_name`怨?`line` ??以??섎굹濡??ㅼ뼱?????덉뼱??`or`瑜??ъ슜?⑸땲??
- `params.get("line_name")`???덉쑝硫?洹멸쾬???곌퀬, ?놁쑝硫?`params.get("line")`???곷땲??

```python
if not _matches(row.get("MODE"), params.get("mode")):
    continue
if not _matches(row.get("DEN"), params.get("den")):
    continue
if not _matches(row.get("TECH"), params.get("tech")):
    continue
if not _matches(row.get("MCP_NO"), params.get("mcp_no")):
    continue
```

?쒗뭹 ?띿꽦 議곌굔??李⑤?濡??뺤씤?⑸땲??

- `MODE`: DDR5, LPDDR5, HBM3 媛숈? mode
- `DEN`: 512G, 256G 媛숈? density
- `TECH`: 湲곗닠 ?몃?
- `MCP_NO`: ?쒗뭹 踰덊샇

媛?議곌굔 以??섎굹?쇰룄 留욎? ?딆쑝硫?`continue`濡??꾩옱 row瑜?踰꾨┰?덈떎.

```python
product_name = params.get("product_name") or params.get("product")
```

?ъ슜?먭? ?쒗뭹紐낆쓣 `product_name` ?먮뒗 `product`濡?以????덉쑝誘濡???以??덈뒗 媛믪쓣 ?좏깮?⑸땲??

```python
if product_name and not any(_matches(row.get(column), product_name) for column in ("MODE", "DEN", "TECH", "MCP_NO", "PKG_TYPE1", "PKG_TYPE2")):
    continue
```

?쒗뭹紐?議곌굔? ?섎굹??而щ읆留?蹂대뒗 寃껋씠 ?꾨땲???щ윭 ?쒗뭹 愿??而щ읆???④퍡 遊낅땲??

?덈? ?ㅼ뼱 ?ъ슜?먭? `"HBM3"`?쇨퀬 臾쇱뿀??????媛믪? `MODE`???덉쓣 ?섎룄 ?덇퀬, ?ㅻⅨ ?쒗뭹 而щ읆???덉쓣 ?섎룄 ?덉뒿?덈떎. 洹몃옒???ㅼ쓬 而щ읆?ㅼ쓣 紐⑤몢 寃?ы빀?덈떎.

```text
MODE, DEN, TECH, MCP_NO, PKG_TYPE1, PKG_TYPE2
```

`any(...)`????以??섎굹?쇰룄 留욎쑝硫?true媛 ?⑸땲??

- ?섎굹?쇰룄 留욎쑝硫?row瑜??듦낵?쒗궢?덈떎.
- ?섎굹????留욎쑝硫?`continue`濡?踰꾨┰?덈떎.

```python
filtered.append(row)
```

?ш린源뚯? ?붾떎??寃껋? ?꾩쓽 紐⑤뱺 議곌굔???듦낵?덈떎???살엯?덈떎. ?곕씪??理쒖쥌 寃곌낵 list???꾩옱 row瑜?異붽??⑸땲??

```python
return filtered
```

寃?щ? 紐⑤몢 ?앸궦 ??議곌굔??留욌뒗 row 紐⑸줉??諛섑솚?⑸땲??

### ?ㅼ젣 ?ㅽ뻾 ?덉떆

?낅젰:

```json
{
  "rows": [
    {"OPER_NAME": "D/A1", "MODE": "DDR5", "DEN": "512G"},
    {"OPER_NAME": "D/A1", "MODE": "LPDDR5", "DEN": "128G"},
    {"OPER_NAME": "W/B1", "MODE": "DDR5", "DEN": "512G"}
  ],
  "params": {
    "process": "D/A1",
    "mode": "DDR5"
  }
}
```

泥섎━ 怨쇱젙:

| row | 怨듭젙 議곌굔 | mode 議곌굔 | 寃곌낵 |
| --- | --- | --- | --- |
| `D/A1, DDR5` | ?듦낵 | ?듦낵 | ?④? |
| `D/A1, LPDDR5` | ?듦낵 | ?ㅽ뙣 | 踰꾨┝ |
| `W/B1, DDR5` | ?ㅽ뙣 | ?뺤씤???꾩슂 ?놁쓬 | 踰꾨┝ |

異쒕젰:

```json
[
  {"OPER_NAME": "D/A1", "MODE": "DDR5", "DEN": "512G"}
]
```

### ???대젃寃??묒꽦?덈굹?

???⑥닔??"?꾪꽣 議곌굔???덉쑝硫??곸슜?섍퀬, ?놁쑝硫??듦낵"?쒗궎??援ъ“?낅땲??

?덈? ?ㅼ뼱 ?ъ슜?먭? mode瑜?留먰븯吏 ?딆븯?ㅻ㈃ `params.get("mode")`??鍮꾩뼱 ?덉뒿?덈떎. ?대븣 `_matches(row.get("MODE"), None)`? ?듦낵濡?泥섎━?⑸땲?? 洹몃옒???ъ슜?먭? 留먰븳 議곌굔留??곸슜?섍퀬, 留먰븯吏 ?딆? 議곌굔?쇰줈 ?곗씠?곕? ?섎せ 以꾩씠吏 ?딆뒿?덈떎.

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `get_production_data`

???⑥닔??dummy ?앹궛 ?곗씠?곕? 留뚮뱶??tool ?⑥닔?낅땲??

### ?⑥닔 input

```json
{
  "date": "20260425",
  "process": "D/A1",
  "mode": "DDR5"
}
```

### ?⑥닔 output

```json
{
  "success": true,
  "tool_name": "get_production_data",
  "dataset_key": "production",
  "data": [
    {"WORK_DT": "20260425", "OPER_NAME": "D/A1", "MODE": "DDR5", "production": 2940}
  ],
  "summary": "total rows 1, production 2,940"
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
rows = _base_rows(params, 100)
```

湲곕낯 怨듭젙/?쒗뭹 議고빀 row瑜?留뚮뱾怨? `params` 議곌굔?쇰줈 ?꾪꽣留곹빀?덈떎. `100`? dummy ?쒖닔 seed瑜?dataset蹂꾨줈 ?ㅻⅤ寃?留뚮뱾湲??꾪븳 offset?낅땲??

```python
for row in rows:
```

?꾪꽣留곷맂 row 媛곴컖???앹궛??媛믪쓣 ?ｊ린 ?꾪빐 諛섎났?⑸땲??

```python
base = 3300 if row.get("family") == "DA" else 2200
row["production"] = int(base * random.uniform(0.6, 1.2))
```

DA 怨꾩뿴? 湲곕낯 ?앹궛?됱쓣 3300 洹쇱쿂濡? 洹??몃뒗 2200 洹쇱쿂濡??≪뒿?덈떎. `random.uniform(0.6, 1.2)`??湲곕낯媛믪쓽 60%-120% 踰붿쐞?먯꽌 媛믪쓣 ?붾뱾??dummy ?곗씠?곕? ?먯뿰?ㅻ읇寃?留뚮벊?덈떎.

```python
if row.get("OPER_NAME") == "D/A3" and row.get("MODE") == "DDR5":
    row["production"] = 2940 if row.get("DEN") == "512G" else 2680
```

?뱀젙 ?뚯뒪??耳?댁뒪媛 ??긽 媛숈? 寃곌낵瑜??삳룄濡??쇰? row??怨좎젙媛믪쓣 ?ｌ뒿?덈떎. ?대젃寃??섎㈃ ?뚭? ?뚯뒪?몃굹 playground ?뺤씤???ъ썙吏묐땲??

```python
total = sum(int(row["production"]) for row in rows)
```

?꾩껜 ?앹궛???⑷퀎瑜?怨꾩궛?⑸땲??

```python
return _result("get_production_data", "production", rows, f"total rows {len(rows)}, production {_quantity(total)}", params)
```

?ㅼ쓬 ?몃뱶媛 ?쎄린 ?ъ슫 ?쒖? source result ?뺤떇?쇰줈 媛먯떥??諛섑솚?⑸땲??

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_run_job`

???⑥닔??retrieval job ?섎굹瑜??ㅼ젣 dummy tool ?⑥닔 ?섎굹濡??ㅽ뻾?⑸땲??

### ?⑥닔 input

```json
{
  "dataset_key": "production",
  "tool_name": "get_production_data",
  "params": {"date": "20260425"},
  "filters": {"process": "D/A1"}
}
```

### ?⑥닔 output

```json
{
  "success": true,
  "dataset_key": "production",
  "tool_name": "get_production_data",
  "data": []
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
tool_name = str(job.get("tool_name") or job.get("dataset_key") or "")
tool = TOOL_REGISTRY.get(tool_name) or TOOL_REGISTRY.get(str(job.get("dataset_key") or ""))
```

job?먯꽌 tool ?대쫫??爰쇰궦 ?? `TOOL_REGISTRY`?먯꽌 ?ㅼ젣 Python ?⑥닔瑜?李얠뒿?덈떎. tool name???놁쑝硫?dataset key濡쒕룄 ??踰???李얠뒿?덈떎.

```python
if tool is None:
    return _error_result(job, f"Unsupported dummy retrieval tool: {tool_name}", "unsupported_tool")
```

?깅줉?섏? ?딆? tool?대㈃ ?ㅽ뙣 payload瑜?諛섑솚?⑸땲?? ?덉쇅瑜??곕쑉由ш린蹂대떎 `source_results` ?덉뿉 ?ㅽ뙣 寃곌낵瑜??댁븘 flow媛 怨꾩냽 ?ㅻ챸?????덇쾶 ?⑸땲??

```python
params = deepcopy(job.get("params", {}))
params.update({key: value for key, value in (job.get("filters") or {}).items() if value not in (None, "", [])})
```

議고쉶 ?뚮씪誘명꽣? filter瑜??⑹묩?덈떎. `deepcopy`???먮옒 job???섏젙?섏? ?딄린 ?꾪븳 蹂듭궗?낅땲??

```python
result = tool(params)
```

?쒕뵒???ㅼ젣 dummy ?⑥닔媛 ?ㅽ뻾?⑸땲?? ?덈? ?ㅼ뼱 `get_production_data(params)`媛 ?몄텧?⑸땲??

```python
result["dataset_key"] = job.get("dataset_key", result.get("dataset_key"))
result["dataset_label"] = job.get("dataset_label", result.get("dataset_label", result.get("dataset_key")))
```

寃곌낵??dataset key/label???뺤떎??梨꾩썎?덈떎. ???몃뱶媛 ?대뼡 dataset 寃곌낵?몄? ?뚯븘???섍린 ?뚮Ц?낅땲??

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `retrieve_dummy_data`

???⑥닔??active branch payload ?꾩껜瑜?諛쏆븘 ?щ윭 retrieval job???ㅽ뻾?⑸땲??

### ?듭떖 肄붾뱶 ?댁꽍

```python
payload = _payload_from_value(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
state = payload.get("state") if isinstance(payload.get("state"), dict) else {}
```

router?먯꽌 ?섏뼱??payload?먯꽌 intent plan怨?state瑜?爰쇰깄?덈떎.

```python
if payload.get("skipped"):
    return {"retrieval_payload": {"skipped": True, ...}}
```

?좏깮?섏? ?딆? branch?쇰㈃ ?ㅼ젣 議고쉶瑜??섏? ?딄퀬 skipped payload瑜?諛섑솚?⑸땲??

```python
jobs = plan.get("retrieval_jobs") if isinstance(plan.get("retrieval_jobs"), list) else []
source_results = [_run_job(job) for job in jobs if isinstance(job, dict)]
```

retrieval job 紐⑸줉???섎굹??`_run_job`?쇰줈 ?ㅽ뻾?⑸땲?? list comprehension? 諛섎났臾몄쓣 吏㏐쾶 ??Python 臾몃쾿?낅땲??

```python
return {
    "retrieval_payload": {
        "route": plan.get("route", "single_retrieval"),
        "source_results": source_results,
        "current_datasets": _build_current_datasets(source_results),
        "source_snapshots": _build_source_snapshots(source_results, jobs),
        ...
    }
}
```

?щ윭 tool 寃곌낵瑜?`source_results`濡?臾띔퀬, ?꾩냽 吏덈Ц?먯꽌 ??`current_datasets`? `source_snapshots`???④퍡 留뚮벊?덈떎.
