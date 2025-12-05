"""
End-to-End Tests for Object Versioning and Preconditions
Tests generation, metageneration, precondition headers, version deletion
"""
import pytest
from app.models.object import Object, ObjectVersion


class TestVersionCreation:
    """Tests for version creation and generation incrementing"""
    
    def test_upload_creates_generation_1(self, app, client):
        """First upload should create generation=1, metageneration=1"""
        with app.app_context():
            # Create bucket
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Upload object
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=test.txt',
                data=b'Version 1',
                headers={'Content-Type': 'text/plain'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['generation'] == '1'
            assert data['metageneration'] == '1'
            assert data['name'] == 'test.txt'
    
    def test_upload_twice_creates_two_generations(self, app, client):
        """Uploading same object twice should create generation 1 and 2"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # First upload
            response1 = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'Version 1'
            )
            assert response1.status_code == 200
            data1 = response1.get_json()
            assert data1['generation'] == '1'
            
            # Second upload (overwrite)
            response2 = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'Version 2'
            )
            assert response2.status_code == 200
            data2 = response2.get_json()
            assert data2['generation'] == '2'
            assert data2['metageneration'] == '1'  # Resets to 1 on new generation
    
    def test_upload_three_times_increments_generation(self, app, client):
        """Multiple uploads should increment generation: 1 → 2 → 3"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            for i in range(1, 4):
                response = client.post(
                    '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                    data=f'Version {i}'.encode()
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data['generation'] == str(i)
                assert data['metageneration'] == '1'


class TestPreconditions:
    """Tests for precondition validation"""
    
    def test_if_generation_match_success(self, app, client):
        """Upload succeeds when generation matches"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Create version 1
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            
            # Overwrite with ifGenerationMatch=1 should succeed
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt&ifGenerationMatch=1',
                data=b'V2'
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['generation'] == '2'
    
    def test_if_generation_match_fails(self, app, client):
        """Upload fails with 412 when generation doesn't match"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Create version 1
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            
            # Try overwrite with ifGenerationMatch=999 should fail
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt&ifGenerationMatch=999',
                data=b'V2'
            )
            assert response.status_code == 412
            data = response.get_json()
            assert 'error' in data
            assert 'Precondition failed' in data['error']['message']
    
    def test_if_generation_not_match_success(self, app, client):
        """Upload succeeds when generation doesn't match specified value"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Create version 1
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            
            # Overwrite with ifGenerationNotMatch=999 should succeed
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt&ifGenerationNotMatch=999',
                data=b'V2'
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['generation'] == '2'
    
    def test_if_generation_not_match_fails(self, app, client):
        """Upload fails with 412 when generation equals specified value"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Create version 1
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            
            # Try overwrite with ifGenerationNotMatch=1 should fail
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt&ifGenerationNotMatch=1',
                data=b'V2'
            )
            assert response.status_code == 412
    
    def test_if_generation_match_zero_for_new_object(self, app, client):
        """ifGenerationMatch=0 succeeds only for new objects"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Create new object with ifGenerationMatch=0 should succeed
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=newfile.txt&ifGenerationMatch=0',
                data=b'New'
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['generation'] == '1'
    
    def test_if_generation_match_zero_fails_for_existing(self, app, client):
        """ifGenerationMatch=0 fails with 412 for existing objects"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Create object first
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            
            # Try with ifGenerationMatch=0 should fail
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt&ifGenerationMatch=0',
                data=b'V2'
            )
            assert response.status_code == 412
    
    def test_if_metageneration_match_success(self, app, client):
        """Upload succeeds when metageneration matches"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Create object
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            
            # Overwrite with ifMetagenerationMatch=1 should succeed
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt&ifMetagenerationMatch=1',
                data=b'V2'
            )
            assert response.status_code == 200
    
    def test_if_metageneration_match_fails(self, app, client):
        """Upload fails with 412 when metageneration doesn't match"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Create object
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            
            # Try with wrong metageneration
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt&ifMetagenerationMatch=999',
                data=b'V2'
            )
            assert response.status_code == 412


