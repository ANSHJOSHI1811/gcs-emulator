"""
Validators - Input validation utilities
"""
import re


def is_valid_bucket_name(name: str) -> bool:
    """Validate bucket name"""
    if not name or len(name) < 3 or len(name) > 63:
        return False
    return re.match(r'^[a-z0-9][a-z0-9._-]*[a-z0-9]$', name) is not None


def is_valid_object_name(name: str) -> bool:
    """Validate object name"""
    if not name or len(name) > 1024:
        return False
    return True


def is_valid_content_type(content_type: str) -> bool:
    """Validate content type"""
    if not content_type or "/" not in content_type:
        return False
    return True
