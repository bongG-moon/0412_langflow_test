# 19. Normalize Pandas Plan

## ??以???븷

LLM??留뚮뱺 pandas 遺꾩꽍 怨꾪쉷???뚯떛?섍퀬, ?ㅽ뻾 媛?ν븳 `analysis_plan_payload`濡??뺣━?섎뒗 ?몃뱶?낅땲??

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `llm_result` | `LLM JSON Caller (Pandas)` 異쒕젰?낅땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `analysis_plan_payload` | pandas 肄붾뱶, ?낅젰 row, 而щ읆, intent plan???댁? ?ㅽ뻾 怨꾪쉷?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_extract_json_object`: LLM ?묐떟?먯꽌 JSON??李얠뒿?덈떎.
- `_fallback_code`: LLM ?묐떟???녾굅??源⑥죱????湲곕낯 pandas 肄붾뱶瑜?留뚮벊?덈떎.
- `normalize_pandas_plan`: 肄붾뱶, ?ㅻ챸, warnings, retrieval payload瑜??뺣━?⑸땲??

## LLM??湲곕??섎뒗 諛섑솚 ?뺥깭

```json
{
  "code": "result = df.groupby('MODE', as_index=False)['production'].sum()",
  "explanation": "MODE蹂??앹궛???⑷퀎瑜?怨꾩궛?⑸땲??"
}
```

## 珥덈낫???ъ씤??
???몃뱶??LLM 肄붾뱶瑜?諛붾줈 ?ㅽ뻾?섏? ?딆뒿?덈떎.
?ㅽ뻾 ????踰?援ъ“瑜??뺣━?섎뒗 ?덉쟾?μ튂?낅땲??

LLM???ㅽ뙣?대룄 fallback code瑜?留뚮뱾??flow媛 ?꾩쟾??硫덉텛吏 ?딄쾶 ?⑸땲??

## ?곌껐

```text
LLM JSON Caller (Pandas).llm_result
-> Normalize Pandas Plan.llm_result

Normalize Pandas Plan.analysis_plan_payload
-> Pandas Analysis Executor.analysis_plan_payload
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "llm_result": {
    "llm_text": "{\"code\":\"result_df = df.groupby('MODE', as_index=False)['production'].sum()\",\"explanation\":\"mode蹂??앹궛???⑷퀎\"}",
    "prompt_payload": {
      "rows": [
        {"MODE": "A", "production": 100}
      ],
      "columns": ["MODE", "production"]
    }
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "analysis_plan_payload": {
    "analysis_plan": {
      "code": "result_df = df.groupby('MODE', as_index=False)['production'].sum()",
      "explanation": "mode蹂??앹궛???⑷퀎",
      "input_columns": ["MODE", "production"]
    },
    "rows": [
      {"MODE": "A", "production": 100}
    ],
    "columns": ["MODE", "production"],
    "errors": []
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_strip_code_fence` | ```json ... ``` | JSON 臾몄옄??| LLM??肄붾뱶釉붾줉?쇰줈 ?묐떟?대룄 ?뚯떛 媛?ν븯寃??⑸땲?? |
| `_extract_json_object` | ?ㅻ챸臾?+ JSON | JSON dict | LLM ?묐떟?먯꽌 ?ㅼ젣 JSON 遺遺꾨쭔 李얠뒿?덈떎. |
| `_fallback_code` | plan, columns | pandas code 臾몄옄??| LLM ?묐떟??鍮꾩뼱??湲곕낯 groupby/?뺣젹 肄붾뱶瑜?留뚮뱾???뚯뒪??媛?ν븯寃??⑸땲?? |
| `normalize_pandas_plan` | llm_result | analysis_plan_payload | LLM ?묐떟??executor媛 ?댄빐?섎뒗 code/rows/columns 援ъ“濡?留욎땅?덈떎. |
| `build_plan` | Langflow input | `Data(data=analysis_plan_payload)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
LLM raw text ?뚯떛
-> code/explanation 異붿텧
-> prompt_payload??rows/columns ?좎?
-> code媛 ?놁쑝硫?fallback code ?앹꽦
-> Pandas Analysis Executor???섍만 plan 諛섑솚
```

### 珥덈낫???ъ씤??
LLM??留뚮뱺 肄붾뱶瑜?諛붾줈 ?ㅽ뻾?섏? ?딄퀬 ??踰??쒖? ?뺥깭濡??뺣━?⑸땲?? ???④퀎媛 ?덉뼱??executor?먯꽌 ?낅젰 ?곗씠?곗? code瑜??덉젙?곸쑝濡?諛쏆쓣 ???덉뒿?덈떎.

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `normalize_pandas_plan`

???⑥닔??Pandas LLM ?묐떟??executor媛 ?ㅽ뻾?????덈뒗 `analysis_plan_payload`濡?諛붽퓠?덈떎.

### ?⑥닔 input

```json
{
  "llm_result": {
    "llm_text": "{\"code\":\"result = df.groupby('MODE', as_index=False)['production'].sum()\"}",
    "prompt_payload": {
      "rows": [{"MODE": "A", "production": 100}],
      "columns": ["MODE", "production"],
      "plan": {"group_by": ["MODE"]}
    }
  }
}
```

### ?⑥닔 output

```json
{
  "analysis_plan_payload": {
    "analysis_plan": {
      "code": "result = df.groupby('MODE', as_index=False)['production'].sum()",
      "source": "llm"
    },
    "rows": [{"MODE": "A", "production": 100}],
    "columns": ["MODE", "production"]
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
payload = _payload_from_value(llm_result_value)
llm_result = payload.get("llm_result") if isinstance(payload.get("llm_result"), dict) else payload
```

LLM Caller output?먯꽌 ?ㅼ젣 `llm_result`瑜?爰쇰깄?덈떎.

```python
prompt_payload = llm_result.get("prompt_payload") if isinstance(llm_result.get("prompt_payload"), dict) else {}
```

LLM ?몄텧 ?꾩뿉 ?ъ슜?덈뜕 rows, columns, plan???ㅼ떆 爰쇰깄?덈떎. executor??洹몃?濡??꾨떖?댁빞 ?섍린 ?뚮Ц?낅땲??

```python
raw_plan, errors = _parse_jsonish(llm_result.get("llm_text", ""))
```

LLM??諛섑솚??JSON 臾몄옄?댁쓣 ?뚯떛?⑸땲??

```python
if not isinstance(raw_plan, dict):
    raw_plan = {}
```

?뚯떛 寃곌낵媛 dict媛 ?꾨땲硫?鍮?plan?쇰줈 泥섎━?⑸땲??

```python
code = str(raw_plan.get("code") or "").strip()
if not code:
    code = _fallback_code(prompt_payload.get("plan", {}), columns)
```

LLM??code瑜?紐?留뚮뱾?덉쑝硫?fallback pandas code瑜?留뚮벊?덈떎.

```python
analysis_plan = {**raw_plan, "code": code, "source": "llm" if raw_plan.get("code") else "fallback"}
```

理쒖쥌 ?ㅽ뻾 怨꾪쉷??code? source瑜??ｌ뒿?덈떎. source???섏쨷???붾쾭源낇븷 ??LLM 肄붾뱶?몄? fallback 肄붾뱶?몄? ?뚮젮以띾땲??