class TestVersionDownload:
    """Tests for downloading specific versions"""
    
    def test_download_latest_version(self, app, client):
        """Download without generation parameter returns latest version"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Upload two versions
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'Version 1'
            )
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'Version 2'
            )
            
            # Download latest
            response = client.get('/storage/v1/b/test-bucket/o/file.txt?alt=media')
            assert response.status_code == 200
            assert response.data == b'Version 2'
    
    def test_download_specific_version(self, app, client):
        """Download with generation parameter returns that specific version"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Upload two versions
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'Version 1'
            )
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'Version 2'
            )
            
            # Download generation 1
            response = client.get('/storage/v1/b/test-bucket/o/file.txt?alt=media&generation=1')
            assert response.status_code == 200
            assert response.data == b'Version 1'
    
    def test_download_nonexistent_version_fails(self, app, client):
        """Downloading non-existent version returns 404"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Upload one version
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'Version 1'
            )
            
            # Try to download non-existent generation 99
            response = client.get('/storage/v1/b/test-bucket/o/file.txt?alt=media&generation=99')
            assert response.status_code == 404


class TestVersionMetadata:
    """Tests for getting version metadata"""
    
    def test_get_metadata_latest_version(self, app, client):
        """Get metadata without generation returns latest version info"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Upload two versions
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V2'
            )
            
            # Get metadata
            response = client.get('/storage/v1/b/test-bucket/o/file.txt')
            assert response.status_code == 200
            data = response.get_json()
            assert data['generation'] == '2'
            assert data['metageneration'] == '1'
    
    def test_get_metadata_specific_version(self, app, client):
        """Get metadata with generation returns that version's info"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Upload two versions
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V2'
            )
            
            # Get generation 1 metadata
            response = client.get('/storage/v1/b/test-bucket/o/file.txt?generation=1')
            assert response.status_code == 200
            data = response.get_json()
            assert data['generation'] == '1'
            assert data['size'] == '2'  # "V1" is 2 bytes


class TestVersionDeletion:
    """Tests for deleting specific versions"""
    
    def test_delete_specific_version(self, app, client):
        """Delete specific version leaves other versions intact"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Upload three versions
            for i in range(1, 4):
                client.post(
                    '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                    data=f'V{i}'.encode()
                )
            
            # Delete generation 2
            response = client.delete('/storage/v1/b/test-bucket/o/file.txt?generation=2')
            assert response.status_code == 204
            
            # Verify generation 1 and 3 still exist
            resp1 = client.get('/storage/v1/b/test-bucket/o/file.txt?generation=1')
            assert resp1.status_code == 200
            
            resp3 = client.get('/storage/v1/b/test-bucket/o/file.txt?generation=3')
            assert resp3.status_code == 200
            
            # Generation 2 should be gone
            resp2 = client.get('/storage/v1/b/test-bucket/o/file.txt?generation=2')
            assert resp2.status_code == 404
    
    def test_delete_latest_version_promotes_previous(self, app, client):
        """Deleting latest version makes previous version the latest"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Upload two versions
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V2'
            )
            
            # Delete generation 2 (latest)
            client.delete('/storage/v1/b/test-bucket/o/file.txt?generation=2')
            
            # Download latest should now return V1
            response = client.get('/storage/v1/b/test-bucket/o/file.txt?alt=media')
            assert response.status_code == 200
            assert response.data == b'V1'
    
    def test_delete_all_versions(self, app, client):
        """Delete without generation removes all versions"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Upload two versions
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V2'
            )
            
            # Delete all versions
            response = client.delete('/storage/v1/b/test-bucket/o/file.txt')
            assert response.status_code == 204
            
            # Object should not exist anymore
            response = client.get('/storage/v1/b/test-bucket/o/file.txt')
            assert response.status_code == 404


class TestRoundTripVersioning:
    """Integration tests for complete versioning workflows"""
    
    def test_upload_download_multiple_versions_round_trip(self, app, client):
        """Complete flow: upload multiple versions, download each"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            versions = [b'Content A', b'Content B', b'Content C']
            
            # Upload all versions
            for i, content in enumerate(versions, 1):
                response = client.post(
                    '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=multi.txt',
                    data=content
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data['generation'] == str(i)
            
            # Download each version and verify
            for i, expected_content in enumerate(versions, 1):
                response = client.get(f'/storage/v1/b/test-bucket/o/multi.txt?alt=media&generation={i}')
                assert response.status_code == 200
                assert response.data == expected_content
    
    def test_complex_precondition_scenario(self, app, client):
        """Test combined preconditions: generation and metageneration"""
        with app.app_context():
            client.post('/storage/v1/b?project=test-project', json={'name': 'test-bucket'})
            
            # Create initial version
            client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt',
                data=b'V1'
            )
            
            # Overwrite with both generation=1 and metageneration=1
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt&ifGenerationMatch=1&ifMetagenerationMatch=1',
                data=b'V2'
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['generation'] == '2'
            
            # Try with generation match but metageneration mismatch
            response = client.post(
                '/upload/storage/v1/b/test-bucket/o?uploadType=media&name=file.txt&ifGenerationMatch=2&ifMetagenerationMatch=999',
                data=b'V3'
            )
            assert response.status_code == 412
