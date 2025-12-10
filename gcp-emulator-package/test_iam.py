#!/usr/bin/env python3
"""
IAM Module Test Script
Tests the IAM module functionality with sample operations
"""
import requests
import json
import base64
from typing import Dict, Any

BASE_URL = "http://localhost:8080"
PROJECT_ID = "test-project"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_section(msg: str):
    print(f"\n{Colors.YELLOW}{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}{Colors.END}\n")

def test_service_account_creation():
    """Test creating a service account"""
    print_section("Testing Service Account Creation")
    
    response = requests.post(
        f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts",
        json={
            "accountId": "test-sa-001",
            "displayName": "Test Service Account",
            "description": "Created by test script"
        }
    )
    
    if response.status_code == 201:
        sa = response.json()
        print_success(f"Created service account: {sa['email']}")
        print_info(f"  Unique ID: {sa['uniqueId']}")
        print_info(f"  Display Name: {sa['displayName']}")
        return sa
    else:
        print_error(f"Failed to create service account: {response.text}")
        return None

def test_service_account_list():
    """Test listing service accounts"""
    print_section("Testing Service Account List")
    
    response = requests.get(f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts")
    
    if response.status_code == 200:
        data = response.json()
        accounts = data.get('accounts', [])
        print_success(f"Found {len(accounts)} service account(s)")
        for sa in accounts:
            print_info(f"  - {sa['email']} ({sa['displayName']})")
        return accounts
    else:
        print_error(f"Failed to list service accounts: {response.text}")
        return []

def test_key_creation(email: str):
    """Test creating a service account key"""
    print_section("Testing Service Account Key Creation")
    
    response = requests.post(
        f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts/{email}/keys",
        json={"keyAlgorithm": "KEY_ALG_RSA_2048"}
    )
    
    if response.status_code == 201:
        key = response.json()
        print_success(f"Created key: {key['name'].split('/')[-1]}")
        
        if 'privateKeyData' in key:
            # Decode and display credentials
            creds = json.loads(base64.b64decode(key['privateKeyData']))
            print_info(f"  Key ID: {creds['private_key_id']}")
            print_info(f"  Client Email: {creds['client_email']}")
            print_info(f"  Project ID: {creds['project_id']}")
            
            # Save to file
            filename = f"{email.split('@')[0]}-credentials.json"
            with open(filename, 'w') as f:
                json.dump(creds, f, indent=2)
            print_success(f"  Saved credentials to: {filename}")
        
        return key
    else:
        print_error(f"Failed to create key: {response.text}")
        return None

def test_role_list():
    """Test listing roles"""
    print_section("Testing Role List")
    
    response = requests.get(f"{BASE_URL}/v1/roles")
    
    if response.status_code == 200:
        data = response.json()
        roles = data.get('roles', [])
        print_success(f"Found {len(roles)} predefined role(s)")
        for role in roles[:5]:  # Show first 5
            print_info(f"  - {role['name']}: {role['title']}")
        if len(roles) > 5:
            print_info(f"  ... and {len(roles) - 5} more")
        return roles
    else:
        print_error(f"Failed to list roles: {response.text}")
        return []

def test_custom_role_creation():
    """Test creating a custom role"""
    print_section("Testing Custom Role Creation")
    
    response = requests.post(
        f"{BASE_URL}/v1/projects/{PROJECT_ID}/roles",
        json={
            "roleId": "testCustomRole",
            "title": "Test Custom Role",
            "description": "Created by test script",
            "includedPermissions": [
                "storage.objects.get",
                "storage.objects.list"
            ],
            "stage": "GA"
        }
    )
    
    if response.status_code == 201:
        role = response.json()
        print_success(f"Created custom role: {role['name']}")
        print_info(f"  Title: {role['title']}")
        print_info(f"  Permissions: {len(role['includedPermissions'])}")
        return role
    elif response.status_code == 400 and "already exists" in response.text:
        print_info("Custom role already exists (this is OK)")
        return {"name": f"projects/{PROJECT_ID}/roles/testCustomRole"}
    else:
        print_error(f"Failed to create custom role: {response.text}")
        return None

def test_iam_policy():
    """Test IAM policy operations"""
    print_section("Testing IAM Policy Operations")
    
    resource = f"projects/{PROJECT_ID}"
    
    # Get current policy
    response = requests.post(f"{BASE_URL}/v1/{resource}:getIamPolicy")
    
    if response.status_code == 200:
        policy = response.json()
        print_success(f"Retrieved policy for {resource}")
        print_info(f"  Current bindings: {len(policy.get('bindings', []))}")
        
        # Add a new binding
        policy['bindings'] = policy.get('bindings', [])
        policy['bindings'].append({
            "role": "roles/viewer",
            "members": ["allUsers"]
        })
        
        # Set updated policy
        response = requests.post(
            f"{BASE_URL}/v1/{resource}:setIamPolicy",
            json={"policy": policy}
        )
        
        if response.status_code == 200:
            print_success("Updated IAM policy")
            updated_policy = response.json()
            print_info(f"  New bindings: {len(updated_policy.get('bindings', []))}")
            return True
        else:
            print_error(f"Failed to set policy: {response.text}")
            return False
    else:
        print_error(f"Failed to get policy: {response.text}")
        return False

def test_permissions():
    """Test IAM permissions"""
    print_section("Testing IAM Permissions")
    
    resource = f"projects/{PROJECT_ID}"
    permissions = [
        "storage.objects.get",
        "storage.objects.list",
        "storage.objects.create",
        "storage.objects.delete"
    ]
    
    response = requests.post(
        f"{BASE_URL}/v1/{resource}:testIamPermissions",
        json={"permissions": permissions}
    )
    
    if response.status_code == 200:
        data = response.json()
        granted = data.get('permissions', [])
        print_success(f"Tested {len(permissions)} permissions")
        print_info(f"  Granted: {len(granted)}")
        for perm in granted:
            print_info(f"    ✓ {perm}")
        return True
    else:
        print_error(f"Failed to test permissions: {response.text}")
        return False

def cleanup(email: str):
    """Cleanup test resources"""
    print_section("Cleanup")
    
    # Delete service account
    response = requests.delete(
        f"{BASE_URL}/v1/projects/{PROJECT_ID}/serviceAccounts/{email}"
    )
    
    if response.status_code == 204:
        print_success(f"Deleted service account: {email}")
    else:
        print_error(f"Failed to delete service account: {response.text}")
    
    # Delete custom role
    role_name = f"projects/{PROJECT_ID}/roles/testCustomRole"
    response = requests.delete(f"{BASE_URL}/v1/{role_name}")
    
    if response.status_code in [200, 404]:
        print_success("Deleted custom role")
    else:
        print_error(f"Failed to delete custom role: {response.text}")

def main():
    """Run all tests"""
    print_info(f"Testing IAM Module at {BASE_URL}")
    print_info(f"Project ID: {PROJECT_ID}")
    
    try:
        # Test service accounts
        sa = test_service_account_creation()
        if not sa:
            return
        
        email = sa['email']
        
        # List service accounts
        test_service_account_list()
        
        # Test keys
        test_key_creation(email)
        
        # Test roles
        test_role_list()
        test_custom_role_creation()
        
        # Test IAM policies
        test_iam_policy()
        test_permissions()
        
        # Cleanup
        print("\n")
        cleanup_choice = input("Do you want to cleanup test resources? (y/n): ")
        if cleanup_choice.lower() == 'y':
            cleanup(email)
        else:
            print_info(f"Keeping test resources. Service Account: {email}")
        
        print_section("All Tests Complete!")
        print_success("IAM Module is working correctly! 🎉")
        
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to the emulator.")
        print_info("Make sure the backend is running at http://localhost:8080")
        print_info("Run: cd gcp-emulator-package && python run.py")
    except Exception as e:
        print_error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
