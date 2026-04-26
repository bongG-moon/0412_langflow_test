from __future__ import annotations

import os
from pathlib import Path


try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(Path(__file__).resolve().parents[3] / ".env")


MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://bonggeon:qhdrjs123@datagov.5qcxapn.mongodb.net/?retryWrites=true&w=majority&appName=datagov",
)
DEFAULT_DB_NAME = os.getenv("MONGO_DB_NAME", "datagov")
DOMAIN_ITEMS_COLLECTION = os.getenv("MONGO_DOMAIN_ITEMS_COLLECTION", "manufacturing_domain_items")
TABLE_CATALOG_ITEMS_COLLECTION = os.getenv(
    "MONGO_TABLE_CATALOG_ITEMS_COLLECTION",
    "manufacturing_table_catalog_items",
)
LLM_API_KEY = os.getenv("LLM_API_KEY", "aaaaaa")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

VALID_GBNS = ("products", "process_groups", "terms", "datasets", "metrics", "join_rules")
VALID_COLUMN_TYPES = {"string", "number", "date", "datetime", "boolean"}
VALID_JOIN_TYPES = {"left", "inner", "right", "outer"}
VALID_CALCULATION_MODES = {
    "",
    "ratio",
    "difference",
    "sum",
    "mean",
    "count",
    "condition_flag",
    "threshold_flag",
    "custom",
}
