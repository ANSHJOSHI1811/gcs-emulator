"""
Validation service - Input validation and constraints
"""
import re


def validate_bucket_name(name: str) -> tuple[bool, str]:
    """
    Validate bucket name according to GCS rules
    - 3-63 characters
    - Must start and end with lowercase letter or digit
    - Can contain lowercase letters, digits, hyphens, underscores, periods
    
    Args:
        name: Bucket name to validate
        
    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Bucket name cannot be empty"
    
    if len(name) < 3 or len(name) > 63:
        return False, "Bucket name must be between 3 and 63 characters"
    
    if not re.match(r'^[a-z0-9][a-z0-9._-]*[a-z0-9]$', name) and len(name) > 1:
        if len(name) == 1:
            return True, ""
        return False, "Bucket name must contain only lowercase letters, digits, hyphens, and periods"
    
    return True, ""


def validate_object_name(name: str) -> tuple[bool, str]:
    """
    Validate object name
    - Max 1024 characters
    - UTF-8 encoded
    
    Args:
        name: Object name to validate
        
    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Object name cannot be empty"
    
    if len(name) > 1024:
        return False, "Object name must be at most 1024 characters"
    
    return True, ""


def validate_content_type(content_type: str) -> tuple[bool, str]:
    """
    Validate content type
    
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
