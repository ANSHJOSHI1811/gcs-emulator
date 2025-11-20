"""
Datetime utilities - ISO8601 formatting
"""
from datetime import datetime


def to_iso8601(dt: datetime) -> str:
    """
    Convert datetime to ISO8601 string with Z suffix
    
    Args:
        dt: Datetime object
        
    Returns:
        ISO8601 formatted string
    """
    if dt.tzinfo is None:
        return dt.isoformat() + "Z"
    return dt.isoformat() + "Z"


def from_iso8601(date_string: str) -> datetime:
    """
    Parse ISO8601 string to datetime
    
    Args:
        date_string: ISO8601 formatted string
        
    Returns:
        Datetime object
    """
    if date_string.endswith("Z"):
        date_string = date_string[:-1]
    return datetime.fromisoformat(date_string)
