# Phase 2 Quick Reference

## What Changed in Phase 2?

### 1. Timestamp Format (RFC 3339)
All timestamps now use RFC 3339 format with millisecond precision:
- **Format:** `YYYY-MM-DDTHH:MM:SS.sssZ`
- **Example:** `2025-12-05T12:34:56.789Z`
- **Affects:** `timeCreated`, `updated` fields in buckets and objects

### 2. Error Response Structure
All errors now follow GCS JSON API format:

```json
{
  "error": {
    "code": 404,
    "message": "The bucket 'my-bucket' does not exist.",
    "errors": [
      {
        "message": "The bucket 'my-bucket' does not exist.",
        "domain": "global",
        "reason": "notFound"
      }
    ]
  }
}
```

**Error Reasons:**
- `404` → `notFound`
- `400` → `invalid`
- `409` → `conflict`
- `412` → `conditionNotMet`
- `500` → `internalError`

### 3. Bucket Metadata
- **Bucket `id` field:** Now returns bucket name (was internal UUID)
- **Example:** `"id": "my-bucket"` instead of `"id": "my-bucket-8a18eab3"`

### 4. Object Metadata
- **Object `bucket` field:** Returns bucket name (not UUID)
- **Object `selfLink`:** Always `/storage/v1/b/{bucket}/o/{object}`
- **Consistent generation/metageneration** after version deletions

## Testing Phase 2 Features

### Run Phase 2 Tests
```powershell
cd gcp-emulator-package
$env:PYTHONPATH="."
python -m pytest tests\test_phase2_fixes.py -v
```

### Test Categories
1. **Metadata Tests** (5 tests) - RFC 3339, field formats
2. **Error Schema Tests** (5 tests) - 404, 409, 412, 400 responses
3. **Versioning Tests** (3 tests) - Deletion consistency
4. **List Behavior Tests** (3 tests) - Response structures

## API Examples

### GET Object Metadata
**Request:**
```http
GET /storage/v1/b/my-bucket/o/my-object.txt
```

**Response:**
```json
{
  "kind": "storage#object",
  "id": "my-bucket/my-object.txt/1",
  "selfLink": "/storage/v1/b/my-bucket/o/my-object.txt",
  "name": "my-object.txt",
  "bucket": "my-bucket",
  "generation": "1",
  "metageneration": "1",
  "contentType": "text/plain",
  "timeCreated": "2025-12-05T12:34:56.789Z",
  "updated": "2025-12-05T12:34:56.789Z",
  "size": "1024",
  "md5Hash": "...",
  "crc32c": "..."
}
```

### Error Response (404)
**Request:**
```http
GET /storage/v1/b/nonexistent-bucket
```

**Response:**
```json
{
  "error": {
    "code": 404,
    "message": "The bucket 'nonexistent-bucket' does not exist.",
    "errors": [
      {
        "message": "The bucket 'nonexistent-bucket' does not exist.",
        "domain": "global",
        "reason": "notFound"
      }
    ]
  }
}
```

### List Objects
**Request:**
```http
GET /storage/v1/b/my-bucket/o
```

**Response:**
```json
{
  "kind": "storage#objects",
  "items": [
    {
      "kind": "storage#object",
      "name": "file1.txt",
      "bucket": "my-bucket",
      ...
    },
    {
      "kind": "storage#object",
      "name": "file2.txt",
      "bucket": "my-bucket",
      ...
    }
  ]
}
```

## Migration Notes

### No Breaking Changes
Phase 2 changes are **backward compatible**:
- All endpoints remain unchanged
- Request formats unchanged
- Only response formats improved
- Error codes unchanged (only format enhanced)

### Client Impact
Clients should handle:
1. New error response structure (contains `error.errors` array)
2. RFC 3339 timestamps (already valid ISO 8601)
3. Bucket `id` now matches `name`

### Python SDK Compatibility
No changes needed - SDK automatically handles response format variations.

## Files Modified Summary

**New Files:**
- `app/utils/gcs_errors.py` - Error utility

**Modified Models:**
- `app/models/object.py` - RFC 3339 timestamps
- `app/models/bucket.py` - RFC 3339 timestamps, proper ID

**Modified Handlers:**
- `app/handlers/objects.py`
- `app/handlers/upload.py`
- `app/handlers/bucket_handler.py`
- `app/handlers/download.py`
- `app/handlers/errors.py`

**New Tests:**
- `tests/test_phase2_fixes.py` - 16 tests

## Quick Verification

```powershell
# Run all Phase 2 tests
python -m pytest tests\test_phase2_fixes.py -v

# Verify metadata format
curl http://localhost:8080/storage/v1/b/test-bucket

# Verify error format
curl http://localhost:8080/storage/v1/b/nonexistent

# Check timestamp format
curl http://localhost:8080/storage/v1/b/test-bucket/o/test.txt
```

## Support

For issues or questions about Phase 2 changes:
1. Check `PHASE_2_IMPLEMENTATION.md` for detailed implementation
2. Review test cases in `tests/test_phase2_fixes.py`
3. Examine `app/utils/gcs_errors.py` for error handling patterns
