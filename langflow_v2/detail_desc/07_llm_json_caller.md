# 07. LLM JSON Caller

## ??以???븷

???몃뱶媛 留뚮뱺 prompt瑜?LLM??蹂대궡怨? LLM ?묐떟 ?띿뒪?몃? `llm_result`濡?諛섑솚?⑸땲??

## ?대뵒???곕굹?

???몃뱶??媛숈? ?뚯씪??Langflow ?붾㈃????踰??щ젮???ъ슜?⑸땲??

1. `LLM JSON Caller (Intent)`: ?ъ슜???섎룄 遺꾨쪟
2. `LLM JSON Caller (Pandas)`: pandas 肄붾뱶 怨꾪쉷 ?앹꽦
3. `LLM JSON Caller (Answer)`: 理쒖쥌 ?먯뿰???듬? ?앹꽦

## ?낅젰

| ?낅젰 ?ы듃 | ?섎? |
| --- | --- |
| `prompt_payload` | prompt 臾몄옄?닿낵 愿??context?낅땲?? |
| `llm_api_key` | LLM API key?낅땲?? 鍮꾩슦硫???normalize ?몃뱶??fallback???숈옉?⑸땲?? |
| `model_name` | ?ъ슜??紐⑤뜽 ?대쫫?낅땲?? API key瑜??ｌ쑝硫??④퍡 ?낅젰?댁빞 ?⑸땲?? |
| `temperature` | ?듬????쒕뜡?깆엯?덈떎. 蹂댄넻 `0`??沅뚯옣?⑸땲?? |

## 異쒕젰

| 異쒕젰 ?ы듃 | ?섎? |
| --- | --- |
| `llm_result` | LLM ?먮Ц ?묐떟, ?먮윭 紐⑸줉, ?먮옒 prompt_payload瑜??ы븿?⑸땲?? |

## 二쇱슂 ?⑥닔 ?ㅻ챸

- `_payload_from_value`: `prompt_payload`瑜?dict濡?爰쇰깄?덈떎.
- `_load_llm`: LangChain chat model 媛앹껜瑜?留뚮벊?덈떎.
- `call_llm_json`: prompt瑜?LLM??蹂대궡怨??묐떟 ?띿뒪?몃? 諛쏆뒿?덈떎.

## OpenAI 紐⑤뜽濡?諛붽? ??
?꾩옱 ?뚯뒪?몄슜 援ы쁽? LangChain chat model??遺덈윭?ㅻ뒗 遺遺꾨쭔 諛붽씀硫??⑸땲??
肄붾뱶 ?덉뿉???ㅼ쓬 ?덉떆 二쇱꽍???ㅼ뼱 ?덉뒿?덈떎.

```python
from langchain_openai import ChatOpenAI
return ChatOpenAI(api_key=llm_api_key, model=model_name, temperature=temperature)
```

## 珥덈낫???ъ씤??
???몃뱶??JSON??吏곸젒 ?뚯떛?섏? ?딆뒿?덈떎.
洹??댁쑀??LLM ?묐떟??源⑥?嫄곕굹 鍮꾩뼱 ?덉뼱??flow媛 硫덉텛吏 ?딄쾶 ?섍린 ?꾪빐?쒖엯?덈떎.
?뚯떛怨?蹂댁젙? ?ㅼ쓽 normalize ?몃뱶媛 ?대떦?⑸땲??

## ?곌껐

```text
Build Intent Prompt.prompt_payload
-> LLM JSON Caller (Intent).prompt_payload
-> Normalize Intent Plan.llm_result

Build Pandas Prompt.prompt_payload
-> LLM JSON Caller (Pandas).prompt_payload
-> Normalize Pandas Plan.llm_result

Build Final Answer Prompt.prompt_payload
-> LLM JSON Caller (Answer).prompt_payload
-> Normalize Answer Text.llm_result
```

## Python 肄붾뱶 ?곸꽭 ?댁꽍

### ?낅젰 ?덉떆

```json
{
  "prompt_payload": {
    "prompt": "Return JSON only: {\"route\":\"single_retrieval\"}"
  },
  "llm_api_key": "sk-...",
  "model_name": "gpt-4o-mini",
  "temperature": "0"
}
```

### 異쒕젰 ?덉떆

```json
{
  "llm_result": {
    "llm_text": "{\"route\":\"single_retrieval\",\"datasets\":[\"production\"]}",
    "prompt_payload": {
      "prompt": "Return JSON only..."
    },
    "model_name": "gpt-4o-mini",
    "errors": []
  }
}
```

API key媛 鍮꾩뼱 ?덉쑝硫??뚯뒪?몄슜 fallback???묐룞?????덉뒿?덈떎.

```json
{
  "llm_result": {
    "llm_text": "",
    "errors": ["LLM API key is empty; downstream normalizer will use fallback logic."]
  }
}
```

### ?듭떖 ?⑥닔蹂??댁꽍

