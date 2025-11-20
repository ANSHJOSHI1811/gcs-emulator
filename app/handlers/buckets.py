"""
Bucket handlers - Flask routes for bucket operations
"""
from flask import Blueprint, request, jsonify

buckets_bp = Blueprint("buckets", __name__)


@buckets_bp.route("", methods=["GET"])
def list_buckets():
    """List buckets"""
    return jsonify({"items": []}), 200


@buckets_bp.route("", methods=["POST"])
def create_bucket():
    """Create bucket"""
    return jsonify({"name": "bucket-name"}), 200


@buckets_bp.route("/<bucket>", methods=["GET"])
def get_bucket(bucket):
    """Get bucket"""
    return jsonify({"name": bucket}), 200


@buckets_bp.route("/<bucket>", methods=["DELETE"])
def delete_bucket(bucket):
    """Delete bucket"""
    return "", 204
