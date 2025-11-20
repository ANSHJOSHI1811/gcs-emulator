"""
Error serializer - Format error responses
"""


def serialize_error(status_code: int, error_code: str, message: str) -> dict:
    """
    Serialize error response to Google Cloud API format
    
    Args:
        status_code: HTTP status code
        error_code: Error code (e.g., "NotFound")
        message: Error message
        
    Returns:
        Dictionary with error response
    """
    return {
        "error": {
            "code": status_code,
            "message": message,
            "errors": [
                {
                    "domain": "global",
                    "reason": error_code,
                    "message": message
                }
            ]
        }
    }
