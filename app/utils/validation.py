"""
Input Validation và URL Sanitization
"""
from urllib.parse import urlparse
from typing import Optional, Tuple
from app.config import settings


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate URL với các kiểm tra:
    - Protocol hợp lệ (http/https)
    - Domain được phép (nếu có whitelist)
    - Format URL hợp lệ
    
    Args:
        url: URL cần validate
    
    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL không được để trống"
    
    # Kiểm tra độ dài URL
    if len(url) > 2048:
        return False, "URL quá dài (tối đa 2048 ký tự)"
    
    # Kiểm tra protocol
    if not url.startswith(("http://", "https://")):
        return False, "URL phải bắt đầu với http:// hoặc https://"
    
    try:
        parsed = urlparse(url)
        
        # Kiểm tra có domain không
        if not parsed.netloc:
            return False, "URL không hợp lệ: thiếu domain"
        
        # Kiểm tra domain whitelist (nếu có)
        if settings.ALLOWED_DOMAINS and settings.ALLOWED_DOMAINS[0]:
            allowed_domains = [d.strip().lower() for d in settings.ALLOWED_DOMAINS if d.strip()]
            domain = parsed.netloc.lower()
            
            # Remove port nếu có
            if ":" in domain:
                domain = domain.split(":")[0]
            
            # Kiểm tra domain có trong whitelist không
            domain_allowed = any(
                domain == allowed or domain.endswith(f".{allowed}")
                for allowed in allowed_domains
            )
            
            if not domain_allowed:
                return False, f"Domain không được phép. Chỉ hỗ trợ: {', '.join(allowed_domains)}"
        
        # Kiểm tra các ký tự nguy hiểm (cơ bản)
        dangerous_chars = ["<", ">", '"', "'", "`"]
        if any(char in url for char in dangerous_chars):
            return False, "URL chứa ký tự không hợp lệ"
        
        return True, None
        
    except Exception as e:
        return False, f"Lỗi validate URL: {str(e)}"


def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize input string
    
    Args:
        input_str: String cần sanitize
        max_length: Độ dài tối đa
    
    Returns:
        str: Sanitized string
    """
    if not input_str:
        return ""
    
    # Chuyển sang string nếu không phải
    if not isinstance(input_str, str):
        input_str = str(input_str)
    
    # Trim whitespace
    input_str = input_str.strip()
    
    # Giới hạn độ dài
    if len(input_str) > max_length:
        input_str = input_str[:max_length]
    
    # Remove các ký tự control
    input_str = "".join(char for char in input_str if ord(char) >= 32 or char in "\n\r\t")
    
    return input_str
