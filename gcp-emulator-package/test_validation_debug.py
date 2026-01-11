"""Quick debug test to check validation"""
from google.cloud import compute_v1
from google.auth.credentials import AnonymousCredentials
from google.api_core.client_options import ClientOptions
from google.api_core import exceptions
import time

credentials = AnonymousCredentials()
client_options = ClientOptions(api_endpoint="http://localhost:8080")
client = compute_v1.InstancesClient(credentials=credentials, client_options=client_options)

project = "test-project"
zone = "us-central1-a"

# Test invalid machine type
timestamp = int(time.time())
print(f"Testing invalid machine type (timestamp: {timestamp})...")
try:
    instance = compute_v1.Instance(
        name=f"test-invalid-type-{timestamp}",
        machine_type=f"zones/{zone}/machineTypes/invalid-type"
    )
    operation = client.insert(project=project, zone=zone, instance_resource=instance)
    print(f"FAIL: Accepted invalid machine type (operation id: {operation.name})")
except exceptions.InvalidArgument as e:
    print(f"PASS: Rejected with InvalidArgument - {e.message}")
except exceptions.BadRequest as e:
    print(f"PASS: Rejected with BadRequest - {e.message}")
except Exception as e:
    print(f"ERROR: Unexpected exception - {type(e).__name__}: {e}")

# Test invalid zone
print(f"\nTesting invalid zone (timestamp: {timestamp})...")
try:
    instance = compute_v1.Instance(
        name=f"test-invalid-zone-{timestamp}",
        machine_type=f"zones/us-central1-z/machineTypes/e2-micro"
    )
    operation = client.insert(project=project, zone="us-central1-z", instance_resource=instance)
    print(f"FAIL: Accepted invalid zone (operation id: {operation.name})")
except exceptions.InvalidArgument as e:
    print(f"PASS: Rejected with InvalidArgument - {e.message}")
except exceptions.BadRequest as e:
    print(f"PASS: Rejected with BadRequest - {e.message}")
except Exception as e:
    print(f"ERROR: Unexpected exception - {type(e).__name__}: {e}")
