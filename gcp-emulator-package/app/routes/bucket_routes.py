"""
Bucket routes - Router stage (HTTP → Endpoint mapping)
Maps HTTP methods and paths to bucket handler functions
"""
from flask import Blueprint, request, jsonify
from app.handlers.bucket_handler import (
    handle_list_buckets,
    handle_create_bucket,
    handle_get_bucket,
    handle_delete_bucket,
    handle_update_bucket
)
from app.utils.gcs_errors import invalid_argument_error
from app.utils.signer import SignedURLService

buckets_bp = Blueprint("buckets", __name__)


@buckets_bp.route("/<bucket_name>/o/<path:object_name>/signedUrl", methods=["POST"])
def generate_signed_url(bucket_name, object_name):
    """
    Generate a signed URL for object access
    
    POST /storage/v1/b/{bucket}/o/{object}/signedUrl
    Body: {
        "method": "GET" | "PUT",
        "expiresIn": 3600
    }
    
    Returns:
        {
            "signedUrl": "http://localhost:8080/signed/bucket/object?...",
            "expiresAt": "2025-12-06T12:00:00Z"
        }
    """
    try:
        data = request.get_json() or {}
        method = data.get('method', 'GET')
        expires_in = data.get('expiresIn', 3600)
        
        # Validate method
        if method not in ['GET', 'PUT']:
            return invalid_argument_error("Method must be GET or PUT")
        
        # Generate signed URL
        signed_url = SignedURLService.generate_signed_url(
            method=method,
            bucket=bucket_name,
            object_name=object_name,
            expires_in=expires_in
        )
        
        # Calculate expiry timestamp
        import time
        from datetime import datetime, timezone
        expiry_timestamp = int(time.time()) + expires_in
        expiry_dt = datetime.fromtimestamp(expiry_timestamp, tz=timezone.utc)
        
        return jsonify({
            "signedUrl": signed_url,
            "expiresAt": expiry_dt.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to generate signed URL",
            "message": str(e)
        }), 500


@buckets_bp.route("", methods=["GET"])
def list_buckets():
    """
    List all buckets for a project
    GET /storage/v1/b?project=my-project
    """
    return handle_list_buckets(request)


@buckets_bp.route("", methods=["POST"])
def create_bucket():
    """
    Create a new bucket
    POST /storage/v1/b?project=my-project
    """
    return handle_create_bucket(request)


@buckets_bp.route("/<bucket>", methods=["GET"])
def get_bucket(bucket):
    """
    Get bucket metadata
    GET /storage/v1/b/{bucket}
    """
    return handle_get_bucket(request, bucket)


@buckets_bp.route("/<bucket>", methods=["DELETE"])
def delete_bucket(bucket):
    """
    Delete a bucket (must be empty)
    DELETE /storage/v1/b/{bucket}
    """
    return handle_delete_bucket(request, bucket)


@buckets_bp.route("/<bucket>", methods=["PATCH"])
def update_bucket(bucket):
    """
    Update bucket metadata (e.g., enable versioning)
    PATCH /storage/v1/b/{bucket}
    """
    return handle_update_bucket(request, bucket)
