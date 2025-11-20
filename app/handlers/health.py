"""
Health check endpoints
"""
from datetime import datetime
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@health_bp.route("/ready", methods=["GET"])
def ready():
    """Readiness check endpoint"""
    from app.factory import db
    try:
        db.session.execute("SELECT 1")
        return jsonify({
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 503
