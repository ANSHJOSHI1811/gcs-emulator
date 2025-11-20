#!/usr/bin/env python3
"""
GCP SDK Explorer Script
Purpose: Test google-cloud-storage SDK behavior with real credentials
and capture request/response formats for our emulator implementation
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Try to import google-cloud-storage
try:
    from google.cloud import storage
    from google.auth import credentials
    from google.oauth2 import service_account
    print("✅ google-cloud-storage SDK installed")
except ImportError as e:
    print(f"❌ Missing google-cloud-storage: {e}")
    print("Install with: pip install google-cloud-storage")
    sys.exit(1)

# Try to import requests for capturing HTTP details
try:
    import requests
    from unittest.mock import patch
    print("✅ requests library available")
except ImportError:
    print("⚠️ requests not available, some tests may be limited")


def load_credentials(cred_file: str) -> dict:
    """Load and validate service account credentials"""
    print(f"\n📋 Loading credentials from: {cred_file}")
    try:
        with open(cred_file, 'r') as f:
            creds_dict = json.load(f)
        
        print(f"✅ Credentials loaded successfully")
        print(f"   Project ID: {creds_dict.get('project_id')}")
        print(f"   Service Account: {creds_dict.get('client_email')}")
        print(f"   Type: {creds_dict.get('type')}")
        return creds_dict
    except FileNotFoundError:
        print(f"❌ Credentials file not found: {cred_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in credentials file")
        sys.exit(1)


def test_credentials_loading(cred_file: str):
    """Test if SDK can load credentials"""
    print("\n" + "="*60)
    print("TEST 1: Credentials Loading")
    print("="*60)
    
    try:
        credentials_obj = service_account.Credentials.from_service_account_file(cred_file)
        print("✅ Credentials loaded via service_account.Credentials")
        print(f"   Project: {credentials_obj.project_id}")
        print(f"   Service Account Email: {credentials_obj.service_account_email}")
        return credentials_obj
    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        return None


def test_client_creation(cred_file: str):
    """Test creating a storage client"""
    print("\n" + "="*60)
    print("TEST 2: Storage Client Creation")
    print("="*60)
    
    try:
        # Load credentials
        credentials_obj = service_account.Credentials.from_service_account_file(cred_file)
        
        # Create client
        client = storage.Client(credentials=credentials_obj, project=credentials_obj.project_id)
        print("✅ Storage client created successfully")
        print(f"   Project: {client.project}")
        print(f"   API Endpoint: {client.api_endpoint if hasattr(client, 'api_endpoint') else 'default'}")
        
        return client
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        return None


def test_custom_endpoint(cred_file: str, endpoint: str = "http://localhost:5000"):
    """Test if SDK supports custom endpoint"""
    print("\n" + "="*60)
    print(f"TEST 3: Custom Endpoint Configuration")
    print(f"Testing endpoint: {endpoint}")
    print("="*60)
    
    try:
        credentials_obj = service_account.Credentials.from_service_account_file(cred_file)
        
        # Try different ways to set custom endpoint
        print("\n🔧 Method 1: Using api_endpoint parameter...")
        try:
            client = storage.Client(
                credentials=credentials_obj,
                project=credentials_obj.project_id,
                api_endpoint=endpoint
            )
            print(f"✅ api_endpoint parameter works!")
            print(f"   Endpoint: {client.api_endpoint}")
            return client, "api_endpoint"
        except TypeError as e:
            print(f"⚠️ api_endpoint parameter not supported: {e}")
        
        # Try alternative method
        print("\n🔧 Method 2: Setting _api_endpoint after creation...")
        try:
            client = storage.Client(credentials=credentials_obj, project=credentials_obj.project_id)
            client._api_endpoint = endpoint
            print(f"✅ Setting _api_endpoint works!")
            print(f"   Endpoint: {client._api_endpoint}")
            return client, "_api_endpoint"
        except Exception as e:
            print(f"⚠️ Failed to set _api_endpoint: {e}")
        
        print("❌ No method found to configure custom endpoint")
        return None, None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None


def test_list_buckets(client):
    """Test listing buckets (read-only, safe)"""
    print("\n" + "="*60)
    print("TEST 4: List Buckets Operation")
    print("="*60)
    
    if not client:
        print("⚠️ No client available")
        return
    
    try:
        print("Attempting to list buckets...")
        buckets = list(client.list_buckets(max_results=5))
        print(f"✅ Successfully listed buckets!")
        print(f"   Count: {len(buckets)}")
        
        if buckets:
            print("\n📦 Sample Bucket (First):")
            bucket = buckets[0]
            print(f"   Name: {bucket.name}")
            print(f"   Location: {bucket.location}")
            print(f"   Storage Class: {bucket.storage_class}")
            print(f"   Created: {bucket.time_created}")
            print(f"   Updated: {bucket.updated}")
            print(f"   ID: {bucket.id}")
            
            # Print raw data if available
            if hasattr(bucket, '_properties'):
                print("\n📄 Raw Bucket Properties:")
                print(json.dumps(bucket._properties, indent=2, default=str))
        
        return buckets
        
    except Exception as e:
        print(f"❌ Failed to list buckets: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_bucket_info(client):
    """Get detailed info about a bucket"""
    print("\n" + "="*60)
    print("TEST 5: Bucket Detailed Information")
    print("="*60)
    
    if not client:
        print("⚠️ No client available")
        return
    
    try:
        buckets = list(client.list_buckets(max_results=1))
        if not buckets:
            print("⚠️ No buckets found")
            return
        
        bucket = buckets[0]
        print(f"\n📦 Bucket: {bucket.name}")
        
        # Reload bucket metadata
        bucket.reload()
        
        print("\n📊 Bucket Metadata:")
        print(f"   ID: {bucket.id}")
        print(f"   Project Number: {bucket.project_number}")
        print(f"   Name: {bucket.name}")
        print(f"   Location: {bucket.location}")
        print(f"   Storage Class: {bucket.storage_class}")
        print(f"   Time Created: {bucket.time_created}")
        print(f"   Updated: {bucket.updated}")
        print(f"   Etag: {bucket.etag}")
        print(f"   Metageneration: {bucket.metageneration}")
        print(f"   Versioning Enabled: {bucket.versioning_enabled}")
        
        # Print raw properties
        if hasattr(bucket, '_properties'):
            print("\n📄 Raw Properties (as returned by API):")
            print(json.dumps(bucket._properties, indent=2, default=str))
        
        return bucket
        
    except Exception as e:
        print(f"❌ Failed to get bucket info: {e}")
        import traceback
        traceback.print_exc()
        return None


def capture_request_format(cred_file: str):
    """Attempt to capture HTTP request/response details"""
    print("\n" + "="*60)
    print("TEST 6: HTTP Request/Response Capture")
    print("="*60)
    
    try:
        from unittest.mock import patch, MagicMock
        import logging
        
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG)
        
        credentials_obj = service_account.Credentials.from_service_account_file(cred_file)
        client = storage.Client(credentials=credentials_obj, project=credentials_obj.project_id)
        
        print("\n🔍 Attempting to capture HTTP requests...")
        print("This will show the actual API calls being made")
        
        # List buckets with captured requests
        try:
            buckets = list(client.list_buckets(max_results=1))
            print(f"✅ Captured request for list_buckets")
        except Exception as e:
            print(f"⚠️ Error during capture: {e}")
        
    except ImportError:
        print("⚠️ Cannot capture requests (unittest.mock not available)")
    except Exception as e:
        print(f"❌ Error: {e}")


def generate_sdk_configuration_examples(endpoint: str = "http://localhost:5000"):
    """Generate example code for SDK configuration"""
    print("\n" + "="*60)
    print("TEST 7: SDK Configuration Examples")
    print("="*60)
    
    print(f"\n📝 Example 1: Configure SDK for emulator at {endpoint}")
    print("-" * 60)
    print("""
