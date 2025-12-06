"""
GCS-Compatible Error Response Utility

Standardizes error responses to match Google Cloud Storage JSON API format.
All errors should follow this structure:
{
  "error": {
    "code": <HTTP_CODE>,
    "message": "<string>",
    "errors": [
      {
        "message": "<string>",
        "domain": "global",
        "reason": "<reason>"
      }
    ]
  }
}
"""
from flask import jsonify
from typing import Tuple


def gcs_error_response(code: int, message: str, reason: str = None) -> Tuple:
    """
    Create a GCS-compatible error response.
    
    Args:
        code: HTTP status code (404, 409, 412, etc.)
        message: Human-readable error message
        reason: GCS error reason (notFound, conflict, conditionNotMet, etc.)
        
    Returns:
        Tuple of (jsonify response, status code)
    """
    if reason is None:
        reason = _default_reason_for_code(code)
    
    error_response = {
        "error": {
            "code": code,
            "message": message,
            "errors": [
                {
                    "message": message,
                    "domain": "global",
                    "reason": reason
                }
            ]
        }
    }
    
    return jsonify(error_response), code


def _default_reason_for_code(code: int) -> str:
    """Map HTTP status code to GCS error reason."""
    reason_map = {
        400: "invalid",
        404: "notFound",
        409: "conflict",
        412: "conditionNotMet",
        500: "internalError"
    }
    return reason_map.get(code, "backendError")


# Convenience functions for common errors
def not_found_error(resource: str, resource_type: str = "resource") -> Tuple:
    """404 Not Found error."""
    return gcs_error_response(
        404,
        f"The {resource_type} '{resource}' does not exist.",
        "notFound"
    )


def conflict_error(message: str) -> Tuple:
    """409 Conflict error."""
    return gcs_error_response(409, message, "conflict")


def precondition_failed_error(message: str) -> Tuple:
    """412 Precondition Failed error."""
    return gcs_error_response(412, message, "conditionNotMet")


def invalid_argument_error(message: str) -> Tuple:
    """400 Bad Request error."""
    return gcs_error_response(400, message, "invalid")


def internal_error(message: str = "Internal server error") -> Tuple:
    """500 Internal Server Error."""
    return gcs_error_response(500, message, "internalError")
