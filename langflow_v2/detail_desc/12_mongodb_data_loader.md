# 12. MongoDB Data Loader

## ??以???븷

`data_ref`留??⑥븘 ?덈뒗 payload?먯꽌 MongoDB????λ맂 ?ㅼ젣 row list瑜??ㅼ떆 遺덈윭?ㅻ뒗 ?몃뱶?낅땲??

## ???꾩슂?쒓?

???곗씠???꾩껜瑜?Langflow state??怨꾩냽 ?ㅺ퀬 ?덉쑝硫??좏겙怨?硫붾え由щ? 留롮씠 ?곷땲??
洹몃옒??`MongoDB Data Store`媛 ??row list瑜?MongoDB????ν븯怨?state?먮뒗 二쇱냼留??④만 ???덉뒿?덈떎.

?꾩냽 吏덈Ц?먯꽌 ?ㅼ젣 row媛 ?ㅼ떆 ?꾩슂?섎㈃ ???몃뱶媛 洹?二쇱냼瑜??곕씪媛 row瑜?蹂듭썝?⑸땲??

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `payload` | `data_ref`媛 ?ы븿??payload?낅땲?? 蹂댄넻 follow-up branch?먯꽌 ?ㅼ뼱?듬땲?? |
| `mongo_uri` | row ??μ냼 MongoDB URI?낅땲?? |
| `db_name` | database ?대쫫?낅땲?? |
| `collection_name` | row data ref collection ?대쫫?낅땲?? |
| `enabled` | `true`?대㈃ 濡쒕뱶?섍퀬, `false`?대㈃ ?듦낵?쒗궢?덈떎. |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `loaded_payload` | data_ref媛 ?ㅼ젣 data row濡?蹂듭썝??payload?낅땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_connect_collection`: MongoDB collection???곌껐?⑸땲??
- `_load_rows`: data_ref???덈뒗 `ref_id`濡???λ맂 row瑜?李얠뒿?덈떎.
- `_hydrate_refs`: payload ?덉쓣 ?ш??곸쑝濡??뚮ŉ data_ref瑜??ㅼ젣 row濡?諛붽퓠?덈떎.
- `load_payload_from_mongo`: ?꾩껜 濡쒕뵫 ?묒뾽???ㅽ뻾?⑸땲??

## 珥덈낫???ъ씤??
???몃뱶??紐⑤뱺 吏덈Ц?먯꽌 瑗??꾩슂?섏????딆뒿?덈떎.

`MongoDB Data Store`瑜??ъ슜?댁꽌 ???곗씠?곕? ref濡???ν븯??援ъ“瑜????? ?꾩냽 遺꾩꽍 branch ?욎뿉 ?곌껐?⑸땲??

## ?곌껐

```text
Intent Route Router.followup_transform
-> MongoDB Data Loader (Follow-up).payload

