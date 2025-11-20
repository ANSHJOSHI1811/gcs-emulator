"""
Error handlers
"""
from flask import jsonify
from app.serializers.error_serializer import serialize_error


def handle_not_found(error):
    """Handle 404 Not Found"""
    return jsonify(serialize_error(404, "Not Found", "The requested resource was not found")), 404


def handle_bad_request(error):
    """Handle 400 Bad Request"""
    return jsonify(serialize_error(400, "Bad Request", "Invalid request parameters")), 400


def handle_internal_error(error):
    """Handle 500 Internal Server Error"""
    return jsonify(serialize_error(500, "Internal Server Error", "An unexpected error occurred")), 500
