# 22. MongoDB Data Store

## ??以???븷

??row list瑜?MongoDB????ν븯怨? flow payload?먮뒗 ?묒? preview? `data_ref`留??④린???몃뱶?낅땲??

## ???꾩슂?쒓?

議고쉶 寃곌낵媛 ?섏쿇 row媛 ?섎㈃ 紐⑤뱺 ?곗씠?곕? LLM prompt??Langflow state??怨꾩냽 ?ㅺ퀬 ?덇린 ?대졄?듬땲??

???몃뱶瑜??ъ슜?섎㈃ ?ㅼ쓬泥섎읆 諛붾앸땲??

```json
{
  "data": [{"preview": "rows"}],
  "data_ref": {
    "store": "mongodb",
    "ref_id": "...",
    "row_count": 1234
  },
  "data_is_reference": true
}
```

利? ?꾩껜 ?곗씠?곕뒗 MongoDB???덇퀬 state?먮뒗 二쇱냼留??⑥뒿?덈떎.

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `payload` | row list媛 ?ы븿??payload?낅땲?? 蹂댄넻 Analysis Result Merger 異쒕젰?낅땲?? |
| `mongo_uri` | MongoDB URI?낅땲?? |
| `db_name` | database ?대쫫?낅땲?? |
| `collection_name` | row ???collection ?대쫫?낅땲?? |
| `enabled` | `true`?대㈃ ??ν븯怨? `false`?대㈃ ?듦낵?쒗궢?덈떎. |
| `preview_row_limit` | payload???④만 誘몃━蹂닿린 row ?섏엯?덈떎. |
| `min_rows` | 紐?row ?댁긽????MongoDB????ν븷吏 ?뺥빀?덈떎. |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `stored_payload` | ??row list媛 preview + data_ref ?뺥깭濡??뺤텞??payload?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_is_row_list`: 媛믪씠 row list?몄? ?뺤씤?⑸땲??
- `_find_session_id`: payload ?덉뿉??session_id瑜?李얠븘 ???臾몄꽌???ｌ뒿?덈떎.
- `_store_rows`: MongoDB???ㅼ젣 rows瑜???ν빀?덈떎.
- `_compact_with_refs`: payload ?덉쓣 ?뚮ŉ ??row list瑜?data_ref濡?諛붽퓠?덈떎.
- `store_payload_in_mongo`: ?꾩껜 ??κ낵 ?뺤텞???ㅽ뻾?⑸땲??

## 珥덈낫???ъ씤??
???몃뱶???좏깮 ?ы빆?낅땲??
泥섏쓬 ?뚯뒪?명븷 ?뚮뒗 ?곌껐?섏? ?딆븘???⑸땲??

?곗씠?곌? 而ㅼ?怨??꾩냽 吏덈Ц源뚯? 吏?먰븯?ㅻ㈃ ?ㅼ쓬 ?몃뱶? ?명듃濡??ъ슜?⑸땲??

- ??? `MongoDB Data Store`
- ?ㅼ떆 遺덈윭?ㅺ린: `MongoDB Data Loader`

## ?곌껐

```text
Analysis Result Merger.analysis_result
-> MongoDB Data Store.payload

MongoDB Data Store.stored_payload
-> Build Final Answer Prompt.analysis_result

