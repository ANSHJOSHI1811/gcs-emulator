"""
Constants - Application constants
"""

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409
HTTP_INTERNAL_ERROR = 500

# Error Messages
ERROR_BUCKET_NOT_FOUND = "The specified bucket does not exist."
ERROR_OBJECT_NOT_FOUND = "The specified object does not exist."
ERROR_BUCKET_ALREADY_EXISTS = "The specified bucket already exists."
ERROR_OBJECT_ALREADY_EXISTS = "The specified object already exists."
ERROR_BUCKET_NOT_EMPTY = "The bucket you tried to delete is not empty."
ERROR_INVALID_BUCKET_NAME = "The specified bucket name is invalid."
ERROR_INVALID_OBJECT_NAME = "The specified object name is invalid."

# Default Values
DEFAULT_STORAGE_CLASS = "STANDARD"
DEFAULT_LOCATION = "US"
DEFAULT_CONTENT_TYPE = "application/octet-stream"

# Project Defaults
DEFAULT_PROJECT_ID = "default_project"
DEFAULT_PROJECT_NAME = "Default Project"
