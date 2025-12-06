"""
CORS configuration handler for buckets
Implements GET/PUT endpoints for bucket CORS rules
"""
from flask import Blueprint, request, jsonify
import json
from app.services.bucket_service import BucketService
from app.utils.gcs_errors import (
    not_found_error,
    invalid_argument_error,
    internal_error
)

cors_bp = Blueprint("cors", __name__)


@cors_bp.route("/b/<bucket>/cors", methods=["GET"])
def get_bucket_cors(bucket):
    """
    Get CORS configuration for a bucket
    GET /storage/v1/b/{bucket}/cors
    
    Returns:
        JSON array of CORS rules or empty array if none configured
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        # Parse CORS configuration from JSON text column
        cors_config = []
        if bucket_obj.cors:
            try:
                cors_config = json.loads(bucket_obj.cors)
            except json.JSONDecodeError:
                pass  # Return empty array if invalid JSON
        
        return jsonify({
            "kind": "storage#bucket#cors",
            "cors": cors_config
        }), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@cors_bp.route("/b/<bucket>/cors", methods=["PUT"])
def update_bucket_cors(bucket):
    """
    Update CORS configuration for a bucket
    PUT /storage/v1/b/{bucket}/cors
    
    Request body: Array of CORS rule objects
    [
        {
            "origin": ["https://example.com"],
            "method": ["GET", "POST"],
            "responseHeader": ["Content-Type"],
            "maxAgeSeconds": 3600
        }
    ]
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        data = request.get_json() or {}
        cors_rules = data.get("cors", [])
        
        # Validate CORS rules structure
        if not isinstance(cors_rules, list):
            return invalid_argument_error("CORS configuration must be an array")
        
        for rule in cors_rules:
            if not isinstance(rule, dict):
                return invalid_argument_error("Each CORS rule must be an object")
            
            # Validate required fields
            if "origin" not in rule or "method" not in rule:
                return invalid_argument_error("CORS rule must have 'origin' and 'method'")
            
            if not isinstance(rule["origin"], list) or not isinstance(rule["method"], list):
                return invalid_argument_error("'origin' and 'method' must be arrays")
        
        # Store CORS configuration as JSON text
        from app.factory import db
        bucket_obj.cors = json.dumps(cors_rules) if cors_rules else None
        db.session.commit()
        
        return jsonify({
            "kind": "storage#bucket#cors",
            "cors": cors_rules
        }), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@cors_bp.route("/b/<bucket>/cors", methods=["DELETE"])
def delete_bucket_cors(bucket):
    """
    Delete CORS configuration for a bucket
    DELETE /storage/v1/b/{bucket}/cors
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        from app.factory import db
        bucket_obj.cors = None
        db.session.commit()
        
        return "", 204
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")
