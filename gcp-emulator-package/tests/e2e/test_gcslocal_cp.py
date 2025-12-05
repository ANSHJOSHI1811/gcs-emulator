"""
End-to-End Tests for gcslocal cp command
Tests upload and download functionality via CLI
"""
import pytest
import tempfile
import os
from pathlib import Path
from app.models.bucket import Bucket
from app.models.object import Object


def test_upload_text_file(app, client):
    """Test uploading a text file via upload endpoint"""
    with app.app_context():
        # Create bucket first
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'upload-test-bucket'}
        )
        
        # Upload file
        file_content = b'Hello, World!'
        response = client.post(
            '/upload/storage/v1/b/upload-test-bucket/o?uploadType=media&name=hello.txt',
            data=file_content,
            headers={'Content-Type': 'text/plain'}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'hello.txt'
        assert 'upload-test-bucket' in data['bucket']  # Bucket ID may have suffix
        assert data['size'] == str(len(file_content))
        assert data['contentType'] == 'text/plain'
        assert 'md5Hash' in data
        assert 'crc32c' in data
        
        # Verify in database
        obj = Object.query.filter_by(name='hello.txt').first()
        assert obj is not None
        assert obj.size == len(file_content)


def test_upload_binary_file(app, client):
    """Test uploading a binary file"""
    with app.app_context():
        # Create bucket
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'binary-test-bucket'}
        )
        
        # Upload binary content
        binary_content = bytes(range(256))
        response = client.post(
            '/upload/storage/v1/b/binary-test-bucket/o?uploadType=media&name=binary.dat',
            data=binary_content,
            headers={'Content-Type': 'application/octet-stream'}
        )
        
        # Verify
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'binary.dat'
        assert data['size'] == str(len(binary_content))
        assert data['contentType'] == 'application/octet-stream'


def test_upload_overwrite_existing(app, client):
    """Test overwriting an existing object"""
    with app.app_context():
        # Create bucket
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'overwrite-bucket'}
        )
        
        # Upload first version
        response1 = client.post(
            '/upload/storage/v1/b/overwrite-bucket/o?uploadType=media&name=file.txt',
            data=b'Version 1',
            headers={'Content-Type': 'text/plain'}
        )
        assert response1.status_code == 200
        
        # Upload second version (overwrite)
        response2 = client.post(
            '/upload/storage/v1/b/overwrite-bucket/o?uploadType=media&name=file.txt',
            data=b'Version 2 - Updated',
            headers={'Content-Type': 'text/plain'}
        )
        assert response2.status_code == 200
        
        # Verify new size
        data = response2.get_json()
        assert data['size'] == str(len(b'Version 2 - Updated'))


def test_upload_missing_bucket(app, client):
    """Test upload to non-existent bucket returns 404"""
    with app.app_context():
        response = client.post(
            '/upload/storage/v1/b/nonexistent-bucket/o?uploadType=media&name=file.txt',
            data=b'test content'
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data


def test_upload_missing_name_parameter(app, client):
    """Test upload without name parameter returns 400"""
    with app.app_context():
        # Create bucket
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'test-bucket'}
        )
        
        # Upload without name parameter
        response = client.post(
            '/upload/storage/v1/b/test-bucket/o?uploadType=media',
            data=b'test content'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


def test_upload_empty_content(app, client):
    """Test upload with empty content returns 400"""
    with app.app_context():
        # Create bucket
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'test-bucket'}
        )
        
        # Upload empty content
        response = client.post(
            '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=empty.txt',
            data=b''
        )
        
        assert response.status_code == 400


def test_upload_invalid_upload_type(app, client):
    """Test upload with invalid uploadType returns 400"""
    with app.app_context():
        # Create bucket
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'test-bucket'}
        )
        
        # Upload with wrong uploadType
        response = client.post(
            '/upload/storage/v1/b/test-bucket/o?uploadType=resumable&name=file.txt',
            data=b'test'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'uploadtype' in data['error']['message'].lower()  # Case-insensitive check


def test_download_text_file(app, client):
    """Test downloading a text file"""
    with app.app_context():
        # Create bucket and upload file
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'download-bucket'}
        )
        
        file_content = b'Download me!'
        client.post(
            '/upload/storage/v1/b/download-bucket/o?uploadType=media&name=download.txt',
            data=file_content,
            headers={'Content-Type': 'text/plain'}
        )
        
        # Download file
        response = client.get('/storage/v1/b/download-bucket/o/download.txt?alt=media')
        
        assert response.status_code == 200
        assert response.data == file_content
        assert response.headers['Content-Type'].startswith('text/plain')  # May include charset


