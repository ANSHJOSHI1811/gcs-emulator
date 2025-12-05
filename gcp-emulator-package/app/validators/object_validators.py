"""
Object validation functions
Validates object names according to GCS naming rules
"""


def is_valid_object_name(name: str) -> bool:
    """
    Validate GCS object name according to naming rules:
    - Must be 1-1024 characters
    - Cannot contain carriage return or line feed
    - Avoid control characters
    
    Args:
        name: Object name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    
    # Length check
    if len(name) < 1 or len(name) > 1024:
        return False
    
    # Check for disallowed characters
    if '\r' in name or '\n' in name:
        return False
    
    return True
