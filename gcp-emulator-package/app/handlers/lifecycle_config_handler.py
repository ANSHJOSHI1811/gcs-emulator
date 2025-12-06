"""
Lifecycle Configuration Handler
Implements bucket-level lifecycle rule management using lifecycle_config column
"""
from flask import Blueprint, request, jsonify
import json
from app.services.bucket_service import BucketService
from app.utils.gcs_errors import (
    not_found_error,
    invalid_argument_error,
    internal_error
)

lifecycle_config_bp = Blueprint("lifecycle_config", __name__)


@lifecycle_config_bp.route("/b/<bucket>/lifecycle", methods=["GET"])
def get_bucket_lifecycle(bucket):
    """
    Get lifecycle configuration for a bucket
    GET /storage/v1/b/{bucket}/lifecycle
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        # Parse lifecycle configuration
        lifecycle_rules = []
        if bucket_obj.lifecycle_config:
            try:
                lifecycle_rules = json.loads(bucket_obj.lifecycle_config)
            except json.JSONDecodeError:
                pass
        
        return jsonify({
            "kind": "storage#bucket#lifecycle",
            "rule": lifecycle_rules
        }), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@lifecycle_config_bp.route("/b/<bucket>/lifecycle", methods=["PUT"])
def update_bucket_lifecycle(bucket):
    """
    Update lifecycle configuration for a bucket
    PUT /storage/v1/b/{bucket}/lifecycle
    
    Request body:
    {
        "rule": [
            {
                "action": "Delete",
                "ageDays": 30
            },
            {
                "action": "Archive",
                "ageDays": 90
            }
        ]
    }
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        data = request.get_json() or {}
        lifecycle_rules = data.get("rule", [])
        
        # Validate lifecycle rules
        if not isinstance(lifecycle_rules, list):
            return invalid_argument_error("Lifecycle configuration must be an array")
        
        for rule in lifecycle_rules:
            if not isinstance(rule, dict):
                return invalid_argument_error("Each lifecycle rule must be an object")
            
            action = rule.get("action")
            age_days = rule.get("ageDays")
            
            if not action:
                return invalid_argument_error("Lifecycle rule must have 'action'")
            
            if action not in ["Delete", "Archive"]:
                return invalid_argument_error("Action must be 'Delete' or 'Archive'")
            
            if age_days is None:
                return invalid_argument_error("Lifecycle rule must have 'ageDays'")
            
            if not isinstance(age_days, int) or age_days < 0:
                return invalid_argument_error("'ageDays' must be a non-negative integer")
        
        # Store lifecycle configuration
        from app.factory import db
        bucket_obj.lifecycle_config = json.dumps(lifecycle_rules) if lifecycle_rules else None
        db.session.commit()
        
        return jsonify({
            "kind": "storage#bucket#lifecycle",
            "rule": lifecycle_rules
        }), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@lifecycle_config_bp.route("/b/<bucket>/lifecycle", methods=["DELETE"])
def delete_bucket_lifecycle(bucket):
    """
    Delete lifecycle configuration for a bucket
    DELETE /storage/v1/b/{bucket}/lifecycle
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        from app.factory import db
        bucket_obj.lifecycle_config = None
        db.session.commit()
        
        return "", 204
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")
