#!/usr/bin/env python3
"""
GCS Local CLI - LocalStack-style interface for GCS Emulator

Usage:
    python gcslocal.py mb gs://bucket-name              # Make bucket
    python gcslocal.py ls gs://                         # List buckets
    python gcslocal.py ls gs://bucket-name/             # List objects
    python gcslocal.py rb gs://bucket-name              # Remove bucket
    python gcslocal.py cp file.txt gs://bucket/file.txt # Upload file
    python gcslocal.py cp gs://bucket/file.txt local/   # Download file
    python gcslocal.py rm gs://bucket/file.txt          # Remove object
"""

import os
import sys
import argparse
import requests
from typing import Optional
from pathlib import Path

# Configuration
EMULATOR_HOST = os.environ.get('STORAGE_EMULATOR_HOST', 'http://localhost:8080')
DEFAULT_PROJECT = os.environ.get('GCP_PROJECT', 'test-project')
DEFAULT_LOCATION = os.environ.get('GCS_LOCATION', 'US')

class Colors:
    """Terminal colors for output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def parse_gs_url(url: str) -> tuple:
    """Parse gs://bucket/object URL"""
    if not url.startswith('gs://'):
        raise ValueError(f"Invalid GCS URL: {url} (must start with gs://)")
    
    path = url[5:]  # Remove 'gs://'
    if '/' in path:
        bucket, obj = path.split('/', 1)
        return bucket, obj
    return path, None

def print_success(message: str):
    """Print success message"""
    # Use 'OK' instead of emoji for Windows compatibility
    try:
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    except UnicodeEncodeError:
        print(f"{Colors.GREEN}[OK] {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message"""
    # Use 'ERROR' instead of emoji for Windows compatibility
    try:
        print(f"{Colors.RED}✗ {message}{Colors.RESET}", file=sys.stderr)
    except UnicodeEncodeError:
        print(f"{Colors.RED}[ERROR] {message}{Colors.RESET}", file=sys.stderr)

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}{message}{Colors.RESET}")

