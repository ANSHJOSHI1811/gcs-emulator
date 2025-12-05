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

objects_bp = Blueprint("objects", __name__)


@objects_bp.route("/<bucket>/o", methods=["GET"])
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
                return jsonify({"error": f"Bucket '{bucket}' not found"}), 404
            
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
        if "not found" in error_msg:
            return jsonify({"error": error_msg}), 404
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@objects_bp.route("/<bucket>/o", methods=["POST"])
def upload_object(bucket):
    """
    Upload an object with versioning support
    POST /storage/v1/b/{bucket}/o?name=object-name
    Binary file content in request body
    """
    try:
        object_name = request.args.get("name", "").strip()
        if not object_name:
            return jsonify({"error": {"message": "Missing 'name' query parameter"}}), 400
        
        # Validate object name
        if not is_valid_object_name(object_name):
            return jsonify({"error": {"message": f"Invalid object name '{object_name}'"}}), 400
        
        # Get file content
        content = request.get_data()
        if not content:
            return jsonify({"error": {"message": "Empty file content"}}), 400
        
        content_type = request.headers.get("Content-Type", "application/octet-stream")
        
        # Check if bucket has versioning enabled
        bucket_obj = Bucket.query.filter_by(name=bucket).first()
        if not bucket_obj:
            return jsonify({"error": f"Bucket '{bucket}' not found"}), 404
        
        # Always use versioning service to ensure version records are created
        # This fixes the "No version found" error on download
        obj = ObjectVersioningService.upload_object_with_versioning(
            bucket_name=bucket,
            object_name=object_name,
            content=content,
            content_type=content_type
        )
        
        return jsonify(obj.to_dict()), 200
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            return jsonify({"error": error_msg}), 404
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@objects_bp.route("/<bucket>/o/<path:object_name>", methods=["GET"])
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
        if "not found" in error_msg:
            return jsonify({"error": error_msg}), 404
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@objects_bp.route("/<bucket>/o/<path:object_name>", methods=["DELETE"])
def delete_object(bucket, object_name):
    """
    Delete an object or specific version
    DELETE /storage/v1/b/{bucket}/o/{object}               - delete all versions
    DELETE /storage/v1/b/{bucket}/o/{object}?generation=123 - delete specific version
    """
    try:
        generation = request.args.get("generation", type=int)
        ObjectVersioningService.delete_object_version(bucket, object_name, generation)
        return "", 204
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            return jsonify({"error": error_msg}), 404
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
