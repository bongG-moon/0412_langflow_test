# 06. Build Intent Prompt

## ??以???븷

?ъ슜??吏덈Ц, ?댁쟾 ?곹깭, domain, table catalog瑜?紐⑥븘 intent 遺꾨쪟??LLM prompt瑜?留뚮뱶???몃뱶?낅땲??

## intent??

intent??"?ъ슜?먭? 吏湲?臾댁뾿???먰븯?붽?"瑜?援ъ“?뷀븳 ?뺣낫?낅땲??

?덈? ?ㅻ㈃ ?ㅼ쓬???먮떒?⑸땲??

- ???곗씠??議고쉶媛 ?꾩슂?쒓??
- ?댁쟾 寃곌낵瑜??댁뼱??遺꾩꽍?섎뒗 吏덈Ц?멸??
- ?대뼡 dataset???꾩슂?쒓??
- ?좎쭨 媛숈? ?꾩닔 議곌굔???덈뒗媛?
- pandas ?꾩쿂由ш? ?꾩슂?쒓??

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `state_payload` | `State Loader` 異쒕젰?낅땲?? ?꾩옱 吏덈Ц怨??댁쟾 ?곹깭媛 ?ㅼ뼱 ?덉뒿?덈떎. |
| `domain_payload` | ?꾨찓??洹쒖튃?낅땲?? MongoDB ?먮뒗 JSON Loader 以??섎굹瑜??곌껐?⑸땲?? |
| `table_catalog_payload` | dataset/tool catalog?낅땲?? |
| `reference_date` | ?뚯뒪?몄슜 湲곗? ?좎쭨?낅땲?? 鍮꾩슦硫??꾩옱 ?좎쭨 湲곗??쇰줈 ?댁꽍?⑸땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `prompt_payload` | LLM JSON Caller???섍만 prompt? 愿??context?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_unwrap_state`: `state_payload`?먯꽌 ?ㅼ젣 state瑜?爰쇰깄?덈떎.
- `_unwrap_domain`: `domain_payload`?먯꽌 domain留?爰쇰깄?덈떎.
- `_unwrap_catalog`: table catalog瑜?爰쇰깄?덈떎.
- `_current_data_summary`: ?댁쟾 寃곌낵媛 ?덉쓣 ??row ?? 而щ읆 ?깆쓣 ?붿빟?⑸땲??
- `build_intent_prompt`: LLM?먭쾶 蹂대궪 instruction怨?JSON schema瑜?留뚮벊?덈떎.

## 珥덈낫???ъ씤??
???몃뱶??LLM???몄텧?섏? ?딆뒿?덈떎.
LLM???쎌쓣 prompt 臾몄옄?대쭔 留뚮벊?덈떎.

利? ??븷? "吏덈Ц吏瑜????묒꽦?섎뒗 ?몃뱶"?낅땲??
?ㅼ젣 ?듭븞 ?묒꽦? ?ㅼ쓬 ?몃뱶??`LLM JSON Caller`媛 ?⑸땲??

## ?곌껐

```text
State Loader.state_payload
-> Build Intent Prompt.state_payload

Domain Loader.domain_payload
-> Build Intent Prompt.domain_payload

Table Catalog Loader.table_catalog_payload
-> Build Intent Prompt.table_catalog_payload