def make_bucket(bucket_name: str, location: str = None, storage_class: str = None, project: str = None):
    """Create a bucket - equivalent to 'awslocal s3 mb s3://bucket'"""
    location = location or DEFAULT_LOCATION
    storage_class = storage_class or 'STANDARD'
    project = project or DEFAULT_PROJECT
    
    url = f"{EMULATOR_HOST}/storage/v1/b?project={project}"
    payload = {
        'name': bucket_name,
        'location': location,
        'storageClass': storage_class
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 201:
            data = response.json()
            print_success(f"Bucket created: gs://{bucket_name}")
            print_info(f"  Location: {data.get('location')}")
            print_info(f"  Storage Class: {data.get('storageClass')}")
        elif response.status_code == 409:
            print_error(f"Bucket gs://{bucket_name} already exists")
            return False
        else:
            print_error(f"Failed to create bucket: {response.status_code}")
            print_error(f"  {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to emulator at {EMULATOR_HOST}")
        print_info("  Make sure server is running: python run.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False
    
    return True

def list_buckets(project: str = None):
    """List all buckets - equivalent to 'awslocal s3 ls'"""
    project = project or DEFAULT_PROJECT
    url = f"{EMULATOR_HOST}/storage/v1/b?project={project}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            buckets = data.get('items', [])
            
            if not buckets:
                print_info("No buckets found")
                return True
            
            print(f"{Colors.BOLD}Buckets in project '{project}':{Colors.RESET}")
            for bucket in buckets:
                name = bucket.get('name')
                location = bucket.get('location', 'N/A')
                storage_class = bucket.get('storageClass', 'N/A')
                created = bucket.get('timeCreated', 'N/A')[:10]  # Date only
                
                print(f"  {Colors.GREEN}gs://{name}/{Colors.RESET}")
                print(f"    Location: {location}, Class: {storage_class}, Created: {created}")
            
            return True
        else:
            print_error(f"Failed to list buckets: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to emulator at {EMULATOR_HOST}")
        print_info("  Make sure server is running: python run.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def list_objects(bucket_name: str):
    """List objects in bucket - equivalent to 'awslocal s3 ls s3://bucket'"""
    url = f"{EMULATOR_HOST}/storage/v1/b/{bucket_name}/o"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            objects = data.get('items', [])
            
            if not objects:
                print_info(f"No objects in gs://{bucket_name}/")
                return True
            
            print(f"{Colors.BOLD}Objects in gs://{bucket_name}/{Colors.RESET}")
            for obj in objects:
                name = obj.get('name')
                size = obj.get('size', 0)
                updated = obj.get('updated', 'N/A')[:10]
                
                # Format size
                size_kb = int(size) / 1024 if size else 0
                size_str = f"{size_kb:.2f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
                
                print(f"  {name} ({size_str}, updated: {updated})")
            
            return True
        elif response.status_code == 404:
            print_error(f"Bucket gs://{bucket_name}/ not found")
            return False
        else:
            print_error(f"Failed to list objects: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to emulator at {EMULATOR_HOST}")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def remove_bucket(bucket_name: str, force: bool = False):
    """Remove bucket - equivalent to 'awslocal s3 rb s3://bucket'"""
    url = f"{EMULATOR_HOST}/storage/v1/b/{bucket_name}"
    
    try:
        response = requests.delete(url, timeout=5)
        if response.status_code == 204:
            print_success(f"Bucket removed: gs://{bucket_name}")
            return True
        elif response.status_code == 404:
            print_error(f"Bucket gs://{bucket_name} not found")
            return False
        elif response.status_code == 409:
            print_error(f"Bucket gs://{bucket_name} is not empty")
            if force:
                print_info("  Use --force to delete non-empty bucket")
            return False
        else:
            print_error(f"Failed to remove bucket: {response.status_code}")
            print_error(f"  {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to emulator at {EMULATOR_HOST}")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def upload_file(local_path: str, gs_url: str):
    """Upload file - equivalent to 'awslocal s3 cp file s3://bucket/key'"""
    bucket_name, object_name = parse_gs_url(gs_url)
    
    if not Path(local_path).exists():
        print_error(f"Local file not found: {local_path}")
        return False
    
    # Read file content
    try:
        with open(local_path, 'rb') as f:
            content = f.read()
    except Exception as e:
        print_error(f"Failed to read file: {e}")
        return False
    
    # Detect content type
    import mimetypes
    content_type, _ = mimetypes.guess_type(local_path)
    if not content_type:
        content_type = 'application/octet-stream'
    
    # Upload to emulator
    url = f"{EMULATOR_HOST}/upload/storage/v1/b/{bucket_name}/o?uploadType=media&name={object_name}"
    headers = {
        'Content-Type': content_type,
        'Content-Length': str(len(content))
    }
    
    try:
        response = requests.post(url, data=content, headers=headers, timeout=30)
        if response.status_code in [200, 201]:
            data = response.json()
            print_success(f"Uploaded: {local_path} -> gs://{bucket_name}/{object_name}")
            print_info(f"  Size: {data.get('size')} bytes")
            print_info(f"  Content-Type: {data.get('contentType')}")
            if 'md5Hash' in data:
                print_info(f"  MD5: {data.get('md5Hash')}")
            return True
        elif response.status_code == 404:
            print_error(f"Bucket gs://{bucket_name} not found")
            return False
        else:
            print_error(f"Upload failed: {response.status_code}")
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print_error(f"  {error_data['error']}")
            except:
                print_error(f"  {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to emulator at {EMULATOR_HOST}")
        print_info("  Make sure server is running: python run.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def download_file(gs_url: str, local_path: str):
    """Download file - equivalent to 'awslocal s3 cp s3://bucket/key file'"""
    bucket_name, object_name = parse_gs_url(gs_url)
    
    # Download from emulator
    url = f"{EMULATOR_HOST}/storage/v1/b/{bucket_name}/o/{object_name}?alt=media"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Create parent directories if needed
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            print_success(f"Downloaded: gs://{bucket_name}/{object_name} -> {local_path}")
            print_info(f"  Size: {len(response.content)} bytes")
            if 'Content-Type' in response.headers:
                print_info(f"  Content-Type: {response.headers['Content-Type']}")
            return True
        elif response.status_code == 404:
            print_error(f"Object gs://{bucket_name}/{object_name} not found")
            return False
        else:
            print_error(f"Download failed: {response.status_code}")
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print_error(f"  {error_data['error']}")
            except:
                print_error(f"  {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to emulator at {EMULATOR_HOST}")
        print_info("  Make sure server is running: python run.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def remove_object(gs_url: str):
    """Remove object - equivalent to 'awslocal s3 rm s3://bucket/key'"""
    bucket_name, object_name = parse_gs_url(gs_url)
    
    url = f"{EMULATOR_HOST}/storage/v1/b/{bucket_name}/o/{object_name}"
    
    try:
        response = requests.delete(url, timeout=5)
        if response.status_code == 204:
            print_success(f"Object removed: gs://{bucket_name}/{object_name}")
            return True
        elif response.status_code == 404:
            print_error(f"Object not found: gs://{bucket_name}/{object_name}")
            return False
        else:
            print_error(f"Failed to remove object: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to emulator at {EMULATOR_HOST}")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='GCS Local CLI - LocalStack-style interface for GCS Emulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gcslocal.py mb gs://my-bucket                # Create bucket
  python gcslocal.py mb gs://my-bucket --location EU  # Create in EU
  python gcslocal.py ls                                # List all buckets
  python gcslocal.py ls gs://my-bucket/               # List objects in bucket
  python gcslocal.py rb gs://my-bucket                # Remove bucket
  python gcslocal.py cp file.txt gs://bucket/key      # Upload file (TODO)
  python gcslocal.py cp gs://bucket/key file.txt      # Download file (TODO)
  python gcslocal.py rm gs://bucket/key               # Remove object

Environment Variables:
  STORAGE_EMULATOR_HOST   Emulator endpoint (default: http://localhost:8080)
  GCP_PROJECT             Project ID (default: test-project)
  GCS_LOCATION            Default location (default: US)
        """
    )
    
    parser.add_argument('command', help='Command to execute (mb, ls, rb, cp, rm)')
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--location', help='Bucket location (for mb command)')
    parser.add_argument('--storage-class', help='Storage class (for mb command)')
    parser.add_argument('--force', action='store_true', help='Force operation')
    parser.add_argument('--project', help='GCP project ID', default=DEFAULT_PROJECT)
    
    args = parser.parse_args()
    
    # Use project from args or default
    project = args.project
    
    # Execute command
    command = args.command.lower()
    
    try:
        if command == 'mb':  # Make bucket
            if not args.args:
                print_error("Usage: python gcslocal.py mb gs://bucket-name")
                return 1
            
            bucket_name, _ = parse_gs_url(args.args[0])
            success = make_bucket(bucket_name, args.location, args.storage_class, project)
            return 0 if success else 1
        
        elif command == 'ls':  # List
            if not args.args:
                # List buckets
                success = list_buckets(project)
            else:
                # List objects in bucket
                bucket_name, _ = parse_gs_url(args.args[0])
                success = list_objects(bucket_name)
            return 0 if success else 1
        
        elif command == 'rb':  # Remove bucket
            if not args.args:
                print_error("Usage: python gcslocal.py rb gs://bucket-name")
                return 1
            
            bucket_name, _ = parse_gs_url(args.args[0])
            success = remove_bucket(bucket_name, args.force)
            return 0 if success else 1
        
        elif command == 'cp':  # Copy (upload/download)
            if len(args.args) < 2:
                print_error("Usage: python gcslocal.py cp <source> <destination>")
                return 1
            
            source = args.args[0]
            dest = args.args[1]
            
            if source.startswith('gs://'):
                # Download
                success = download_file(source, dest)
            else:
                # Upload
                success = upload_file(source, dest)
            return 0 if success else 1
        
        elif command == 'rm':  # Remove object
            if not args.args:
                print_error("Usage: python gcslocal.py rm gs://bucket/object")
                return 1
            
            success = remove_object(args.args[0])
            return 0 if success else 1
        
        else:
            print_error(f"Unknown command: {command}")
            print_info("Supported commands: mb, ls, rb, cp, rm")
            return 1
    
    except ValueError as e:
        print_error(str(e))
        return 1
    except KeyboardInterrupt:
        print("\n" + Colors.YELLOW + "Interrupted" + Colors.RESET)
        return 130

if __name__ == '__main__':
    sys.exit(main())
