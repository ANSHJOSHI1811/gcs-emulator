"""
Compute CLI Module - Thin wrapper around Compute Engine REST API
Phase 4: gcslocal compute commands

Usage:
    gcslocal compute instances list --zone us-central1-a
    gcslocal compute instances create vm-1 --zone us-central1-a --machine-type e2-micro
    gcslocal compute instances start vm-1 --zone us-central1-a
    gcslocal compute instances stop vm-1 --zone us-central1-a
    gcslocal compute instances delete vm-1 --zone us-central1-a
    gcslocal compute instances describe vm-1 --zone us-central1-a
"""

import os
import sys
import json
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime


class ComputeCLI:
    """Compute Engine CLI - REST API wrapper"""
    
    def __init__(self, emulator_host: str = None, project: str = None):
        self.emulator_host = emulator_host or os.environ.get('STORAGE_EMULATOR_HOST', 'http://localhost:8080')
        self.project = project or os.environ.get('GCP_PROJECT', 'test-project')
        self.base_url = f"{self.emulator_host}/compute/v1"
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            return response
        except requests.exceptions.ConnectionError:
            self._print_error(f"Cannot connect to emulator at {self.emulator_host}")
            self._print_info("  Make sure server is running: python run.py")
            sys.exit(1)
        except Exception as e:
            self._print_error(f"Request failed: {e}")
            sys.exit(1)
    
    def _print_error(self, message: str):
        """Print error message"""
        try:
            print(f"\033[91m✗ {message}\033[0m", file=sys.stderr)
        except UnicodeEncodeError:
            print(f"[ERROR] {message}", file=sys.stderr)
    
    def _print_success(self, message: str):
        """Print success message"""
        try:
            print(f"\033[92m✓ {message}\033[0m")
        except UnicodeEncodeError:
            print(f"[OK] {message}")
    
    def _print_info(self, message: str):
        """Print info message"""
        print(f"\033[94m{message}\033[0m")
    
    def _print_warning(self, message: str):
        """Print warning message"""
        try:
            print(f"\033[93m⚠ {message}\033[0m")
        except UnicodeEncodeError:
            print(f"[WARNING] {message}")
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format ISO timestamp to date only"""
        if not timestamp:
            return "N/A"
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except:
            return timestamp[:10] if len(timestamp) >= 10 else timestamp
    
    def _handle_error_response(self, response: requests.Response, context: str = "Operation"):
        """Handle error responses from API"""
        if response.status_code == 404:
            error_data = response.json() if response.text else {}
            message = error_data.get('error', {}).get('message', 'Instance not found.')
            self._print_error(message)
        elif response.status_code == 400:
            error_data = response.json() if response.text else {}
            message = error_data.get('error', {}).get('message', 'Invalid request.')
            self._print_error(message)
        elif response.status_code == 409:
            error_data = response.json() if response.text else {}
            message = error_data.get('error', {}).get('message', 'Resource already exists.')
            self._print_error(message)
        elif response.status_code == 500:
            error_data = response.json() if response.text else {}
            message = error_data.get('error', {}).get('message', 'Internal server error.')
            self._print_error(f"{context} failed: {message}")
        else:
            self._print_error(f"{context} failed with status {response.status_code}")
            if response.text:
                try:
                    error_data = response.json()
                    print(f"  {error_data.get('error', {}).get('message', response.text)}")
                except:
                    print(f"  {response.text[:200]}")
        sys.exit(1)
    
    def list_instances(self, zone: str, project: str = None) -> bool:
        """List all instances in a zone"""
        project = project or self.project
        url = f"{self.base_url}/projects/{project}/zones/{zone}/instances"
        
        response = self._make_request('GET', url)
        
        if response.status_code == 200:
            data = response.json()
            instances = data.get('items', [])
            
            if not instances:
                self._print_info(f"No instances found in zone '{zone}'")
                return True
            
            # Print table header
            print(f"\n\033[1m{'NAME':<20} {'ZONE':<20} {'STATUS':<15} {'MACHINE_TYPE':<20} {'CREATED':<12}\033[0m")
            print("-" * 95)
            
            # Print instances
            for instance in instances:
                name = instance.get('name', 'N/A')
                zone_name = instance.get('zone', 'N/A').split('/')[-1] if instance.get('zone') else zone
                status = instance.get('status', 'N/A')
                machine_type = instance.get('machineType', 'N/A').split('/')[-1] if instance.get('machineType') else 'N/A'
                created = self._format_timestamp(instance.get('creationTimestamp'))
                
                # Color-code status
                if status == 'RUNNING':
                    status_colored = f"\033[92m{status}\033[0m"
                elif status == 'TERMINATED':
                    status_colored = f"\033[91m{status}\033[0m"
                elif status in ['PROVISIONING', 'STAGING']:
                    status_colored = f"\033[93m{status}\033[0m"
                else:
                    status_colored = status
                
                print(f"{name:<20} {zone_name:<20} {status_colored:<24} {machine_type:<20} {created:<12}")
            
            print(f"\nTotal: {len(instances)} instance(s)")
            return True
        else:
            self._handle_error_response(response, "List instances")
            return False
    
    def create_instance(self, name: str, zone: str, machine_type: str = "e2-micro", 
                       metadata: Dict[str, str] = None, labels: Dict[str, str] = None,
                       tags: List[str] = None, project: str = None) -> bool:
        """Create a new instance"""
        project = project or self.project
        url = f"{self.base_url}/projects/{project}/zones/{zone}/instances"
        
        # Build request payload
        payload = {
            "name": name,
            "machineType": f"zones/{zone}/machineTypes/{machine_type}"
        }
        
        if metadata:
            payload["metadata"] = {
                "items": [{"key": k, "value": v} for k, v in metadata.items()]
            }
        
        if labels:
            payload["labels"] = labels
        
        if tags:
            payload["tags"] = {"items": tags}
        
        response = self._make_request('POST', url, json=payload)
        
        if response.status_code == 200:
            operation = response.json()
            instance_name = operation.get('targetLink', '').split('/')[-1] or name
            self._print_success(f"Created instance '{instance_name}' in zone '{zone}' (status: RUNNING)")
            self._print_info(f"  Machine type: {machine_type}")
            if metadata:
                self._print_info(f"  Metadata keys: {', '.join(metadata.keys())}")
            return True
        else:
            self._handle_error_response(response, "Create instance")
            return False
    
    def start_instance(self, name: str, zone: str, project: str = None) -> bool:
        """Start a stopped instance"""
        project = project or self.project
        url = f"{self.base_url}/projects/{project}/zones/{zone}/instances/{name}/start"
        
        response = self._make_request('POST', url)
        
        if response.status_code == 200:
            self._print_success(f"Started instance '{name}' in zone '{zone}'")
            return True
        else:
            self._handle_error_response(response, "Start instance")
            return False
    
    def stop_instance(self, name: str, zone: str, project: str = None) -> bool:
        """Stop a running instance"""
        project = project or self.project
        url = f"{self.base_url}/projects/{project}/zones/{zone}/instances/{name}/stop"
        
        response = self._make_request('POST', url)
        
        if response.status_code == 200:
            self._print_success(f"Stopped instance '{name}' in zone '{zone}'")
            return True
        else:
            self._handle_error_response(response, "Stop instance")
            return False
    
    def delete_instance(self, name: str, zone: str, project: str = None) -> bool:
        """Delete an instance"""
        project = project or self.project
        url = f"{self.base_url}/projects/{project}/zones/{zone}/instances/{name}"
        
        response = self._make_request('DELETE', url)
        
        if response.status_code == 200:
            self._print_success(f"Deleted instance '{name}' from zone '{zone}'")
            return True
        else:
            self._handle_error_response(response, "Delete instance")
            return False
    
    def describe_instance(self, name: str, zone: str, project: str = None) -> bool:
        """Describe (get details of) an instance"""
        project = project or self.project
        url = f"{self.base_url}/projects/{project}/zones/{zone}/instances/{name}"
        
        response = self._make_request('GET', url)
        
        if response.status_code == 200:
            instance = response.json()
            # Pretty print JSON
            print(json.dumps(instance, indent=2))
            return True
        else:
            self._handle_error_response(response, "Describe instance")
            return False


def parse_compute_args(args: List[str]) -> Dict[str, Any]:
    """Parse compute command arguments"""
    parsed = {
        'zone': None,
        'project': None,
        'machine_type': 'e2-micro',
        'metadata': {},
        'labels': {},
        'tags': []
    }
    
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg == '--zone' and i + 1 < len(args):
            parsed['zone'] = args[i + 1]
            i += 2
        elif arg == '--project' and i + 1 < len(args):
            parsed['project'] = args[i + 1]
            i += 2
        elif arg == '--machine-type' and i + 1 < len(args):
            parsed['machine_type'] = args[i + 1]
            i += 2
        elif arg == '--metadata' and i + 1 < len(args):
            # Format: --metadata key1=value1,key2=value2
            metadata_str = args[i + 1]
            for pair in metadata_str.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    parsed['metadata'][key.strip()] = value.strip()
            i += 2
        elif arg == '--labels' and i + 1 < len(args):
            # Format: --labels key1=value1,key2=value2
            labels_str = args[i + 1]
            for pair in labels_str.split(','):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    parsed['labels'][key.strip()] = value.strip()
            i += 2
        elif arg == '--tags' and i + 1 < len(args):
            # Format: --tags tag1,tag2,tag3
            parsed['tags'] = [t.strip() for t in args[i + 1].split(',')]
            i += 2
        else:
            i += 1
    
    return parsed


def handle_compute_command(resource: str, action: str, args: List[str], emulator_host: str = None, project: str = None):
    """Handle compute CLI commands"""
    cli = ComputeCLI(emulator_host=emulator_host, project=project)
    
    if resource != 'instances':
        cli._print_error(f"Unsupported resource: {resource}")
        cli._print_info("  Supported resources: instances")
        return 1
    
    # Parse common arguments
    parsed_args = parse_compute_args(args)
    
    if action == 'list':
        if not parsed_args['zone']:
            cli._print_error("--zone is required for 'list' command")
            cli._print_info("  Usage: gcslocal compute instances list --zone us-central1-a")
            return 1
        
        success = cli.list_instances(
            zone=parsed_args['zone'],
            project=parsed_args['project']
        )
        return 0 if success else 1
    
    elif action == 'create':
        if not args or not args[0] or args[0].startswith('--'):
            cli._print_error("Instance name is required for 'create' command")
            cli._print_info("  Usage: gcslocal compute instances create <name> --zone us-central1-a --machine-type e2-micro")
            return 1
        
        instance_name = args[0]
        
        if not parsed_args['zone']:
            cli._print_error("--zone is required for 'create' command")
            cli._print_info("  Usage: gcslocal compute instances create <name> --zone us-central1-a")
            return 1
        
        success = cli.create_instance(
            name=instance_name,
            zone=parsed_args['zone'],
            machine_type=parsed_args['machine_type'],
            metadata=parsed_args['metadata'] if parsed_args['metadata'] else None,
            labels=parsed_args['labels'] if parsed_args['labels'] else None,
            tags=parsed_args['tags'] if parsed_args['tags'] else None,
            project=parsed_args['project']
        )
        return 0 if success else 1
    
    elif action == 'start':
        if not args or not args[0] or args[0].startswith('--'):
            cli._print_error("Instance name is required for 'start' command")
            cli._print_info("  Usage: gcslocal compute instances start <name> --zone us-central1-a")
            return 1
        
        instance_name = args[0]
        
        if not parsed_args['zone']:
            cli._print_error("--zone is required for 'start' command")
            return 1
        
        success = cli.start_instance(
            name=instance_name,
            zone=parsed_args['zone'],
            project=parsed_args['project']
        )
        return 0 if success else 1
    
    elif action == 'stop':
        if not args or not args[0] or args[0].startswith('--'):
            cli._print_error("Instance name is required for 'stop' command")
            cli._print_info("  Usage: gcslocal compute instances stop <name> --zone us-central1-a")
            return 1
        
        instance_name = args[0]
        
        if not parsed_args['zone']:
            cli._print_error("--zone is required for 'stop' command")
            return 1
        
        success = cli.stop_instance(
            name=instance_name,
            zone=parsed_args['zone'],
            project=parsed_args['project']
        )
        return 0 if success else 1
    
    elif action == 'delete':
        if not args or not args[0] or args[0].startswith('--'):
            cli._print_error("Instance name is required for 'delete' command")
            cli._print_info("  Usage: gcslocal compute instances delete <name> --zone us-central1-a")
            return 1
        
        instance_name = args[0]
        
        if not parsed_args['zone']:
            cli._print_error("--zone is required for 'delete' command")
            return 1
        
        success = cli.delete_instance(
            name=instance_name,
            zone=parsed_args['zone'],
            project=parsed_args['project']
        )
        return 0 if success else 1
    
    elif action == 'describe':
        if not args or not args[0] or args[0].startswith('--'):
            cli._print_error("Instance name is required for 'describe' command")
            cli._print_info("  Usage: gcslocal compute instances describe <name> --zone us-central1-a")
            return 1
        
        instance_name = args[0]
        
        if not parsed_args['zone']:
            cli._print_error("--zone is required for 'describe' command")
            return 1
        
        success = cli.describe_instance(
            name=instance_name,
            zone=parsed_args['zone'],
            project=parsed_args['project']
        )
        return 0 if success else 1
    
    else:
        cli._print_error(f"Unsupported action: {action}")
        cli._print_info("  Supported actions: list, create, start, stop, delete, describe")
        return 1
