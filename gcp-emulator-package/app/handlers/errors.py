"""
Error handlers - Global error handling
"""
from flask import jsonify
from app.utils.gcs_errors import not_found_error, invalid_argument_error, internal_error


def handle_not_found(error):
    """Handle 404 Not Found errors"""
    return not_found_error("resource", "resource")


def handle_bad_request(error):
    """Handle 400 Bad Request errors"""
    return invalid_argument_error("Bad request")


def handle_internal_error(error):
    """Handle 500 Internal Server Error"""
    return internal_error("Internal server error")
