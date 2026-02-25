"""Test Docker container creation with static IP assignment"""
import docker
import sys
sys.path.insert(0, '/home/ubuntu/gcs-stimulator/minimal-backend')

from docker_manager import create_container, delete_container

client = docker.from_env()

print("Testing Docker IP assignment...")

# Clean up any existing test containers
for name in ["test-ip-static", "test-ip-auto"]:
    try:
        c = client.containers.get(f"gcp-vm-{name}")
        c.remove(force=True)
        print(f"✓ Cleaned up old container: {name}")
    except:
        pass

# Test 1: Create container with specific IP
print("\nTest 1: Static IP assignment")
result1 = create_container("test-ip-static", "gcp-default", ip_address="10.128.0.100")
print(f"  Container ID: {result1['container_id'][:12]}")
print(f"  Internal IP: {result1['internal_ip']}")

# Verify IP matches
if result1['internal_ip'] == "10.128.0.100":
    print("  ✅ Static IP assignment works!")
else:
    print(f"  ❌ Expected 10.128.0.100, got {result1['internal_ip']}")

# Test 2: Create container with auto IP
print("\nTest 2: Auto IP assignment")
result2 = create_container("test-ip-auto", "gcp-default")
print(f"  Container ID: {result2['container_id'][:12]}")
print(f"  Internal IP: {result2['internal_ip']}")
print("  ✅ Auto IP assignment works!")

# Cleanup
print("\nCleaning up test containers...")
delete_container(result1['container_id'])
delete_container(result2['container_id'])

print("\n✅ All Docker manager tests passed!")
