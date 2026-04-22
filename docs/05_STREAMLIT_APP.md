# Streamlit App

`app.py` is the interactive UI for the manufacturing agent.

Run it from the repository root:

```powershell
streamlit run app.py
```

## Runtime Path

The app calls:

```text
app.py
-> manufacturing_agent.agent.run_agent_with_progress
-> manufacturing_agent graph/services
```

## Session State

The app keeps these values in `st.session_state`:

- chat messages
- `context`
- `current_data`
- UI flags such as engineer mode

This is important for follow-up questions such as grouping or summarizing the
current table. The next turn needs the previous `current_data` to avoid
unnecessary fresh retrieval.

## Useful Files

- `app.py`
- `manufacturing_agent/agent.py`
- `manufacturing_agent/app/ui_renderer.py`
- `manufacturing_agent/app/ui_domain_knowledge.py`
