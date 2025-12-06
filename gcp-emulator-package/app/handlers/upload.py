"""
Upload handler - Media, Multipart, and Resumable upload endpoints

Supports:
    - Media upload: /upload/storage/v1/b/{bucket}/o?uploadType=media&name={object}
    - Multipart upload: /upload/storage/v1/b/{bucket}/o?uploadType=multipart
    - Resumable upload: /upload/storage/v1/b/{bucket}/o?uploadType=resumable (Phase 3)

Reference: https://cloud.google.com/storage/docs/uploading-objects
"""
from flask import Blueprint, request, jsonify, url_for
from app.services.object_versioning_service import ObjectVersioningService, PreconditionFailedError
from app.services.resumable_upload_service import ResumableUploadService
from app.validators.object_validators import is_valid_object_name
from app.utils.multipart import extract_boundary, parse_multipart_body, MultipartParseError
from app.utils.gcs_errors import (
    not_found_error,
    invalid_argument_error,
    precondition_failed_error,
    internal_error
)

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/storage/v1/b/<bucket>/o", methods=["POST"])
def upload_object(bucket):
    """
    Upload an object via media, multipart, or resumable upload with versioning support.
    
    Media Upload:
        POST /upload/storage/v1/b/{bucket}/o?uploadType=media&name=object-name
        - Content is sent directly in request body
        - Object name provided via 'name' query parameter
        
    Multipart Upload:
        POST /upload/storage/v1/b/{bucket}/o?uploadType=multipart
        - Uses multipart/related format
        - Part 1: JSON metadata with object name
        - Part 2: Binary file content
    
    Resumable Upload (Phase 3):
        POST /upload/storage/v1/b/{bucket}/o?uploadType=resumable
        - Initiates a resumable upload session
        - Returns Location header with session URL
    
    Query Parameters:
        uploadType: 'media', 'multipart', or 'resumable'
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
        elif upload_type == "resumable":
            return _handle_resumable_initiate(bucket)
        else:
            return invalid_argument_error(
                f"Unsupported uploadType: {upload_type}. Supported: 'media', 'multipart', 'resumable'"
            )
            
    except PreconditionFailedError as e:
        return precondition_failed_error(str(e))
    except MultipartParseError as e:
        return invalid_argument_error(f"Multipart parsing error: {str(e)}")
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            if "bucket" in error_msg.lower():
                return not_found_error(bucket, "bucket")
            else:
                return not_found_error("object", "object")
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")


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
    
    return jsonify(response_data), 201


def _handle_resumable_initiate(bucket: str):
    """
    Handle resumable upload initiation (Phase 3)
    
    POST /upload/storage/v1/b/{bucket}/o?uploadType=resumable
    
    Request body: JSON metadata with object name
    Response: 200 with Location header and sessionId
    """
    # Get JSON metadata
    data = request.get_json() or {}
    object_name = data.get("name", "").strip()
    
    if not object_name:
        return invalid_argument_error("Missing 'name' in request body")
    
    # Validate object name
    if not is_valid_object_name(object_name):
        return invalid_argument_error(f"Invalid object name: {object_name}")
    
    # Extract metadata
    content_type = data.get("contentType", "application/octet-stream")
    metadata = {
        "contentType": content_type
    }
    
    # Get total size if provided
    total_size = data.get("size")
    
    # Initiate session
    session = ResumableUploadService.initiate_session(
        bucket_name=bucket,
        object_name=object_name,
        metadata=metadata,
        total_size=total_size
    )
    
    # Construct session URL
    session_url = url_for(
        'resumable.upload_chunk',
        session_id=session.session_id,
        _external=True
    )
    
    # Return response with Location header
    response = jsonify({"sessionId": session.session_id})
    response.headers['Location'] = session_url
    response.status_code = 200
    
    return response


# Resumable upload blueprint for chunk uploads
resumable_bp = Blueprint("resumable", __name__)


@resumable_bp.route("/upload/resumable/<session_id>", methods=["PUT"])
def upload_chunk(session_id):
    """
    Upload a chunk to a resumable session (Phase 3)
    
    PUT /upload/resumable/{session_id}
    
    Headers:
        Content-Length: N
        Content-Range: bytes start-end/total OR bytes */total
    
    Response:
        308 Resume Incomplete (with Range header) if more chunks needed
        200 with object metadata if complete
    """
    try:
        # Get chunk data
        chunk_data = request.get_data()
        
        # Get Content-Range header
        content_range = request.headers.get('Content-Range', '')
        if not content_range:
            return invalid_argument_error("Missing Content-Range header")
        
        # Upload chunk
        is_complete, current_offset, object_metadata = ResumableUploadService.upload_chunk(
            session_id=session_id,
            chunk_data=chunk_data,
            content_range=content_range
        )
        
        if is_complete:
            # Upload complete - return object metadata
            return jsonify(object_metadata), 201
        else:
            # Upload incomplete - return 308 with Range header
            response = jsonify({"message": "Resume Incomplete"})
            response.headers['Range'] = f"bytes=0-{current_offset - 1}"
            response.status_code = 308
            return response
            
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            return not_found_error(session_id, "session")
        if "offset mismatch" in error_msg.lower():
            return invalid_argument_error(error_msg)
        return invalid_argument_error(error_msg)
    except Exception as e:
        return internal_error(f"Internal server error: {str(e)}")

