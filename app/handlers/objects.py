"""
Object handlers - Flask routes for object operations
"""
from flask import Blueprint, request, jsonify, send_file
from io import BytesIO
from app.services.object_service import ObjectService
from app.validators.object_validators import is_valid_object_name

objects_bp = Blueprint("objects", __name__)


@objects_bp.route("/<bucket>/o", methods=["GET"])
def list_objects(bucket):
    """
    List objects in a bucket
    GET /storage/v1/b/{bucket}/o?prefix=path/&delimiter=/
    """
    try:
        prefix = request.args.get("prefix")
        delimiter = request.args.get("delimiter")
        
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
    Upload an object
    POST /storage/v1/b/{bucket}/o?name=object-name
    Binary file content in request body
    """
    try:
        object_name = request.args.get("name", "").strip()
        if not object_name:
            return jsonify({"error": "Missing 'name' query parameter"}), 400
        
        # Validate object name
        if not is_valid_object_name(object_name):
            return jsonify({"error": f"Invalid object name '{object_name}'"}), 400
        
        # Get file content
        content = request.get_data()
        if not content:
            return jsonify({"error": "Empty file content"}), 400
        
        content_type = request.headers.get("Content-Type", "application/octet-stream")
        
        obj = ObjectService.upload_object(
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
    Get object metadata or download
    GET /storage/v1/b/{bucket}/o/{object}             - metadata (returns JSON)
    GET /storage/v1/b/{bucket}/o/{object}?alt=media  - download (returns binary)
    """
    try:
        alt = request.args.get("alt", "json").lower()
        
        if alt == "media":
            # Download file
            content, obj = ObjectService.download_object(bucket, object_name)
            return send_file(
                BytesIO(content),
                mimetype=obj.content_type,
                as_attachment=True,
                download_name=object_name
            ), 200
        else:
            # Return metadata
            obj = ObjectService.get_object(bucket, object_name)
            return jsonify(obj.to_dict()), 200
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
    Delete an object
    DELETE /storage/v1/b/{bucket}/o/{object}
    """
    try:
        ObjectService.delete_object(bucket, object_name)
        return "", 204
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            return jsonify({"error": error_msg}), 404
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
