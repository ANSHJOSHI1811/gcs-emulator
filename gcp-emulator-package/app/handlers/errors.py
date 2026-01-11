"""
Error handlers - Global error handling
"""
from flask import jsonify
from app.utils.gcs_errors import not_found_error, invalid_argument_error, internal_error


def error_response(status_code: int, error_code: str, message: str):
    """
    Create a standard GCP-style error response
    
    Args:
        status_code: HTTP status code
        error_code: GCP error code (e.g. NOT_FOUND, INVALID_ARGUMENT)
        message: Error message
    
    Returns:
        JSON error response with status code
    """
    return jsonify({
        "error": {
            "code": status_code,
            "message": message,
            "status": error_code,
        }
    }), status_code


def handle_not_found(error):
    """Handle 404 Not Found errors"""
    return not_found_error("resource", "resource")


def handle_bad_request(error):
    """Handle 400 Bad Request errors"""
    return invalid_argument_error("Bad request")


def handle_internal_error(error):
    """Handle 500 Internal Server Error"""
    return internal_error("Internal server error")
