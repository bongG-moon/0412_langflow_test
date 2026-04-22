from __future__ import annotations

from typing import Any, Dict

from .config import DEFAULT_DB_NAME, TABLE_CATALOG_ITEMS_COLLECTION
from .mongo import save_table_catalog


def save_table_preview(
    preview: Dict[str, Any],
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = TABLE_CATALOG_ITEMS_COLLECTION,
    mongo_uri: str | None = None,
) -> Dict[str, Any]:
    if not preview.get("can_save", False):
        return {
            "saved": False,
            "saved_count": 0,
            "errors": ["Validation has blocking errors. Fix the preview before saving."],
        }
    table_catalog = preview.get("table_catalog") if isinstance(preview.get("table_catalog"), dict) else {}
    return save_table_catalog(table_catalog, db_name=db_name, collection_name=collection_name, mongo_uri=mongo_uri)
