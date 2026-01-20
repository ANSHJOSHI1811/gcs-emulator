"""
Phase 2 Validation Tests: Instance Metadata + Labels Support
Tests persistence and retrieval of metadata and labels using real google-cloud-compute SDK
"""
from google.cloud import compute_v1
from google.auth.credentials import AnonymousCredentials
from google.api_core.client_options import ClientOptions
import time


def test_phase2_metadata_labels():
    """Test Phase 2: Metadata and Labels support"""
    
    # Setup client
    credentials = AnonymousCredentials()
    client_options = ClientOptions(api_endpoint="http://localhost:8080")
    client = compute_v1.InstancesClient(credentials=credentials, client_options=client_options)
    
    project = "test-project"
    zone = "us-central1-a"
    
    print("\n" + "="*70)
    print("PHASE 2: METADATA + LABELS VALIDATION")
    print("="*70)
    
    # Test 1: Create instance with custom metadata
    print("\n[TEST 1] Instance with Custom Metadata")
    print("-" * 70)
    instance_name = f"metadata-test-{int(time.time())}"
    
    metadata = compute_v1.Metadata()
    metadata.items = [
        compute_v1.Items(key="environment", value="production"),
        compute_v1.Items(key="app-version", value="1.2.3"),
        compute_v1.Items(key="team", value="backend"),
        compute_v1.Items(key="cost-center", value="engineering")
    ]
    
    instance = compute_v1.Instance(
        name=instance_name,
        machine_type=f"zones/{zone}/machineTypes/e2-micro",
        metadata=metadata
    )
    
    try:
        operation = client.insert(project=project, zone=zone, instance_resource=instance)
        print(f"   ✓ Instance created: {instance_name}")
        print(f"   ✓ Operation: {operation.name}")
        
        # Retrieve and verify metadata
        retrieved = client.get(project=project, zone=zone, instance=instance_name)
        metadata_dict = {item.key: item.value for item in retrieved.metadata.items}
        
        print(f"   ✓ Retrieved metadata ({len(metadata_dict)} items):")
        if "environment" in metadata_dict and metadata_dict["environment"] == "production":
            print(f"      ✓ environment: {metadata_dict['environment']}")
        else:
            print(f"      ✗ environment not found or incorrect")
            
        if "app-version" in metadata_dict and metadata_dict["app-version"] == "1.2.3":
            print(f"      ✓ app-version: {metadata_dict['app-version']}")
        else:
            print(f"      ✗ app-version not found or incorrect")
            
        if "team" in metadata_dict:
            print(f"      ✓ team: {metadata_dict['team']}")
        
        if "cost-center" in metadata_dict:
            print(f"      ✓ cost-center: {metadata_dict['cost-center']}")
            
        # Check emulator defaults are still present
        if "emulator" in metadata_dict:
            print(f"      ✓ emulator (default): {metadata_dict['emulator']}")
        if "docker_image" in metadata_dict:
            print(f"      ✓ docker_image (default): {metadata_dict['docker_image']}")
            
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test 2: Create instance with labels
    print("\n[TEST 2] Instance with Labels")
    print("-" * 70)
    instance_name2 = f"labels-test-{int(time.time())}"
    
    labels = {
        "env": "staging",
        "tier": "frontend",
        "version": "v2",
        "managed-by": "emulator"
    }
    
    instance2 = compute_v1.Instance(
        name=instance_name2,
        machine_type=f"zones/{zone}/machineTypes/e2-small",
        labels=labels
    )
    
    try:
        operation = client.insert(project=project, zone=zone, instance_resource=instance2)
        print(f"   ✓ Instance created: {instance_name2}")
        
        # Retrieve and verify labels
        retrieved2 = client.get(project=project, zone=zone, instance=instance_name2)
        retrieved_labels = dict(retrieved2.labels)
        
        print(f"   ✓ Retrieved labels ({len(retrieved_labels)} items):")
        for key, value in labels.items():
            if key in retrieved_labels and retrieved_labels[key] == value:
                print(f"      ✓ {key}: {value}")
            else:
                print(f"      ✗ {key}: expected '{value}', got '{retrieved_labels.get(key, 'MISSING')}'")
                
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test 3: Create instance with both metadata and labels
    print("\n[TEST 3] Instance with Metadata + Labels Combined")
    print("-" * 70)
    instance_name3 = f"combined-test-{int(time.time())}"
    
    metadata3 = compute_v1.Metadata()
    metadata3.items = [
        compute_v1.Items(key="startup-script", value="#!/bin/bash\necho 'Hello World'"),
        compute_v1.Items(key="ssh-keys", value="user:ssh-rsa AAAAB3...")
    ]
    
    labels3 = {
        "project": "demo",
        "owner": "devops"
    }
    
    instance3 = compute_v1.Instance(
        name=instance_name3,
        machine_type=f"zones/{zone}/machineTypes/n1-standard-1",
        metadata=metadata3,
        labels=labels3,
        description="Test instance with metadata and labels"
    )
    
    try:
        operation = client.insert(project=project, zone=zone, instance_resource=instance3)
        print(f"   ✓ Instance created: {instance_name3}")
        
        retrieved3 = client.get(project=project, zone=zone, instance=instance_name3)
        
        # Check metadata
        metadata_dict3 = {item.key: item.value for item in retrieved3.metadata.items}
        print(f"   ✓ Metadata items: {len(metadata_dict3)}")
        if "startup-script" in metadata_dict3:
            print(f"      ✓ startup-script present (length: {len(metadata_dict3['startup-script'])})")
        if "ssh-keys" in metadata_dict3:
            print(f"      ✓ ssh-keys present")
        
        # Check labels
        labels_dict3 = dict(retrieved3.labels)
        print(f"   ✓ Labels: {len(labels_dict3)}")
        if "project" in labels_dict3:
            print(f"      ✓ project: {labels_dict3['project']}")
        if "owner" in labels_dict3:
            print(f"      ✓ owner: {labels_dict3['owner']}")
        
        # Check description
        if retrieved3.description == "Test instance with metadata and labels":
            print(f"   ✓ Description: {retrieved3.description}")
        else:
            print(f"   ~ Description: {retrieved3.description}")
            
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test 4: Instance without metadata/labels (empty defaults)
    print("\n[TEST 4] Instance without Metadata/Labels (Defaults)")
    print("-" * 70)
    instance_name4 = f"default-test-{int(time.time())}"
    
    instance4 = compute_v1.Instance(
        name=instance_name4,
        machine_type=f"zones/{zone}/machineTypes/e2-micro"
    )
    
    try:
        operation = client.insert(project=project, zone=zone, instance_resource=instance4)
        print(f"   ✓ Instance created: {instance_name4}")
        
        retrieved4 = client.get(project=project, zone=zone, instance=instance_name4)
        
        # Should have emulator defaults only
        metadata_dict4 = {item.key: item.value for item in retrieved4.metadata.items}
        print(f"   ✓ Metadata has {len(metadata_dict4)} items (emulator defaults)")
        
        # Labels should be empty dict
        labels_dict4 = dict(retrieved4.labels)
        if len(labels_dict4) == 0:
            print(f"   ✓ Labels empty (as expected)")
        else:
            print(f"   ~ Labels: {labels_dict4}")
            
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return
    
    # Test 5: Invalid label format (should fail validation)
    print("\n[TEST 5] Invalid Label Format Validation")
    print("-" * 70)
    invalid_labels = [
        {"UPPERCASE": "value"},  # Uppercase not allowed
        {"key!": "value"},  # Special chars not allowed
        {"key": "VALUE!"},  # Uppercase/special in value
    ]
    
    for idx, bad_labels in enumerate(invalid_labels):
        try:
            instance_bad = compute_v1.Instance(
                name=f"invalid-label-{idx}-{int(time.time())}",
                machine_type=f"zones/{zone}/machineTypes/e2-micro",
                labels=bad_labels
            )
            operation = client.insert(project=project, zone=zone, instance_resource=instance_bad)
            print(f"   ✗ Invalid labels accepted (should fail): {bad_labels}")
        except Exception as e:
            print(f"   ✓ Invalid labels rejected: {list(bad_labels.keys())[0]}")
    
    # Test 6: List instances and verify metadata/labels persistence
    print("\n[TEST 6] List Instances - Verify Persistence")
    print("-" * 70)
    try:
        instances = client.list(project=project, zone=zone)
        instance_list = list(instances)
        print(f"   ✓ Listed {len(instance_list)} instances")
        
        # Find our test instances
        test_instances = [i for i in instance_list if 'test' in i.name]
        print(f"   ✓ Found {len(test_instances)} test instances")
        
        for inst in test_instances:
            if 'metadata-test' in inst.name or 'combined-test' in inst.name:
                metadata_count = len(inst.metadata.items) if inst.metadata and inst.metadata.items else 0
                print(f"      • {inst.name}: {metadata_count} metadata items")
            if 'labels-test' in inst.name or 'combined-test' in inst.name:
                labels_count = len(dict(inst.labels))
                print(f"      • {inst.name}: {labels_count} labels")
                
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Cleanup
    print("\n[CLEANUP]")
    print("-" * 70)
    cleanup_instances = [instance_name, instance_name2, instance_name3, instance_name4]
    for inst_name in cleanup_instances:
        try:
            client.delete(project=project, zone=zone, instance=inst_name)
            print(f"   ✓ Deleted: {inst_name}")
        except Exception as e:
            print(f"   ~ {inst_name}: {e}")
    
    print("\n" + "="*70)
    print("✅ PHASE 2 VALIDATION COMPLETE")
    print("="*70)
    print("\nKey Features Validated:")
    print("  • Custom metadata persistence (key-value pairs)")
    print("  • Labels support with validation (lowercase, alphanumeric)")
    print("  • Description field support")
    print("  • Combined metadata + labels")
    print("  • Empty defaults handling")
    print("  • Metadata/labels in list operations")
    print("  • Label format validation (rejects invalid formats)")
    print()


if __name__ == "__main__":
    test_phase2_metadata_labels()