def test_download_binary_file(app, client):
    """Test downloading a binary file"""
    with app.app_context():
        # Create bucket and upload binary file
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'binary-download-bucket'}
        )
        
        binary_content = bytes(range(256))
        client.post(
            '/upload/storage/v1/b/binary-download-bucket/o?uploadType=media&name=data.bin',
            data=binary_content,
            headers={'Content-Type': 'application/octet-stream'}
        )
        
        # Download file
        response = client.get('/storage/v1/b/binary-download-bucket/o/data.bin?alt=media')
        
        assert response.status_code == 200
        assert response.data == binary_content


def test_download_nonexistent_object(app, client):
    """Test downloading non-existent object returns 404"""
    with app.app_context():
        # Create bucket
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'test-bucket'}
        )
        
        # Try to download non-existent file
        response = client.get('/storage/v1/b/test-bucket/o/nonexistent.txt?alt=media')
        
        assert response.status_code == 404


def test_download_from_nonexistent_bucket(app, client):
    """Test downloading from non-existent bucket returns 404"""
    with app.app_context():
        response = client.get('/storage/v1/b/nonexistent/o/file.txt?alt=media')
        assert response.status_code == 404


def test_upload_download_round_trip(app, client):
    """Test uploading and then downloading the same file"""
    with app.app_context():
        # Create bucket
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'roundtrip-bucket'}
        )
        
        # Upload file
        original_content = b'Round trip test content with special chars: \x00\xff\xaa'
        upload_response = client.post(
            '/upload/storage/v1/b/roundtrip-bucket/o?uploadType=media&name=roundtrip.dat',
            data=original_content,
            headers={'Content-Type': 'application/octet-stream'}
        )
        assert upload_response.status_code == 200
        
        # Download file
        download_response = client.get('/storage/v1/b/roundtrip-bucket/o/roundtrip.dat?alt=media')
        assert download_response.status_code == 200
        
        # Verify content matches
        assert download_response.data == original_content


def test_upload_with_nested_path(app, client):
    """Test uploading object with nested path (simulated folders)"""
    with app.app_context():
        # Create bucket
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'nested-bucket'}
        )
        
        # Upload with nested path
        response = client.post(
            '/upload/storage/v1/b/nested-bucket/o?uploadType=media&name=folder/subfolder/file.txt',
            data=b'Nested file',
            headers={'Content-Type': 'text/plain'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'folder/subfolder/file.txt'
        
        # Verify we can download it
        download_response = client.get('/storage/v1/b/nested-bucket/o/folder/subfolder/file.txt?alt=media')
        assert download_response.status_code == 200
        assert download_response.data == b'Nested file'


def test_upload_large_file(app, client):
    """Test uploading a larger file"""
    with app.app_context():
        # Create bucket
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'large-file-bucket'}
        )
        
        # Generate 1MB of data
        large_content = b'A' * (1024 * 1024)
        
        response = client.post(
            '/upload/storage/v1/b/large-file-bucket/o?uploadType=media&name=large.dat',
            data=large_content,
            headers={'Content-Type': 'application/octet-stream'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['size'] == str(len(large_content))


def test_get_object_metadata_without_download(app, client):
    """Test getting object metadata without downloading content"""
    with app.app_context():
        # Create bucket and upload
        client.post(
            '/storage/v1/b?project=test-project',
            json={'name': 'metadata-bucket'}
        )
        
        client.post(
            '/upload/storage/v1/b/metadata-bucket/o?uploadType=media&name=metadata.txt',
            data=b'Metadata test',
            headers={'Content-Type': 'text/plain'}
        )
        
        # Get metadata (without alt=media)
        response = client.get('/storage/v1/b/metadata-bucket/o/metadata.txt')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'metadata.txt'
        assert data['size'] == str(len(b'Metadata test'))
        assert data['contentType'] == 'text/plain'
        # Should not contain actual file content
        assert 'Metadata test' not in str(data)
