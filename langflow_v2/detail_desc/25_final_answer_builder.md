# 25. Final Answer Builder

## ??以???븷

?ъ슜?먯뿉寃?蹂댁뿬以?理쒖쥌 硫붿떆吏, API??final_result, ?ㅼ쓬 ?댁슜 next_state瑜?留뚮뱶???몃뱶?낅땲??

## ??媛??以묒슂?쒓?

???몃뱶??flow??理쒖쥌 異쒓뎄?낅땲??

?ш린????媛吏媛 留뚮뱾?댁쭛?덈떎.

1. `answer_message`: Playground Chat Output??蹂대궪 硫붿떆吏
2. `final_result`: API????μ슜 ?꾩껜 寃곌낵
3. `next_state`: ?꾩냽 吏덈Ц???꾪빐 ??ν븷 ?곹깭

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `analysis_result` | 遺꾩꽍 寃곌낵?낅땲?? |
| `answer_text` | Normalize Answer Text???먯뿰???듬??낅땲?? 鍮꾩뼱 ?덉쑝硫?fallback ?듬???留뚮벊?덈떎. |
| `output_row_limit` | final_result???댁쓣 理쒕? row ?섏엯?덈떎. |
| `display_row_limit` | 怨쇨굅 ?명솚?⑹엯?덈떎. ?꾩옱??湲곕낯?곸쑝濡??꾩껜 final data瑜??쒖떆?⑸땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `answer_message` | ?ъ슜?먯뿉寃?蹂댁뿬以??듬? 硫붿떆吏?낅땲?? |
| `final_result` | response, final_data, current_data ?깆쓣 ?ы븿???꾩껜 payload?낅땲?? |
| `next_state` | ?ㅼ쓬 吏덈Ц?먯꽌 ?ъ슜???곹깭?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_build_final_data`: 理쒖쥌 ?곗씠???뚯씠釉??뺣낫瑜?留뚮벊?덈떎.
- `_build_answer_message`: ?먯뿰???듬?怨?final data table???섎굹??markdown 硫붿떆吏濡?留뚮벊?덈떎.
- `_fallback_response`: LLM ?듬????놁쓣 ??洹쒖튃 湲곕컲 ?듬???留뚮벊?덈떎.
- `build_final_answer`: ??異쒕젰媛믪쓣 紐⑤몢 ?앹꽦?⑸땲??

## final_result ?듭떖 援ъ“

```json
{
  "response": "理쒖쥌 ?듬?",
  "final_data": {
    "rows": [],
    "row_count": 12,
    "columns": []
  },
  "current_data": {},
  "state_json": "{...}"
}
```

## 珥덈낫???ъ씤??
?꾩냽 吏덈Ц?????섎젮硫?`next_state`媛 以묒슂?⑸땲??
`next_state` ?덉뿉 `current_data`, `context`, `chat_history`媛 ?ㅼ뼱媛???ㅼ쓬 ?댁뿉??`?대븣`, `洹?寃곌낵` 媛숈? ?쒗쁽???댄빐?????덉뒿?덈떎.

## ?곌껐

```text
Analysis Result Merger.analysis_result
?먮뒗 MongoDB Data Store.stored_payload
-> Final Answer Builder.analysis_result

Normalize Answer Text.answer_text
-> Final Answer Builder.answer_text

Final Answer Builder.answer_message
-> Chat Output.input

Final Answer Builder.next_state
-> State Memory Message Builder.next_state
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
    "state": {
      "session_id": "abc",
      "chat_history": []
    }
  },
  "answer_text": {
    "response": "MODE A媛 150?쇰줈 媛??留롮뒿?덈떎."
  },
  "display_row_limit": "0",
  "output_row_limit": "200"
}
```

### 異쒕젰 ?덉떆

`answer_message`:

```text
MODE A媛 150?쇰줈 媛??留롮뒿?덈떎.

## 理쒖쥌 ?곗씠??2嫄?以?2嫄??쒖떆

