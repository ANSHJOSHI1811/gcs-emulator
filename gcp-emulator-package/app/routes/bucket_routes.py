"""
Bucket routes - Router stage (HTTP → Endpoint mapping)
Maps HTTP methods and paths to bucket handler functions
"""
from flask import Blueprint, request
from app.handlers.bucket_handler import (
    handle_list_buckets,
    handle_create_bucket,
    handle_get_bucket,
    handle_delete_bucket,
    handle_update_bucket
)

buckets_bp = Blueprint("buckets", __name__)


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
