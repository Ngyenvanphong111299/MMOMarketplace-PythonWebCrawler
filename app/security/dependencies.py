"""
FastAPI Dependencies cho API Key Authentication
"""
from fastapi import Header, HTTPException, status
from typing import Optional
from app.security.api_key import verify_api_key
from app.config import settings


async def verify_api_key_header(
    x_api_key: Optional[str] = Header(None, alias=settings.API_KEY_HEADER)
) -> bool:
    """
    Dependency để verify API key từ header
    
    Args:
        x_api_key: API key từ request header
    
    Returns:
        bool: True nếu API key hợp lệ
    
    Raises:
        HTTPException: 401 nếu API key không hợp lệ hoặc thiếu
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key không được cung cấp. Vui lòng thêm header X-API-Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key không hợp lệ",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return True
