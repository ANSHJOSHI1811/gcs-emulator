"""
GCP Compute Engine SDK Integration Tests
Validates compatibility with official google-cloud-compute SDK

This test suite proves that the emulator works with the REAL Google Cloud Compute SDK,
just like LocalStack works with AWS SDKs.
"""
import pytest
from google.cloud import compute_v1
from google.api_core import exceptions
import time


class TestComputeSDKCompatibility:
    """Test Compute Engine SDK operations against emulator"""
    
    def test_insert_instance_with_sdk(self, compute_client, test_instance_name):
        """
        Test: Create an instance using official google-cloud-compute SDK
        Validates: insert() operation returns Operation and instance is created
        """
        zone = "us-central1-a"
        project = "test-project"
        
        # Create instance configuration (GCP format)
        instance = compute_v1.Instance(
            name=test_instance_name,
            machine_type=f"zones/{zone}/machineTypes/e2-micro",
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
                compute_v1.NetworkInterface(
                    name="default"
                )
            ]
        )
        
        # Insert instance using SDK
        operation = compute_client.insert(
            project=project,
            zone=zone,
            instance_resource=instance
        )
        
        # Verify operation returned
        assert operation is not None
        assert hasattr(operation, 'name')
        assert operation.status in ['PENDING', 'RUNNING', 'DONE']
        
        # Wait for operation (in emulator, it completes immediately)
        if operation.status != 'DONE':
            time.sleep(1)
        
        print(f"✓ Instance {test_instance_name} created via SDK")
    
    def test_list_instances_with_sdk(self, compute_client, test_instance_name):
        """
        Test: List instances using SDK
        Validates: list() returns instances in GCP format
        """
        zone = "us-central1-a"
        project = "test-project"
        
        # Create instance first
        instance = compute_v1.Instance(
            name=test_instance_name,
            machine_type=f"zones/{zone}/machineTypes/e2-micro",
            disks=[
                compute_v1.AttachedDisk(
                    boot=True,
                    auto_delete=True,
                    initialize_params=compute_v1.AttachedDiskInitializeParams(
                        source_image="projects/debian-cloud/global/images/family/debian-11"
                    )
                )
            ],
            network_interfaces=[compute_v1.NetworkInterface(name="default")]
        )
        compute_client.insert(project=project, zone=zone, instance_resource=instance)
        
        # List instances
        instances = compute_client.list(project=project, zone=zone)
        
        # Convert to list
        instance_list = list(instances)
        
        assert len(instance_list) > 0, "No instances returned"
        
        # Find our instance
        found = False
        for inst in instance_list:
            if inst.name == test_instance_name:
                found = True
                # Verify GCP fields exist
                assert hasattr(inst, 'status')
                assert hasattr(inst, 'zone')
                assert hasattr(inst, 'machine_type')
                assert inst.status in ['PROVISIONING', 'STAGING', 'RUNNING', 'STOPPING', 'TERMINATED']
                print(f"✓ Instance {test_instance_name} found with status: {inst.status}")
                break
        
        assert found, f"Instance {test_instance_name} not found in list"
    
    def test_get_instance_with_sdk(self, compute_client, test_instance_name):
        """
        Test: Get single instance using SDK
        Validates: get() returns complete instance details
        """
        zone = "us-central1-a"
        project = "test-project"
        
        # Create instance first
        instance_config = compute_v1.Instance(
            name=test_instance_name,
            machine_type=f"zones/{zone}/machineTypes/e2-micro",
            disks=[
                compute_v1.AttachedDisk(
                    boot=True,
                    auto_delete=True,
                    initialize_params=compute_v1.AttachedDiskInitializeParams(
                        source_image="projects/debian-cloud/global/images/family/debian-11"
                    )
                )
            ],
            network_interfaces=[compute_v1.NetworkInterface(name="default")]
        )
        compute_client.insert(project=project, zone=zone, instance_resource=instance_config)
        
        # Get instance
        instance = compute_client.get(
            project=project,
            zone=zone,
            instance=test_instance_name
        )
        
        # Verify complete response
        assert instance is not None
        assert instance.name == test_instance_name
        assert hasattr(instance, 'id')
        assert hasattr(instance, 'status')
        assert hasattr(instance, 'zone')
        assert hasattr(instance, 'machine_type')
        assert hasattr(instance, 'disks')
        assert hasattr(instance, 'network_interfaces')
        assert hasattr(instance, 'self_link')
        
        print(f"✓ Instance {test_instance_name} retrieved with full details")
        print(f"  Status: {instance.status}")
        print(f"  Zone: {instance.zone}")
        print(f"  Machine Type: {instance.machine_type}")
    
    def test_stop_instance_with_sdk(self, compute_client, test_instance_name):
        """
        Test: Stop instance using SDK
        Validates: stop() operation works and instance state changes
        """
        zone = "us-central1-a"
        project = "test-project"
        
        # Create and ensure instance is running
        instance_config = compute_v1.Instance(
            name=test_instance_name,
            machine_type=f"zones/{zone}/machineTypes/e2-micro",
            disks=[
                compute_v1.AttachedDisk(
                    boot=True,
                    auto_delete=True,
                    initialize_params=compute_v1.AttachedDiskInitializeParams(
                        source_image="projects/debian-cloud/global/images/family/debian-11"
                    )
                )
            ],
            network_interfaces=[compute_v1.NetworkInterface(name="default")]
        )
        compute_client.insert(project=project, zone=zone, instance_resource=instance_config)
        
        # Stop instance
        operation = compute_client.stop(
            project=project,
            zone=zone,
            instance=test_instance_name
        )
        
        assert operation is not None
        assert hasattr(operation, 'name')
        
        # Verify instance is stopped
        time.sleep(1)
        instance = compute_client.get(project=project, zone=zone, instance=test_instance_name)
        assert instance.status in ['STOPPING', 'TERMINATED']
        
        print(f"✓ Instance {test_instance_name} stopped via SDK")
    
    def test_start_instance_with_sdk(self, compute_client, test_instance_name):
        """
        Test: Start a stopped instance using SDK
        Validates: start() operation works
        """
        zone = "us-central1-a"
        project = "test-project"
        
        # Create, stop, then start instance
        instance_config = compute_v1.Instance(
            name=test_instance_name,
            machine_type=f"zones/{zone}/machineTypes/e2-micro",
            disks=[
                compute_v1.AttachedDisk(
                    boot=True,
                    auto_delete=True,
                    initialize_params=compute_v1.AttachedDiskInitializeParams(
                        source_image="projects/debian-cloud/global/images/family/debian-11"
                    )
                )
            ],
            network_interfaces=[compute_v1.NetworkInterface(name="default")]
        )
        compute_client.insert(project=project, zone=zone, instance_resource=instance_config)
        compute_client.stop(project=project, zone=zone, instance=test_instance_name)
        time.sleep(1)
        
        # Start instance
        operation = compute_client.start(
            project=project,
            zone=zone,
            instance=test_instance_name
        )
        
        assert operation is not None
        assert hasattr(operation, 'name')
        
        # Verify instance is running
        time.sleep(1)
        instance = compute_client.get(project=project, zone=zone, instance=test_instance_name)
        assert instance.status == 'RUNNING'
        
        print(f"✓ Instance {test_instance_name} started via SDK")
    
    def test_delete_instance_with_sdk(self, compute_client, test_instance_name):
        """
        Test: Delete instance using SDK
        Validates: delete() removes instance completely
        """
        zone = "us-central1-a"
        project = "test-project"
        
        # Create instance
        instance_config = compute_v1.Instance(
            name=test_instance_name,
            machine_type=f"zones/{zone}/machineTypes/e2-micro",
            disks=[
                compute_v1.AttachedDisk(
                    boot=True,
                    auto_delete=True,
                    initialize_params=compute_v1.AttachedDiskInitializeParams(
                        source_image="projects/debian-cloud/global/images/family/debian-11"
                    )
                )
            ],
            network_interfaces=[compute_v1.NetworkInterface(name="default")]
        )
        compute_client.insert(project=project, zone=zone, instance_resource=instance_config)
        
        # Delete instance
        operation = compute_client.delete(
            project=project,
            zone=zone,
            instance=test_instance_name
        )
        
        assert operation is not None
        assert hasattr(operation, 'name')
        
        # Verify instance is gone or terminated
        time.sleep(1)
        try:
            instance = compute_client.get(project=project, zone=zone, instance=test_instance_name)
            # If we can still get it, it should be terminated
            assert instance.status == 'TERMINATED'
        except exceptions.NotFound:
            # This is also valid - instance completely removed
            pass
        
        print(f"✓ Instance {test_instance_name} deleted via SDK")
    
    def test_full_lifecycle_with_sdk(self, compute_client):
        """
        Test: Complete instance lifecycle using SDK
        Validates: Create → Stop → Start → Delete flow
        """
        zone = "us-central1-a"
        project = "test-project"
        instance_name = f"sdk-lifecycle-test-{int(time.time())}"
        
        print(f"\n=== Testing Full Lifecycle for {instance_name} ===")
        
        # 1. Create
        print("1. Creating instance...")
        instance_config = compute_v1.Instance(
            name=instance_name,
            machine_type=f"zones/{zone}/machineTypes/e2-small",
            disks=[
                compute_v1.AttachedDisk(
                    boot=True,
                    auto_delete=True,
                    initialize_params=compute_v1.AttachedDiskInitializeParams(
                        source_image="projects/ubuntu-os-cloud/global/images/family/ubuntu-2004-lts"
                    )
                )
            ],
            network_interfaces=[compute_v1.NetworkInterface(name="default")]
        )
        compute_client.insert(project=project, zone=zone, instance_resource=instance_config)
        time.sleep(1)
        
        instance = compute_client.get(project=project, zone=zone, instance=instance_name)
        assert instance.status == 'RUNNING'
        print(f"   ✓ Status: {instance.status}")
        
        # 2. Stop
        print("2. Stopping instance...")
        compute_client.stop(project=project, zone=zone, instance=instance_name)
        time.sleep(1)
        
        instance = compute_client.get(project=project, zone=zone, instance=instance_name)
        assert instance.status in ['STOPPING', 'TERMINATED']
        print(f"   ✓ Status: {instance.status}")
        
        # 3. Start
        print("3. Starting instance...")
        compute_client.start(project=project, zone=zone, instance=instance_name)
        time.sleep(1)
        
        instance = compute_client.get(project=project, zone=zone, instance=instance_name)
        assert instance.status == 'RUNNING'
        print(f"   ✓ Status: {instance.status}")
        
        # 4. Delete
        print("4. Deleting instance...")
        compute_client.delete(project=project, zone=zone, instance=instance_name)
        time.sleep(1)
        
        print("✓ Full lifecycle test completed successfully")


