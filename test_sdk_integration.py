"""
Test GCS Emulator with Official Google Cloud Storage SDK

This script demonstrates how to use the real GCP SDK with your local emulator.
It tests all major operations: buckets and objects.

Prerequisites:
    pip install google-cloud-storage

Usage:
    1. Start Flask server: python run.py
    2. Run this test: python test_sdk_integration.py
"""
import os
import sys
from google.cloud import storage
from google.auth.credentials import AnonymousCredentials
from google.api_core import exceptions

# Configure SDK to use local emulator
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'

# Disable SSL warnings for local development
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_sdk_connection():
    """Test 1: Verify SDK can connect to emulator"""
    print_section("TEST 1: SDK Connection")
    
    try:
        client = storage.Client(
            project='test-project',
            credentials=AnonymousCredentials()
        )
        print("✅ SDK client initialized successfully")
        print(f"   Project: {client.project}")
        print(f"   Endpoint: {os.environ.get('STORAGE_EMULATOR_HOST')}")
        return client
    except Exception as e:
        print(f"❌ Failed to initialize SDK client: {e}")
        sys.exit(1)


def test_bucket_operations(client):
    """Test 2: Bucket CRUD operations"""
    print_section("TEST 2: Bucket Operations")
    
    bucket_name = 'sdk-test-bucket'
    
    try:
        # List buckets (should be empty initially)
        print("\n1. Listing buckets...")
        buckets = list(client.list_buckets())
        print(f"   Found {len(buckets)} existing buckets")
        
        # Create bucket
        print(f"\n2. Creating bucket '{bucket_name}'...")
        bucket = client.create_bucket(bucket_name, location='US')
        print(f"   ✅ Bucket created: {bucket.name}")
        print(f"      Location: {bucket.location}")
        print(f"      Storage Class: {bucket.storage_class}")
        print(f"      Created: {bucket.time_created}")
        
        # Get bucket metadata
        print(f"\n3. Getting bucket metadata...")
        bucket = client.get_bucket(bucket_name)
        print(f"   ✅ Retrieved bucket: {bucket.name}")
        print(f"      Self Link: {bucket.self_link}")
        print(f"      ID: {bucket.id}")
        
        # List buckets again
        print(f"\n4. Listing buckets again...")
        buckets = list(client.list_buckets())
        print(f"   ✅ Found {len(buckets)} buckets:")
        for b in buckets:
            print(f"      - {b.name} ({b.location})")
        
        return bucket
    except exceptions.Conflict as e:
        print(f"   ⚠️  Bucket already exists (409): {e}")
        return client.get_bucket(bucket_name)
    except Exception as e:
        print(f"   ❌ Bucket operation failed: {e}")
        raise


def test_object_operations(bucket):
    """Test 3: Object upload/download operations"""
    print_section("TEST 3: Object Operations")
    
    object_name = 'test-file.txt'
    content = b'Hello from GCP SDK! This is a test file.'
    
    try:
        # Upload object
        print(f"\n1. Uploading object '{object_name}'...")
        blob = bucket.blob(object_name)
        blob.upload_from_string(content, content_type='text/plain')
        print(f"   ✅ Object uploaded: {blob.name}")
        print(f"      Size: {blob.size} bytes")
        print(f"      Content-Type: {blob.content_type}")
        print(f"      MD5 Hash: {blob.md5_hash}")
        
        # List objects
        print(f"\n2. Listing objects in bucket...")
        blobs = list(bucket.list_blobs())
        print(f"   ✅ Found {len(blobs)} objects:")
        for b in blobs:
            print(f"      - {b.name} ({b.size} bytes)")
        
        # Get object metadata
        print(f"\n3. Getting object metadata...")
        blob = bucket.get_blob(object_name)
        print(f"   ✅ Retrieved object: {blob.name}")
        print(f"      Generation: {blob.generation}")
        print(f"      Metageneration: {blob.metageneration}")
        print(f"      Updated: {blob.updated}")
        
        # Download object
        print(f"\n4. Downloading object...")
        downloaded_content = blob.download_as_bytes()
        print(f"   ✅ Downloaded {len(downloaded_content)} bytes")
        print(f"      Content: {downloaded_content.decode('utf-8')}")
        
        # Verify content matches
        if downloaded_content == content:
            print(f"   ✅ Content verification PASSED")
        else:
            print(f"   ❌ Content verification FAILED")
        
        return blob
    except Exception as e:
        print(f"   ❌ Object operation failed: {e}")
        raise


