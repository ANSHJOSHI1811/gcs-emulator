"""
Error handlers - Global error handling
"""
from flask import jsonify


def handle_not_found(error):
    """Handle 404 Not Found errors"""
    return jsonify({"error": {"message": "Resource not found"}}), 404


def handle_bad_request(error):
    """Handle 400 Bad Request errors"""
    return jsonify({"error": {"message": "Bad request"}}), 400


def handle_internal_error(error):
    """Handle 500 Internal Server Error"""
    return jsonify({"error": {"message": "Internal server error"}}), 500
