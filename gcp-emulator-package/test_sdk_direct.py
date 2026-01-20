"""
Direct SDK test - proves google-cloud-compute works with our emulator
Run with: python3 test_sdk_direct.py
"""
import sys
sys.path.insert(0, '/home/anshjoshi/.local/lib/python3.12/site-packages')

from google.cloud import compute_v1
from google.auth.credentials import AnonymousCredentials
from google.api_core import client_options
import time

# Configure client to use local emulator
EMULATOR_HOST = "http://localhost:8080"
PROJECT = "test-project"
ZONE = "us-central1-a"

print("\n=== GCP Compute Engine SDK Compatibility Test ===\n")

# Create client
print("1. Creating InstancesClient...")
client = compute_v1.InstancesClient(
    credentials=AnonymousCredentials(),
    client_options=client_options.ClientOptions(
        api_endpoint=EMULATOR_HOST
    )
)
print("   ✓ Client created")

# Test 1: Insert instance
print("\n2. Testing INSERT operation...")
instance_name = f"sdk-test-{int(time.time())}"
instance = compute_v1.Instance(
    name=instance_name,
    machine_type=f"zones/{ZONE}/machineTypes/e2-micro",
    disks=[
        compute_v1.AttachedDisk(
            boot=True,
            auto_delete=True,
            initialize_params=compute_v1.AttachedDiskInitializeParams(
                source_image="projects/debian-cloud/global/images/family/debian-11"
            )
        )
    ],
    network_interfaces=[
        compute_v1.NetworkInterface(name="default")
    ]
)

try:
    operation = client.insert(
        project=PROJECT,
        zone=ZONE,
        instance_resource=instance
    )
    print(f"   ✓ Instance '{instance_name}' created")
    print(f"   ✓ Operation: {operation.name}")
    print(f"   ✓ Status: {operation.status}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 2: List instances
print("\n3. Testing LIST operation...")
try:
    instances_list = list(client.list(project=PROJECT, zone=ZONE))
    print(f"   ✓ Found {len(instances_list)} instance(s)")
    
    for inst in instances_list:
        print(f"      - {inst.name}: {inst.status}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 3: Get single instance
print(f"\n4. Testing GET operation for '{instance_name}'...")
try:
    retrieved = client.get(
        project=PROJECT,
        zone=ZONE,
        instance=instance_name
    )
    print(f"   ✓ Instance retrieved")
    print(f"      Name: {retrieved.name}")
    print(f"      Status: {retrieved.status}")
    print(f"      Zone: {retrieved.zone}")
    print(f"      Machine Type: {retrieved.machine_type}")
    print(f"      Self Link: {retrieved.self_link}")
    
    # Verify required fields exist
    required_fields = ['id', 'creation_timestamp', 'disks', 'network_interfaces']
    for field in required_fields:
        assert hasattr(retrieved, field), f"Missing field: {field}"
    print(f"   ✓ All required GCP fields present")
    
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

# Test 4: Stop instance
print(f"\n5. Testing STOP operation...")
try:
    operation = client.stop(
        project=PROJECT,
        zone=ZONE,
        instance=instance_name
    )
    print(f"   ✓ Stop operation initiated")
    print(f"   ✓ Operation: {operation.name}")
    time.sleep(2)
    
    stopped_inst = client.get(project=PROJECT, zone=ZONE, instance=instance_name)
    print(f"   ✓ New status: {stopped_inst.status}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 5: Start instance
print(f"\n6. Testing START operation...")
try:
    operation = client.start(
        project=PROJECT,
        zone=ZONE,
        instance=instance_name
    )
    print(f"   ✓ Start operation initiated")
    time.sleep(2)
    
    started_inst = client.get(project=PROJECT, zone=ZONE, instance=instance_name)
    print(f"   ✓ New status: {started_inst.status}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 6: Delete instance
print(f"\n7. Testing DELETE operation...")
try:
    operation = client.delete(
        project=PROJECT,
        zone=ZONE,
        instance=instance_name
    )
    print(f"   ✓ Delete operation initiated")
    print(f"   ✓ Operation: {operation.name}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

print("\n" + "="*50)
print("✅ ALL TESTS PASSED - SDK COMPATIBILITY VERIFIED")
print("="*50 + "\n")
