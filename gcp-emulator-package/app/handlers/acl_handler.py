"""
ACL Handler - Phase 4

Minimal ACL endpoints (private/publicRead).
"""
from flask import Blueprint, request, jsonify
from app.services.acl_service import ACLService
from app.utils.gcs_errors import not_found_error, invalid_argument_error, internal_error

acl_bp = Blueprint("acl", __name__)


@acl_bp.route("/storage/v1/b/<bucket>/acl", methods=["PATCH"])
def update_bucket_acl(bucket):
    """
    Update bucket ACL
    
    PATCH /storage/v1/b/{bucket}/acl
    Body: { "acl": "private" | "publicRead" }
    """
    try:
        data = request.get_json()
        if not data or "acl" not in data:
            return invalid_argument_error("Missing 'acl' field in request body")
        
        acl = data["acl"]
        updated_bucket = ACLService.set_bucket_acl(bucket, acl)
        
        return jsonify({
            "kind": "storage#bucket",
            "name": updated_bucket.name,
            "acl": updated_bucket.acl
        }), 200
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return not_found_error(bucket, "bucket")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Failed to update bucket ACL: {str(e)}")


@acl_bp.route("/storage/v1/b/<bucket>/acl", methods=["GET"])
def get_bucket_acl(bucket):
    """
    Get bucket ACL
    
    GET /storage/v1/b/{bucket}/acl
    """
    try:
        acl = ACLService.get_bucket_acl(bucket)
        
        return jsonify({
            "kind": "storage#bucketAccessControl",
            "bucket": bucket,
            "acl": acl
        }), 200
        
    except ValueError as e:
        return not_found_error(bucket, "bucket")
    except Exception as e:
        return internal_error(f"Failed to get bucket ACL: {str(e)}")


@acl_bp.route("/storage/v1/b/<bucket>/o/<path:object_name>/acl", methods=["PATCH"])
def update_object_acl(bucket, object_name):
    """
    Update object ACL
    
    PATCH /storage/v1/b/{bucket}/o/{object}/acl
    Body: { "acl": "private" | "publicRead" }
    """
    try:
        data = request.get_json()
        if not data or "acl" not in data:
            return invalid_argument_error("Missing 'acl' field in request body")
        
        acl = data["acl"]
        updated_object = ACLService.set_object_acl(bucket, object_name, acl)
        
        return jsonify({
            "kind": "storage#objectAccessControl",
            "bucket": bucket,
            "object": object_name,
            "generation": str(updated_object.generation),
            "acl": updated_object.acl
        }), 200
        
    except ValueError as e:
        error_msg = str(e)
        if "bucket" in error_msg.lower() and "not found" in error_msg.lower():
            return not_found_error(bucket, "bucket")
        elif "object" in error_msg.lower() and "not found" in error_msg.lower():
            return not_found_error(object_name, "object")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Failed to update object ACL: {str(e)}")


@acl_bp.route("/storage/v1/b/<bucket>/o/<path:object_name>/acl", methods=["GET"])
def get_object_acl(bucket, object_name):
    """
    Get object ACL
    
    GET /storage/v1/b/{bucket}/o/{object}/acl
    """
    try:
        acl = ACLService.get_object_acl(bucket, object_name)
        
        return jsonify({
            "kind": "storage#objectAccessControl",
            "bucket": bucket,
            "object": object_name,
            "acl": acl
        }), 200
        
    except ValueError as e:
        error_msg = str(e)
        if "bucket" in error_msg.lower() and "not found" in error_msg.lower():
            return not_found_error(bucket, "bucket")
        elif "object" in error_msg.lower() and "not found" in error_msg.lower():
            return not_found_error(object_name, "object")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Failed to get object ACL: {str(e)}")