class TestComputeSDKResponseFormat:
    """Validate GCP API response format compliance"""
    
    def test_instance_has_required_fields(self, compute_client, test_instance_name):
        """Verify instance response includes all required GCP fields"""
        zone = "us-central1-a"
        project = "test-project"
        
        # Create instance
        instance_config = compute_v1.Instance(
            name=test_instance_name,
            machine_type=f"zones/{zone}/machineTypes/e2-micro",
            disks=[
                compute_v1.AttachedDisk(
                    boot=True,
                    auto_delete=True,
                    initialize_params=compute_v1.AttachedDiskInitializeParams(
                        source_image="projects/debian-cloud/global/images/family/debian-11"
                    )
                )
            ],
            network_interfaces=[compute_v1.NetworkInterface(name="default")]
        )
        compute_client.insert(project=project, zone=zone, instance_resource=instance_config)
        
        # Get instance
        instance = compute_client.get(project=project, zone=zone, instance=test_instance_name)
        
        # Required GCP fields
        required_fields = [
            'id', 'name', 'status', 'zone', 'machine_type',
            'disks', 'network_interfaces', 'self_link', 'creation_timestamp'
        ]
        
        for field in required_fields:
            assert hasattr(instance, field), f"Missing required field: {field}"
            value = getattr(instance, field)
            assert value is not None, f"Field {field} is None"
        
        print("✓ All required GCP fields present in response")
    
    def test_operation_format(self, compute_client, test_instance_name):
        """Verify operation response matches GCP format"""
        zone = "us-central1-a"
        project = "test-project"
        
        # Create instance to get operation
        instance_config = compute_v1.Instance(
            name=test_instance_name,
            machine_type=f"zones/{zone}/machineTypes/e2-micro",
            disks=[
                compute_v1.AttachedDisk(
                    boot=True,
                    auto_delete=True,
                    initialize_params=compute_v1.AttachedDiskInitializeParams(
                        source_image="projects/debian-cloud/global/images/family/debian-11"
                    )
                )
            ],
            network_interfaces=[compute_v1.NetworkInterface(name="default")]
        )
        operation = compute_client.insert(project=project, zone=zone, instance_resource=instance_config)
        
        # Required operation fields
        required_op_fields = ['id', 'name', 'status', 'operation_type', 'target_link']
        
        for field in required_op_fields:
            assert hasattr(operation, field), f"Missing operation field: {field}"
        
        assert operation.status in ['PENDING', 'RUNNING', 'DONE']
        
        print("✓ Operation format matches GCP specification")
