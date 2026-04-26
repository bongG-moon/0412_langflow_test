# 20. Pandas Analysis Executor

## ??以???븷

`analysis_plan_payload` ?덉쓽 pandas 肄붾뱶瑜??ㅽ뻾?댁꽌 理쒖쥌 遺꾩꽍 row瑜?留뚮뱶???몃뱶?낅땲??

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `analysis_plan_payload` | `Normalize Pandas Plan` 異쒕젰?낅땲?? |
| `retrieval_payload` | ?ㅽ뿕??override?낅땲?? 蹂댄넻 ?곌껐?섏? ?딆븘???⑸땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `analysis_result` | pandas 遺꾩꽍 寃곌낵?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_merge_sources`: ?щ윭 source result瑜?pandas DataFrame?쇰줈 留뚮뱾 row list濡??⑹묩?덈떎.
- `_apply_filters`: intent filter瑜?DataFrame???곸슜?⑸땲??
- `_validate_code`: ?ㅽ뻾 ?꾩뿉 肄붾뱶媛 ?덈Т ?꾪뿕?섏? ?딆?吏 媛꾨떒???뺤씤?⑸땲??
- `_execute_code`: ?쒗븳???섍꼍?먯꽌 pandas 肄붾뱶瑜??ㅽ뻾?⑸땲??
- `execute_pandas_analysis`: ?꾩껜 ?ㅽ뻾 怨쇱젙??愿由ы빀?덈떎.

## ?ㅽ뻾 寃곌낵 援ъ“

```json
{
  "analysis_result": {
    "success": true,
    "data": [],
    "summary": "遺꾩꽍 寃곌낵 ...",
    "intent_plan": {}
  }
}
```

## 珥덈낫???ъ씤??
???몃뱶???ㅼ젣濡?肄붾뱶瑜??ㅽ뻾?섎?濡?媛??議곗떖?댁빞 ?섎뒗 遺遺꾩엯?덈떎.

洹몃옒???ㅽ뻾 ?섍꼍??`pd`, `df`, `source_frames` 媛숈? ?꾩슂??媛믩쭔 ?ｊ퀬, ?꾪뿕??built-in ?ъ슜? ?쒗븳?⑸땲??

## ?곌껐

```text
Normalize Pandas Plan.analysis_plan_payload
-> Pandas Analysis Executor.analysis_plan_payload

