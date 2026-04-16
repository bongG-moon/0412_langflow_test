# Paste-Ready Langflow Nodes

This folder mirrors the root custom-node files in a visible standalone form.

Key points:
- Each node keeps the Langflow graph shape but contains the Python helpers it needs directly in the file.
- The files avoid hidden string-bundle runtime bootstrapping.
- No local repository package import is required when pasting a node into Langflow Desktop.
- External runtime packages such as pandas, langchain-core, langchain-google-genai, python-dotenv, and typing-extensions still need to exist in the Langflow environment.

Regenerate with:
- `python scripts/export_standalone_langflow_nodes.py`

Nodes:
- `domain_rules.py`
- `domain_registry.py`
- `session_memory.py`
- `extract_params.py`
- `decide_mode.py`
- `route_mode.py`
- `run_followup.py`
- `plan_datasets.py`
- `build_jobs.py`
- `route_plan.py`
- `exec_jobs.py`
- `route_single.py`
- `route_multi.py`
- `build_single.py`
- `analyze_single.py`
- `build_multi.py`
- `analyze_multi.py`
- `merge_final.py`
