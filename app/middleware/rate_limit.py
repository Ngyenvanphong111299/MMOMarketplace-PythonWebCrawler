"""
Rate Limiting Middleware
Giới hạn số lượng requests từ mỗi IP
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import time
from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware để giới hạn rate limit theo IP
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Store: {ip: [(timestamp, count)]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 300  # 5 phút
        self.last_cleanup = time.time()
    
    def _get_client_ip(self, request: Request) -> str:
        """Lấy IP address từ request"""
        # Check X-Forwarded-For header (nếu có proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback về client host
        return request.client.host if request.client else "unknown"
    
    def _cleanup_old_requests(self):
        """Xóa các request cũ hơn 1 giờ"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # 1 giờ trước
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                (ts, count) for ts, count in self.requests[ip] if ts > cutoff_time
            ]
            if not self.requests[ip]:
                del self.requests[ip]
        
        self.last_cleanup = current_time
    
    def _check_rate_limit(self, ip: str, path: str) -> Tuple[bool, int]:
        """
        Kiểm tra rate limit cho IP
        
        Returns:
            Tuple[bool, int]: (allowed, remaining_requests)
        """
        current_time = time.time()
        
        # Cleanup old requests
        self._cleanup_old_requests()
        
        # Xác định limit dựa trên endpoint
        if "/api/crawl-detail" in path or "/api/test-scheduler" in path or "/api/scheduler-status" in path:
            # Protected endpoints: 30 requests/minute
            limit = 30
            window = 60  # 1 phút
        else:
            # Public endpoints: 60 requests/minute
            limit = settings.RATE_LIMIT_PER_MINUTE
            window = 60  # 1 phút
        
        # Lọc requests trong window
        window_start = current_time - window
        self.requests[ip] = [
            (ts, count) for ts, count in self.requests[ip] if ts > window_start
        ]
        
        # Đếm số requests trong window
        request_count = sum(count for _, count in self.requests[ip])
        
        # Kiểm tra limit
        if request_count >= limit:
            return False, 0
        
        # Thêm request mới
        self.requests[ip].append((current_time, 1))
        remaining = limit - request_count - 1
        
        return True, remaining
    
    async def dispatch(self, request: Request, call_next):
        """Xử lý request và kiểm tra rate limit"""
        
        # Bỏ qua rate limiting cho health check và root endpoint
        if request.url.path in ["/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Kiểm tra nếu rate limiting được bật
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Lấy client IP
        client_ip = self._get_client_ip(request)
        
        # Kiểm tra rate limit
        allowed, remaining = self._check_rate_limit(client_ip, request.url.path)
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "detail": "Quá nhiều requests. Vui lòng thử lại sau.",
                    "retry_after": 60
                },
                headers={
                    "X-RateLimit-Limit": "60",
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60"
                }
            )
        
        # Thêm rate limit headers vào response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = "60"
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
