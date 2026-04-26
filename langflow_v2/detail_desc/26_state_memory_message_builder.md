# 26. State Memory Message Builder

## ??以???븷

`Final Answer Builder.next_state`瑜?Langflow Message History????ν븷 ???덈뒗 message ?뺥깭濡?諛붽씀???몃뱶?낅땲??

## ???꾩슂?쒓?

Langflow Message History??蹂댄넻 user/assistant 硫붿떆吏瑜???ν빀?덈떎.
?곕━??洹??덉뿉 ?ㅼ쓬 ?댁뿉???ъ슜??state???④퍡 ??ν빐???⑸땲??

洹몃옒?????몃뱶??state JSON ?욎뿉 marker瑜?遺숈씤 ?밸퀎??硫붿떆吏瑜?留뚮벊?덈떎.
?ㅼ쓬 ?댁쓽 `State Memory Extractor`媛 洹?marker瑜?李얠븘 ?ㅼ떆 state瑜??쎌뒿?덈떎.

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `next_state` | `Final Answer Builder.next_state` 異쒕젰?낅땲?? |
| `memory_marker` | ?곹깭 硫붿떆吏?꾩쓣 ?쒖떆?섎뒗 臾몄옄?댁엯?덈떎. 湲곕낯媛믪쓣 洹몃?濡??곕㈃ ?⑸땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `memory_message` | Message History Store???ｌ쓣 message?낅땲?? |
| `memory_payload` | ??λ맆 state payload瑜??뺤씤?섍린 ?꾪븳 Data 異쒕젰?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_state_from_value`: next_state ?낅젰?먯꽌 ?ㅼ젣 state瑜?爰쇰깄?덈떎.
- `_json_safe`: datetime ??JSON ??μ씠 ?대젮??媛믪쓣 ?덉쟾??媛믪쑝濡?諛붽퓠?덈떎.
- `build_state_memory_message`: marker + JSON 臾몄옄???뺥깭??message瑜?留뚮벊?덈떎.

## 珥덈낫???ъ씤??
???몃뱶???ъ슜?먯뿉寃?蹂댁씠???듬???留뚮뱶???몃뱶媛 ?꾨떃?덈떎.
?꾩냽 吏덈Ц???꾪빐 Langflow ?대? 湲곗뼲????ν븯???몃뱶?낅땲??

Playground?먯꽌 ?꾩냽 吏덈Ц?????쒕떎硫????몃뱶媛 Message History Store???곌껐?섏뼱 ?덈뒗吏 ?뺤씤?댁빞 ?⑸땲??

## ?곌껐

```text
Final Answer Builder.next_state
-> State Memory Message Builder.next_state