from google.oauth2 import service_account
from google.cloud import storage

# Load credentials
creds = service_account.Credentials.from_service_account_file('path/to/creds.json')

# Create client pointing to emulator
client = storage.Client(
    credentials=creds,
    project=creds.project_id,
    api_endpoint='""" + endpoint + """'
)

# Now use client as normal
buckets = list(client.list_buckets())
""")
    
    print("\n📝 Example 2: Using environment variable for endpoint")
    print("-" * 60)
    print("""
import os
from google.cloud import storage

os.environ['GOOGLE_CLOUD_UNIVERSE_DOMAIN'] = 'googleapis.com'
os.environ['GRPC_PYTHON_BUILD_WITH_CYTHON'] = 'false'

# Set custom endpoint via environment or code
client = storage.Client(project='my-project', api_endpoint='""" + endpoint + """')
""")
    
    print("\n📝 Example 3: Dummy credentials for testing")
    print("-" * 60)
    print("""
{
  "type": "service_account",
  "project_id": "test-project",
  "private_key_id": "test-key-id",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\\nMIIEpAIBAAKCAQEA0Z1DVTzl...\\n-----END RSA PRIVATE KEY-----\\n",
  "client_email": "test@test-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test@test-project.iam.gserviceaccount.com"
}
""")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("GCP CLOUD STORAGE SDK EXPLORER")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Path to credentials
    cred_file = "gen-lang-client-0790195659-28a88c826eed.json"
    
    if not Path(cred_file).exists():
        print(f"\n❌ Credentials file not found: {cred_file}")
        print("Please ensure the file is in the current directory")
        sys.exit(1)
    
    # Run tests
    creds_dict = load_credentials(cred_file)
    
    creds_obj = test_credentials_loading(cred_file)
    client = test_client_creation(cred_file)
    
    custom_client, method = test_custom_endpoint(cred_file)
    if custom_client and method:
        print(f"\n✅ Custom endpoint configuration method: {method}")
    
    buckets = test_list_buckets(client)
    bucket = test_bucket_info(client)
    
    capture_request_format(cred_file)
    generate_sdk_configuration_examples()
    
    print("\n" + "="*60)
    print("EXPLORATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
