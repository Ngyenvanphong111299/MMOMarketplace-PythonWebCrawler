"""
API Key Authentication System
Sử dụng hashing để bảo mật API key
"""
import hashlib
import hmac
from typing import Optional
from app.config import settings


def hash_api_key(api_key: str) -> str:
    """
    Hash API key sử dụng SHA-256
    
    Args:
        api_key: API key cần hash
    
    Returns:
        str: Hashed API key (hex string)
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(provided_key: str) -> bool:
    """
    Verify API key bằng cách so sánh hash
    
    Args:
        provided_key: API key từ request
    
    Returns:
        bool: True nếu API key hợp lệ, False nếu không
    """
    if not provided_key:
        return False
    
    # Hash API key được cung cấp
    provided_hash = hash_api_key(provided_key)
    
    # Hash API key đúng từ config
    correct_hash = hash_api_key(settings.API_KEY)
    
    # So sánh sử dụng constant-time comparison để tránh timing attacks
    return hmac.compare_digest(provided_hash, correct_hash)


def get_api_key_hash() -> str:
    """
    Lấy hash của API key hiện tại (dùng để lưu trữ)
    
    Returns:
        str: Hashed API key
    """
    return hash_api_key(settings.API_KEY)
