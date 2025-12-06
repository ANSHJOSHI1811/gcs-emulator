"""
Notification configuration handler
Implements webhook registration for bucket notifications
"""
from flask import Blueprint, request, jsonify
import json
import uuid
from app.services.bucket_service import BucketService
from app.utils.gcs_errors import (
    not_found_error,
    invalid_argument_error,
    internal_error
)

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/b/<bucket>/notificationConfigs", methods=["GET"])
def list_notification_configs(bucket):
    """
    List notification configurations for a bucket
    GET /storage/v1/b/{bucket}/notificationConfigs
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        # Parse notification configs from JSON
        configs = []
        if bucket_obj.notification_configs:
            try:
                configs = json.loads(bucket_obj.notification_configs)
            except json.JSONDecodeError:
                pass
        
        return jsonify({
            "kind": "storage#notificationConfigs",
            "items": configs
        }), 200
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@notifications_bp.route("/b/<bucket>/notificationConfigs", methods=["POST"])
def create_notification_config(bucket):
    """
    Create a notification configuration
    POST /storage/v1/b/{bucket}/notificationConfigs
    
    Request body:
    {
        "webhookUrl": "https://example.com/webhook",
        "eventTypes": ["OBJECT_FINALIZE", "OBJECT_DELETE"],  // optional, defaults to all
        "objectNamePrefix": "logs/",  // optional filter
        "payloadFormat": "JSON_API_V1"  // optional
    }
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        data = request.get_json() or {}
        webhook_url = data.get("webhookUrl")
        
        if not webhook_url:
            return invalid_argument_error("webhookUrl is required")
        
        # Validate URL format
        if not webhook_url.startswith(("http://", "https://")):
            return invalid_argument_error("webhookUrl must be a valid HTTP(S) URL")
        
        # Create notification config
        config_id = str(uuid.uuid4())
        new_config = {
            "id": config_id,
            "webhookUrl": webhook_url,
            "eventTypes": data.get("eventTypes", []),  # Empty means all events
            "objectNamePrefix": data.get("objectNamePrefix", ""),
            "payloadFormat": data.get("payloadFormat", "JSON_API_V1")
        }
        
        # Load existing configs
        from app.factory import db
        existing_configs = []
        if bucket_obj.notification_configs:
            try:
                existing_configs = json.loads(bucket_obj.notification_configs)
            except json.JSONDecodeError:
                pass
        
        # Add new config
        existing_configs.append(new_config)
        bucket_obj.notification_configs = json.dumps(existing_configs)
        db.session.commit()
        
        return jsonify({
            "kind": "storage#notificationConfig",
            **new_config
        }), 201
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@notifications_bp.route("/b/<bucket>/notificationConfigs/<config_id>", methods=["GET"])
def get_notification_config(bucket, config_id):
    """
    Get a specific notification configuration
    GET /storage/v1/b/{bucket}/notificationConfigs/{configId}
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        # Find config by ID
        if bucket_obj.notification_configs:
            try:
                configs = json.loads(bucket_obj.notification_configs)
                for config in configs:
                    if config.get("id") == config_id:
                        return jsonify({
                            "kind": "storage#notificationConfig",
                            **config
                        }), 200
            except json.JSONDecodeError:
                pass
        
        return not_found_error(config_id, "notificationConfig")
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@notifications_bp.route("/b/<bucket>/notificationConfigs/<config_id>", methods=["DELETE"])
def delete_notification_config(bucket, config_id):
    """
    Delete a notification configuration
    DELETE /storage/v1/b/{bucket}/notificationConfigs/{configId}
    """
    try:
        bucket_obj = BucketService.get_bucket(bucket)
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        # Remove config by ID
        from app.factory import db
        if bucket_obj.notification_configs:
            try:
                configs = json.loads(bucket_obj.notification_configs)
                updated_configs = [c for c in configs if c.get("id") != config_id]
                
                if len(updated_configs) == len(configs):
                    # Config not found
                    return not_found_error(config_id, "notificationConfig")
                
                bucket_obj.notification_configs = json.dumps(updated_configs) if updated_configs else None
                db.session.commit()
                
                return "", 204
            except json.JSONDecodeError:
                pass
        
        return not_found_error(config_id, "notificationConfig")
    except ValueError as e:
        return invalid_argument_error(str(e))
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")
