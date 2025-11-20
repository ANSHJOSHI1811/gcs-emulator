"""
Object handlers - Flask routes for object operations
"""
from flask import Blueprint, request, jsonify

objects_bp = Blueprint("objects", __name__)


@objects_bp.route("/<bucket>/o", methods=["GET"])
def list_objects(bucket):
    """List objects"""
    return jsonify({"items": []}), 200


@objects_bp.route("/<bucket>/o", methods=["POST"])
def upload_object(bucket):
    """Upload object"""
    return jsonify({"name": "object-name"}), 200


@objects_bp.route("/<bucket>/o/<path:object_name>", methods=["GET"])
def get_object(bucket, object_name):
    """Get object metadata or download"""
    alt = request.args.get("alt", "json")
    if alt == "media":
        return b"file content", 200
    return jsonify({"name": object_name}), 200


@objects_bp.route("/<bucket>/o/<path:object_name>", methods=["DELETE"])
def delete_object(bucket, object_name):
    """Delete object"""
    return "", 204
