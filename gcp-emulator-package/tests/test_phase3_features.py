"""
Phase 3 Tests - Resumable Uploads and Signed URLs

Tests for:
1. Resumable Uploads (uploadType=resumable)
2. Signed URLs (GET and PUT)
"""
import pytest
import time


class TestPhase3ResumableUploads:
    """Test 1: Resumable Uploads"""
    
    def test_initiate_resumable_session(self, client, setup_bucket):
        """Test initiating a resumable upload session"""
        bucket_name = setup_bucket
        
        # Initiate resumable upload
        response = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=resumable",
            json={
                "name": "test-resumable.txt",
                "contentType": "text/plain"
            },
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        # Check Location header
        assert 'Location' in response.headers
        location = response.headers['Location']
        assert '/upload/resumable/' in location
        
        # Check response body
        data = response.get_json()
        assert 'sessionId' in data
        assert len(data['sessionId']) > 0
    
    def test_upload_single_chunk(self, client, setup_bucket):
        """Test uploading a single chunk"""
        bucket_name = setup_bucket
        
        # Initiate session
        init_resp = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=resumable",
            json={
                "name": "single-chunk.txt",
                "contentType": "text/plain"
            },
            headers={"Content-Type": "application/json"}
        )
        assert init_resp.status_code == 200
        session_id = init_resp.get_json()['sessionId']
        
        # Upload chunk (incomplete)
        content = b"Hello World"
        total_size = 100
        
        chunk_resp = client.put(
            f"/upload/resumable/{session_id}",
            data=content,
            headers={
                "Content-Range": f"bytes 0-10/{total_size}",
                "Content-Length": str(len(content))
            }
        )
        
        # Should return 308 (Resume Incomplete)
        assert chunk_resp.status_code == 308
        assert 'Range' in chunk_resp.headers
        assert chunk_resp.headers['Range'] == 'bytes=0-10'
    
    def test_upload_final_chunk_creates_object(self, client, setup_bucket):
        """Test that uploading final chunk creates the object"""
        bucket_name = setup_bucket
        
        # Initiate session
        init_resp = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=resumable",
            json={
                "name": "final-chunk-test.txt",
                "contentType": "text/plain"
            },
            headers={"Content-Type": "application/json"}
        )
        assert init_resp.status_code == 200
        session_id = init_resp.get_json()['sessionId']
        
        # Upload complete file in one chunk
        content = b"Complete file content"
        
        chunk_resp = client.put(
            f"/upload/resumable/{session_id}",
            data=content,
            headers={
                "Content-Range": f"bytes 0-{len(content)-1}/{len(content)}",
                "Content-Length": str(len(content))
            }
        )
        
        # Should return 200 with object metadata
        assert chunk_resp.status_code == 200
        
        data = chunk_resp.get_json()
        assert 'kind' in data
        assert data['kind'] == 'storage#object'
        assert data['name'] == 'final-chunk-test.txt'
        assert data['bucket'] == bucket_name
        assert 'generation' in data
    
    def test_upload_multiple_chunks_sequentially(self, client, setup_bucket):
        """Test uploading multiple chunks sequentially"""
        bucket_name = setup_bucket
        
        # Initiate session
        init_resp = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=resumable",
            json={
                "name": "multi-chunk.txt",
                "contentType": "text/plain"
            },
            headers={"Content-Type": "application/json"}
        )
        assert init_resp.status_code == 200
        session_id = init_resp.get_json()['sessionId']
        
        # Upload chunk 1
        chunk1 = b"Part 1 "
        resp1 = client.put(
            f"/upload/resumable/{session_id}",
            data=chunk1,
            headers={
                "Content-Range": f"bytes 0-6/20",
                "Content-Length": str(len(chunk1))
            }
        )
        assert resp1.status_code == 308
        assert resp1.headers['Range'] == 'bytes=0-6'
        
        # Upload chunk 2
        chunk2 = b"Part 2 "
        resp2 = client.put(
            f"/upload/resumable/{session_id}",
            data=chunk2,
            headers={
                "Content-Range": f"bytes 7-13/20",
                "Content-Length": str(len(chunk2))
            }
        )
        assert resp2.status_code == 308
        assert resp2.headers['Range'] == 'bytes=0-13'
        
        # Upload final chunk
        chunk3 = b"Part 3"
        resp3 = client.put(
            f"/upload/resumable/{session_id}",
            data=chunk3,
            headers={
                "Content-Range": f"bytes 14-19/20",
                "Content-Length": str(len(chunk3))
            }
        )
        assert resp3.status_code == 200
        
        # Verify object was created
        obj_data = resp3.get_json()
        assert obj_data['name'] == 'multi-chunk.txt'
        assert int(obj_data['size']) == 20
    
    def test_upload_wrong_offset_returns_error(self, client, setup_bucket):
        """Test that uploading with wrong offset returns error"""
        bucket_name = setup_bucket
        
        # Initiate session
        init_resp = client.post(
            f"/upload/storage/v1/b/{bucket_name}/o?uploadType=resumable",
            json={
                "name": "wrong-offset.txt",
                "contentType": "text/plain"
            },
            headers={"Content-Type": "application/json"}
        )
        assert init_resp.status_code == 200
        session_id = init_resp.get_json()['sessionId']
        
        # Upload first chunk
        chunk1 = b"First"
        client.put(
            f"/upload/resumable/{session_id}",
            data=chunk1,
            headers={
                "Content-Range": f"bytes 0-4/20",
                "Content-Length": str(len(chunk1))
            }
        )
        
        # Try to upload with wrong offset (skip bytes)
        chunk2 = b"Third"
        resp2 = client.put(
            f"/upload/resumable/{session_id}",
            data=chunk2,
            headers={
                "Content-Range": f"bytes 10-14/20",  # Wrong! Should be 5-9
                "Content-Length": str(len(chunk2))
            }
        )
        
        # Should return 400 error
        assert resp2.status_code == 400
        data = resp2.get_json()
        assert 'error' in data
        assert 'offset mismatch' in data['error']['message'].lower()