| ?⑥닔 | ?낅젰 ?덉떆 | 異쒕젰 ?덉떆 | ????肄붾뱶媛 ?꾩슂?쒓? |
| --- | --- | --- | --- |
| `_payload_from_value` | `Data(data={"prompt_payload": {...}})` | `{"prompt_payload": {...}}` | ??prompt builder??Data瑜?dict濡?爰쇰깄?덈떎. |
| `_load_llm` | `api_key`, `model_name`, `temperature` | LangChain chat model 媛앹껜 | ?ㅼ젣 LLM provider 媛앹껜瑜?留뚮뱶??遺遺꾩엯?덈떎. ?꾩옱??踰붿슜 ?대쫫???곌퀬, ?대? 援ы쁽??援먯껜?섍린 ?쎄쾶 ?〓땲?? |
| `call_llm_json` | prompt payload, key, model | `llm_result` | prompt 臾몄옄?댁쓣 LLM??蹂대궡怨??묐떟 text瑜?諛쏆븘 ?쒖? payload濡?媛먯뙃?덈떎. |
| `build_result` | Langflow ?낅젰媛?| `Data(data=llm_result)` | Langflow output method?낅땲?? |

### 肄붾뱶 ?먮쫫

```text
prompt_payload?먯꽌 prompt 臾몄옄??異붿텧
-> API key媛 ?덉쑝硫?LLM 媛앹껜 ?앹꽦
-> llm.invoke(prompt)
-> response.content瑜?llm_text?????-> ?ㅼ쓬 normalizer媛 ?쎌쓣 llm_result 諛섑솚
```

### 珥덈낫???ъ씤??
???몃뱶??JSON??寃利앺븯吏 ?딆뒿?덈떎. LLM ?묐떟??"臾몄옄??洹몃?濡? ?ㅼ쓬 ?몃뱶???섍퉩?덈떎. JSON ?뚯떛怨?湲곕낯媛?蹂댁젙? ?ㅼ쓽 normalize ?몃뱶媛 ?대떦?⑸땲??

## ?⑥닔 肄붾뱶 ?⑥쐞 ?댁꽍: `call_llm_json`

???⑥닔??prompt瑜?LLM??蹂대궡怨??묐떟 text瑜?`llm_result`濡?媛먯떥 諛섑솚?⑸땲??

### ?⑥닔 input

```json
{
  "prompt_payload_value": {
    "prompt_payload": {
      "prompt": "Return JSON only."
    }
  },
  "llm_api_key": "sk-...",
  "model_name": "gpt-4o-mini",
  "temperature": "0"
}
```

### ?⑥닔 output

```json
{
  "llm_result": {
    "llm_text": "{\"route\":\"single_retrieval\"}",
    "prompt_payload": {"prompt": "Return JSON only."},
    "model_name": "gpt-4o-mini",
    "errors": []
  }
}
```

### ?듭떖 肄붾뱶 ?댁꽍

```python
payload = _payload_from_value(prompt_payload_value)
prompt_payload = payload.get("prompt_payload") if isinstance(payload.get("prompt_payload"), dict) else payload
prompt = str(prompt_payload.get("prompt") or "")
```

???몃뱶?먯꽌 ??媛믪쓣 dict濡?諛붽씀怨? 洹??덉뿉???ㅼ젣 prompt 臾몄옄?댁쓣 爰쇰깄?덈떎.

```python
if not str(llm_api_key or "").strip():
    return {
        "llm_result": {
            "llm_text": "",
            "errors": ["LLM API key is empty; downstream normalizer will use fallback logic."],
            ...
        }
    }
```

API key媛 ?놁쑝硫?LLM???몄텧?섏? ?딆뒿?덈떎. ?????normalizer媛 fallback logic???곕룄濡?鍮?`llm_text`? ?ㅻ쪟 硫붿떆吏瑜?諛섑솚?⑸땲??

```python
llm = _load_llm(str(llm_api_key), str(model_name or ""), float(temperature or 0))
```

LangChain chat model 媛앹껜瑜?留뚮벊?덈떎. ?꾩옱 肄붾뱶?먯꽌??provider ?대쫫???몄텧?섏? ?딄퀬 踰붿슜 `llm_api_key`, `model_name`???ъ슜?⑸땲??

```python
response = llm.invoke(prompt)
text = getattr(response, "content", str(response))
```

LLM??prompt瑜?蹂대궡怨? ?묐떟 媛앹껜??`content`瑜?爰쇰깄?덈떎. `content`媛 ?놁쑝硫?媛앹껜瑜?臾몄옄?대줈 諛붽퓠?덈떎.

```python
return {
    "llm_result": {
        "llm_text": text,
        "prompt_payload": prompt_payload,
        "model_name": model_name,
        "errors": [],
    }
}
```

?묐떟???뚯떛?섏? ?딄퀬 text 洹몃?濡??댁뒿?덈떎. ???ㅺ퀎 ?뺣텇??Intent, Pandas, Answer ??怨녹뿉??媛숈? LLM Caller瑜??ъ궗?⑺븷 ???덉뒿?덈떎.
