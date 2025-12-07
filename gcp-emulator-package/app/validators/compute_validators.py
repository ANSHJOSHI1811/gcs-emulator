"""
Compute Engine validation functions
Validates instance names, zones, and machine types according to GCE rules
"""
import re
from app.models.compute import MachineType


def is_valid_instance_name(name: str) -> bool:
    """
    Validate GCE instance name according to naming rules:
    - Must be 1-63 characters
    - Can contain lowercase letters, numbers, and hyphens
    - Must start with a lowercase letter
    - Must end with a lowercase letter or number
    
    Args:
        name: Instance name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    
    # Length check
    if len(name) < 1 or len(name) > 63:
        return False
    
    # Pattern check: must start with lowercase letter, end with letter or number
    # Can contain lowercase letters, numbers, and hyphens
    pattern = r'^[a-z][a-z0-9-]*[a-z0-9]$'
    
    # Allow single character names (just lowercase letter)
    if len(name) == 1:
        return name.isalpha() and name.islower()
    
    if not re.match(pattern, name):
        return False
    
    # Cannot have consecutive hyphens
    if '--' in name:
        return False
    
    return True


def is_valid_zone(zone: str) -> bool:
    """
    Validate GCE zone format
    
    Expected format: {region}-{zone_letter}
    Examples: us-central1-a, europe-west1-b, asia-east1-c
    
    Args:
        zone: Zone name to validate
        
    Returns:
        True if valid format, False otherwise
    """
    if not zone:
        return False
    
    # Pattern: region (lowercase + hyphens) followed by dash and zone letter
    pattern = r'^[a-z]+-[a-z0-9]+-[a-z]$'
    
    return bool(re.match(pattern, zone))


def is_valid_machine_type(machine_type: str) -> bool:
    """
    Validate machine type exists in catalog
    
    Args:
        machine_type: Machine type to validate
        
    Returns:
        True if valid, False otherwise
    """
    return MachineType.is_valid(machine_type)


def get_instance_name_error(name: str) -> str:
    """
    Get detailed error message for invalid instance name
    
    Args:
        name: Instance name to validate
        
    Returns:
        Error message string, or empty string if valid
    """
    if not name:
        return "Instance name is required"
    
    if len(name) < 1:
        return "Instance name must be at least 1 character"
    
    if len(name) > 63:
        return "Instance name must be at most 63 characters"
    
    if len(name) == 1:
        if not (name.isalpha() and name.islower()):
            return "Single character instance name must be a lowercase letter"
        return ""
    
    if not name[0].isalpha() or not name[0].islower():
        return "Instance name must start with a lowercase letter"
    
    if not (name[-1].isalnum() and name[-1].islower()):
        return "Instance name must end with a lowercase letter or number"
    
    if '--' in name:
        return "Instance name cannot contain consecutive hyphens"
    
    # Check for invalid characters
    pattern = r'^[a-z][a-z0-9-]*[a-z0-9]$'
    if not re.match(pattern, name):
        return "Instance name can only contain lowercase letters, numbers, and hyphens"
    
    return ""


def get_zone_error(zone: str) -> str:
    """
    Get detailed error message for invalid zone
    
    Args:
        zone: Zone to validate
        
    Returns:
        Error message string, or empty string if valid
    """
    if not zone:
        return "Zone is required"
    
    pattern = r'^[a-z]+-[a-z0-9]+-[a-z]$'
    if not re.match(pattern, zone):
        return "Zone must be in format: {region}-{zone} (e.g., us-central1-a)"
    
    return ""


def get_machine_type_error(machine_type: str) -> str:
    """
    Get detailed error message for invalid machine type
    
    Args:
        machine_type: Machine type to validate
        
    Returns:
        Error message string, or empty string if valid
    """
    if not machine_type:
        return "Machine type is required"
    
    if not MachineType.is_valid(machine_type):
        available_types = list(MachineType.get_all().keys())[:5]  # Show first 5
        return f"Invalid machine type '{machine_type}'. Available types include: {', '.join(available_types)}, ..."
    
    return ""