class TestPhase3SignedURLs:
    """Test 2: Signed URLs"""
    
    def test_generate_signed_url_validates(self, client, setup_bucket):
        """Test that generated signed URL validates correctly"""
        from app.utils.signer import SignedURLService
        
        bucket_name = setup_bucket
        object_name = "test-signed.txt"
        
        # Upload object first
        client.post(
            f"/storage/v1/b/{bucket_name}/o?name={object_name}",
            data=b"Content for signed URL",
            headers={"Content-Type": "text/plain"}
        )
        
        # Generate signed URL
        signed_url = SignedURLService.generate_signed_url(
            method="GET",
            bucket=bucket_name,
            object_name=object_name,
            expires_in=3600
        )
        
        assert 'X-Goog-Algorithm' in signed_url
        assert 'X-Goog-Expires' in signed_url
        assert 'X-Goog-Timestamp' in signed_url
        assert 'X-Goog-Signature' in signed_url
        assert f"/signed/{bucket_name}/{object_name}" in signed_url
    
    def test_expired_signed_url_rejected(self, client, setup_bucket):
        """Test that expired signed URL is rejected"""
        from app.utils.signer import SignedURLService
        
        bucket_name = setup_bucket
        object_name = "expired-test.txt"
        
        # Upload object
        client.post(
            f"/storage/v1/b/{bucket_name}/o?name={object_name}",
            data=b"Content",
            headers={"Content-Type": "text/plain"}
        )
        
        # Generate signed URL with very short expiry
        signed_url = SignedURLService.generate_signed_url(
            method="GET",
            bucket=bucket_name,
            object_name=object_name,
            expires_in=1  # 1 second
        )
        
        # Wait for expiry
        time.sleep(2)
        
        # Try to use expired URL
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(signed_url)
        query_string = parsed.query
        
        # Make request - should fail
        response = client.get(f"/signed/{bucket_name}/{object_name}?{query_string}")
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'expired' in data['error']['message'].lower()
    
    def test_modified_signature_rejected(self, client, setup_bucket):
        """Test that modified query parameter invalidates signature"""
        from app.utils.signer import SignedURLService
        from urllib.parse import urlparse, parse_qs
        
        bucket_name = setup_bucket
        object_name = "tampered.txt"
        
        # Generate signed URL
        signed_url = SignedURLService.generate_signed_url(
            method="GET",
            bucket=bucket_name,
            object_name=object_name,
            expires_in=3600
        )
        
        # Parse URL and tamper with signature
        parsed = urlparse(signed_url)
        query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        query_params['X-Goog-Signature'] = 'tampered_signature'
        
        # Build tampered query string
        from urllib.parse import urlencode
        tampered_query = urlencode(query_params)
        
        # Upload object so it exists
        client.post(
            f"/storage/v1/b/{bucket_name}/o?name={object_name}",
            data=b"Content",
            headers={"Content-Type": "text/plain"}
        )
        
        # Try to use tampered URL
        response = client.get(f"/signed/{bucket_name}/{object_name}?{tampered_query}")
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'signature' in data['error']['message'].lower()
    
    def test_signed_get_download_works(self, client, setup_bucket):
        """Test that signed GET URL downloads object"""
        from app.utils.signer import SignedURLService
        
        bucket_name = setup_bucket
        object_name = "download-signed.txt"
        content = b"Downloaded via signed URL"
        
        # Upload object
        client.post(
            f"/storage/v1/b/{bucket_name}/o?name={object_name}",
            data=content,
            headers={"Content-Type": "text/plain"}
        )
        
        # Generate signed URL
        signed_url = SignedURLService.generate_signed_url(
            method="GET",
            bucket=bucket_name,
            object_name=object_name,
            expires_in=3600
        )
        
        # Extract query params
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(signed_url)
        query_string = parsed.query
        
        # Make request to signed endpoint
        response = client.get(f"/signed/{bucket_name}/{object_name}?{query_string}")
        
        assert response.status_code == 200
        assert response.data == content
    
    def test_signed_put_upload_works(self, client, setup_bucket):
        """Test that signed PUT URL uploads object"""
        from app.utils.signer import SignedURLService
        
        bucket_name = setup_bucket
        object_name = "upload-signed.txt"
        content = b"Uploaded via signed URL"
        
        # Generate signed PUT URL
        signed_url = SignedURLService.generate_signed_url(
            method="PUT",
            bucket=bucket_name,
            object_name=object_name,
            expires_in=3600
        )
        
        # Extract query params
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(signed_url)
        query_string = parsed.query
        
        # Make PUT request to signed endpoint
        response = client.put(
            f"/signed/{bucket_name}/{object_name}?{query_string}",
            data=content,
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 200
        
        # Verify object metadata
        data = response.get_json()
        assert data['name'] == object_name
        assert data['bucket'] == bucket_name
        
        # Verify object was actually uploaded
        get_resp = client.get(f"/storage/v1/b/{bucket_name}/o/{object_name}")
        assert get_resp.status_code == 200
