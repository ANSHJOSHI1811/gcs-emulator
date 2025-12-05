"""
Upload handler - Media and Multipart upload endpoints for object uploads with versioning

Supports:
    - Media upload: /upload/storage/v1/b/{bucket}/o?uploadType=media&name={object}
    - Multipart upload: /upload/storage/v1/b/{bucket}/o?uploadType=multipart

Reference: https://cloud.google.com/storage/docs/uploading-objects
"""
from flask import Blueprint, request, jsonify
from app.services.object_versioning_service import ObjectVersioningService, PreconditionFailedError
from app.validators.object_validators import is_valid_object_name
from app.utils.multipart import extract_boundary, parse_multipart_body, MultipartParseError

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/storage/v1/b/<bucket>/o", methods=["POST"])
def upload_object(bucket):
    """
    Upload an object via media or multipart upload with versioning support.
    
    Media Upload:
        POST /upload/storage/v1/b/{bucket}/o?uploadType=media&name=object-name
        - Content is sent directly in request body
        - Object name provided via 'name' query parameter
        
    Multipart Upload:
        POST /upload/storage/v1/b/{bucket}/o?uploadType=multipart
        - Uses multipart/related format
        - Part 1: JSON metadata with object name
        - Part 2: Binary file content
    
    Query Parameters:
        uploadType: 'media' or 'multipart'
        name: Object name (required for media upload, in metadata for multipart)
        ifGenerationMatch: Proceed only if generation matches (optional)
        ifGenerationNotMatch: Proceed only if generation doesn't match (optional)
        ifMetagenerationMatch: Proceed only if metageneration matches (optional)
        ifMetagenerationNotMatch: Proceed only if metageneration doesn't match (optional)
        
    Returns:
        JSON response with object metadata including generation/metageneration
    """
    try:
        # Validate upload type
        upload_type = request.args.get("uploadType", "").lower()
        
        if upload_type == "multipart":
            return _handle_multipart_upload(bucket)
        elif upload_type == "media":
            return _handle_media_upload(bucket)
        else:
            return jsonify({
                "error": {
                    "message": f"Unsupported uploadType: {upload_type}. Supported: 'media', 'multipart'"
                }
            }), 400
            
    except PreconditionFailedError as e:
        return jsonify({
            "error": {
                "code": 412,
                "message": str(e)
            }
        }), 412
    except MultipartParseError as e:
        return jsonify({
            "error": {
                "code": 400,
                "message": f"Multipart parsing error: {str(e)}"
            }
        }), 400
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return jsonify({
                "error": {
                    "code": 404,
                    "message": error_msg
                }
            }), 404
        return jsonify({
            "error": {
                "code": 400,
                "message": error_msg
            }
        }), 400
    except Exception as e:
        return jsonify({
            "error": {
                "code": 500,
                "message": f"Internal server error: {str(e)}"
            }
        }), 500


def _handle_media_upload(bucket: str):
    """Handle uploadType=media requests."""
    # Get object name from query parameter
    object_name = request.args.get("name", "").strip()
    if not object_name:
        return jsonify({
            "error": {
                "message": "Missing required query parameter 'name'"
            }
        }), 400
    
    # Validate object name
    if not is_valid_object_name(object_name):
        return jsonify({
            "error": {
                "message": f"Invalid object name: {object_name}"
            }
        }), 400
    
    # Get file content from request body
    content = request.get_data()
    if not content:
        return jsonify({
            "error": {
                "message": "Empty request body. File content is required."
            }
        }), 400
    
    # Get content type from header
    content_type = request.headers.get("Content-Type", "application/octet-stream")
    
    return _upload_with_preconditions(bucket, object_name, content, content_type)


def _handle_multipart_upload(bucket: str):
    """
    Handle uploadType=multipart requests.
    
    Parses multipart/related format:
        --boundary
        Content-Type: application/json
        
        {"name": "object-name"}
        
        --boundary
        Content-Type: text/plain
        
        <file content>
        --boundary--
    """
    content_type_header = request.headers.get("Content-Type", "")
    
    # Extract boundary from Content-Type header
    boundary = extract_boundary(content_type_header)
    
    # Get raw body
    body = request.get_data()
    if not body:
        return jsonify({
            "error": {
                "message": "Empty request body"
            }
        }), 400
    
    # Parse multipart body
    parsed = parse_multipart_body(body, boundary)
    
    # Validate object name
    if not is_valid_object_name(parsed.object_name):
        return jsonify({
            "error": {
                "message": f"Invalid object name: {parsed.object_name}"
            }
        }), 400
    
    return _upload_with_preconditions(
        bucket, 
        parsed.object_name, 
        parsed.content, 
        parsed.content_type
    )


def _upload_with_preconditions(bucket: str, object_name: str, 
                                content: bytes, content_type: str):
    """
    Common upload logic with precondition support.
    
    Extracts precondition headers and calls the versioning service.
    """
    # Extract precondition parameters from query string
    if_generation_match = request.args.get("ifGenerationMatch", type=int)
    if_generation_not_match = request.args.get("ifGenerationNotMatch", type=int)
    if_metageneration_match = request.args.get("ifMetagenerationMatch", type=int)
    if_metageneration_not_match = request.args.get("ifMetagenerationNotMatch", type=int)
    
    # Upload object with versioning
    obj = ObjectVersioningService.upload_object_with_versioning(
        bucket_name=bucket,
        object_name=object_name,
        content=content,
        content_type=content_type,
        if_generation_match=if_generation_match,
        if_generation_not_match=if_generation_not_match,
        if_metageneration_match=if_metageneration_match,
        if_metageneration_not_match=if_metageneration_not_match
    )
    
    # Return GCS-compliant JSON response
    response_data = obj.to_dict()
    
    return jsonify(response_data), 200

