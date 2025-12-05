"""
Health check handler - Simple health endpoint
"""
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint
    GET /health
    """
    return jsonify({"status": "ok"}), 200
