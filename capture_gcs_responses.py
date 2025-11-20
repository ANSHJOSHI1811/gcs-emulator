#!/usr/bin/env python3
"""
GCP API Response Capture Script
Purpose: Capture real API responses from GCS to use as templates for emulator
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    from google.cloud import storage
    from google.oauth2 import service_account
    import requests
    from unittest.mock import patch
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    sys.exit(1)


class ResponseCapture:
    """Capture and save real API responses"""
    
    def __init__(self, cred_file: str):
        self.cred_file = cred_file
        self.responses = {}
        self.load_credentials()
    
    def load_credentials(self):
        """Load credentials"""
        print(f"Loading credentials from {self.cred_file}...")
        with open(self.cred_file) as f:
            self.creds_dict = json.load(f)
        
        self.creds = service_account.Credentials.from_service_account_file(self.cred_file)
        self.project_id = self.creds.project_id
        print(f"✅ Credentials loaded for project: {self.project_id}")
    
    def capture_list_buckets(self):
        """Capture list buckets response"""
        print("\n" + "="*60)
        print("CAPTURING: List Buckets Response")
        print("="*60)
        
        try:
            client = storage.Client(credentials=self.creds, project=self.project_id)
            
            # Intercept HTTP responses
            original_list_buckets = client.list_buckets
            
            print("Making API call to list_buckets()...")
            response = client._connection.api_request(
                method="GET",
                path=f"/b",
                query_params={
                    "project": self.project_id,
                    "projection": "noAcl",
                    "prettyPrint": "false"
                }
            )
            
            print("✅ Response captured!")
            print(json.dumps(response, indent=2, default=str))
            
            self.responses['list_buckets'] = response
            return response
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def capture_bucket_metadata(self, bucket_name: Optional[str] = None):
        """Capture bucket metadata response"""
        print("\n" + "="*60)
        print("CAPTURING: Get Bucket Metadata Response")
        print("="*60)
        
        try:
            client = storage.Client(credentials=self.creds, project=self.project_id)
            
            # If no bucket specified, create one for testing
            if not bucket_name:
                import random
                import string
                bucket_name = f"test-capture-{random.randint(1000, 9999)}"
                print(f"Creating test bucket: {bucket_name}...")
                
                try:
                    bucket = client.create_bucket(bucket_name, location="US")
                    print(f"✅ Bucket created: {bucket_name}")
                except Exception as e:
                    print(f"⚠️ Could not create bucket: {e}")
                    # Try to list existing buckets instead
                    buckets = list(client.list_buckets(max_results=1))
                    if buckets:
                        bucket_name = buckets[0].name
                        print(f"Using existing bucket: {bucket_name}")
                    else:
                        print("❌ No buckets available")
                        return None
            
            # Get bucket metadata via API
            print(f"Fetching metadata for bucket: {bucket_name}...")
            response = client._connection.api_request(
                method="GET",
                path=f"/b/{bucket_name}",
                query_params={
                    "projection": "full"
                }
            )
            
            print("✅ Response captured!")
            print(json.dumps(response, indent=2, default=str))
            
            self.responses['get_bucket'] = response
            return response
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def capture_list_objects(self, bucket_name: Optional[str] = None):
        """Capture list objects response"""
        print("\n" + "="*60)
        print("CAPTURING: List Objects Response")
        print("="*60)
        
        try:
            client = storage.Client(credentials=self.creds, project=self.project_id)
            
            if not bucket_name:
                # Get first available bucket
                buckets = list(client.list_buckets(max_results=1))
                if not buckets:
                    print("⚠️ No buckets available")
                    return None
                bucket_name = buckets[0].name
            
            print(f"Listing objects in bucket: {bucket_name}...")
            response = client._connection.api_request(
                method="GET",
                path=f"/b/{bucket_name}/o",
                query_params={
                    "projection": "full",
                    "prettyPrint": "false"
                }
            )
            
            print("✅ Response captured!")
            print(json.dumps(response, indent=2, default=str))
            
            self.responses['list_objects'] = response
            return response
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def capture_error_response(self):
        """Capture error response (404 not found)"""
        print("\n" + "="*60)
        print("CAPTURING: Error Response (404 Not Found)")
        print("="*60)
        
        try:
            client = storage.Client(credentials=self.creds, project=self.project_id)
            
            print("Attempting to get non-existent bucket...")
            response = client._connection.api_request(
                method="GET",
                path="/b/this-bucket-does-not-exist-12345",
                query_params={"projection": "full"}
            )
            
        except Exception as e:
            print(f"✅ Error captured (as expected)!")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            
            # Try to get error details
            if hasattr(e, 'response'):
                print(f"Response: {e.response}")
            if hasattr(e, 'status_code'):
                print(f"Status code: {e.status_code}")
            
            self.responses['error_404'] = {
                'error_type': type(e).__name__,
                'message': str(e)
            }
            return None
    
    def save_responses(self, output_file: str = "gcs_api_responses.json"):
        """Save captured responses to file"""
        print("\n" + "="*60)
        print("SAVING RESPONSES")
        print("="*60)
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'project_id': self.project_id,
            'responses': self.responses
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"✅ Responses saved to {output_file}")


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("GCP API RESPONSE CAPTURE")
    print("="*60)
    
    cred_file = "gen-lang-client-0790195659-28a88c826eed.json"
    
    if not Path(cred_file).exists():
        print(f"❌ Credentials file not found: {cred_file}")
        sys.exit(1)
    
    # Create capture instance
    capture = ResponseCapture(cred_file)
    
    # Capture responses
    capture.capture_list_buckets()
    capture.capture_bucket_metadata()
    capture.capture_list_objects()
    capture.capture_error_response()
    
    # Save all responses
    capture.save_responses("gcs_api_responses.json")
    
    print("\n" + "="*60)
    print("CAPTURE COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
