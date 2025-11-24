"""
Validation service - Input validation and constraints
"""
import re

# GCS bucket name constraints
MIN_BUCKET_NAME_LENGTH = 3
MAX_BUCKET_NAME_LENGTH = 63
MAX_OBJECT_NAME_LENGTH = 1024

# Bucket name pattern: lowercase letters, digits, hyphens, periods, underscores
# Must start and end with alphanumeric
BUCKET_NAME_PATTERN = r'^[a-z0-9][a-z0-9._-]*[a-z0-9]$'


def validate_bucket_name(name: str) -> tuple[bool, str]:
    """
    Validate bucket name according to GCS rules
    
    Args:
        name: Bucket name to validate
        
    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Bucket name cannot be empty"
    
    # Check length constraints
    if not _is_valid_bucket_length(name):
        return False, f"Bucket name must be between {MIN_BUCKET_NAME_LENGTH} and {MAX_BUCKET_NAME_LENGTH} characters"
    
    # Check character constraints (unless single character bucket)
    if not _matches_bucket_pattern(name):
        return False, "Bucket name must contain only lowercase letters, digits, hyphens, and periods"
    
    return True, ""


def validate_object_name(name: str) -> tuple[bool, str]:
    """
    Validate object name according to GCS rules
    
    Args:
        name: Object name to validate
        
    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Object name cannot be empty"
    
    if len(name) > MAX_OBJECT_NAME_LENGTH:
        return False, f"Object name must be at most {MAX_OBJECT_NAME_LENGTH} characters"
    
    return True, ""


def validate_content_type(content_type: str) -> tuple[bool, str]:
    """
    Validate content type format (type/subtype)
    
    Args:
        content_type: Content type to validate
        
    Returns:
        (is_valid, error_message)
    """
    if not content_type:
        return False, "Content type cannot be empty"
    
    if "/" not in content_type:
        return False, "Content type must be in format type/subtype"
    
    return True, ""


# ========== Private Helper Functions ==========

def _is_valid_bucket_length(name: str) -> bool:
    """Check if bucket name length is within allowed range"""
    return MIN_BUCKET_NAME_LENGTH <= len(name) <= MAX_BUCKET_NAME_LENGTH


def _matches_bucket_pattern(name: str) -> bool:
    """
    Check if bucket name matches GCS naming pattern
    Single character names are allowed and skip pattern validation
    """
    if len(name) == 1:
        return True
    
    return re.match(BUCKET_NAME_PATTERN, name) is not None