Pandas Analysis Executor.analysis_result
-> Analysis Result Merger.pandas_result
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "analysis_plan_payload": {
    "analysis_plan": {
      "code": "result_df = df.groupby('MODE', as_index=False)['production'].sum()"
    },
    "rows": [
      {"MODE": "A", "production": 100},
      {"MODE": "A", "production": 50},
      {"MODE": "B", "production": 30}
    ],
    "columns": ["MODE", "production"]
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "analysis_result": {
    "success": true,
    "result_type": "pandas_analysis",
    "final_rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "final_columns": ["MODE", "production"],
    "row_count": 2,
    "errors": []
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_analysis_plan_payload` | `{"analysis_plan_payload": {...}}` | plan payload | ???몃뱶 異쒕젰?먯꽌 ?ㅼ젣 ?ㅽ뻾 怨꾪쉷??爰쇰깄?덈떎. |
| `_retrieval_payload` | optional retrieval payload | retrieval dict | plan??rows媛 遺議깊븯硫??먮옒 議고쉶 寃곌낵?먯꽌 rows瑜?蹂댁땐?????덇쾶 ?⑸땲?? |
| `_merge_sources` | ?щ윭 source_results | ?듯빀 rows/columns | ?щ윭 dataset??pandas DataFrame ?섎굹濡?留뚮뱾湲??꾪븳 以鍮꾩엯?덈떎. |
| `_apply_filters` | DataFrame, filters | ?꾪꽣 ?곸슜 DataFrame | intent filter媛 ?⑥븘 ?덉쑝硫??ㅽ뻾 ?꾩뿉 ?곗씠?곕? ??踰???嫄곕쫭?덈떎. |
| `_validate_code` | pandas code | `(true, "")` ?먮뒗 `(false, reason)` | ?꾪뿕?섍굅???덉슜?섏? ?딅뒗 肄붾뱶瑜??ㅽ뻾?섏? ?딅룄濡??ъ쟾 寃?ы빀?덈떎. |
| `_execute_code` | code, rows, plan | final rows/result | ?쒗븳??namespace?먯꽌 pandas code瑜??ㅽ뻾?섍퀬 `result_df`瑜?rows濡?諛붽퓠?덈떎. |
| `execute_pandas_analysis` | analysis plan | analysis result | code ?ㅽ뻾, ?ㅻ쪟 泥섎━, 寃곌낵 schema ?앹꽦???대떦?⑸땲?? |
| `build_result` | Langflow input | `Data(data=analysis_result)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
analysis_plan_payload ?낅젰
-> rows瑜?pandas DataFrame?쇰줈 蹂??-> code ?덉쟾??寃??-> ?쒗븳???ㅽ뻾 ?섍꼍?먯꽌 code ?ㅽ뻾
-> result_df瑜?list[dict] final_rows濡?蹂??-> 理쒖쥌 analysis_result 諛섑솚
```

### 珥덈낫???ъ씤??
LLM? 怨꾩궛 寃곌낵瑜?吏곸젒 留뚮뱾吏 ?딆뒿?덈떎. LLM? pandas code 怨꾪쉷留?留뚮뱾怨? ?ㅼ젣 ?レ옄 怨꾩궛? ???몃뱶?먯꽌 pandas媛 ?섑뻾?⑸땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_validate_code`

???⑥닔??LLM??留뚮뱺 pandas code瑜??ㅽ뻾?섍린 ?꾩뿉 ?꾪뿕?섍굅???섎せ??肄붾뱶?몄? 寃?ы빀?덈떎.

### ?⑥닔 input

```python
"result = df.groupby('MODE', as_index=False)['production'].sum()"
```

### ?⑥닔 output

```json
[true, ""]
```

臾몄젣媛 ?덉쑝硫?

```json
[false, "Forbidden Python node: Import"]
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
tree = ast.parse(code)
```

臾몄옄??code瑜?Python AST濡?諛붽퓠?덈떎. AST??肄붾뱶瑜??ㅽ뻾?섏? ?딄퀬 援ъ“留?遺꾩꽍?????덇쾶 ?댁＜???뺥깭?낅땲??

```python
except SyntaxError as exc:
    return False, f"Generated pandas code syntax error: {exc}"
```

臾몃쾿 ?ㅻ쪟媛 ?덉쑝硫??ㅽ뻾?섏? ?딄퀬 ?ㅽ뙣瑜?諛섑솚?⑸땲??

```python
for node in ast.walk(tree):
```

肄붾뱶 ?덉쓽 紐⑤뱺 臾몃쾿 ?붿냼瑜??섎굹??寃?ы빀?덈떎.

```python
if isinstance(node, (ast.Import, ast.ImportFrom, ast.With, ast.Try, ast.While, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda, ast.Delete)):
    return False, f"Forbidden Python node: {type(node).__name__}"
```

LLM??留뚮뱺 肄붾뱶媛 import, class, while 媛숈? ?꾪뿕?섍굅???꾩슂 ?녿뒗 臾몃쾿???곕㈃ 李⑤떒?⑸땲?? pandas 吏묎퀎?먮뒗 ?대윴 臾몃쾿???꾩슂?섏? ?딄린 ?뚮Ц?낅땲??

```python
if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
    return False, f"Forbidden Python name: {node.id}"
```

`open`, `exec`, `eval` 媛숈? ?꾪뿕???대쫫???곗? 紐삵븯寃?留됱뒿?덈떎.

```python
if isinstance(node, ast.Assign):
    has_result = has_result or any(isinstance(target, ast.Name) and target.id == "result" for target in node.targets)
```

??executor??理쒖쥌 寃곌낵瑜?`result` 蹂?섏뿉???쎌뒿?덈떎. 洹몃옒??肄붾뱶媛 `result = ...`瑜?諛섎뱶???ы븿?섎뒗吏 寃?ы빀?덈떎.

```python
return (True, "") if has_result else (False, "Generated pandas code must assign result.")
```

`result`瑜?留뚮뱾硫??듦낵, 留뚮뱾吏 ?딆쑝硫??ㅽ뙣?낅땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_execute_code`

???⑥닔??寃利앸맂 pandas code瑜??ㅼ젣濡??ㅽ뻾?⑸땲??

### ?⑥닔 input

```json
{
  "code": "result = df.groupby('MODE', as_index=False)['production'].sum()",
  "rows": [
    {"MODE": "A", "production": 100},
    {"MODE": "A", "production": 50},
    {"MODE": "B", "production": 30}
  ],
  "plan": {
    "filters": {}
  }
}
```

### ?⑥닔 output

```json
{
  "success": true,
  "data": [
    {"MODE": "A", "production": 150},
    {"MODE": "B", "production": 30}
  ],
  "filter_notes": []
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
frame = pd.DataFrame(rows or [])
```

list of dict瑜?pandas DataFrame?쇰줈 諛붽퓠?덈떎. pandas 怨꾩궛? DataFrame??湲곗??쇰줈 ?⑸땲??

```python
frame, filter_notes = _apply_filters(frame, plan.get("filters", {}) if isinstance(plan.get("filters"), dict) else {})
```

plan??filter媛 ?덉쑝硫?DataFrame??癒쇱? ?곸슜?⑸땲?? `filter_notes`?먮뒗 紐?嫄댁뿉??紐?嫄댁쑝濡?以꾩뿀?붿? 湲곕줉?⑸땲??

```python
ok, error = _validate_code(code)
if not ok:
    return {"success": False, "error_message": error, "data": [], "filter_notes": filter_notes}
```

肄붾뱶 寃利앹씠 ?ㅽ뙣?섎㈃ ?ㅽ뻾?섏? ?딄퀬 ?ㅻ쪟瑜?諛섑솚?⑸땲??

```python
local_vars = {"df": frame.copy(), "pd": pd, "result": None}
```

LLM code媛 ?ъ슜?????덈뒗 蹂?섎뱾??以鍮꾪빀?덈떎.

- `df`: ?낅젰 ?곗씠??DataFrame
- `pd`: pandas module
- `result`: 理쒖쥌 寃곌낵瑜??댁븘???섎뒗 蹂??
```python
exec(code, {"__builtins__": SAFE_BUILTINS}, local_vars)
```

?ㅼ젣 肄붾뱶 ?ㅽ뻾 遺遺꾩엯?덈떎. `SAFE_BUILTINS`留??덉슜?댁꽌 ?꾨Т Python 湲곕뒫?대굹 ?곗? 紐삵븯寃??쒗븳?⑸땲??

```python
result = local_vars.get("result")
```

?ㅽ뻾???앸궃 ??LLM code媛 留뚮뱺 `result` 蹂?섎? 爰쇰깄?덈떎.

```python
if isinstance(result, pd.Series):
    result = result.to_frame().reset_index()
```

寃곌낵媛 Series?대㈃ DataFrame?쇰줈 諛붽퓠?덈떎. ???몃뱶??row list瑜?湲곕??섍린 ?뚮Ц?낅땲??

```python
if not isinstance(result, pd.DataFrame):
    return {"success": False, "error_message": "Pandas code result is not a DataFrame.", "data": [], "filter_notes": filter_notes}
```

理쒖쥌 寃곌낵媛 DataFrame???꾨땲硫??ㅽ뙣 泥섎━?⑸땲??

```python
result = result.where(pd.notnull(result), None)
return {"success": True, "data": result.to_dict(orient="records"), "filter_notes": filter_notes}
```

NaN 媛믪쓣 JSON?먯꽌 ?ㅻ（湲??ъ슫 `None`?쇰줈 諛붽씀怨? DataFrame??`list[dict]`濡?諛붽퓭 諛섑솚?⑸땲??

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `execute_pandas_analysis`

???⑥닔??pandas 遺꾩꽍 ?몃뱶??理쒖긽???ㅽ뻾 ?⑥닔?낅땲?? plan??爰쇰궡怨? ?곗씠?곌? ?덈뒗吏 ?뺤씤?섍퀬, 肄붾뱶瑜??ㅽ뻾?섍퀬, 理쒖쥌 analysis result瑜?留뚮벊?덈떎.

### ?⑥닔 input

```json
{
  "analysis_plan_payload_value": {
    "analysis_plan_payload": {
      "analysis_plan": {
        "code": "result = df.groupby('MODE', as_index=False)['production'].sum()",
        "source": "llm"
      },
      "rows": [
        {"MODE": "A", "production": 100},
        {"MODE": "A", "production": 50}
      ],
      "columns": ["MODE", "production"]
    }
  }
}
```

### ?⑥닔 output

```json
{
  "analysis_result": {
    "success": true,
    "tool_name": "analyze_current_data",
    "data": [
      {"MODE": "A", "production": 150}
    ],
    "summary": "data analysis complete: 1 rows",
    "analysis_logic": "llm",
    "generated_code": "result = df.groupby('MODE', as_index=False)['production'].sum()"
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
payload = _analysis_plan_payload(analysis_plan_payload_value)
```

???몃뱶?먯꽌 ??媛믪쓣 ?쒖? analysis plan payload濡?爰쇰깄?덈떎.

```python
retrieval = payload.get("retrieval_payload") if isinstance(payload.get("retrieval_payload"), dict) else {}
if retrieval_payload_value is not None:
    override = _retrieval_payload(retrieval_payload_value)
    if override:
        retrieval = override
```

湲곕낯?곸쑝濡?plan payload ?덉쓽 retrieval ?뺣낫瑜??곗?留? ?ㅽ뿕?⑹쑝濡?蹂꾨룄 retrieval payload媛 ?곌껐?섎㈃ 洹멸쾬?쇰줈 ??뼱?????덉뒿?덈떎.

```python
if payload.get("skipped") or retrieval.get("skipped"):
    result = {"skipped": True, ...}
    return {"analysis_result": result}
```

?좏깮?섏? ?딆? branch?쇰㈃ pandas瑜??ㅽ뻾?섏? ?딄퀬 skipped result瑜?諛섑솚?⑸땲??

```python
table = payload.get("table") if isinstance(payload.get("table"), dict) and payload.get("table") else _merge_sources(source_results)
```

遺꾩꽍??table??以鍮꾪빀?덈떎. ?대? table???덉쑝硫?洹멸쾬???곌퀬, ?놁쑝硫?source_results瑜?蹂묓빀?⑸땲??

```python
if not table.get("success") or not rows:
    result = {"success": False, "analysis_logic": "no_data", ...}
    return {"analysis_result": result}
```

遺꾩꽍???곗씠?곌? ?놁쑝硫?pandas ?ㅽ뻾???섏? ?딆뒿?덈떎.

```python
code = str(analysis_plan.get("code") or "").strip()
if not code:
    code = _fallback_code(plan, [str(column) for column in columns])
```

LLM??code瑜?留뚮뱾吏 紐삵뻽?쇰㈃ fallback code瑜??앹꽦?⑸땲??

```python
executed = _execute_code(code, rows, plan)
```

?ㅼ젣 pandas ?ㅽ뻾? `_execute_code`??留↔퉩?덈떎.

```python
if not executed.get("success") and analysis_logic == "llm":
    fallback = _fallback_code(plan, [str(column) for column in columns])
    executed = _execute_code(fallback, rows, plan)
```

LLM code媛 ?ㅽ뙣?섎㈃ fallback code濡???踰????쒕룄?⑸땲??

```python
result_rows = executed.get("data", []) if executed.get("success") else []
```

?ㅽ뻾 ?깃났 ??理쒖쥌 row瑜?爰쇰깄?덈떎. ?ㅽ뙣?섎㈃ 鍮?list?낅땲??

```python
result = {
    "success": bool(executed.get("success")),
    "data": _json_safe(result_rows),
    "summary": ...,
    "generated_code": code,
    "source_results": source_results,
    "intent_plan": plan,
    "state": state,
}
```

理쒖쥌 ?듬? builder媛 ?쎌쓣 ?쒖? analysis result瑜?留뚮벊?덈떎. ?ш린?먮뒗 怨꾩궛 寃곌낵肉??꾨땲???ъ슜??肄붾뱶, ?먮낯 source, intent plan, state??媛숈씠 ?ㅼ뼱媛묐땲??
