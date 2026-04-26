# 24. Normalize Answer Text

## ??以???븷

理쒖쥌 ?듬? LLM ?묐떟???뚯떛?댁꽌 `answer_text`濡??뺣━?섎뒗 ?몃뱶?낅땲??

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `llm_result` | `LLM JSON Caller (Answer)` 異쒕젰?낅땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `answer_text` | ?먯뿰???듬?, ?섏씠?쇱씠?? warnings ?깆쓣 ?댁뒿?덈떎. |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_extract_json_object`: LLM ?묐떟?먯꽌 JSON??李얠뒿?덈떎.
- `_fallback_answer`: LLM ?묐떟???녾굅???뚯떛 ?ㅽ뙣?덉쓣 ??洹쒖튃 湲곕컲 ?듬???留뚮벊?덈떎.
- `_fallback_success_answer`: ?깃났 寃곌낵瑜??щ엺???쎌쓣 ???덈뒗 臾몄옣?쇰줈 留뚮벊?덈떎.
- `normalize_answer_text`: LLM ?묐떟怨?fallback???⑹퀜 理쒖쥌 answer_text瑜?留뚮벊?덈떎.

## 湲곕? JSON ?덉떆

```json
{
  "answer": "?ㅻ뒛 DA怨듭젙 ?앹궛?됱? 珥?33,097?낅땲??",
  "highlights": ["珥?12嫄?湲곗??낅땲??"]
}
```

## 珥덈낫???ъ씤??
???몃뱶???ъ슜?먯뿉寃?諛붾줈 異쒕젰?섏? ?딆뒿?덈떎.
臾몄옣留??뺣━?섍퀬, ?ㅼ젣 ?붾㈃??硫붿떆吏? final_result??`Final Answer Builder`媛 留뚮벊?덈떎.

LLM ?몄텧???ㅽ뙣?대룄 fallback ?듬????덉쑝誘濡??뚯뒪?멸? 媛?ν빀?덈떎.

## ?곌껐

```text
LLM JSON Caller (Answer).llm_result
-> Normalize Answer Text.llm_result

Normalize Answer Text.answer_text
-> Final Answer Builder.answer_text
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "llm_result": {
    "llm_text": "{\"response\":\"MODE A媛 150?쇰줈 媛??留롮뒿?덈떎.\"}",
    "prompt_payload": {
      "analysis_result": {
        "final_rows": [
          {"MODE": "A", "production": 150}
        ]
      }
    }
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "answer_text": {
    "response": "MODE A媛 150?쇰줈 媛??留롮뒿?덈떎.",
    "answer_source": "llm",
    "errors": []
  }
}
```

LLM ?묐떟??鍮꾩뼱 ?덉쑝硫?fallback ?듬???留뚮벊?덈떎.

```json
{
  "answer_text": {
    "response": "珥?1嫄댁쓽 寃곌낵媛 ?덉뒿?덈떎. MODE A??production? 150?낅땲??",
    "answer_source": "fallback"
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_extract_json_object` | LLM ?띿뒪??| JSON dict | 理쒖쥌 ?듬? LLM??JSON ??臾몄옣??遺숈뿬??response瑜?爰쇰깄?덈떎. |
| `_preview_table` | rows | markdown table 臾몄옄??| fallback ?듬??먯꽌 ?곗씠?곕? ?щ엺???쎄린 ?쎄쾶 蹂댁뿬以띾땲?? |
| `_metric_column` | rows | `"production"` | ?レ옄 metric 而щ읆??李얠븘 fallback 臾몄옣??留뚮뱾 ???곷땲?? |
| `_dimension_text` | `{"MODE": "A"}` | `"MODE A"` | row??李⑥썝 ?뺣낫瑜??먯뿰?댁쿂???쒗쁽?⑸땲?? |
| `_fallback_success_answer` | analysis result | ?듬? 臾몄옣 | LLM???ㅽ뙣?대룄 理쒖쥌 ?곗씠??湲곕컲 ?듬???留뚮뱾湲??꾪븳 ?덉쟾?μ튂?낅땲?? |
| `_fallback_answer` | analysis result | ?듬? 臾몄옣 | success/error ?곹깭蹂?fallback ?듬???怨좊쫭?덈떎. |
| `normalize_answer_text` | llm_result | answer_text payload | LLM ?듬? JSON???쒖? `response` ?뺥깭濡?留욎땅?덈떎. |
| `build_answer` | Langflow input | `Data(data=answer_text)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
LLM answer text ?뚯떛
-> response ?꾨뱶 異붿텧
-> ?녾굅???ㅻ쪟硫?analysis_result 湲곕컲 fallback ?앹꽦
-> Final Answer Builder媛 ?쎌쓣 answer_text 諛섑솚
```

### 珥덈낫???ъ씤??
???몃뱶???듬???留덉?留??덉쟾留앹엯?덈떎. LLM??JSON???섎せ 二쇨굅??API key媛 鍮꾩뼱 ?덉뼱?? 理쒖쥌 ?곗씠?곌? ?덉쑝硫?理쒖냼?쒖쓽 ?듬????앹꽦?⑸땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `normalize_answer_text`

???⑥닔??理쒖쥌 ?듬? LLM???묐떟??`{"response": "..."}` ?뺥깭濡??뺣━?⑸땲??

### ?⑥닔 input

```json
{
  "llm_result": {
    "llm_text": "{\"response\":\"MODE A媛 150?쇰줈 媛??留롮뒿?덈떎.\"}",
    "prompt_payload": {
      "analysis_result": {
        "data": [{"MODE": "A", "production": 150}]
      }
    }
  }
}
```

### ?⑥닔 output

```json
{
  "answer_text": {
    "response": "MODE A媛 150?쇰줈 媛??留롮뒿?덈떎.",
    "answer_source": "llm",
    "errors": []
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
analysis_result = prompt_payload.get("analysis_result") if isinstance(prompt_payload.get("analysis_result"), dict) else {}
```

LLM ?듬????ㅽ뙣?덉쓣 ??fallback ?듬???留뚮뱾湲??꾪빐 ?먮옒 analysis result瑜?爰쇰깄?덈떎.

```python
raw, errors = _parse_jsonish(llm_result.get("llm_text", ""))
```

LLM ?묐떟 JSON???뚯떛?⑸땲??

```python
response = str(raw.get("response") or raw.get("answer") or "").strip() if isinstance(raw, dict) else ""
```

LLM??`response` ???`answer`?쇨퀬 諛섑솚?대룄 ?듬??쇰줈 ?ъ슜?????덇쾶 ?????뺤씤?⑸땲??

```python
if not response:
    response = _fallback_answer(analysis_result)
    source = "fallback"
else:
    source = "llm"
```

LLM ?듬????놁쑝硫?final data瑜?蹂닿퀬 fallback ?듬???留뚮벊?덈떎.

```python
return {"answer_text": {"response": response, "answer_source": source, "errors": errors}}
```

Final Answer Builder媛 ?쎌쓣 ???덈뒗 ?쒖? ?뺥깭濡?諛섑솚?⑸땲??
