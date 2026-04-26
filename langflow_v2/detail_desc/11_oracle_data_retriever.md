# 11. Oracle Data Retriever

## ??以???븷

intent plan???ㅼ뼱 ?덈뒗 retrieval job??蹂닿퀬 Oracle DB?먯꽌 ?ㅼ젣 ?곗씠?곕? 議고쉶?섎뒗 ?몃뱶?낅땲??

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `intent_plan` | single ?먮뒗 multi retrieval branch?먯꽌 ??議고쉶 怨꾪쉷?낅땲?? |
| `db_config` | Oracle ?묒냽 ?뺣낫 JSON?낅땲?? triple-quoted DSN??泥섎━?⑸땲?? |
| `fetch_limit` | 理쒕? 議고쉶 row ?섏엯?덈떎. |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `retrieval_payload` | Oracle 議고쉶 寃곌낵瑜?source_results? current_data ?뺥깭濡??댁뒿?덈떎. |

## db_config ?덉떆

```json
{
  "PKG_RPT": {
    "user": "USER",
    "password": "PASSWORD",
    "dsn": "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=host)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=svc)))"
  }
}
```

DSN??湲몃㈃ ?ㅼ쓬泥섎읆 triple quote??媛?ν빀?덈떎.

```python
{
  "PKG_RPT": {
    "user": "USER",
    "password": "PASSWORD",
    "dsn": """(DESCRIPTION=
      (ADDRESS=(PROTOCOL=TCP)(HOST=host)(PORT=1521))
      (CONNECT_DATA=(SERVICE_NAME=svc))
    )"""
  }
}
```

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_normalize_triple_quoted_json`: `""" ... """` ?덉쓽 DSN??JSON 臾몄옄?대줈 諛붽퓠?덈떎.
- `parse_jsonish`: JSON ?먮뒗 Python dict泥섎읆 蹂댁씠???낅젰???덉쟾?섍쾶 ?뚯떛?⑸땲??
- `DBConnector`: Oracle ?곌껐怨?SQL ?ㅽ뻾???대떦?섎뒗 ?묒? class?낅땲??
- `_execute_oracle_sql`: SQL ?ㅽ뻾 ??row list瑜?留뚮벊?덈떎.
- `get_production_data`, `get_target_data` ?? dataset蹂??ㅼ젣 SQL???대뒗 ?⑥닔?낅땲??
- `_run_job`: retrieval job??蹂닿퀬 ?곸젅??dataset ?⑥닔瑜??몄텧?⑸땲??
- `retrieve_oracle_data`: ?꾩껜 job 紐⑸줉???ㅽ뻾?섍퀬 寃곌낵瑜??⑹묩?덈떎.

## 珥덈낫???ъ씤??
???몃뱶?먯꽌 ?ㅼ젣 SQL??愿由ы빀?덈떎.
Table Catalog?먮뒗 SQL???ｌ? ?딄퀬, `tool_name`怨?`db_key`留??〓땲??

?덈? ?ㅼ뼱 catalog?먯꽌 `tool_name`??`get_production_data`?대㈃ ???뚯씪 ?덉쓽 媛숈? ?대쫫 ?⑥닔瑜??몄텧?⑸땲??

## ?먯＜ ?섎뒗 ?ㅻ쪟

- `DB connections JSON parse failed`: JSON 臾몃쾿 ?ㅻ쪟 ?먮뒗 ?곗샂??臾몄젣?낅땲??
- `Unknown Target DB`: `db_key`媛 `db_config`???놁뒿?덈떎.
- ?꾩닔 議곌굔 遺議? job??`date` 媛숈? 媛믪씠 ?놁뒿?덈떎.

## ?곌껐

```text
Intent Route Router.single_retrieval
-> Oracle Data Retriever (Single).intent_plan

Intent Route Router.multi_retrieval
-> Oracle Data Retriever (Multi).intent_plan

