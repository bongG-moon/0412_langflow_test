from __future__ import annotations

from typing import Any, Dict

from .config import DEFAULT_DB_NAME, DOMAIN_ITEMS_COLLECTION
from .mongo import save_domain_items


def save_domain_preview(
    preview: Dict[str, Any],
    db_name: str = DEFAULT_DB_NAME,
    collection_name: str = DOMAIN_ITEMS_COLLECTION,
    mongo_uri: str | None = None,
) -> Dict[str, Any]:
    items = preview.get("normalized_domain_items") if isinstance(preview.get("normalized_domain_items"), list) else []
    validation = preview.get("validation") if isinstance(preview.get("validation"), dict) else {}
    if validation and not validation.get("can_save", False):
        return {
            "saved": False,
            "saved_count": 0,
            "errors": ["Validation has blocking errors. Fix the preview before saving."],
        }
    return save_domain_items(items, db_name=db_name, collection_name=collection_name, mongo_uri=mongo_uri)
