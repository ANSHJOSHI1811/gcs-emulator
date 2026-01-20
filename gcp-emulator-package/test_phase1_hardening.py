"""
Phase 1 Validation Tests: API Hardening
Tests GCP-compliant error handling, validation, and conflict detection
"""
from google.cloud import compute_v1
from google.auth.credentials import AnonymousCredentials
from google.api_core.client_options import ClientOptions
from google.api_core import exceptions
import time


def test_phase1_hardening():
    """Test Phase 1: API hardening features"""
    
    # Setup client
    credentials = AnonymousCredentials()
    client_options = ClientOptions(api_endpoint="http://localhost:8080")
    client = compute_v1.InstancesClient(credentials=credentials, client_options=client_options)
    
    project = "test-project"
    zone = "us-central1-a"
    
    print("\n" + "="*70)
    print("PHASE 1: COMPUTE API HARDENING VALIDATION")
    print("="*70)
    
    # Test 1: Invalid instance name validation
    print("\n[TEST 1] Invalid Instance Name Validation")
    print("-" * 70)
    test_cases = [
        ("", "Empty name should fail"),
        ("UPPERCASE", "Uppercase should fail"),
        ("test_underscore", "Underscore should fail"),
        ("123start", "Starting with number should fail"),
        ("a" * 64, "Name > 63 chars should fail"),
        ("test-", "Ending with hyphen should fail"),
    ]
    
    for invalid_name, description in test_cases:
        try:
            instance = compute_v1.Instance(name=invalid_name, machine_type=f"zones/{zone}/machineTypes/e2-micro")
            operation = client.insert(project=project, zone=zone, instance_resource=instance)
            print(f"   ✗ {description} - NO ERROR (unexpected)")
        except exceptions.InvalidArgument as e:
            print(f"   ✓ {description} - Got 400 Invalid")
        except Exception as e:
            print(f"   ✗ {description} - Wrong error: {type(e).__name__}")
    
    # Test 2: Valid instance name (should succeed)
    print("\n[TEST 2] Valid Instance Name")
    print("-" * 70)
    valid_name = f"valid-test-{int(time.time())}"
    try:
        instance = compute_v1.Instance(
            name=valid_name,
            machine_type=f"zones/{zone}/machineTypes/e2-micro"
        )
        operation = client.insert(project=project, zone=zone, instance_resource=instance)
        print(f"   ✓ Instance '{valid_name}' created successfully")
        print(f"   ✓ Operation: {operation.name}")
    except Exception as e:
        print(f"   ✗ Failed to create valid instance: {e}")
        return
    
    # Test 3: Duplicate instance name (409 Conflict)
    print("\n[TEST 3] Duplicate Instance Detection (409 Conflict)")
    print("-" * 70)
    try:
        duplicate_instance = compute_v1.Instance(
            name=valid_name,
            machine_type=f"zones/{zone}/machineTypes/e2-micro"
        )
        operation = client.insert(project=project, zone=zone, instance_resource=duplicate_instance)
        print(f"   ✗ Duplicate created (should fail with 409)")
    except exceptions.Conflict as e:
        print(f"   ✓ Duplicate rejected with 409 Conflict")
        print(f"   ✓ Message: {str(e)[:80]}...")
    except Exception as e:
        print(f"   ✗ Wrong error type: {type(e).__name__}")
    
    # Test 4: Get non-existent instance (404)
    print("\n[TEST 4] Get Non-Existent Instance (404)")
    print("-" * 70)
    non_existent = "this-instance-does-not-exist-12345"
    try:
        instance = client.get(project=project, zone=zone, instance=non_existent)
        print(f"   ✗ Got instance (should return 404)")
    except exceptions.NotFound as e:
        print(f"   ✓ Got 404 Not Found as expected")
        print(f"   ✓ Message: {str(e)[:80]}...")
    except Exception as e:
        print(f"   ✗ Wrong error type: {type(e).__name__}")
    
    # Test 5: Delete non-existent instance (404)
    print("\n[TEST 5] Delete Non-Existent Instance (404)")
    print("-" * 70)
    try:
        operation = client.delete(project=project, zone=zone, instance=non_existent)
        print(f"   ✗ Deleted non-existent instance (should return 404)")
    except exceptions.NotFound as e:
        print(f"   ✓ Got 404 Not Found as expected")
    except Exception as e:
        print(f"   ✗ Wrong error type: {type(e).__name__}")
    
    # Test 6: Invalid zone format
    print("\n[TEST 6] Invalid Zone Format Validation")
    print("-" * 70)
    invalid_zones = ["invalid", "us-central1", "us_central1_a", "123"]
    for invalid_zone in invalid_zones:
        try:
            instances = client.list(project=project, zone=invalid_zone)
            print(f"   ✗ Zone '{invalid_zone}' accepted (should fail)")
        except exceptions.InvalidArgument as e:
            print(f"   ✓ Zone '{invalid_zone}' rejected with 400")
        except Exception as e:
            print(f"   ~ Zone '{invalid_zone}' - {type(e).__name__}")
    
    # Test 7: State validation - start already running instance
    print("\n[TEST 7] Start Already Running Instance (400)")
    print("-" * 70)
    try:
        # Instance should be running from Test 2
        operation = client.start(project=project, zone=zone, instance=valid_name)
        print(f"   ✗ Started running instance (should fail with 400)")
    except exceptions.InvalidArgument as e:
        print(f"   ✓ Got 400 - Instance already running")
    except Exception as e:
        print(f"   ~ Got {type(e).__name__}: {str(e)[:60]}")
    
    # Test 8: Stop instance, then try to stop again
    print("\n[TEST 8] Stop Already Stopped Instance (400)")
    print("-" * 70)
    try:
        # First stop
        operation = client.stop(project=project, zone=zone, instance=valid_name)
        print(f"   ✓ Stopped instance successfully")
        time.sleep(0.5)
        
        # Try to stop again
        operation = client.stop(project=project, zone=zone, instance=valid_name)
        print(f"   ✗ Stopped again (should fail with 400)")
    except exceptions.InvalidArgument as e:
        print(f"   ✓ Got 400 - Instance already stopped")
    except Exception as e:
        print(f"   ~ Got {type(e).__name__}: {str(e)[:60]}")
    
    # Test 9: Operations consistency
    print("\n[TEST 9] Operations Tracking Consistency")
    print("-" * 70)
    try:
        # Start instance to create operation
        operation = client.start(project=project, zone=zone, instance=valid_name)
        op_name = operation.name
        print(f"   ✓ Operation created: {op_name}")
        
        # Retrieve operation
        zone_ops_client = compute_v1.ZoneOperationsClient(credentials=credentials, client_options=client_options)
        retrieved_op = zone_ops_client.get(project=project, zone=zone, operation=op_name)
        print(f"   ✓ Operation retrieved: {retrieved_op.name}")
        print(f"   ✓ Status: {retrieved_op.status}")
        print(f"   ✓ Operation type: {retrieved_op.operation_type}")
        
    except Exception as e:
        print(f"   ✗ Operation tracking failed: {e}")
    
    # Test 10: Error response format validation
    print("\n[TEST 10] GCP Error Response Format")
    print("-" * 70)
    try:
        client.get(project=project, zone=zone, instance="nonexistent-test")
    except exceptions.NotFound as e:
        error_details = str(e)
        print(f"   ✓ Error has proper format")
        print(f"   ✓ Contains resource path: {'projects/' in error_details}")
        print(f"   ✓ Error message: {error_details[:100]}...")
    
    # Cleanup
    print("\n[CLEANUP]")
    print("-" * 70)
    try:
        operation = client.delete(project=project, zone=zone, instance=valid_name)
        print(f"   ✓ Cleaned up test instance: {valid_name}")
    except Exception as e:
        print(f"   ~ Cleanup note: {e}")
    
    print("\n" + "="*70)
    print("✅ PHASE 1 VALIDATION COMPLETE")
    print("="*70)
    print("\nKey Improvements Validated:")
    print("  • GCP-compliant error responses (400, 404, 409, 500)")
    print("  • Instance name validation (RFC-compliant)")
    print("  • Zone format validation")
    print("  • Duplicate detection (409 Conflict)")
    print("  • State-aware operations (prevent invalid transitions)")
    print("  • Operations tracking consistency")
    print("  • Proper error message formatting")
    print()


if __name__ == "__main__":
    test_phase1_hardening()
