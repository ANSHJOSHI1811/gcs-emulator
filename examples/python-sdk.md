# Python SDK Examples

**Using Python client libraries to interact with GCP Stimulator**

Point your Python code to the local stimulator instead of real GCP.

---

## Setup

```bash
# Install required packages
pip install google-cloud-storage google-cloud-compute google-cloud-iam
```

### Configuration

```python
import os

# Point to local stimulator
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
os.environ['CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE'] = 'http://localhost:8080/compute/v1/'

# Or set in code
STIMULATOR_HOST = "http://localhost:8080"
```

---

## Cloud Storage

### Basic Operations

```python
from google.cloud import storage
import os

# Configure to use local stimulator
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'

# Create client
client = storage.Client(project='my-project')

# Create bucket
bucket = client.create_bucket('my-bucket', location='US')
print(f"Bucket {bucket.name} created")

# List buckets
buckets = list(client.list_buckets())
for bucket in buckets:
    print(f"- {bucket.name}")

# Get bucket
bucket = client.get_bucket('my-bucket')
print(f"Bucket: {bucket.name}, Location: {bucket.location}")

# Delete bucket
bucket.delete()
print(f"Bucket {bucket.name} deleted")
```

### Object Operations

```python
from google.cloud import storage
import os

os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
client = storage.Client(project='my-project')

bucket = client.bucket('my-bucket')

# Upload from string
blob = bucket.blob('file.txt')
blob.upload_from_string('Hello World')
print(f"Uploaded to {blob.name}")

# Upload from file
blob = bucket.blob('document.pdf')
blob.upload_from_filename('./local-document.pdf')
print(f"Uploaded {blob.name}")

# Upload with metadata
blob = bucket.blob('data.json')
blob.metadata = {'source': 'python-script', 'version': '1.0'}
blob.content_type = 'application/json'
blob.upload_from_filename('./data.json')

# List objects
blobs = list(bucket.list_blobs())
for blob in blobs:
    print(f"- {blob.name} ({blob.size} bytes)")

# Download to string
blob = bucket.blob('file.txt')
content = blob.download_as_text()
print(f"Content: {content}")

# Download to file
blob = bucket.blob('document.pdf')
blob.download_to_filename('./downloaded-document.pdf')
print("Downloaded successfully")

# Get object metadata
blob = bucket.get_blob('file.txt')
print(f"Name: {blob.name}")
print(f"Size: {blob.size} bytes")
print(f"Content-Type: {blob.content_type}")
print(f"MD5: {blob.md5_hash}")

# Delete object
blob = bucket.blob('file.txt')
blob.delete()
print(f"Deleted {blob.name}")

# Copy object
source_blob = bucket.blob('file.txt')
dest_bucket = client.bucket('dest-bucket')
bucket.copy_blob(source_blob, dest_bucket, 'copied-file.txt')
print("Copied successfully")
```

### Advanced Storage Operations

```python
from google.cloud import storage
import os

os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
client = storage.Client(project='my-project')

# Enable versioning
bucket = client.get_bucket('my-bucket')
bucket.versioning_enabled = True
bucket.patch()
print("Versioning enabled")

# List object versions
blobs = list(bucket.list_blobs(versions=True))
for blob in blobs:
    print(f"- {blob.name} (generation: {blob.generation})")

# Resumable upload (for large files)
blob = bucket.blob('large-file.bin')
with open('./large-file.bin', 'rb') as file:
    blob.upload_from_file(file, size=file.seek(0, 2))
print("Large file uploaded")

# Batch operations
from google.cloud.storage import Batch

with Batch(client):
    bucket.blob('file1.txt').upload_from_string('Content 1')
    bucket.blob('file2.txt').upload_from_string('Content 2')
    bucket.blob('file3.txt').upload_from_string('Content 3')
print("Batch upload complete")

# Signed URLs (if supported)
blob = bucket.blob('private-file.txt')
url = blob.generate_signed_url(
    version='v4',
    expiration=3600,  # 1 hour
    method='GET'
)
print(f"Signed URL: {url}")
```

---

## Compute Engine

### Setup

```python
import os
from google.cloud import compute_v1

# Point to local stimulator
os.environ['CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE'] = 'http://localhost:8080/compute/v1/'

project = 'my-project'
zone = 'us-central1-a'
```

### Instance Operations