| MODE | production |
| --- | --- |
| A | 150 |
| B | 30 |
```

`final_result`:

```json
{
  "response": "MODE A媛 150?쇰줈 媛??留롮뒿?덈떎.",
  "success": true,
  "final_data": {
    "rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "row_count": 2
  },
  "current_data": {
    "rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ]
  }
}
```

`next_state`:

```json
{
  "state": {
    "session_id": "abc",
    "current_data": {
      "rows": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ]
    },
    "context": {}
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_make_message` | ?듬? 臾몄옄??| Langflow Message | Chat Output???먯뿰??硫붿떆吏濡??쒖떆?섍린 ?꾪빐 ?곷땲?? |
| `_safe_rows` | rows, limit | ?쒗븳??rows | API output?대굹 memory媛 ?덈Т 而ㅼ?吏 ?딄쾶 row ?섎? ?쒗븳?⑸땲?? |
| `_preview_table` | rows | markdown table | ?ъ슜???붾㈃??理쒖쥌 ?곗씠?곕? ???뺥깭濡?蹂댁뿬以띾땲?? |
| `_build_final_data` | result, rows, row_count, ref | final_data dict | ?듬????ъ슜??理쒖쥌 媛怨??곗씠?곕? ?쒖? 援ъ“濡?留뚮벊?덈떎. |
| `_build_answer_message` | response, final_data | ?붾㈃ 異쒕젰 臾몄옄??| ?듬? 臾몄옣怨?理쒖쥌 ?곗씠???쒕? ?⑹퀜 Chat Output 硫붿떆吏瑜?留뚮벊?덈떎. |
| `_fallback_response` | result | ?듬? 臾몄옣 | LLM ?듬????놁쓣 ??final data濡?理쒖냼 ?듬???留뚮벊?덈떎. |
| `build_final_answer` | analysis result, answer text | final payload | `answer_message`, `final_result`, `next_state`瑜???踰덉뿉 留뚮벊?덈떎. |
| `_payload` | ?놁쓬 | cached final payload | output??3媛쒕씪 媛숈? 怨꾩궛??諛섎났?섏? ?딅룄濡??대? cache泥섎읆 ?곷땲?? |
| `build_answer_message` | ?놁쓬 | Message | ?ъ슜?먯뿉寃?蹂댁씠??異쒕젰?낅땲?? |
| `build_final_result` | ?놁쓬 | Data | API/??μ슜 ?꾩껜 寃곌낵?낅땲?? |
| `build_next_state` | ?놁쓬 | Data | ?ㅼ쓬 ??memory????ν븷 state?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
analysis_result? answer_text ?낅젰
-> response 寃곗젙
-> final_rows濡?final_data ?앹꽦
-> ?듬? + 理쒖쥌 ?곗씠??markdown ?앹꽦
-> final_result? next_state 援ъ꽦
-> ??output port濡?媛곴컖 諛섑솚
```

### 珥덈낫???ъ씤??
???몃뱶???ъ슜?먯뿉寃?蹂댁씠??理쒖쥌 紐⑥뼇??寃곗젙?⑸땲?? "?듬? 臾몄옣留????꾨땲??"?듬????ъ슜??理쒖쥌 ?곗씠?????④퍡 蹂댁뿬?щ씪???붽뎄媛 ?ш린??諛섏쁺?⑸땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `build_final_answer`

???⑥닔??理쒖쥌 ?듬? 臾몄옣, 理쒖쥌 ?곗씠?? ?ㅼ쓬 ??state瑜???踰덉뿉 留뚮뱶???듭떖 ?⑥닔?낅땲??

### ?⑥닔 input

```json
{
  "analysis_result_value": {
    "analysis_result": {
      "success": true,
      "tool_name": "analyze_current_data",
      "data": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ],
      "summary": "data analysis complete: 2 rows",
      "state": {
        "session_id": "abc",
        "chat_history": []
      },
      "intent_plan": {
        "route": "followup_transform"
      }
    }
  },
  "answer_text_value": {
    "answer_text": {
      "response": "MODE A媛 150?쇰줈 媛??留롮뒿?덈떎."
    }
  },
  "output_row_limit_value": "200",
  "display_row_limit_value": "0"
}
```

### ?⑥닔 output

```json
{
  "answer_message": "MODE A媛 150?쇰줈 媛??留롮뒿?덈떎.\n\n### 理쒖쥌 ?곗씠??n...",
  "final_result": {
    "response": "MODE A媛 150?쇰줈 媛??留롮뒿?덈떎.",
    "final_data": {
      "rows": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ],
      "row_count": 2
    }
  },
  "next_state": {
    "state": {
      "session_id": "abc",
      "current_data": {
        "data": [
          {"MODE": "A", "production": 150},
          {"MODE": "B", "production": 30}
        ]
      }
    }
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
result = _analysis_result(analysis_result_value)
state = result.get("state") if isinstance(result.get("state"), dict) else {}
plan = result.get("intent_plan") if isinstance(result.get("intent_plan"), dict) else {}
```

???몃뱶?먯꽌 ??analysis result瑜?爰쇰궡怨? 洹??덉쓽 state? intent plan???곕줈 爰쇰깄?덈떎.

```python
response = _text_from_value(answer_text_value) or _fallback_response(result, display_row_limit)
```

理쒖쥌 ?듬? LLM??留뚮뱺 臾몄옣??癒쇱? ?ъ슜?⑸땲?? 留뚯빟 鍮꾩뼱 ?덉쑝硫?遺꾩꽍 寃곌낵瑜?蹂닿퀬 fallback ?듬???留뚮벊?덈떎.

```python
rows = result.get("data") if isinstance(result.get("data"), list) else []
actual_row_count = _row_count_from_result(result, rows)
slim_rows = _safe_rows(rows, output_row_limit)
```

- `rows`: 理쒖쥌 遺꾩꽍 ?곗씠?곗엯?덈떎.
- `actual_row_count`: ?꾩껜 寃곌낵 嫄댁닔?낅땲??
- `slim_rows`: API payload??memory???ｌ쓣 ???덈Т 而ㅼ?吏 ?딄쾶 ?쒗븳??row 紐⑸줉?낅땲??

```python
data_ref = deepcopy(result.get("data_ref")) if isinstance(result.get("data_ref"), dict) else None
final_data = _build_final_data(result, rows, actual_row_count, display_row_limit, data_ref)
answer_message = _build_answer_message(response, final_data)
```

理쒖쥌 ?곗씠??援ъ“瑜?留뚮뱾怨? ?ъ슜?먯뿉寃?蹂댁뿬以?message瑜?留뚮벊?덈떎. `data_ref`媛 ?덉쑝硫??먮낯 ?곗씠?곕뒗 MongoDB???덇퀬 ?붾㈃?먮뒗 preview留??덉쓣 ???덉쓬???쒖떆?⑸땲??

```python
current_data = state.get("current_data")
if result.get("success"):
    current_data = {
        "success": True,
        "tool_name": result.get("tool_name", "analyze_current_data"),
        "data": slim_rows,
        "row_count": actual_row_count,
        ...
    }
```

?ㅼ쓬 ???꾩냽 吏덈Ц???꾪빐 `current_data`瑜???寃곌낵濡?媛깆떊?⑸땲?? ?ъ슜?먭? "?대븣 媛????媛믪??"?대씪怨?臾쇱쑝硫??ㅼ쓬 ?댁뿉?????곗씠?곌? 湲곗????⑸땲??

```python
next_state = deepcopy(state)
next_state.pop("pending_user_question", None)
```

湲곗〈 state瑜?蹂듭궗???ㅼ쓬 ??state瑜?留뚮벊?덈떎. `pending_user_question`? ?대쾲 ?댁뿉?쒕쭔 ?꾩슂??媛믪씠誘濡??쒓굅?⑸땲??

```python
if user_question:
    chat_history = [*chat_history, {"role": "user", "content": user_question}, {"role": "assistant", "content": response}]
next_state["chat_history"] = chat_history[-20:]
```

?꾩옱 吏덈Ц怨??듬???chat history??異붽??⑸땲?? ?덈Т 湲몄뼱吏吏 ?딄쾶 理쒓렐 20媛쒕쭔 ?좎??⑸땲??

```python
context.update({
    "last_intent": plan,
    "last_retrieval_plan": {"route": plan.get("route"), "jobs": plan.get("retrieval_jobs", [])},
    "last_extracted_params": extracted_params,
    "last_analysis_summary": result.get("summary", "")
})
```

?ㅼ쓬 ?댁뿉??李멸퀬??留λ씫????ν빀?덈떎.

- 留덉?留??섎룄
- 留덉?留?議고쉶 怨꾪쉷
- 留덉?留??꾪꽣/?좎쭨 ?뚮씪誘명꽣
- 留덉?留?遺꾩꽍 ?붿빟

```python
tool_result = {
    "success": result.get("success", False),
    "tool_name": result.get("tool_name", "analyze_current_data"),
    "data": slim_rows,
    "row_count": actual_row_count,
    ...
}
```

API???붾쾭源??붾㈃?먯꽌 蹂닿린 醫뗭? tool result瑜?留뚮벊?덈떎. ?ш린?먮룄 理쒖쥌 ?곗씠???쇰?? row count媛 ?ㅼ뼱媛묐땲??

### ?????⑥닔媛 以묒슂?쒓??

???⑥닔??v2 flow??留덉?留?怨꾩빟??留뚮벊?덈떎.

- ?ъ슜?먭? 蹂대뒗 硫붿떆吏: `answer_message`
- ?몃? ?쒖뒪?쒖씠 ?쎌쓣 寃곌낵: `final_result`
- ?ㅼ쓬 吏덈Ц???꾪븳 湲곗뼲: `next_state`

????媛吏媛 ?ш린???숈떆??留뚮뱾?댁?湲??뚮Ц?? 理쒖쥌 異쒕젰 ?뺤떇??諛붽씀?ㅻ㈃ ???⑥닔瑜?媛??癒쇱? ?뺤씤?섎㈃ ?⑸땲??

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_build_final_data`

???⑥닔???ъ슜?먯뿉寃?蹂댁뿬以?理쒖쥌 ?곗씠??臾띠쓬??留뚮벊?덈떎.

### ?⑥닔 input

```json
{
  "rows": [
    {"MODE": "A", "production": 150},
    {"MODE": "B", "production": 30}
  ],
  "row_count": 2,
  "data_ref": null
}
```

### ?⑥닔 output

```json
{
  "rows": [
    {"MODE": "A", "production": 150},
    {"MODE": "B", "production": 30}
  ],
  "row_count": 2,
  "display_row_limit": "all",
  "displayed_row_count": 2,
  "columns": ["MODE", "production"],
  "data_is_preview": false
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
display_rows = _safe_rows(rows, 0)
```

?ъ슜???붾㈃??蹂댁뿬以?rows瑜?以鍮꾪빀?덈떎. ?꾩옱 臾몄꽌 湲곗??쇰줈 `0`? ?꾩껜 ?쒖떆瑜??섎??⑸땲??

```python
is_preview = bool(data_ref) or row_count > len(display_rows)
```

?먮낯 ?곗씠?곌? MongoDB reference濡???λ릺???덇굅?? ?꾩껜 row_count媛 ?붾㈃???쒖떆??row ?섎낫??留롮쑝硫?preview?쇨퀬 ?쒖떆?⑸땲??

```python
final_data = {
    "rows": display_rows,
    "row_count": row_count,
    "display_row_limit": "all",
    "displayed_row_count": len(display_rows),
    "columns": _rows_columns(display_rows),
    ...
}
```

理쒖쥌 ?곗씠?곗쓽 row, ?꾩껜 嫄댁닔, ?쒖떆 嫄댁닔, 而щ읆 紐⑸줉???쒓납??紐⑥쓭?덈떎.

```python
if data_ref:
    final_data["data_ref"] = deepcopy(data_ref)
    final_data["data_is_reference"] = True
```

?먮낯 ?꾩껜 ?곗씠?곌? MongoDB????λ릺???덉쑝硫?洹?二쇱냼??媛숈씠 ?댁뒿?덈떎.

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_build_answer_message`

???⑥닔???먯뿰???듬?怨?理쒖쥌 ?곗씠???쒕? ?⑹퀜 Chat Output??蹂댁뿬以?臾몄옄?댁쓣 留뚮벊?덈떎.

### ?⑥닔 input

```json
{
  "response": "MODE A媛 150?쇰줈 媛??留롮뒿?덈떎.",
  "final_data": {
    "rows": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ],
    "row_count": 2
  }
}
```

### ?⑥닔 output

```text
MODE A媛 150?쇰줈 媛??留롮뒿?덈떎.

### 理쒖쥌 ?곗씠??
珥?2嫄?
| MODE | production |
| --- | --- |
| A | 150 |
| B | 30 |
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
rows = final_data.get("rows") if isinstance(final_data.get("rows"), list) else []
if not rows:
    return response
```

理쒖쥌 ?곗씠??row媛 ?놁쑝硫??듬? 臾몄옣留?諛섑솚?⑸땲??

```python
row_count = final_data.get("row_count") or len(rows)
displayed = len(rows)
table = _preview_table(rows, 0)
```

?꾩껜 嫄댁닔, ?쒖떆 嫄댁닔, markdown table??以鍮꾪빀?덈떎.

```python
count_text = f"珥?{row_count}嫄? if row_count == displayed else f"?꾩껜 {row_count}嫄?以?{displayed}嫄??쒖떆"
```

?꾩껜媛 ???쒖떆?섎㈃ `珥?n嫄?, ?쇰?留??쒖떆?섎㈃ `?꾩껜 n嫄?以?m嫄??쒖떆`?쇨퀬 臾멸뎄瑜??ㅻⅤ寃?留뚮벊?덈떎.

```python
parts = [
    response,
    "",
    "### 理쒖쥌 ?곗씠??,
    "",
    count_text,
    "",
    table,
]
return "\n".join(str(part) for part in parts).strip()
```

?듬? 臾몄옣, ?쒕ぉ, 嫄댁닔, ?쒕? 以꾨컮轅덉쑝濡??⑹퀜 理쒖쥌 硫붿떆吏瑜?留뚮벊?덈떎.
