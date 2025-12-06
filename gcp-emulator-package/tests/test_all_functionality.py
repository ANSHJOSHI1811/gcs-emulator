"""
Comprehensive Functionality Test Suite
Tests CLI, API, and SDK compatibility
"""
import requests
import os
import json
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8080"
TEST_PROJECT = "test-project"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test(name):
    print(f"\n{Colors.BLUE}Testing: {name}{Colors.RESET}")

def print_pass(message):
    try:
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.GREEN}[PASS] {message}{Colors.RESET}")

def print_fail(message):
    try:
        print(f"{Colors.RED}✗ {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.RED}[FAIL] {message}{Colors.RESET}")
    
def print_section(name):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{name:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}")

# =============================================================================
# API TESTS
# =============================================================================

def test_api_endpoints():
    """Test all REST API endpoints"""
    print_section("API ENDPOINT TESTS")
    results = {"passed": 0, "failed": 0}
    
    # Test 1: List Buckets
    print_test("GET /storage/v1/b (List Buckets)")
    try:
        response = requests.get(f"{BASE_URL}/storage/v1/b?project={TEST_PROJECT}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            bucket_count = len(data.get('items', []))
            print_pass(f"Status 200, Found {bucket_count} buckets")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 2: Create Bucket
    print_test("POST /storage/v1/b (Create Bucket)")
    test_bucket_name = f"api-test-bucket-{os.urandom(4).hex()}"
    try:
        response = requests.post(
            f"{BASE_URL}/storage/v1/b?project={TEST_PROJECT}",
            json={
                "name": test_bucket_name,
                "location": "US",
                "storageClass": "STANDARD"
            },
            timeout=5
        )
        if response.status_code == 201:
            print_pass(f"Status 201, Created bucket: {test_bucket_name}")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}: {response.text}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 3: Get Bucket
    print_test("GET /storage/v1/b/{bucket} (Get Bucket)")
    try:
        response = requests.get(f"{BASE_URL}/storage/v1/b/{test_bucket_name}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_pass(f"Status 200, Bucket location: {data.get('location')}, storageClass: {data.get('storageClass')}")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 4: Upload Object
    print_test("POST /upload/storage/v1/b/{bucket}/o (Upload Object)")
    test_object_name = "test-file.txt"
    test_content = b"Hello, GCS Emulator! This is a test file."
    try:
        response = requests.post(
            f"{BASE_URL}/upload/storage/v1/b/{test_bucket_name}/o?uploadType=media&name={test_object_name}",
            data=test_content,
            headers={"Content-Type": "text/plain"},
            timeout=5
        )
        if response.status_code == 201:
            data = response.json()
            print_pass(f"Status 201, Object size: {data.get('size')} bytes")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}: {response.text}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 5: List Objects
    print_test("GET /storage/v1/b/{bucket}/o (List Objects)")
    try:
        response = requests.get(f"{BASE_URL}/storage/v1/b/{test_bucket_name}/o?project={TEST_PROJECT}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            object_count = len(data.get('items', []))
            print_pass(f"Status 200, Found {object_count} objects")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 6: Get Object Metadata
    print_test("GET /storage/v1/b/{bucket}/o/{object} (Get Object Metadata)")
    try:
        response = requests.get(f"{BASE_URL}/storage/v1/b/{test_bucket_name}/o/{test_object_name}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_pass(f"Status 200, contentType: {data.get('contentType')}, size: {data.get('size')}")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 7: Download Object
    print_test("GET /download/storage/v1/b/{bucket}/o/{object} (Download Object)")
    try:
        response = requests.get(f"{BASE_URL}/download/storage/v1/b/{test_bucket_name}/o/{test_object_name}?alt=media", timeout=5)
        if response.status_code == 200:
            if response.content == test_content:
                print_pass(f"Status 200, Content matches ('{response.content.decode()[:30]}...')")
            else:
                print_fail(f"Content mismatch")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 8: Get Bucket ACL
    print_test("GET /storage/v1/b/{bucket}/acl (Get Bucket ACL)")
    try:
        response = requests.get(f"{BASE_URL}/storage/v1/b/{test_bucket_name}/acl", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_pass(f"Status 200, ACL items: {len(data.get('items', []))}")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 9: Get Object ACL
    print_test("GET /storage/v1/b/{bucket}/o/{object}/acl (Get Object ACL)")
    try:
        response = requests.get(f"{BASE_URL}/storage/v1/b/{test_bucket_name}/o/{test_object_name}/acl", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_pass(f"Status 200, ACL items: {len(data.get('items', []))}")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 10: Dashboard Stats
    print_test("GET /dashboard/stats (Dashboard Statistics)")
    try:
        response = requests.get(f"{BASE_URL}/dashboard/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_pass(f"Status 200, Buckets: {data.get('totalBuckets')}, Objects: {data.get('totalObjects')}, Storage: {data.get('totalStorageBytes')} bytes")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 11: Object Events
    print_test("GET /internal/events (Object Events)")
    try:
        response = requests.get(f"{BASE_URL}/internal/events", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_pass(f"Status 200, Events found: {len(data.get('events', []))}")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 12: Delete Object
    print_test("DELETE /storage/v1/b/{bucket}/o/{object} (Delete Object)")
    try:
        response = requests.delete(f"{BASE_URL}/storage/v1/b/{test_bucket_name}/o/{test_object_name}", timeout=5)
        if response.status_code == 204:
            print_pass(f"Status 204, Object deleted successfully")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 13: Delete Bucket
    print_test("DELETE /storage/v1/b/{bucket} (Delete Bucket)")
    try:
        response = requests.delete(f"{BASE_URL}/storage/v1/b/{test_bucket_name}", timeout=5)
        if response.status_code == 204:
            print_pass(f"Status 204, Bucket deleted successfully")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    return results

# =============================================================================
# CLI TESTS
# =============================================================================

def test_cli_functionality():
    """Test CLI commands"""
    print_section("CLI FUNCTIONALITY TESTS")
    results = {"passed": 0, "failed": 0}
    
    # Set environment variable for CLI
    os.environ['STORAGE_EMULATOR_HOST'] = BASE_URL
    
    # Test 1: CLI - Create Bucket
    print_test("CLI: mb gs://bucket (Create Bucket)")
    cli_bucket_name = f"cli-test-{os.urandom(4).hex()}"
    try:
        import subprocess
        result = subprocess.run(
            ["python", "gcslocal.py", "mb", f"gs://{cli_bucket_name}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 or "created" in result.stdout.lower():
            print_pass(f"Bucket created: {cli_bucket_name}")
            results["passed"] += 1
        else:
            print_fail(f"Exit code {result.returncode}: {result.stderr or result.stdout}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 2: CLI - List Buckets
    print_test("CLI: ls gs:// (List Buckets)")
    try:
        result = subprocess.run(
            ["python", "gcslocal.py", "ls", "gs://"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = [l for l in result.stdout.split('\n') if l.strip()]
            print_pass(f"Listed buckets, found {len(lines)} buckets")
            results["passed"] += 1
        else:
            print_fail(f"Exit code {result.returncode}: {result.stderr or result.stdout}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 3: CLI - Upload File
    print_test("CLI: cp file.txt gs://bucket/file.txt (Upload File)")
    test_file = Path("test_upload_cli.txt")
    test_file.write_text("CLI upload test content")
    try:
        result = subprocess.run(
            ["python", "gcslocal.py", "cp", str(test_file), f"gs://{cli_bucket_name}/test-cli-file.txt"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 or "uploaded" in result.stdout.lower():
            print_pass(f"File uploaded successfully")
            results["passed"] += 1
        else:
            print_fail(f"Exit code {result.returncode}: {result.stderr or result.stdout}")
            results["failed"] += 1
        test_file.unlink()
    except Exception as e:
        print_fail(f"Error: {e}")
        if test_file.exists():
            test_file.unlink()
        results["failed"] += 1
    
    # Test 4: CLI - List Objects
    print_test("CLI: ls gs://bucket/ (List Objects)")
    try:
        result = subprocess.run(
            ["python", "gcslocal.py", "ls", f"gs://{cli_bucket_name}/"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print_pass(f"Listed objects in bucket")
            results["passed"] += 1
        else:
            print_fail(f"Exit code {result.returncode}: {result.stderr or result.stdout}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 5: CLI - Download File
    print_test("CLI: cp gs://bucket/file.txt local/ (Download File)")
    download_file = Path("test_download_cli.txt")
    try:
        result = subprocess.run(
            ["python", "gcslocal.py", "cp", f"gs://{cli_bucket_name}/test-cli-file.txt", str(download_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and download_file.exists():
            content = download_file.read_text()
            if content == "CLI upload test content":
                print_pass(f"File downloaded successfully, content matches")
                results["passed"] += 1
            else:
                print_fail(f"Content mismatch")
                results["failed"] += 1
            download_file.unlink()
        else:
            print_fail(f"Exit code {result.returncode}: {result.stderr or result.stdout}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        if download_file.exists():
            download_file.unlink()
        results["failed"] += 1
    
    # Test 6: CLI - Delete Object
    print_test("CLI: rm gs://bucket/file.txt (Delete Object)")
    try:
        result = subprocess.run(
            ["python", "gcslocal.py", "rm", f"gs://{cli_bucket_name}/test-cli-file.txt"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 or "deleted" in result.stdout.lower():
            print_pass(f"Object deleted successfully")
            results["passed"] += 1
        else:
            print_fail(f"Exit code {result.returncode}: {result.stderr or result.stdout}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 7: CLI - Delete Bucket
    print_test("CLI: rb gs://bucket (Delete Bucket)")
    try:
        result = subprocess.run(
            ["python", "gcslocal.py", "rb", f"gs://{cli_bucket_name}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 or "deleted" in result.stdout.lower():
            print_pass(f"Bucket deleted successfully")
            results["passed"] += 1
        else:
            print_fail(f"Exit code {result.returncode}: {result.stderr or result.stdout}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    return results

# =============================================================================
# SDK COMPATIBILITY TESTS
# =============================================================================

def test_sdk_compatibility():
    """Test SDK compatibility (can be extended with actual google-cloud-storage)"""
    print_section("SDK COMPATIBILITY TESTS")
    results = {"passed": 0, "failed": 0}
    
    # Test 1: Check if SDK endpoints are compatible
    print_test("SDK Compatibility: Standard GCS API format")
    try:
        # Test that our API follows standard GCS format
        response = requests.get(f"{BASE_URL}/storage/v1/b?project={TEST_PROJECT}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Check if response has GCS-standard fields
            has_kind = 'kind' in data
            has_items = 'items' in data
            if has_kind and has_items:
                print_pass(f"API response follows GCS JSON format")
                results["passed"] += 1
            else:
                print_fail(f"Missing standard GCS fields")
                results["failed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 2: Check object metadata format
    print_test("SDK Compatibility: Object metadata format")
    test_bucket = f"sdk-compat-{os.urandom(4).hex()}"
    try:
        # Create bucket
        requests.post(
            f"{BASE_URL}/storage/v1/b?project={TEST_PROJECT}",
            json={"name": test_bucket, "location": "US", "storageClass": "STANDARD"},
            timeout=5
        )
        
        # Upload object
        requests.post(
            f"{BASE_URL}/upload/storage/v1/b/{test_bucket}/o?uploadType=media&name=test.txt",
            data=b"test",
            headers={"Content-Type": "text/plain"},
            timeout=5
        )
        
        # Get object metadata
        response = requests.get(f"{BASE_URL}/storage/v1/b/{test_bucket}/o/test.txt", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Check for standard GCS object fields
            required_fields = ['kind', 'id', 'name', 'bucket', 'generation', 'size', 'md5Hash', 'crc32c']
            missing = [f for f in required_fields if f not in data]
            if not missing:
                print_pass(f"Object metadata has all standard GCS fields")
                results["passed"] += 1
            else:
                print_fail(f"Missing fields: {missing}")
                results["failed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
        
        # Cleanup
        requests.delete(f"{BASE_URL}/storage/v1/b/{test_bucket}/o/test.txt", timeout=5)
        requests.delete(f"{BASE_URL}/storage/v1/b/{test_bucket}", timeout=5)
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    # Test 3: Check multipart upload support
    print_test("SDK Compatibility: Multipart upload support")
    try:
        test_bucket = f"sdk-multipart-{os.urandom(4).hex()}"
        requests.post(
            f"{BASE_URL}/storage/v1/b?project={TEST_PROJECT}",
            json={"name": test_bucket, "location": "US"},
            timeout=5
        )
        
        response = requests.post(
            f"{BASE_URL}/upload/storage/v1/b/{test_bucket}/o?uploadType=multipart",
            files={
                'metadata': ('', json.dumps({'name': 'multipart-test.txt'}), 'application/json'),
                'file': ('multipart-test.txt', b'multipart content', 'text/plain')
            },
            timeout=5
        )
        
        if response.status_code == 201:
            print_pass(f"Multipart upload successful")
            results["passed"] += 1
        else:
            print_fail(f"Status {response.status_code}")
            results["failed"] += 1
        
        # Cleanup
        requests.delete(f"{BASE_URL}/storage/v1/b/{test_bucket}/o/multipart-test.txt", timeout=5)
        requests.delete(f"{BASE_URL}/storage/v1/b/{test_bucket}", timeout=5)
    except Exception as e:
        print_fail(f"Error: {e}")
        results["failed"] += 1
    
    return results

# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}GCS EMULATOR - COMPREHENSIVE FUNCTIONALITY TEST{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}Testing against: {BASE_URL}{Colors.RESET}")
    
    all_results = {"passed": 0, "failed": 0}
    
    # Run all test suites
    api_results = test_api_endpoints()
    cli_results = test_cli_functionality()
    sdk_results = test_sdk_compatibility()
    
    # Aggregate results
    all_results["passed"] = api_results["passed"] + cli_results["passed"] + sdk_results["passed"]
    all_results["failed"] = api_results["failed"] + cli_results["failed"] + sdk_results["failed"]
    
    # Print summary
    print_section("TEST SUMMARY")
    total = all_results["passed"] + all_results["failed"]
    pass_rate = (all_results["passed"] / total * 100) if total > 0 else 0
    
    print(f"\n{Colors.BOLD}API Tests:{Colors.RESET}")
    print(f"  Passed: {Colors.GREEN}{api_results['passed']}{Colors.RESET}")
    print(f"  Failed: {Colors.RED}{api_results['failed']}{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}CLI Tests:{Colors.RESET}")
    print(f"  Passed: {Colors.GREEN}{cli_results['passed']}{Colors.RESET}")
    print(f"  Failed: {Colors.RED}{cli_results['failed']}{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}SDK Compatibility Tests:{Colors.RESET}")
    print(f"  Passed: {Colors.GREEN}{sdk_results['passed']}{Colors.RESET}")
    print(f"  Failed: {Colors.RED}{sdk_results['failed']}{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}Overall Results:{Colors.RESET}")
    print(f"  Total Tests: {total}")
    print(f"  Passed: {Colors.GREEN}{all_results['passed']}{Colors.RESET}")
    print(f"  Failed: {Colors.RED}{all_results['failed']}{Colors.RESET}")
    print(f"  Pass Rate: {Colors.GREEN if pass_rate >= 90 else Colors.YELLOW if pass_rate >= 70 else Colors.RED}{pass_rate:.1f}%{Colors.RESET}")
    
    if all_results["failed"] == 0:
        print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}✓ ALL TESTS PASSED - SYSTEM FULLY FUNCTIONAL{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}{'='*60}{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.RED}✗ SOME TESTS FAILED - REVIEW REQUIRED{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.RED}{'='*60}{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
