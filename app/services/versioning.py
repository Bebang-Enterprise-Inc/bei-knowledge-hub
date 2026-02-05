"""Document versioning and incremental updates."""

import hashlib
from typing import Dict, Any, List
from .storage import get_supabase_client


def detect_changes(old_content: str, new_content: str) -> bool:
    """Detect if content changed via checksum."""
    old_checksum = hashlib.sha256(old_content.encode()).hexdigest()
    new_checksum = hashlib.sha256(new_content.encode()).hexdigest()
    return old_checksum != new_checksum


def create_version(document_id: str, new_content: str, metadata: Dict[str, Any] = None) -> str:
    """Create new document version."""
    supabase = get_supabase_client()

    # Get current document
    current_doc = supabase.table("kb_documents")\
        .select("*")\
        .eq("id", document_id)\
        .execute()\
        .data[0]

    # Mark old version as not latest
    supabase.table("kb_documents")\
        .update({"is_latest": False})\
        .eq("id", document_id)\
        .execute()

    # Create new version
    new_version = {
        "title": current_doc["title"],
        "source_type": current_doc["source_type"],
        "source_path": current_doc["source_path"],
        "file_id": current_doc["file_id"],
        "version": current_doc["version"] + 1,
        "previous_version_id": document_id,
        "is_latest": True,
        "content_checksum": hashlib.sha256(new_content.encode()).hexdigest(),
        "status": "processing"
    }

    if metadata:
        new_version.update(metadata)

    response = supabase.table("kb_documents")\
        .insert(new_version)\
        .execute()

    return response.data[0]["id"]