Oracle Data Retriever.retrieval_payload
-> Retrieval Payload Merger.single_retrieval ?먮뒗 multi_retrieval
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "intent_plan": {
    "retrieval_jobs": [
      {
        "dataset_key": "production",
        "tool_name": "get_production_data",
        "params": {
          "date": "20260425",
          "process": "DA"
        },
        "required_params": ["date"]
      }
    ]
  },
  "db_config": {
    "PKG_RPT": {
      "user": "USER",
      "password": "PASSWORD",
      "dsn": "HOST:1521/SERVICE"
    }
  },
  "fetch_limit": 5000
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
        "summary": "total rows 1, production 1200"
      }
    ],
    "errors": []
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_normalize_triple_quoted_json` | `{"dsn": """HOST/SVC"""}` | ?뚯떛 媛?ν븳 JSON 臾몄옄??| DSN?대굹 SQL??triple quote濡??ㅼ뼱???JSON ?뚯떛 ?ㅽ뙣瑜?以꾩엯?덈떎. |
| `parse_jsonish` | DB config 臾몄옄??| `(dict, errors)` | Langflow ?낅젰李쎌쓽 DB JSON???덉쟾?섍쾶 dict濡?諛붽퓠?덈떎. |
| `_db_config_from_value` | `db_config` ?낅젰 | `(config, errors)` | Oracle ?곌껐???꾩슂??user/password/dsn 援ъ“瑜?寃利앺빀?덈떎. |
| `_sql_literal` | `"D/A1"` | `"'D/A1'"` | SQL 臾몄옄?댁뿉 ?ㅼ뼱媛?媛믪쓣 ?덉쟾?섍쾶 ?곗샂??泥섎━?⑸땲?? |
| `DBConnector.get_connection` | `"PKG_RPT"` | Oracle connection | target DB ?대쫫?쇰줈 ?ㅼ젙??李얠븘 `oracledb.connect`瑜??ㅽ뻾?⑸땲?? |
| `DBConnector.execute_query` | target DB, SQL | row dict list | cursor 寃곌낵瑜?`[{而щ읆: 媛?]` ?뺥깭濡?諛붽퓠?덈떎. |
| `_execute_oracle_sql` | SQL, connector | source result | SQL ?ㅽ뻾 ?깃났/?ㅽ뙣瑜??쒖? retrieval 寃곌낵濡?媛먯뙃?덈떎. |
| `get_production_data` ??| params, connector | source result | dataset蹂?SQL??留뚮뱾怨??ㅽ뻾?섎뒗 ?ㅼ젣 議고쉶 ?⑥닔?낅땲?? |
| `_missing_required_params` | params, `["date"]` | ?꾨씫 紐⑸줉 | ?꾩닔 ?좎쭨 媛숈? 媛믪씠 ?놁쑝硫?DB 議고쉶 ?꾩뿉 留됱뒿?덈떎. |
| `_run_job` | retrieval job | source result | `tool_name`??留욌뒗 Oracle 議고쉶 ?⑥닔瑜??ㅽ뻾?⑸땲?? |
| `retrieve_oracle_data` | intent plan, db_config | retrieval payload | ?щ윭 job???ㅽ뻾?섍퀬 `source_results`濡?臾띠뒿?덈떎. |

### 肄붾뱶 ?먮쫫

```text
DB config JSON ?뚯떛
-> DBConnector ?앹꽦
-> retrieval_jobs 諛섎났
-> ?꾩닔 params ?뺤씤
-> tool_name蹂?SQL ?앹꽦
-> Oracle execute
-> source_results? current_data 援ъ꽦
```

### 珥덈낫???ъ씤??
Oracle ?몃뱶??"?대뼡 ?곗씠?곕? 議고쉶?좎? ?먮떒"?섏? ?딆뒿?덈떎. ?대? `07 Normalize Intent Plan`??留뚮뱺 `retrieval_jobs`瑜?蹂닿퀬, 媛?job???ㅼ젣 SQL ?ㅽ뻾?쇰줈 諛붽씀????븷?낅땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `DBConnector.execute_query`

???⑥닔??Oracle??SQL???ㅽ뻾?섍퀬 寃곌낵瑜?`list[dict]` ?뺥깭濡?諛붽씀???⑥닔?낅땲??

### ?⑥닔 input

```json
{
  "target_db": "PKG_RPT",
  "sql": "SELECT WORK_DT, MODE, production FROM AAA_TABLE WHERE WORK_DT = '20260425'",
  "fetch_limit": 5000
}
```

### ?⑥닔 output

```json
[
  {"WORK_DT": "20260425", "MODE": "DDR5", "production": 1200},
  {"WORK_DT": "20260425", "MODE": "LPDDR5", "production": 900}
]
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
conn = self.get_connection(target_db)
cursor = conn.cursor()
```

`target_db` ?대쫫?쇰줈 DB ?ㅼ젙??李얘퀬 Oracle connection???쎈땲?? 洹??ㅼ쓬 SQL ?ㅽ뻾???꾪븳 cursor瑜?留뚮벊?덈떎.

```python
cursor.execute(sql)
```

?ㅼ젣 SQL??Oracle DB濡??꾩넚?섎뒗 遺遺꾩엯?덈떎.

```python
columns = [col[0] for col in cursor.description]
```

Oracle cursor??description?먮뒗 議고쉶 寃곌낵 而щ읆 ?뺣낫媛 ?ㅼ뼱 ?덉뒿?덈떎. ?ш린??而щ읆紐낅쭔 戮묒뒿?덈떎.

??

```json
["WORK_DT", "MODE", "production"]
```

```python
rows = cursor.fetchmany(fetch_limit) if fetch_limit else cursor.fetchall()
```

`fetch_limit`???덉쑝硫?理쒕? 洹?嫄댁닔留?媛?몄샃?덈떎. ?놁쑝硫??꾩껜瑜?媛?몄샃?덈떎. ?댁쁺?먯꽌???덈Т 留롮? ?곗씠?곕? ??踰덉뿉 媛?몄삤吏 ?딄린 ?꾪빐 limit???먮뒗 寃껋씠 醫뗭뒿?덈떎.

```python
return [dict(zip(columns, row)) for row in rows]
```

Oracle cursor row??蹂댄넻 tuple泥섎읆 ?섏샃?덈떎.

```python
("20260425", "DDR5", 1200)
```

`zip(columns, row)`瑜??곕㈃ 而щ읆紐낃낵 媛믪쓣 吏앹??????덉뒿?덈떎.

```python
{"WORK_DT": "20260425", "MODE": "DDR5", "production": 1200}
```

?대젃寃?諛붽씀???댁쑀????Langflow/pandas ?몃뱶媛 而щ읆紐낆쑝濡?媛믪쓣 ?쎄린 ?쎄쾶 ?섍린 ?꾪빐?쒖엯?덈떎.

```python
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
```

?깃났?섎뱺 ?ㅽ뙣?섎뱺 cursor? connection???レ뒿?덈떎. DB ?곌껐??怨꾩냽 ?댁뼱?먮㈃ ?댁쁺 ?섍꼍?먯꽌 connection??遺議깊빐吏????덉뒿?덈떎.

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_run_job`

???⑥닔??`retrieval_jobs`??job ?섎굹瑜??ㅼ젣 Oracle 議고쉶 ?⑥닔濡??곌껐?⑸땲??

### ?듭떖 ?먮쫫

```text
job ?낅젰
-> tool_name ?뺤씤
-> ?꾩닔 params ?꾨씫 ?뺤씤
-> TOOL_REGISTRY?먯꽌 ?⑥닔 李얘린
-> get_production_data 媛숈? ?⑥닔 ?ㅽ뻾
-> source result 諛섑솚
```

?덈? ?ㅼ뼱 job???ㅼ쓬怨?媛숈쑝硫?

```json
{
  "dataset_key": "production",
  "tool_name": "get_production_data",
  "params": {"date": "20260425"}
}
```

`TOOL_REGISTRY["get_production_data"]`瑜?李얠븘 `get_production_data(params, connector, ...)`瑜??ㅽ뻾?⑸땲??

?대젃寃?registry瑜??곕뒗 ?댁쑀??if/elif瑜?湲멸쾶 ?곗? ?딄퀬??`tool_name`?쇰줈 ?⑥닔瑜??좏깮?????덇쾶 ?섍린 ?꾪빐?쒖엯?덈떎.

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `_db_config_from_value`

???⑥닔??Langflow ?낅젰李쎌뿉 ?ㅼ뼱??DB ?ㅼ젙??Oracle ?곌껐???????덈뒗 dict濡?諛붽퓠?덈떎.

### ?⑥닔 input

```json
{
  "PKG_RPT": {
    "user": "USER",
    "password": "PASSWORD",
    "dsn": "HOST:1521/SERVICE"
  }
}
```

臾몄옄?대줈 ?ㅼ뼱?ㅻ㈃ ?ㅼ쓬泥섎읆 ?ㅼ뼱???섎룄 ?덉뒿?덈떎.

```text
{
  "PKG_RPT": {
    "user": "USER",
    "password": "PASSWORD",
    "dsn": """HOST:1521/SERVICE"""
  }
}
```

### ?⑥닔 output

```json
[
  {
    "PKG_RPT": {
      "user": "USER",
      "password": "PASSWORD",
      "dsn": "HOST:1521/SERVICE"
    }
  },
  []
]
```

??踰덉㎏ 媛믪? errors list?낅땲??

### ?듭떖 肄붾뱶 ?댁꽍

```python
payload, errors = parse_jsonish(value)
```

?낅젰媛믪씠 dict?몄? JSON 臾몄옄?댁씤吏 ?뺤씤?섍퀬 ?뚯떛?⑸땲?? triple quote 臾몄옄?대룄 ?욌떒?먯꽌 蹂댁젙?⑸땲??

```python
if not isinstance(payload, dict):
    return {}, ["DB config must be a JSON object."]
```

DB ?ㅼ젙? 諛섎뱶??dict?ъ빞 ?⑸땲?? list???⑥닚 臾몄옄?댁씠硫??곌껐 ?뺣낫瑜?李얠쓣 ???놁쑝誘濡??ㅻ쪟瑜?諛섑솚?⑸땲??

```python
for key, conf in payload.items():
```

`PKG_RPT`, `MES`, `ERP`泥섎읆 target DB ?대쫫蹂??ㅼ젙???섎굹???뺤씤?⑸땲??

```python
if not isinstance(conf, dict):
    errors.append(f"{key} config must be an object.")
    continue
```

媛?DB ?ㅼ젙??dict?ъ빞 ?⑸땲?? ?꾨땲硫??대떦 DB ?ㅼ젙??嫄대꼫?곷땲??

```python
cleaned[str(key)] = {
    "user": str(conf.get("user") or ""),
    "password": str(conf.get("password") or ""),
    "dsn": str(conf.get("dsn") or ""),
}
```

Oracle ?곌껐???꾩슂????媛믪쓣 臾몄옄?대줈 ?뺣━?⑸땲??

- `user`
- `password`
- `dsn`

### ?????⑥닔媛 以묒슂?쒓??

Oracle ?곌껐 ?ㅻ쪟 以??곷떦?섎뒗 DB config ?낅젰 ?뺤떇 臾몄젣?먯꽌 諛쒖깮?⑸땲?? 洹몃옒?????⑥닔?먯꽌 ?낅젰??理쒕????좎뿰?섍쾶 諛쏆븘二쇨퀬, ?ㅽ뙣???뚮뒗 ?대뼡 ?ㅼ젙??臾몄젣?몄? `errors`濡??뚮젮以띾땲??

## 異붽? ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `retrieve_oracle_data`

???⑥닔??Intent Plan??retrieval jobs瑜??ㅼ젣 Oracle 議고쉶 寃곌낵濡?諛붽씀??理쒖긽???⑥닔?낅땲??

### ?⑥닔 input

```json
{
  "intent_plan_value": {
    "intent_plan": {
      "route": "single_retrieval",
      "retrieval_jobs": [
        {
          "dataset_key": "production",
          "tool_name": "get_production_data",
          "params": {"date": "20260425"}
        }
      ]
    }
  },
  "db_config_value": {
    "PKG_RPT": {
      "user": "USER",
      "password": "PASSWORD",
      "dsn": "HOST:1521/SERVICE"
    }
  }
}
```

### ?⑥닔 output

```json
{
  "retrieval_payload": {
    "route": "single_retrieval",
    "source_results": [
      {
        "success": true,
        "dataset_key": "production",
        "data": []
      }
    ],
    "used_oracle_data": true
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
payload = _payload_from_value(intent_plan_value)
plan = payload.get("intent_plan") if isinstance(payload.get("intent_plan"), dict) else payload
```

router?먯꽌 ?섏뼱??媛믪뿉???ㅼ젣 intent plan??爰쇰깄?덈떎.

```python
db_config, config_errors = _db_config_from_value(db_config_value)
```

Langflow ?낅젰??DB config瑜?Oracle connector媛 ?쎌쓣 ???덈뒗 ?뺥깭濡??뺣━?⑸땲??

```python
if config_errors:
    ...
```

DB config媛 ?섎せ?섎㈃ Oracle???묒냽?섍린 ?꾩뿉 retrieval ?ㅽ뙣 payload瑜?留뚮뱾 ???덉뒿?덈떎.

```python
connector = DBConnector(db_config)
```

DB ?곌껐怨?SQL ?ㅽ뻾???대떦?섎뒗 connector 媛앹껜瑜?留뚮벊?덈떎.

```python
jobs = plan.get("retrieval_jobs") if isinstance(plan.get("retrieval_jobs"), list) else []
source_results = [_run_job(job, connector, fetch_limit) for job in jobs if isinstance(job, dict)]
```

媛?retrieval job??`_run_job`?쇰줈 ?ㅽ뻾?⑸땲?? `_run_job` ?대??먯꽌 `get_production_data` 媛숈? SQL ?⑥닔媛 ?몄텧?⑸땲??

```python
return {
    "retrieval_payload": {
        "route": plan.get("route", "single_retrieval"),
        "source_results": source_results,
        "current_datasets": _build_current_datasets(source_results),
        ...
    }
}
```

Oracle 議고쉶 寃곌낵瑜?dummy retriever? 媛숈? 援ъ“濡?諛섑솚?⑸땲?? ?대젃寃??댁빞 ???몃뱶?ㅼ씠 ?곗씠??source媛 dummy?몄? Oracle?몄? 紐곕씪??媛숈? 諛⑹떇?쇰줈 泥섎━?????덉뒿?덈떎.