State Memory Message Builder.memory_message
-> Message History (Store).message
```

?ㅼ쓬 ?댁뿉?쒕뒗 ?ㅼ떆:

```text
Message History (Retrieve).messages
-> State Memory Extractor.memory_messages
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "next_state": {
    "state": {
      "session_id": "abc",
      "chat_history": [],
      "context": {
        "last_route": "post_analysis"
      },
      "current_data": {
        "rows": [
          {"MODE": "A", "production": 150}
        ]
      }
    }
  },
  "memory_marker": "__MANUFACTURING_AGENT_STATE__"
}
```

### 異쒕젰 ?덉떆

`memory_message`:

```text
__MANUFACTURING_AGENT_STATE__
{"marker":"__MANUFACTURING_AGENT_STATE__","state":{"session_id":"abc","current_data":{"rows":[...]}},"state_json":"{\"session_id\":\"abc\",...}"}
```

`memory_payload`:

```json
{
  "memory_payload": {
    "marker": "__MANUFACTURING_AGENT_STATE__",
    "state": {
      "session_id": "abc",
      "current_data": {
        "rows": [
          {"MODE": "A", "production": 150}
        ]
      }
    },
    "state_json": "{\"session_id\":\"abc\",...}"
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_make_message` | memory text | Langflow Message | Message History Store????ν븷 ???덈뒗 硫붿떆吏 媛앹껜瑜?留뚮벊?덈떎. |
| `_state_from_value` | `{"state": {...}}` | state dict | Final Answer Builder??next_state?먯꽌 ?ㅼ젣 state留?爰쇰깄?덈떎. |
| `_json_safe` | state dict | JSON ???媛?ν븳 dict | datetime/ObjectId 媛숈? 媛믪씠 ?덉뼱??JSON 臾몄옄?대줈 留뚮뱾 ???덇쾶 ?⑸땲?? |
| `build_state_memory_message` | next_state, marker | memory payload | marker媛 遺숈? state snapshot 硫붿떆吏? JSON payload瑜?留뚮벊?덈떎. |
| `_payload` | ?놁쓬 | cached memory payload | ??output??媛숈? 怨꾩궛??怨듭쑀?섍쾶 ?⑸땲?? |
| `build_memory_message` | ?놁쓬 | Message | Message History Store???곌껐?섎뒗 異쒕젰?낅땲?? |
| `build_memory_payload` | ?놁쓬 | Data | ?붾쾭源낆씠??API ??μ슜?쇰줈 蹂????덈뒗 援ъ“??異쒕젰?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
Final Answer Builder.next_state ?낅젰
-> state留?異붿텧
-> JSON ?덉쟾 ?뺥깭濡?蹂??-> marker ?ы븿 memory text ?앹꽦
-> Message History Store????ν븷 Message 諛섑솚
```

### 珥덈낫???ъ씤??
???몃뱶??Langflow ?먯껜 Message History瑜?short-term memory泥섎읆 ?곌린 ?꾪븳 留덉?留??④퀎?낅땲?? ?ㅼ쓬 吏덈Ц ??`00 State Memory Extractor`媛 ??marker瑜?李얠븘 ?댁쟾 state瑜?蹂듭썝?⑸땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `build_state_memory_message`

???⑥닔???ㅼ쓬 ?댁뿉???쎌쓣 ???덈뒗 state snapshot 硫붿떆吏瑜?留뚮벊?덈떎.

### ?⑥닔 input

```json
{
  "next_state_value": {
    "state": {
      "session_id": "abc",
      "current_data": {
        "data": [{"MODE": "A", "production": 150}]
      }
    }
  },
  "marker_value": "__MANUFACTURING_AGENT_STATE__"
}
```

### ?⑥닔 output

```json
{
  "memory_text": "__MANUFACTURING_AGENT_STATE__\n{\"marker\":\"__MANUFACTURING_AGENT_STATE__\",\"state\":{\"session_id\":\"abc\"}}",
  "memory_payload": {
    "marker": "__MANUFACTURING_AGENT_STATE__",
    "state": {"session_id": "abc"},
    "state_json": "{\"session_id\":\"abc\"}"
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
state = _state_from_value(next_state_value)
```

Final Answer Builder媛 留뚮뱺 next_state?먯꽌 ?ㅼ젣 state dict留?爰쇰깄?덈떎.

```python
marker = str(marker_value or DEFAULT_MEMORY_MARKER).strip() or DEFAULT_MEMORY_MARKER
```

Message History?먯꽌 ?섏쨷????硫붿떆吏瑜?李얘린 ?꾪븳 marker瑜??뺥빀?덈떎.

```python
safe_state = _json_safe(state)
```

state ?덉뿉 JSON?쇰줈 諛붾줈 ??ν븯湲??대젮??媛믪씠 ?덉쑝硫?臾몄옄???깆쑝濡?諛붽퓠?덈떎.

```python
state_json = json.dumps(safe_state, ensure_ascii=False)
```

state瑜?JSON 臾몄옄?대줈 留뚮벊?덈떎. ?쒓???源⑥졇 蹂댁씠吏 ?딅룄濡?`ensure_ascii=False`瑜??ъ슜?⑸땲??

```python
record = {
    "marker": marker,
    "state": safe_state,
    "state_json": state_json,
}
```

?섏쨷??State Memory Extractor媛 ?쎌쓣 ???덈뒗 record 援ъ“瑜?留뚮벊?덈떎.

```python
memory_text = f"{marker}\n{json.dumps(record, ensure_ascii=False)}"
```

Langflow Message History?먮뒗 Message text濡???ν빐???섎?濡?marker? JSON record瑜??섎굹??臾몄옄?대줈 ?⑹묩?덈떎.