MongoDB Data Store.stored_payload
-> Final Answer Builder.analysis_result
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "payload": {
    "analysis_result": {
      "state": {"session_id": "abc"},
      "final_rows": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ]
    }
  },
  "enabled": "true",
  "preview_row_limit": "1",
  "min_rows": "1"
}
```

### 異쒕젰 ?덉떆

```json
{
  "stored_payload": {
    "analysis_result": {
      "final_rows": [
        {"MODE": "A", "production": 150}
      ],
      "final_rows_ref": {
        "db_name": "datagov",
        "collection_name": "langflow_v2_data_store",
        "document_id": "abc123",
        "row_count": 2
      }
    }
  },
  "stored_refs": [
    {
      "path": "analysis_result.final_rows",
      "row_count": 2
    }
  ]
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_truthy` | `"false"` | `false` | Langflow 臾몄옄???듭뀡??bool濡??댁꽍?⑸땲?? |
| `_is_row_list` | `[{"A": 1}]` | `true` | ?????곸씠 row list?몄? ?먮떒?⑸땲?? |
| `_find_session_id` | payload ?꾩껜 | `"abc"` | ???document??session id瑜??④린湲??꾪빐 payload ?덉뿉??李얠뒿?덈떎. |
| `_store_rows` | collection, rows, path | data_ref dict | ??row list瑜?MongoDB????ν븯怨?reference ?뺣낫瑜?留뚮벊?덈떎. |
| `_compact_with_refs` | payload ?꾩껜 | preview + ref payload | 以묒꺽??row list瑜?李얠븘 preview留??④린怨??먮낯? MongoDB ref濡?諛붽퓠?덈떎. |
| `store_payload_in_mongo` | payload, Mongo ?ㅼ젙 | stored payload | ???곗씠?곕? ??ν븯怨?compact payload瑜?諛섑솚?⑸땲?? |
| `build_payload` | Langflow input | `Data(data=stored_payload)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
analysis_result ?낅젰
-> enabled/min_rows ?뺤씤
-> ??row list ?먯깋
-> MongoDB???먮낯 rows ???-> payload?먮뒗 preview rows? data_ref留??좎?
```

### 珥덈낫???ъ씤??
???몃뱶??token ?덇컧?⑹엯?덈떎. LLM怨?memory?먮뒗 ?꾩껜 ?곗씠?곕? 怨꾩냽 ?ㅺ퀬 ?ㅻ땲吏 ?딄퀬, ?꾩슂??寃쎌슦 ?ㅼ떆 遺덈윭?????덈뒗 二쇱냼留??④퉩?덈떎.

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_compact_with_refs`

???⑥닔??payload ?덉쓽 ??row list瑜?MongoDB????ν븯怨? payload?먮뒗 preview? reference留??④퉩?덈떎.

### ?⑥닔 input

```json
{
  "analysis_result": {
    "data": [
      {"MODE": "A", "production": 150},
      {"MODE": "B", "production": 30}
    ]
  }
}
```

### ?⑥닔 output

```json
{
  "analysis_result": {
    "data": [
      {"MODE": "A", "production": 150}
    ],
    "data_ref": {
      "document_id": "abc123",
      "row_count": 2
    },
    "data_is_preview": true
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
if _is_row_list(value) and len(value) >= min_rows:
```

?꾩옱 媛믪씠 row list?닿퀬, ???湲곗? 嫄댁닔 ?댁긽?대㈃ compact ??곸엯?덈떎.

```python
data_ref = _store_rows(collection, value, session_id, path, db_name, collection_name)
```

?먮낯 rows瑜?MongoDB????ν븯怨?reference ?뺣낫瑜?諛쏆뒿?덈떎.

```python
preview = value[:preview_limit]
```

?붾㈃?대굹 LLM prompt??蹂댁뿬以?preview row留??④퉩?덈떎.

```python
refs.append({"path": path, **data_ref})
```

?대뒓 ?꾩튂??rows瑜???ν뻽?붿? 湲곕줉?⑸땲?? ?섏쨷???붾쾭源낇븷 ???대뼡 ?곗씠?곌? reference濡?諛붾뚯뿀?붿? ?????덉뒿?덈떎.

```python
return {
    "data": preview,
    "data_ref": data_ref,
    "data_is_preview": True,
    ...
}
```

?먮낯 ?꾩껜 ???preview? ref瑜?媛吏?dict瑜?諛섑솚?⑸땲??

```python
if isinstance(value, dict):
    return {key: _compact_with_refs(item, ...) for key, item in value.items()}
```

?꾩옱 媛믪씠 dict?쇰㈃ ?대? 媛믪쓣 ?섎굹???ш??곸쑝濡?寃?ы빀?덈떎. 洹몃옒??payload 源딆? 怨녹뿉 ?덈뒗 rows??李얠쓣 ???덉뒿?덈떎.

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `store_payload_in_mongo`

???⑥닔??MongoDB Data Store ?몃뱶??理쒖긽???⑥닔?낅땲?? ???湲곕뒫??耳ㅼ? ?먮떒?섍퀬, payload瑜?compact 泥섎━????寃곌낵瑜?諛섑솚?⑸땲??

### ?⑥닔 input

```json
{
  "payload_value": {
    "analysis_result": {
      "state": {"session_id": "abc"},
      "data": [
        {"MODE": "A", "production": 150},
        {"MODE": "B", "production": 30}
      ]
    }
  },
  "enabled_value": "true",
  "preview_row_limit_value": "1",
  "min_rows_value": "1"
}
```

### ?⑥닔 output

```json
{
  "stored_payload": {
    "analysis_result": {
      "data": [
        {"MODE": "A", "production": 150}
      ],
      "data_ref": {"document_id": "abc123", "row_count": 2},
      "data_is_preview": true
    }
  },
  "stored_refs": [
    {"path": "analysis_result.data", "row_count": 2}
  ],
  "errors": []
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
payload = _payload_from_value(payload_value)
```

???몃뱶??analysis result瑜?dict濡?爰쇰깄?덈떎.

```python
if not _truthy(enabled_value):
    return {"stored_payload": payload, "stored_refs": [], "errors": [], "storage_enabled": False}
```

???湲곕뒫??爰쇱졇 ?덉쑝硫??꾨Т寃껊룄 ??ν븯吏 ?딄퀬 ?먮낯 payload瑜?洹몃?濡?諛섑솚?⑸땲??

```python
preview_limit = max(0, int(preview_row_limit_value or 20))
min_rows = max(1, int(min_rows_value or 1))
```

preview濡??④만 row ?섏? ??μ쓣 ?쒖옉??理쒖냼 row ?섎? ?レ옄濡?諛붽퓠?덈떎.

```python
collection_client, collection = _connect_collection(mongo_uri, db_name, collection_name)
```

MongoDB collection???곌껐?⑸땲??

```python
session_id = _find_session_id(payload)
refs: list[Dict[str, Any]] = []
compact_payload = _compact_with_refs(payload, collection, session_id, db_name, collection_name, preview_limit, min_rows, "root", refs)
```

payload ?대?瑜??ш??곸쑝濡??묒쑝硫???row list瑜?MongoDB????ν븯怨? payload?먮뒗 preview? ref留??④퉩?덈떎.

```python
return {
    "stored_payload": compact_payload,
    "stored_refs": refs,
    "errors": [],
    "storage_enabled": True,
}
```

?????compact payload? ??λ맂 ref 紐⑸줉??諛섑솚?⑸땲??

### ?????⑥닔媛 以묒슂?쒓??

???⑥닔媛 ?놁쑝硫?議고쉶 寃곌낵 ?꾩껜媛 final prompt? memory??怨꾩냽 ?ㅼ뼱媛????덉뒿?덈떎. ?곗씠?곌? 而ㅼ쭏?섎줉 token 鍮꾩슜, latency, ?붾㈃ ?뚮뜑留?臾몄젣媛 ?앷린誘濡?reference 諛⑹떇???꾩슂?⑸땲??
