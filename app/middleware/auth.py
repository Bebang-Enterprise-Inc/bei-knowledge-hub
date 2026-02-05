"""Authentication middleware - API key + Frappe session support."""

from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from ..config import config

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(request: Request):
    """
    Verify API key or Frappe session.

    Supports dual authentication:
    1. X-API-Key header
    2. Frappe session cookie (sid)
    """
    # Check API key header
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key == config.api_key:
        return True

    # Check Frappe session cookie
    sid = request.cookies.get("sid")
    if sid:
        # TODO: Validate sid with Frappe API
        # For now, accept any sid
        return True

    # No valid auth found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required: Provide X-API-Key header or valid Frappe session"
    )