```python
from google.cloud import compute_v1
import os

os.environ['CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE'] = 'http://localhost:8080/compute/v1/'

# Create clients
instances_client = compute_v1.InstancesClient()
project = 'my-project'
zone = 'us-central1-a'

# Create VM instance
def create_instance(instance_name):
    instance = compute_v1.Instance()
    instance.name = instance_name
    instance.machine_type = f"zones/{zone}/machineTypes/e2-medium"
    
    # Configure disk
    disk = compute_v1.AttachedDisk()
    disk.boot = True
    disk.auto_delete = True
    initialize_params = compute_v1.AttachedDiskInitializeParams()
    initialize_params.source_image = "projects/debian-cloud/global/images/debian-11"
    initialize_params.disk_size_gb = 10
    disk.initialize_params = initialize_params
    instance.disks = [disk]
    
    # Configure network
    network_interface = compute_v1.NetworkInterface()
    network_interface.network = "global/networks/default"
    instance.network_interfaces = [network_interface]
    
    operation = instances_client.insert(
        project=project,
        zone=zone,
        instance_resource=instance
    )
    print(f"Creating instance {instance_name}...")
    return operation

# List instances
def list_instances():
    result = instances_client.list(project=project, zone=zone)
    instances = list(result)
    
    print(f"Instances in {zone}:")
    for instance in instances:
        print(f"- {instance.name} ({instance.status})")
    
    return instances

# Get instance details
def get_instance(instance_name):
    instance = instances_client.get(
        project=project,
        zone=zone,
        instance=instance_name
    )
    
    print(f"Instance: {instance.name}")
    print(f"Machine Type: {instance.machine_type}")
    print(f"Status: {instance.status}")
    print(f"Internal IP: {instance.network_interfaces[0].network_i_p}")
    
    return instance

# Start instance
def start_instance(instance_name):
    operation = instances_client.start(
        project=project,
        zone=zone,
        instance=instance_name
    )
    print(f"Starting instance {instance_name}...")
    return operation

# Stop instance
def stop_instance(instance_name):
    operation = instances_client.stop(
        project=project,
        zone=zone,
        instance=instance_name
    )
    print(f"Stopping instance {instance_name}...")
    return operation

# Delete instance
def delete_instance(instance_name):
    operation = instances_client.delete(
        project=project,
        zone=zone,
        instance=instance_name
    )
    print(f"Deleting instance {instance_name}...")
    return operation

# Usage
create_instance('my-vm')
list_instances()
get_instance('my-vm')
stop_instance('my-vm')
start_instance('my-vm')
delete_instance('my-vm')
```

### Zones and Machine Types

```python
from google.cloud import compute_v1
import os

os.environ['CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE'] = 'http://localhost:8080/compute/v1/'

# List zones
zones_client = compute_v1.ZonesClient()
project = 'my-project'

zones = list(zones_client.list(project=project))
print("Available zones:")
for zone in zones:
    print(f"- {zone.name}: {zone.description} ({zone.status})")

# List machine types
machine_types_client = compute_v1.MachineTypesClient()
zone = 'us-central1-a'

machine_types = list(machine_types_client.list(project=project, zone=zone))
print(f"\nMachine types in {zone}:")
for mt in machine_types:
    print(f"- {mt.name}: {mt.guest_cpus} vCPUs, {mt.memory_mb}MB RAM")

# Get machine type details
machine_type = machine_types_client.get(
    project=project,
    zone=zone,
    machine_type='e2-medium'
)
print(f"\nMachine Type: {machine_type.name}")
print(f"vCPUs: {machine_type.guest_cpus}")
print(f"Memory: {machine_type.memory_mb}MB")
print(f"Shared CPU: {machine_type.is_shared_cpu}")
```

---

## VPC Networking

### Networks

```python
from google.cloud import compute_v1
import os

os.environ['CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE'] = 'http://localhost:8080/compute/v1/'

networks_client = compute_v1.NetworksClient()
project = 'my-project'

# Create custom VPC
def create_network(network_name):
    network = compute_v1.Network()
    network.name = network_name
    network.auto_create_subnetworks = False
    network.description = "Custom VPC network"
    
    operation = networks_client.insert(
        project=project,
        network_resource=network
    )
    print(f"Creating network {network_name}...")
    return operation

# List networks
def list_networks():
    result = networks_client.list(project=project)
    networks = list(result)
    
    print("Networks:")
    for network in networks:
        print(f"- {network.name}")
    
    return networks

# Get network details
def get_network(network_name):
    network = networks_client.get(
        project=project,
        network=network_name
    )
    
    print(f"Network: {network.name}")
    print(f"Auto-create subnets: {network.auto_create_subnetworks}")
    
    return network

# Delete network
def delete_network(network_name):
    operation = networks_client.delete(
        project=project,
        network=network_name
    )
    print(f"Deleting network {network_name}...")
    return operation

# Usage
create_network('my-vpc')
list_networks()
get_network('my-vpc')
delete_network('my-vpc')
```

### Subnets

