"""Supabase storage helper."""

from functools import lru_cache
from supabase import create_client, Client
from ..config import config


@lru_cache()
def get_supabase_client() -> Client:
    """Get cached Supabase client instance."""
    if not config.supabase_url or not config.supabase_service_role_key:
        raise ValueError("Supabase credentials not configured")

    return create_client(
        config.supabase_url,
        config.supabase_service_role_key
    )
