"""
Object handlers - Flask routes for object operations with versioning support
"""
from flask import Blueprint, request, jsonify, send_file
from io import BytesIO
from app.services.object_versioning_service import ObjectVersioningService
from app.services.object_service import ObjectService
from app.validators.object_validators import is_valid_object_name
from app.models.bucket import Bucket
from app.models.object import ObjectVersion
from app.utils.gcs_errors import (
    not_found_error, 
    invalid_argument_error, 
    internal_error
)
from app.utils.iam_enforcer import require_permission

objects_bp = Blueprint("objects", __name__)


@objects_bp.route("/<bucket>/o", methods=["GET"])
@require_permission('bucket', 'storage.objects.list', 'bucket')
def list_objects(bucket):
    """
    List objects in a bucket
    GET /storage/v1/b/{bucket}/o?prefix=path/&delimiter=/
    GET /storage/v1/b/{bucket}/o?versions=true  - List all versions
    """
    try:
        prefix = request.args.get("prefix")
        delimiter = request.args.get("delimiter")
        versions = request.args.get("versions", "false").lower() == "true"
        
        if versions:
            # List all object versions in the bucket
            bucket_obj = Bucket.query.filter_by(name=bucket).first()
            if not bucket_obj:
                return not_found_error(bucket, "bucket")
            
            all_versions = ObjectVersion.query.filter_by(
                bucket_id=bucket_obj.id,
                deleted=False
            ).order_by(ObjectVersion.name, ObjectVersion.generation.desc()).all()
            
            items = [version.to_dict() for version in all_versions]
            
            response = {
                "kind": "storage#objects",
                "items": items
            }
            return jsonify(response), 200
        
        result = ObjectService.list_objects(bucket, prefix=prefix, delimiter=delimiter)
        items = [obj.to_dict() for obj in result["items"]]
        
        response = {
            "kind": "storage#objects",
            "items": items
        }
        
        if result["prefixes"]:
            response["prefixes"] = result["prefixes"]
        
        return jsonify(response), 200
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            # Extract resource name from error message
            return not_found_error(bucket, "bucket")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@objects_bp.route("/<bucket>/o", methods=["POST"])
@require_permission('bucket', 'storage.objects.create', 'bucket')
def upload_object(bucket):
    """
    Upload an object with versioning support
    POST /storage/v1/b/{bucket}/o?name=object-name
    Binary file content in request body
    """
    try:
        object_name = request.args.get("name", "").strip()
        if not object_name:
            return invalid_argument_error("Missing 'name' query parameter")
        
        # Validate object name
        if not is_valid_object_name(object_name):
            return invalid_argument_error(f"Invalid object name '{object_name}'")
        
        # Get file content
        content = request.get_data()
        if not content:
            return invalid_argument_error("Empty file content")
        
        content_type = request.headers.get("Content-Type", "application/octet-stream")
        
        # Check if bucket has versioning enabled
        bucket_obj = Bucket.query.filter_by(name=bucket).first()
        if not bucket_obj:
            return not_found_error(bucket, "bucket")
        
        # Always use versioning service to ensure version records are created
        # This fixes the "No version found" error on download
        obj = ObjectVersioningService.upload_object_with_versioning(
            bucket_name=bucket,
            object_name=object_name,
            content=content,
            content_type=content_type
        )
        
        # Trigger notifications for upload event
        from app.services.notification_service import NotificationService
        NotificationService.trigger_notifications(
            bucket_obj=bucket_obj,
            object_name=object_name,
            event_type="OBJECT_FINALIZE",
            generation=obj.generation
        )
        
        return jsonify(obj.to_dict()), 201
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            if "bucket" in error_msg.lower():
                return not_found_error(bucket, "bucket")
            else:
                return not_found_error(object_name, "object")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@objects_bp.route("/<bucket>/o/<path:object_name>", methods=["GET"])
@require_permission('bucket', 'storage.objects.get', 'bucket')
def get_object(bucket, object_name):
    """
    Get object metadata or download with versioning support
    GET /storage/v1/b/{bucket}/o/{object}                    - metadata (latest)
    GET /storage/v1/b/{bucket}/o/{object}?generation=123     - metadata (specific version)
    GET /storage/v1/b/{bucket}/o/{object}?alt=media          - download (latest)
    GET /storage/v1/b/{bucket}/o/{object}?alt=media&generation=123  - download (specific version)
    """
    try:
        alt = request.args.get("alt", "json").lower()
        generation = request.args.get("generation", type=int)
        
        if alt == "media":
            # Download file content
            content, version = ObjectVersioningService.download_object_version(
                bucket, object_name, generation
            )
            return send_file(
                BytesIO(content),
                mimetype=version.content_type,
                as_attachment=True,
                download_name=object_name
            ), 200
        else:
            # Return metadata
            obj, version = ObjectVersioningService.get_object_version(
                bucket, object_name, generation
            )
            return jsonify(version.to_dict()), 200
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            if "bucket" in error_msg.lower():
                return not_found_error(bucket, "bucket")
            else:
                return not_found_error(object_name, "object")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@objects_bp.route("/<bucket>/o/<path:object_name>", methods=["DELETE"])
@require_permission('bucket', 'storage.objects.delete', 'bucket')
def delete_object(bucket, object_name):
    """
    Delete an object or specific version
    DELETE /storage/v1/b/{bucket}/o/{object}               - delete all versions
    DELETE /storage/v1/b/{bucket}/o/{object}?generation=123 - delete specific version
    """
    try:
        # Get bucket for notifications
        bucket_obj = Bucket.query.filter_by(name=bucket).first()
        
        generation = request.args.get("generation", type=int)
        ObjectVersioningService.delete_object_version(bucket, object_name, generation)
        
        # Trigger notifications for delete event
        if bucket_obj:
            from app.services.notification_service import NotificationService
            NotificationService.trigger_notifications(
                bucket_obj=bucket_obj,
                object_name=object_name,
                event_type="OBJECT_DELETE",
                generation=generation
            )
        
        return "", 204
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            if "bucket" in error_msg.lower():
                return not_found_error(bucket, "bucket")
            else:
                return not_found_error(object_name, "object")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


@objects_bp.route("/<src_bucket>/o/<path:src_object>/copyTo/b/<dst_bucket>/o/<path:dst_object>", methods=["POST"])
@require_permission('bucket', 'storage.objects.get', 'src_bucket')
@require_permission('bucket', 'storage.objects.create', 'dst_bucket')
def copy_object(src_bucket, src_object, dst_bucket, dst_object):
    """
    Copy an object from source to destination
    POST /storage/v1/b/{srcBucket}/o/{srcObject}/copyTo/b/{dstBucket}/o/{dstObject}
    
    Supports:
    - Same-bucket copy
    - Cross-bucket copy
    - Metadata preservation
    - New generation/metageneration for destination
    """
    try:
        copied_obj = ObjectService.copy_object(
            src_bucket_name=src_bucket,
            src_object_name=src_object,
            dst_bucket_name=dst_bucket,
            dst_object_name=dst_object
        )
        
        return jsonify(copied_obj.to_dict()), 201
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            if "bucket" in error_msg.lower():
                bucket_name = src_bucket if "source" in error_msg.lower() else dst_bucket
                return not_found_error(bucket_name, "bucket")
            else:
                return not_found_error(src_object, "object")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")