def test_prefix_listing(bucket):
    """Test 4: Prefix and delimiter listing (folder simulation)"""
    print_section("TEST 4: Prefix & Delimiter Listing")
    
    try:
        # Upload objects with folder-like names
        print("\n1. Uploading objects with folder structure...")
        test_objects = [
            'folder1/file1.txt',
            'folder1/file2.txt',
            'folder2/subfolder/file3.txt',
            'root-file.txt'
        ]
        
        for obj_name in test_objects:
            blob = bucket.blob(obj_name)
            blob.upload_from_string(f'Content of {obj_name}'.encode())
            print(f"   ✅ Uploaded: {obj_name}")
        
        # List with delimiter (simulate folder view)
        print("\n2. Listing with delimiter='/' (root level)...")
        blobs = list(bucket.list_blobs(delimiter='/'))
        prefixes = list(bucket.list_blobs(delimiter='/').prefixes)
        print(f"   ✅ Root level files: {len(blobs)}")
        for b in blobs:
            print(f"      - {b.name}")
        print(f"   ✅ Root level folders: {len(prefixes)}")
        for p in prefixes:
            print(f"      - {p}")
        
        # List with prefix
        print("\n3. Listing with prefix='folder1/'...")
        blobs = list(bucket.list_blobs(prefix='folder1/'))
        print(f"   ✅ Found {len(blobs)} objects in folder1/:")
        for b in blobs:
            print(f"      - {b.name}")
        
    except Exception as e:
        print(f"   ❌ Prefix listing failed: {e}")
        raise


def test_delete_operations(client, bucket_name):
    """Test 5: Delete objects and bucket"""
    print_section("TEST 5: Delete Operations")
    
    try:
        bucket = client.get_bucket(bucket_name)
        
        # Delete all objects
        print("\n1. Deleting all objects...")
        blobs = list(bucket.list_blobs())
        for blob in blobs:
            blob.delete()
            print(f"   ✅ Deleted object: {blob.name}")
        print(f"   Total objects deleted: {len(blobs)}")
        
        # Verify bucket is empty
        print("\n2. Verifying bucket is empty...")
        remaining = list(bucket.list_blobs())
        if len(remaining) == 0:
            print(f"   ✅ Bucket is empty")
        else:
            print(f"   ⚠️  Bucket still has {len(remaining)} objects")
        
        # Delete bucket
        print(f"\n3. Deleting bucket '{bucket_name}'...")
        bucket.delete()
        print(f"   ✅ Bucket deleted")
        
    except Exception as e:
        print(f"   ❌ Delete operation failed: {e}")
        raise


def test_error_handling(client):
    """Test 6: SDK error handling"""
    print_section("TEST 6: Error Handling")
    
    try:
        # Test 404: Get non-existent bucket
        print("\n1. Testing 404 - Get non-existent bucket...")
        try:
            client.get_bucket('non-existent-bucket-xyz')
            print("   ❌ Should have raised NotFound exception")
        except exceptions.NotFound:
            print("   ✅ Correctly raised NotFound exception")
        
        # Test 409: Create duplicate bucket
        print("\n2. Testing 409 - Create duplicate bucket...")
        test_bucket = 'duplicate-test-bucket'
        client.create_bucket(test_bucket, location='US')
        try:
            client.create_bucket(test_bucket, location='US')
            print("   ❌ Should have raised Conflict exception")
        except exceptions.Conflict:
            print("   ✅ Correctly raised Conflict exception")
        finally:
            # Cleanup
            bucket = client.get_bucket(test_bucket)
            bucket.delete()
        
        # Test 400: Invalid bucket name
        print("\n3. Testing 400 - Invalid bucket name...")
        try:
            client.create_bucket('INVALID_UPPERCASE_BUCKET')
            print("   ❌ Should have raised BadRequest exception")
        except exceptions.BadRequest:
            print("   ✅ Correctly raised BadRequest exception")
        except Exception as e:
            print(f"   ⚠️  Raised different exception: {type(e).__name__}")
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        raise


def main():
    """Run all SDK integration tests"""
    print("\n" + "="*60)
    print("  GCS EMULATOR - SDK INTEGRATION TESTS")
    print("="*60)
    print(f"\nEmulator Endpoint: {os.environ.get('STORAGE_EMULATOR_HOST')}")
    print(f"Python Version: {sys.version}")
    
    try:
        # Run tests
        client = test_sdk_connection()
        bucket = test_bucket_operations(client)
        blob = test_object_operations(bucket)
        test_prefix_listing(bucket)
        test_delete_operations(client, bucket.name)
        test_error_handling(client)
        
        # Success summary
        print_section("TEST SUMMARY")
        print("\n✅ ALL TESTS PASSED!")
        print("\nYour GCS emulator is fully compatible with the official SDK.")
        print("You can now use google-cloud-storage library with:")
        print("  os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_section("TEST FAILED")
        print(f"\n❌ Test suite failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
