"""
Bucket handler - Handler stage (Parse request, validate, invoke service)
Extracts data from HTTP requests and delegates to service layer
"""
import time
from flask import jsonify
from app.services.bucket_service import BucketService
from app.validators.bucket_validators import is_valid_bucket_name
from app.logging import log_handler_stage
from app.utils.gcs_errors import (
    not_found_error,
    invalid_argument_error,
    conflict_error,
    internal_error
)


def handle_list_buckets(request):
    """
    Handle list buckets request
    Parses project parameter and returns bucket list
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handler list_buckets processing request",
        details={
            "handler": "handle_list_buckets"
        }
    )
    
    try:
        project_id = request.args.get("project")
        if not project_id:
            return jsonify({"error": {"message": "Missing 'project' query parameter"}}), 400
        
        buckets = BucketService.list_buckets(project_id)
        items = [b.to_dict() for b in buckets]
        
        duration_ms = (time.time() - start_time) * 1000
        log_handler_stage(
            message="Handler list_buckets completed successfully",
            duration_ms=duration_ms,
            details={
                "project_id": project_id,
                "buckets_found": len(buckets),
                "http_status": 200
            }
        )
        
        return jsonify({
            "kind": "storage#buckets",
            "items": items
        }), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


def handle_create_bucket(request):
    """
    Handle create bucket request
    Parses request body, validates input, creates bucket via service
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handler bucket_create processing request",
        details={
            "handler": "handle_create_bucket",
            "content_type": request.content_type
        }
    )
    
    try:
        project_id = request.args.get("project")
        if not project_id:
            return jsonify({"error": {"message": "Missing 'project' query parameter"}}), 400
        
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        location = data.get("location", "US")
        storage_class = data.get("storageClass", "STANDARD")
        versioning_enabled = data.get("versioning", {}).get("enabled", False)
        
        log_handler_stage(
            message="Request body parsed and validated",
            details={
                "parsed_fields": ["project_id", "name", "location", "storageClass", "versioning"],
                "project_id": project_id,
                "bucket_name": name,
                "location": location,
                "storage_class": storage_class,
                "versioning_enabled": versioning_enabled
            }
        )
        
        # Validate bucket name
        if not is_valid_bucket_name(name):
            return invalid_argument_error(
                f"Invalid bucket name '{name}'. Must be 3-63 characters, lowercase, alphanumeric with hyphens/dots/underscores"
            )
        
        log_handler_stage(
            message="Delegating to BucketService.create_bucket",
            details={
                "service": "BucketService",
                "method": "create_bucket"
            }
        )
        
        bucket = BucketService.create_bucket(
            project_id=project_id,
            name=name,
            location=location,
            storage_class=storage_class,
            versioning_enabled=versioning_enabled
        )
        
        duration_ms = (time.time() - start_time) * 1000
        log_handler_stage(
            message="Handler create_bucket completed successfully",
            duration_ms=duration_ms,
            details={
                "created_bucket_id": bucket.id,
                "http_status": 201
            }
        )
        
        return jsonify(bucket.to_dict()), 201
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            return conflict_error(error_msg)
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


def handle_get_bucket(request, bucket_name):
    """
    Handle get bucket request
    Retrieves bucket metadata from service layer
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handler get_bucket processing request",
        details={
            "handler": "handle_get_bucket",
            "bucket_name": bucket_name
        }
    )
    
    try:
        bucket_obj = BucketService.get_bucket(bucket_name)
        if not bucket_obj:
            duration_ms = (time.time() - start_time) * 1000
            log_handler_stage(
                message="Handler get_bucket completed - bucket not found",
                duration_ms=duration_ms,
                details={
                    "bucket_name": bucket_name,
                    "found": False,
                    "http_status": 404
                }
            )
            return not_found_error(bucket_name, "bucket")
        
        duration_ms = (time.time() - start_time) * 1000
        log_handler_stage(
            message="Handler get_bucket completed successfully",
            duration_ms=duration_ms,
            details={
                "bucket_name": bucket_name,
                "bucket_id": bucket_obj.id,
                "http_status": 200
            }
        )
        
        return jsonify(bucket_obj.to_dict()), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


def handle_delete_bucket(request, bucket_name):
    """
    Handle delete bucket request
    Deletes bucket via service layer (enforces empty bucket rule)
    """
    try:
        BucketService.delete_bucket(bucket_name)
        return "", 204
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            return conflict_error(error_msg)
        if "not found" in error_msg.lower():
            return not_found_error(bucket_name, "bucket")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


def handle_update_bucket(request, bucket_name):
    """
    Handle update bucket request (PATCH)
    Updates bucket metadata like versioning
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handler update_bucket processing request",
        details={
            "handler": "handle_update_bucket",
            "bucket_name": bucket_name
        }
    )
    
    try:
        data = request.get_json() or {}
        
        # Extract versioning configuration if present
        versioning_enabled = None
        if "versioning" in data:
            versioning_enabled = data["versioning"].get("enabled", False)
        
        # Update bucket via service
        bucket_obj = BucketService.update_bucket(
            bucket_name=bucket_name,
            versioning_enabled=versioning_enabled
        )
        
        duration_ms = (time.time() - start_time) * 1000
        log_handler_stage(
            message="Handler update_bucket completed successfully",
            duration_ms=duration_ms,
            details={
                "bucket_name": bucket_name,
                "versioning_enabled": versioning_enabled,
                "http_status": 200
            }
        )
        
        return jsonify(bucket_obj.to_dict()), 200
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return not_found_error(bucket_name, "bucket")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")