Build Intent Prompt.prompt_payload
-> LLM JSON Caller (Intent).prompt_payload
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "state_payload": {
    "user_question": "?댁젣 WB怨듭젙 ?앹궛?ъ꽦瑜좎쓣 mode蹂꾨줈 ?뚮젮以?,
    "state": {
      "session_id": "abc",
      "current_data": null
    }
  },
  "domain_payload": {
    "domain": {
      "metrics": {
        "achievement_rate": {
          "aliases": ["?ъ꽦瑜?],
          "required_datasets": ["production", "wip"]
        }
      }
    }
  },
  "table_catalog_payload": {
    "table_catalog": {
      "datasets": {
        "production": {"keywords": ["?앹궛"]},
        "wip": {"keywords": ["?ш났"]}
      }
    }
  }
}
```

### 異쒕젰 ?덉떆

```json
{
  "prompt_payload": {
    "prompt": "You are an intent planner...\nReturn JSON only...",
    "state": {"session_id": "abc"},
    "domain": {"metrics": {"achievement_rate": "..."}},
    "table_catalog": {"datasets": {"production": "..."}},
    "reference_date": "2026-04-26"
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_unwrap_state` | `{"state_payload": {"state": {...}}}` | `{"state": {...}, "user_question": "..."}` | ???몃뱶 異쒕젰????寃?媛먯떥???덉뼱???ㅼ젣 state瑜?爰쇰깄?덈떎. |
| `_unwrap_domain` | `{"domain_payload": {"domain": {...}}}` | `{"metrics": {...}}` | prompt???ｌ쓣 domain dict留?異붿텧?⑸땲?? |
| `_unwrap_catalog` | `{"table_catalog_payload": {"table_catalog": {...}}}` | `{"datasets": {...}}` | prompt???ｌ쓣 dataset ?ㅻ챸留?異붿텧?⑸땲?? |
| `_current_data_summary` | `{"rows": [{"A": 1}]}` | `{"row_count": 1, "columns": ["A"]}` | ?꾩냽 吏덈Ц ?먮떒???꾩슂???꾩옱 ?곗씠???붿빟留?留뚮벊?덈떎. ?꾩껜 row瑜?prompt??留롮씠 ?ｌ? ?딄린 ?꾪븿?낅땲?? |
| `build_intent_prompt` | state/domain/catalog | `prompt_payload` | LLM??route, dataset, filter, pandas ?꾩슂 ?щ?瑜?JSON?쇰줈 ?듯븯寃??섎뒗 吏?쒕Ц??留뚮벊?덈떎. |
| `build_prompt` | Langflow ?낅젰媛?| `Data(data=prompt_payload)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
State?먯꽌 吏덈Ц怨??댁쟾 current_data ?붿빟 異붿텧
-> Domain?먯꽌 metric/alias/required_datasets 異붿텧
-> Table catalog?먯꽌 dataset ?ㅻ챸 異붿텧
-> LLM?먭쾶 諛섑솚?댁빞 ??JSON schema? ?먮떒 湲곗???prompt濡??묒꽦
```

### 珥덈낫???ъ씤??
???몃뱶??LLM???몄텧?섏? ?딆뒿?덈떎. LLM?먭쾶 以?"?쒗뿕吏"瑜?留뚮뱶???몃뱶?낅땲?? 寃곌낵媛 ?댁긽?섎㈃ 癒쇱? ???몃뱶??`prompt` ?덉뿉 ?꾩슂???뺣낫媛 ?ㅼ뼱媛붾뒗吏 蹂대㈃ ?⑸땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `build_intent_prompt`

???⑥닔???꾩옱 吏덈Ц, ?댁쟾 state, domain, table catalog瑜?紐⑥븘 Intent LLM?먭쾶 以?prompt瑜?留뚮벊?덈떎.

### ?⑥닔 input

```json
{
  "state_payload": {
    "user_question": "?ㅻ뒛 DA怨듭젙 ?앹궛???뚮젮以?,
    "state": {
      "session_id": "abc",
      "current_data": null
    }
  },
  "domain_payload": {
    "domain": {
      "process_groups": {
        "da": {"aliases": ["DA怨듭젙"], "processes": ["D/A1", "D/A2"]}
      }
    }
  },
  "table_catalog_payload": {
    "table_catalog": {
      "datasets": {
        "production": {"keywords": ["?앹궛??], "tool_name": "get_production_data"}
      }
    }
  }
}
```

### ?⑥닔 output

```json
{
  "prompt_payload": {
    "prompt": "You are a manufacturing data intent planner...",
    "state": {"session_id": "abc", "current_data": null},
    "domain": {"process_groups": "..."},
    "table_catalog": {"datasets": "..."}
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
state_payload = _unwrap_state(state_payload)
domain = _unwrap_domain(domain_payload)
table_catalog = _unwrap_catalog(table_catalog_payload)
```

???몃뱶 異쒕젰?ㅼ? `Data(data={...})`濡???踰?媛먯떥???덉뒿?덈떎. ????以꾩? 洹??덉뿉???ㅼ젣 state, domain, catalog留?爰쇰깄?덈떎.

```python
question = str(state_payload.get("user_question") or state.get("pending_user_question") or "").strip()
```

?꾩옱 ?ъ슜??吏덈Ц??李얠뒿?덈떎. `user_question`???놁쑝硫?state????λ맂 `pending_user_question`???ъ슜?⑸땲??

```python
current_data_summary = _current_data_summary(state.get("current_data") if isinstance(state.get("current_data"), dict) else {})
```

?꾩냽 吏덈Ц ?먮떒???꾩슂???꾩옱 ?곗씠???붿빟??留뚮벊?덈떎. ?꾩껜 row瑜????ｊ린蹂대떎 row ?? 而щ읆, data_ref 媛숈? ?묒? ?뺣낫留?prompt???ｊ린 ?꾪븳 以鍮꾩엯?덈떎.

```python
prompt = f"""..."""
```

LLM?먭쾶 以?instruction??留뚮벊?덈떎. ??prompt ?덉뿉???ㅼ쓬 ?댁슜???ы븿?⑸땲??

- 媛?ν븳 route 醫낅쪟
- dataset ?좏깮 湲곗?
- filter瑜?JSON?쇰줈 諛섑솚?섎씪??吏??- pandas媛 ?꾩슂??寃쎌슦
- domain metric??required_datasets瑜?諛섏쁺?섎씪??吏??- 諛섎뱶??JSON留?諛섑솚?섎씪??吏??
```python
return {
    "prompt_payload": {
        "prompt": prompt,
        "state": state,
        "domain": domain,
        "table_catalog": table_catalog,
        ...
    }
}
```

LLM ?몄텧 ?몃뱶??prompt 臾몄옄?대쭔 ?곗?留? ??normalizer??state/domain/catalog???ㅼ떆 ?꾩슂?⑸땲?? 洹몃옒??prompt? context瑜?媛숈씠 ?댁븘 蹂대깄?덈떎.
