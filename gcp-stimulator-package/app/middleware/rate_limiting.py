"""
Rate Limiting Middleware - Prevent API abuse

Supports:
- Per-IP rate limiting
- Per-API-key rate limiting
- Per-endpoint rate limiting
- Configurable limits and windows
- Redis-backed (or in-memory fallback)
"""

import time
from functools import wraps
from collections import defaultdict, deque
from flask import request, jsonify, current_app
from datetime import datetime, timedelta


class RateLimiter:
    """
    Rate limiter with sliding window algorithm
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize rate limiter
        
        Args:
            redis_client: Optional Redis client for distributed rate limiting
        """
        self.redis = redis_client
        # Fallback to in-memory storage
        self.memory_store = defaultdict(lambda: deque())
        self.use_redis = redis_client is not None
    
    def _get_client_id(self):
        """Get unique identifier for client"""
        # Try API key first
        api_key_header = current_app.config.get('API_KEY_HEADER', 'X-API-Key')
        api_key = request.headers.get(api_key_header)
        if api_key:
            return f"apikey:{api_key[:16]}"  # Use first 16 chars
        
        # Fall back to IP address
        return f"ip:{request.remote_addr}"
    
    def _check_limit_memory(self, key: str, limit: int, window_seconds: int) -> tuple:
        """
        Check rate limit using in-memory storage
        
        Returns:
            (allowed: bool, remaining: int, reset_time: int)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Get request timestamps for this key
        timestamps = self.memory_store[key]
        
        # Remove old timestamps outside window
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()
        
        # Check if limit exceeded
        if len(timestamps) >= limit:
            # Calculate reset time (when oldest request expires)
            reset_time = int(timestamps[0] + window_seconds)
            return False, 0, reset_time
        
        # Add current request
        timestamps.append(now)
        
        remaining = limit - len(timestamps)
        reset_time = int(now + window_seconds)
        
        return True, remaining, reset_time
    
    def _check_limit_redis(self, key: str, limit: int, window_seconds: int) -> tuple:
        """
        Check rate limit using Redis storage
        
        Returns:
            (allowed: bool, remaining: int, reset_time: int)
        """
        now = int(time.time())
        window_key = f"ratelimit:{key}"
        
        # Use Redis sorted set with timestamps as scores
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(window_key, 0, now - window_seconds)
        
        # Count requests in window
        pipe.zcard(window_key)
        
        # Add current request
        pipe.zadd(window_key, {f"{now}:{time.time()}": now})
        
        # Set expiration
        pipe.expire(window_key, window_seconds + 60)
        
        results = pipe.execute()
        count = results[1]
        
        if count >= limit:
            # Get oldest timestamp for reset time
            oldest = self.redis.zrange(window_key, 0, 0, withscores=True)
            if oldest:
                reset_time = int(oldest[0][1]) + window_seconds
            else:
                reset_time = now + window_seconds
            
            # Remove the request we just added since it's denied
            self.redis.zrem(window_key, f"{now}:{time.time()}")
            
            return False, 0, reset_time
        
        remaining = limit - count - 1
        reset_time = now + window_seconds
        
        return True, remaining, reset_time
    
    def check_limit(self, key: str, limit: int, window_seconds: int) -> tuple:
        """
        Check if request is within rate limit
        
        Args:
            key: Unique key for rate limiting
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            (allowed: bool, remaining: int, reset_time: int)
        """
        if self.use_redis:
            return self._check_limit_redis(key, limit, window_seconds)
        else:
            return self._check_limit_memory(key, limit, window_seconds)


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter():
    """Get or create rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        # Try to get Redis client from app config
        redis_client = current_app.config.get('REDIS_CLIENT')
        _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter


def rate_limit(limit: int = 100, window_seconds: int = 60, per_client: bool = True):
    """
    Decorator for rate limiting endpoints
    
    Args:
        limit: Maximum requests allowed
        window_seconds: Time window in seconds
        per_client: If True, limit per client; if False, limit globally
    
    Usage:
        @app.route('/api/resource')
        @rate_limit(limit=10, window_seconds=60)
        def get_resource():
            ...
    
    Response headers:
        X-RateLimit-Limit: Maximum requests allowed
        X-RateLimit-Remaining: Requests remaining in window
        X-RateLimit-Reset: Unix timestamp when limit resets
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check if rate limiting is enabled
            if not current_app.config.get('RATE_LIMITING_ENABLED', True):
                return f(*args, **kwargs)
            
            limiter = get_rate_limiter()
            
            # Build rate limit key
            if per_client:
                client_id = limiter._get_client_id()
                endpoint = request.endpoint or 'unknown'
                key = f"{client_id}:{endpoint}"
            else:
                key = f"global:{request.endpoint or 'unknown'}"
            
            # Check limit
            allowed, remaining, reset_time = limiter.check_limit(key, limit, window_seconds)
            
            # Add rate limit headers
            headers = {
                'X-RateLimit-Limit': str(limit),
                'X-RateLimit-Remaining': str(remaining),
                'X-RateLimit-Reset': str(reset_time)
            }
            
            if not allowed:
                # Rate limit exceeded
                retry_after = reset_time - int(time.time())
                headers['Retry-After'] = str(retry_after)
                
                return jsonify({
                    'error': {
                        'code': 429,
                        'message': 'Rate limit exceeded',
                        'status': 'RESOURCE_EXHAUSTED',
                        'details': {
                            'limit': limit,
                            'window_seconds': window_seconds,
                            'retry_after_seconds': retry_after
                        }
                    }
                }), 429, headers
            
            # Execute endpoint
            response = f(*args, **kwargs)
            
            # Add headers to response
            if isinstance(response, tuple):
                if len(response) == 2:
                    data, status = response
                    return data, status, headers
                elif len(response) == 3:
                    data, status, resp_headers = response
                    resp_headers.update(headers)
                    return data, status, resp_headers
            
            return response
        
        return wrapper
    return decorator


# Predefined rate limits for different tiers
class RateLimitTiers:
    """Common rate limit configurations"""
    
    # Free tier - conservative limits
    FREE = {'limit': 10, 'window_seconds': 60}  # 10 req/min
    
    # Basic tier - moderate limits
    BASIC = {'limit': 100, 'window_seconds': 60}  # 100 req/min
    
    # Premium tier - generous limits
    PREMIUM = {'limit': 1000, 'window_seconds': 60}  # 1000 req/min
    
    # Admin tier - very high limits
    ADMIN = {'limit': 10000, 'window_seconds': 60}  # 10000 req/min
    
    # Write operations - more restrictive
    WRITE_OPS = {'limit': 20, 'window_seconds': 60}  # 20 writes/min
    
    # Read operations - less restrictive
    READ_OPS = {'limit': 200, 'window_seconds': 60}  # 200 reads/min


def rate_limit_tier(tier_name: str):
    """
    Apply predefined rate limit tier
    
    Usage:
        @app.route('/api/resource')
        @rate_limit_tier('basic')
        def get_resource():
            ...
    """
    tier = getattr(RateLimitTiers, tier_name.upper(), RateLimitTiers.BASIC)
    return rate_limit(**tier)