```python
from google.cloud import compute_v1
import os

os.environ['CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE'] = 'http://localhost:8080/compute/v1/'

subnetworks_client = compute_v1.SubnetworksClient()
project = 'my-project'
region = 'us-central1'

# Create subnet
def create_subnet(subnet_name, network_name):
    subnetwork = compute_v1.Subnetwork()
    subnetwork.name = subnet_name
    subnetwork.network = f"projects/{project}/global/networks/{network_name}"
    subnetwork.ip_cidr_range = "10.0.1.0/24"
    subnetwork.region = region
    
    operation = subnetworks_client.insert(
        project=project,
        region=region,
        subnetwork_resource=subnetwork
    )
    print(f"Creating subnet {subnet_name}...")
    return operation

# List subnets
def list_subnets():
    result = subnetworks_client.list(project=project, region=region)
    subnets = list(result)
    
    print(f"Subnets in {region}:")
    for subnet in subnets:
        print(f"- {subnet.name} ({subnet.ip_cidr_range})")
    
    return subnets

# Get subnet details
def get_subnet(subnet_name):
    subnet = subnetworks_client.get(
        project=project,
        region=region,
        subnetwork=subnet_name
    )
    
    print(f"Subnet: {subnet.name}")
    print(f"CIDR: {subnet.ip_cidr_range}")
    print(f"Gateway: {subnet.gateway_address}")
    
    return subnet

# Delete subnet
def delete_subnet(subnet_name):
    operation = subnetworks_client.delete(
        project=project,
        region=region,
        subnetwork=subnet_name
    )
    print(f"Deleting subnet {subnet_name}...")
    return operation
```

### Firewall Rules

```python
from google.cloud import compute_v1
import os

os.environ['CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE'] = 'http://localhost:8080/compute/v1/'

firewalls_client = compute_v1.FirewallsClient()
project = 'my-project'

# Create firewall rule (allow SSH)
def create_firewall_rule(rule_name, network_name):
    firewall = compute_v1.Firewall()
    firewall.name = rule_name
    firewall.network = f"projects/{project}/global/networks/{network_name}"
    firewall.direction = "INGRESS"
    firewall.priority = 1000
    
    # Allow SSH
    allowed = compute_v1.Allowed()
    allowed.I_p_protocol = "tcp"
    allowed.ports = ["22"]
    firewall.allowed = [allowed]
    
    firewall.source_ranges = ["0.0.0.0/0"]
    
    operation = firewalls_client.insert(
        project=project,
        firewall_resource=firewall
    )
    print(f"Creating firewall rule {rule_name}...")
    return operation

# List firewall rules
def list_firewall_rules():
    result = firewalls_client.list(project=project)
    rules = list(result)
    
    print("Firewall Rules:")
    for rule in rules:
        print(f"- {rule.name} ({rule.direction}, priority: {rule.priority})")
    
    return rules

# Get firewall rule
def get_firewall_rule(rule_name):
    rule = firewalls_client.get(
        project=project,
        firewall=rule_name
    )
    
    print(f"Rule: {rule.name}")
    print(f"Direction: {rule.direction}")
    print(f"Priority: {rule.priority}")
    
    return rule

# Delete firewall rule
def delete_firewall_rule(rule_name):
    operation = firewalls_client.delete(
        project=project,
        firewall=rule_name
    )
    print(f"Deleting firewall rule {rule_name}...")
    return operation
```

---

## IAM

### Service Accounts

```python
from google.cloud import iam_admin_v1
import os

# Note: IAM client may need custom endpoint configuration
project = 'my-project'

# Create IAM client
iam_client = iam_admin_v1.IAMClient()

# Create service account
def create_service_account(account_id):
    request = iam_admin_v1.CreateServiceAccountRequest()
    request.name = f"projects/{project}"
    request.account_id = account_id
    
    service_account = iam_admin_v1.ServiceAccount()
    service_account.display_name = "My Service Account"
    service_account.description = "Service account for my app"
    request.service_account = service_account
    
    result = iam_client.create_service_account(request=request)
    print(f"Created service account: {result.email}")
    return result

# List service accounts
def list_service_accounts():
    request = iam_admin_v1.ListServiceAccountsRequest()
    request.name = f"projects/{project}"
    
    result = iam_client.list_service_accounts(request=request)
    
    print("Service Accounts:")
    for account in result.accounts:
        print(f"- {account.email}: {account.display_name}")
    
    return result.accounts

# Get service account
def get_service_account(email):
    request = iam_admin_v1.GetServiceAccountRequest()
    request.name = f"projects/{project}/serviceAccounts/{email}"
    
    account = iam_client.get_service_account(request=request)
    
    print(f"Email: {account.email}")
    print(f"Display Name: {account.display_name}")
    print(f"Unique ID: {account.unique_id}")
    
    return account

# Delete service account
def delete_service_account(email):
    request = iam_admin_v1.DeleteServiceAccountRequest()
    request.name = f"projects/{project}/serviceAccounts/{email}"
    
    iam_client.delete_service_account(request=request)
    print(f"Deleted service account: {email}")
```

---

## Complete Application Example

