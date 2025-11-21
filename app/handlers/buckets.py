"""
Bucket handlers - Flask routes for bucket operations
"""
from flask import Blueprint, request, jsonify
from app.services.bucket_service import BucketService
from app.utils.validators import is_valid_bucket_name

buckets_bp = Blueprint("buckets", __name__)


@buckets_bp.route("", methods=["GET"])
def list_buckets():
    """
    List all buckets for a project
    GET /storage/v1/b?project=my-project
    """
    try:
        project_id = request.args.get("project")
        if not project_id:
            return jsonify({"error": "Missing 'project' query parameter"}), 400
        
        buckets = BucketService.list_buckets(project_id)
        items = [b.to_dict() for b in buckets]
        
        return jsonify({
            "kind": "storage#buckets",
            "items": items
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@buckets_bp.route("", methods=["POST"])
def create_bucket():
    """
    Create a new bucket
    POST /storage/v1/b?project=my-project
    {
        "name": "my-bucket",
        "location": "US",
        "storageClass": "STANDARD"
    }
    """
    try:
        project_id = request.args.get("project")
        if not project_id:
            return jsonify({"error": "Missing 'project' query parameter"}), 400
        
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        location = data.get("location", "US")
        storage_class = data.get("storageClass", "STANDARD")
        
        # Validate bucket name
        if not is_valid_bucket_name(name):
            return jsonify({
                "error": f"Invalid bucket name '{name}'. Must be 3-63 characters, lowercase, alphanumeric with hyphens/dots/underscores"
            }), 400
        
        bucket = BucketService.create_bucket(
            project_id=project_id,
            name=name,
            location=location,
            storage_class=storage_class
        )
        
        return jsonify(bucket.to_dict()), 201
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            return jsonify({"error": error_msg}), 409
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@buckets_bp.route("/<bucket>", methods=["GET"])
def get_bucket(bucket):
    """
    Get bucket metadata
    GET /storage/v1/b/{bucket}
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return jsonify({"error": f"Bucket '{bucket}' not found"}), 404
        
        return jsonify(bucket_obj.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@buckets_bp.route("/<bucket>", methods=["DELETE"])
def delete_bucket(bucket):
    """
    Delete a bucket (must be empty)
    DELETE /storage/v1/b/{bucket}
    """
    try:
        BucketService.delete_bucket(bucket)
        return "", 204
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            return jsonify({"error": error_msg}), 404
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