MongoDB Data Loader.loaded_payload
-> Current Data Retriever.intent_plan
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "payload": {
    "intent_plan": {
      "state": {
        "current_data": {
          "rows": [],
          "data_ref": {
            "db_name": "datagov",
            "collection_name": "langflow_v2_data_store",
            "document_id": "abc123"
          }
        }
      }
    }
  },
  "mongo_uri": "mongodb://localhost:27017",
  "enabled": "true"
}
```

### 異쒕젰 ?덉떆

```json
{
  "loaded_payload": {
    "intent_plan": {
      "state": {
        "current_data": {
          "rows": [
            {"MODE": "A", "production": 10}
          ],
          "data_ref": {
            "document_id": "abc123"
          }
        }
      }
    }
  },
  "loaded_refs": [
    {
      "path": "intent_plan.state.current_data",
      "row_count": 1
    }
  ],
  "errors": []
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_truthy` | `"true"` | `true` | Langflow ?낅젰媛믪? 臾몄옄?댁씠 留롮쑝誘濡?enabled 媛숈? ?듭뀡??bool濡?諛붽퓠?덈떎. |
| `_connect_collection` | mongo uri/db/collection | collection 媛앹껜 | MongoDB collection???곌껐?⑸땲?? |
| `_load_rows` | `{"document_id": "abc123"}` | row list | ??λ맂 ???곗씠??document?먯꽌 rows瑜??쎌뒿?덈떎. |
| `_hydrate_refs` | payload ?꾩껜 | data_ref ?꾩튂媛 rows濡?梨꾩썙吏?payload | 以묒꺽??dict/list ?덉쓽 `data_ref`瑜?李얠븘 ?ㅼ젣 rows濡?蹂듭썝?⑸땲?? |
| `load_payload_from_mongo` | payload, Mongo ?ㅼ젙 | loaded payload | follow-up 遺꾩꽍 ?꾩뿉 compact payload瑜??ㅼ젣 ?곗씠???ы븿 payload濡?諛붽퓠?덈떎. |
| `build_payload` | Langflow ?낅젰媛?| `Data(data=loaded_payload)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
payload ?낅젰
-> enabled ?뺤씤
-> MongoDB collection ?곌껐
-> payload ?대? data_ref ?먯깋
-> 媛?ref??rows 濡쒕뱶
-> ?먮옒 payload ?꾩튂??rows ?쎌엯
```

### 珥덈낫???ъ씤??
???몃뱶?????곗씠?곕? "????섏? ?딄퀬 "?ㅼ떆 遺덈윭?ㅻ뒗" ?몃뱶?낅땲?? ?꾩냽 吏덈Ц?먯꽌 `current_data`媛 reference留?媛吏怨??덉쓣 ??pandas 遺꾩꽍??媛?ν븯?꾨줉 ?먮낯 row瑜?蹂듭썝?⑸땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_hydrate_refs`

???⑥닔??payload ?덉쓣 ?ш??곸쑝濡??뚮㈃??`data_ref`瑜?李얠븘 ?ㅼ젣 rows濡?諛붽퓠?덈떎.

### ?⑥닔 input

```json
{
  "value": {
    "current_data": {
      "data_ref": {"document_id": "abc123"},
      "data": []
    }
  },
  "path": "root"
}
```

### ?⑥닔 output

```json
{
  "current_data": {
    "data_ref": {"document_id": "abc123"},
    "data": [
      {"MODE": "A", "production": 10}
    ]
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
if isinstance(value, dict):
```

?꾩옱 寃??以묒씤 媛믪씠 dict?몄? ?뺤씤?⑸땲?? `current_data`, `analysis_result` 媛숈? payload???遺遺?dict?낅땲??

```python
data_ref = value.get("data_ref") or value.get("final_rows_ref")
```

??dict ?덉뿉 MongoDB reference媛 ?덈뒗吏 李얠뒿?덈떎. ????몃뱶媛 `data_ref` ?먮뒗 `final_rows_ref` 媛숈? key濡?二쇱냼瑜??④꼈湲??뚮Ц?낅땲??

```python
if isinstance(data_ref, dict):
    rows = _load_rows(collection, data_ref)
```

reference媛 dict?대㈃ MongoDB?먯꽌 ?ㅼ젣 rows瑜?遺덈윭?듬땲??

```python
hydrated = deepcopy(value)
hydrated["data"] = rows
```

?먮낯 payload瑜?吏곸젒 怨좎튂吏 ?딄퀬 蹂듭궗蹂몄쓣 留뚮뱺 ??`data`??rows瑜?梨꾩썎?덈떎.

```python
for key, item in value.items():
    hydrated[key] = _hydrate_refs(item, collection, loaded, f"{path}.{key}")
```

dict ?덉뿉 ???ㅻⅨ dict/list媛 ?덉쓣 ???덉쑝誘濡??ш??곸쑝濡?怨꾩냽 ?먯깋?⑸땲?? `path`???붾쾭源낇븷 ???대뒓 ?꾩튂?먯꽌 ref瑜?李얠븯?붿? 湲곕줉?섍린 ?꾪븳 臾몄옄?댁엯?덈떎.