```python
"""
Complete infrastructure setup using Python SDK
"""
import os
from google.cloud import storage, compute_v1

# Configure
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
os.environ['CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE'] = 'http://localhost:8080/compute/v1/'

PROJECT = 'my-project'
ZONE = 'us-central1-a'
REGION = 'us-central1'

def setup_infrastructure():
    print("🚀 Setting up infrastructure...")
    
    # 1. Create Storage bucket
    print("\n1. Creating storage bucket...")
    storage_client = storage.Client(project=PROJECT)
    bucket = storage_client.create_bucket('app-data-bucket', location='US')
    print(f"✅ Created bucket: {bucket.name}")
    
    # 2. Upload config file
    print("\n2. Uploading configuration...")
    blob = bucket.blob('config.json')
    blob.upload_from_string('{"environment": "production"}')
    print(f"✅ Uploaded config.json")
    
    # 3. Create VPC network
    print("\n3. Creating VPC network...")
    networks_client = compute_v1.NetworksClient()
    network = compute_v1.Network()
    network.name = 'app-vpc'
    network.auto_create_subnetworks = False
    networks_client.insert(project=PROJECT, network_resource=network)
    print(f"✅ Created network: app-vpc")
    
    # 4. Create subnet
    print("\n4. Creating subnet...")
    subnets_client = compute_v1.SubnetworksClient()
    subnet = compute_v1.Subnetwork()
    subnet.name = 'app-subnet'
    subnet.network = f"projects/{PROJECT}/global/networks/app-vpc"
    subnet.ip_cidr_range = "10.1.0.0/24"
    subnet.region = REGION
    subnets_client.insert(project=PROJECT, region=REGION, subnetwork_resource=subnet)
    print(f"✅ Created subnet: app-subnet")
    
    # 5. Create firewall rule
    print("\n5. Creating firewall rule...")
    firewalls_client = compute_v1.FirewallsClient()
    firewall = compute_v1.Firewall()
    firewall.name = 'allow-http'
    firewall.network = f"projects/{PROJECT}/global/networks/app-vpc"
    firewall.direction = "INGRESS"
    firewall.priority = 1000
    allowed = compute_v1.Allowed()
    allowed.I_p_protocol = "tcp"
    allowed.ports = ["80", "443"]
    firewall.allowed = [allowed]
    firewall.source_ranges = ["0.0.0.0/0"]
    firewalls_client.insert(project=PROJECT, firewall_resource=firewall)
    print(f"✅ Created firewall rule: allow-http")
    
    # 6. Create VM instance
    print("\n6. Creating VM instance...")
    instances_client = compute_v1.InstancesClient()
    instance = compute_v1.Instance()
    instance.name = 'app-vm'
    instance.machine_type = f"zones/{ZONE}/machineTypes/e2-medium"
    
    disk = compute_v1.AttachedDisk()
    disk.boot = True
    disk.auto_delete = True
    initialize_params = compute_v1.AttachedDiskInitializeParams()
    initialize_params.source_image = "projects/debian-cloud/global/images/debian-11"
    disk.initialize_params = initialize_params
    instance.disks = [disk]
    
    network_interface = compute_v1.NetworkInterface()
    network_interface.subnetwork = f"projects/{PROJECT}/regions/{REGION}/subnetworks/app-subnet"
    instance.network_interfaces = [network_interface]
    
    instances_client.insert(project=PROJECT, zone=ZONE, instance_resource=instance)
    print(f"✅ Created VM: app-vm")
    
    print("\n🎉 Infrastructure setup complete!")

if __name__ == "__main__":
    setup_infrastructure()
```

---

## Error Handling

```python
from google.cloud import storage
from google.api_core import exceptions
import os

os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
client = storage.Client(project='my-project')

try:
    # Try to get non-existent bucket
    bucket = client.get_bucket('non-existent-bucket')
except exceptions.NotFound:
    print("Bucket not found")
except exceptions.Forbidden:
    print("Access denied")
except exceptions.GoogleAPIError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Testing Tips

```python
import unittest
from google.cloud import storage
import os

class TestGCPStimulator(unittest.TestCase):
    def setUp(self):
        os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
        self.client = storage.Client(project='test-project')
        
    def test_bucket_creation(self):
        bucket_name = 'test-bucket'
        bucket = self.client.create_bucket(bucket_name)
        self.assertEqual(bucket.name, bucket_name)
        
    def test_object_upload(self):
        bucket = self.client.bucket('test-bucket')
        blob = bucket.blob('test.txt')
        blob.upload_from_string('test content')
        
        content = blob.download_as_text()
        self.assertEqual(content, 'test content')
        
    def tearDown(self):
        # Clean up
        buckets = list(self.client.list_buckets())
        for bucket in buckets:
            bucket.delete(force=True)

if __name__ == '__main__':
    unittest.main()
```
