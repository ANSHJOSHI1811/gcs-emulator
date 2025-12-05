"""
Bucket validation functions
Validates bucket names according to GCS naming rules
"""
import re


def is_valid_bucket_name(name: str) -> bool:
    """
    Validate GCS bucket name according to naming rules:
    - Must be 3-63 characters
    - Can contain lowercase letters, numbers, hyphens, underscores, dots
    - Must start and end with alphanumeric character
    
    Args:
        name: Bucket name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    
    # Length check
    if len(name) < 3 or len(name) > 63:
        return False
    
    # Pattern check: lowercase alphanumeric + hyphens/dots/underscores
    # Must start and end with alphanumeric
    pattern = r'^[a-z0-9][a-z0-9._-]*[a-z0-9]$'
    
    if not re.match(pattern, name):
        return False
    
    return True
