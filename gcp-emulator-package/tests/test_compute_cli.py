"""
Tests for Compute CLI (Phase 4)
Tests CLI commands for instance lifecycle management
"""
import os
import sys
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.compute_cli import ComputeCLI, handle_compute_command, parse_compute_args


class TestParseComputeArgs:
    """Test argument parsing"""
    
    def test_parse_zone(self):
        """Parse --zone argument"""
        args = ['--zone', 'us-central1-a']
        parsed = parse_compute_args(args)
        assert parsed['zone'] == 'us-central1-a'
    
    def test_parse_machine_type(self):
        """Parse --machine-type argument"""
        args = ['--machine-type', 'n1-standard-2']
        parsed = parse_compute_args(args)
        assert parsed['machine_type'] == 'n1-standard-2'
    
    def test_parse_project(self):
        """Parse --project argument"""
        args = ['--project', 'my-project']
        parsed = parse_compute_args(args)
        assert parsed['project'] == 'my-project'
    
    def test_parse_metadata(self):
        """Parse --metadata argument"""
        args = ['--metadata', 'key1=value1,key2=value2']
        parsed = parse_compute_args(args)
        assert parsed['metadata'] == {'key1': 'value1', 'key2': 'value2'}
    
    def test_parse_labels(self):
        """Parse --labels argument"""
        args = ['--labels', 'env=prod,team=backend']
        parsed = parse_compute_args(args)
        assert parsed['labels'] == {'env': 'prod', 'team': 'backend'}
    
    def test_parse_tags(self):
        """Parse --tags argument"""
        args = ['--tags', 'web,https,production']
        parsed = parse_compute_args(args)
        assert parsed['tags'] == ['web', 'https', 'production']
    
    def test_parse_multiple_args(self):
        """Parse multiple arguments together"""
        args = ['--zone', 'us-west1-a', '--machine-type', 'e2-small', '--project', 'test-proj']
        parsed = parse_compute_args(args)
        assert parsed['zone'] == 'us-west1-a'
        assert parsed['machine_type'] == 'e2-small'
        assert parsed['project'] == 'test-proj'


class TestComputeCLI:
    """Test ComputeCLI class"""
    
    @pytest.fixture
    def cli(self):
        """Create CLI instance"""
        return ComputeCLI(emulator_host='http://localhost:8080', project='test-project')
    
    @pytest.fixture
    def mock_response(self):
        """Create mock response"""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {}
        response.text = ''
        return response
    
    def test_cli_initialization(self, cli):
        """Test CLI initialization"""
        assert cli.emulator_host == 'http://localhost:8080'
        assert cli.project == 'test-project'
        assert cli.base_url == 'http://localhost:8080/compute/v1'
    
    def test_cli_default_values(self):
        """Test CLI with default values"""
        with patch.dict(os.environ, {'STORAGE_EMULATOR_HOST': 'http://custom:9000', 'GCP_PROJECT': 'my-project'}):
            cli = ComputeCLI()
            assert cli.emulator_host == 'http://custom:9000'
            assert cli.project == 'my-project'
    
    @patch('cli.compute_cli.requests.request')
    def test_list_instances_success(self, mock_request, cli, mock_response):
        """Test successful list instances"""
        mock_response.json.return_value = {
            'items': [
                {
                    'name': 'vm-1',
                    'zone': 'projects/test-project/zones/us-central1-a',
                    'status': 'RUNNING',
                    'machineType': 'zones/us-central1-a/machineTypes/e2-micro',
                    'creationTimestamp': '2025-12-05T10:00:00Z'
                }
            ]
        }
        mock_request.return_value = mock_response
        
        result = cli.list_instances(zone='us-central1-a')
        
        assert result is True
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == 'GET'
        assert 'us-central1-a/instances' in call_args[0][1]
    
    @patch('cli.compute_cli.requests.request')
    def test_list_instances_empty(self, mock_request, cli, mock_response):
        """Test list instances with no instances"""
        mock_response.json.return_value = {'items': []}
        mock_request.return_value = mock_response
        
        result = cli.list_instances(zone='us-central1-a')
        
        assert result is True
    
    @patch('cli.compute_cli.requests.request')
    @patch('sys.exit')
    def test_list_instances_404(self, mock_exit, mock_request, cli):
        """Test list instances with 404 error"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'error': {'message': 'Zone not found'}}
        mock_response.text = 'Zone not found'
        mock_request.return_value = mock_response
        
        cli.list_instances(zone='invalid-zone')
        
        mock_exit.assert_called_once_with(1)
    
    @patch('cli.compute_cli.requests.request')
    def test_create_instance_success(self, mock_request, cli, mock_response):
        """Test successful instance creation"""
        mock_response.json.return_value = {
            'targetLink': 'projects/test-project/zones/us-central1-a/instances/vm-1',
            'status': 'DONE'
        }
        mock_request.return_value = mock_response
        
        result = cli.create_instance(
            name='vm-1',
            zone='us-central1-a',
            machine_type='e2-micro'
        )
        
        assert result is True
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == 'POST'
        assert 'us-central1-a/instances' in call_args[0][1]
        
        # Check payload
        payload = call_args[1]['json']
        assert payload['name'] == 'vm-1'
        assert 'e2-micro' in payload['machineType']
    
    @patch('cli.compute_cli.requests.request')
    def test_create_instance_with_metadata(self, mock_request, cli, mock_response):
        """Test instance creation with metadata"""
        mock_response.json.return_value = {'targetLink': 'vm-1', 'status': 'DONE'}
        mock_request.return_value = mock_response
        
        result = cli.create_instance(
            name='vm-1',
            zone='us-central1-a',
            machine_type='e2-micro',
            metadata={'startup-script': 'echo hello'}
        )
        
        assert result is True
        payload = mock_request.call_args[1]['json']
        assert 'metadata' in payload
        assert payload['metadata']['items'][0]['key'] == 'startup-script'
    
    @patch('cli.compute_cli.requests.request')
    @patch('sys.exit')
    def test_create_instance_conflict(self, mock_exit, mock_request, cli):
        """Test instance creation with conflict (already exists)"""
        mock_response = Mock()
        mock_response.status_code = 409
        mock_response.json.return_value = {'error': {'message': 'Instance already exists'}}
        mock_response.text = 'Instance already exists'
        mock_request.return_value = mock_response
        
        cli.create_instance(name='vm-1', zone='us-central1-a')
        
        mock_exit.assert_called_once_with(1)
    
    @patch('cli.compute_cli.requests.request')
    def test_start_instance_success(self, mock_request, cli, mock_response):
        """Test successful instance start"""
        mock_request.return_value = mock_response
        
        result = cli.start_instance(name='vm-1', zone='us-central1-a')
        
        assert result is True
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == 'POST'
        assert 'vm-1/start' in call_args[0][1]
    
    @patch('cli.compute_cli.requests.request')
    @patch('sys.exit')
    def test_start_instance_invalid_state(self, mock_exit, mock_request, cli):
        """Test start instance with invalid state"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': {'message': 'Instance already running'}}
        mock_response.text = 'Invalid state'
        mock_request.return_value = mock_response
        
        cli.start_instance(name='vm-1', zone='us-central1-a')
        
        mock_exit.assert_called_once_with(1)
    
    @patch('cli.compute_cli.requests.request')
    def test_stop_instance_success(self, mock_request, cli, mock_response):
        """Test successful instance stop"""
        mock_request.return_value = mock_response
        
        result = cli.stop_instance(name='vm-1', zone='us-central1-a')
        
        assert result is True
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == 'POST'
        assert 'vm-1/stop' in call_args[0][1]
    
    @patch('cli.compute_cli.requests.request')
    def test_delete_instance_success(self, mock_request, cli, mock_response):
        """Test successful instance deletion"""
        mock_request.return_value = mock_response
        
        result = cli.delete_instance(name='vm-1', zone='us-central1-a')
        
        assert result is True
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == 'DELETE'
        assert 'instances/vm-1' in call_args[0][1]
    
    @patch('cli.compute_cli.requests.request')
    @patch('sys.exit')
    def test_delete_instance_not_found(self, mock_exit, mock_request, cli):
        """Test delete non-existent instance"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'error': {'message': 'Instance not found'}}
        mock_response.text = 'Not found'
        mock_request.return_value = mock_response
        
        cli.delete_instance(name='nonexistent', zone='us-central1-a')
        
        mock_exit.assert_called_once_with(1)
    
    @patch('cli.compute_cli.requests.request')
    @patch('builtins.print')
    def test_describe_instance_success(self, mock_print, mock_request, cli, mock_response):
        """Test successful describe instance"""
        instance_data = {
            'name': 'vm-1',
            'zone': 'us-central1-a',
            'status': 'RUNNING',
            'machineType': 'e2-micro'
        }
        mock_response.json.return_value = instance_data
        mock_request.return_value = mock_response
        
        result = cli.describe_instance(name='vm-1', zone='us-central1-a')
        
        assert result is True
        # Verify JSON was printed
        mock_print.assert_called()
        printed_output = str(mock_print.call_args)
        assert 'vm-1' in printed_output


class TestHandleComputeCommand:
    """Test handle_compute_command function"""
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_unsupported_resource(self, mock_cli_class):
        """Test unsupported resource type"""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command('networks', 'list', ['--zone', 'us-central1-a'])
        
        assert exit_code == 1
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_list_without_zone(self, mock_cli_class):
        """Test list command without zone"""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command('instances', 'list', [])
        
        assert exit_code == 1
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_list_with_zone(self, mock_cli_class):
        """Test list command with zone"""
        mock_cli = Mock()
        mock_cli.list_instances.return_value = True
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command('instances', 'list', ['--zone', 'us-central1-a'])
        
        assert exit_code == 0
        mock_cli.list_instances.assert_called_once_with(zone='us-central1-a', project=None)
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_create_without_name(self, mock_cli_class):
        """Test create command without instance name"""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command('instances', 'create', ['--zone', 'us-central1-a'])
        
        assert exit_code == 1
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_create_without_zone(self, mock_cli_class):
        """Test create command without zone"""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command('instances', 'create', ['vm-1'])
        
        assert exit_code == 1
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_create_with_all_args(self, mock_cli_class):
        """Test create command with all arguments"""
        mock_cli = Mock()
        mock_cli.create_instance.return_value = True
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command(
            'instances',
            'create',
            ['vm-1', '--zone', 'us-central1-a', '--machine-type', 'n1-standard-1', '--project', 'my-proj']
        )
        
        assert exit_code == 0
        mock_cli.create_instance.assert_called_once()
        call_kwargs = mock_cli.create_instance.call_args[1]
        assert call_kwargs['name'] == 'vm-1'
        assert call_kwargs['zone'] == 'us-central1-a'
        assert call_kwargs['machine_type'] == 'n1-standard-1'
        assert call_kwargs['project'] == 'my-proj'
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_start_with_name_and_zone(self, mock_cli_class):
        """Test start command"""
        mock_cli = Mock()
        mock_cli.start_instance.return_value = True
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command('instances', 'start', ['vm-1', '--zone', 'us-central1-a'])
        
        assert exit_code == 0
        mock_cli.start_instance.assert_called_once_with(name='vm-1', zone='us-central1-a', project=None)
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_stop_with_name_and_zone(self, mock_cli_class):
        """Test stop command"""
        mock_cli = Mock()
        mock_cli.stop_instance.return_value = True
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command('instances', 'stop', ['vm-1', '--zone', 'us-central1-a'])
        
        assert exit_code == 0
        mock_cli.stop_instance.assert_called_once_with(name='vm-1', zone='us-central1-a', project=None)
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_delete_with_name_and_zone(self, mock_cli_class):
        """Test delete command"""
        mock_cli = Mock()
        mock_cli.delete_instance.return_value = True
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command('instances', 'delete', ['vm-1', '--zone', 'us-central1-a'])
        
        assert exit_code == 0
        mock_cli.delete_instance.assert_called_once_with(name='vm-1', zone='us-central1-a', project=None)
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_describe_with_name_and_zone(self, mock_cli_class):
        """Test describe command"""
        mock_cli = Mock()
        mock_cli.describe_instance.return_value = True
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command('instances', 'describe', ['vm-1', '--zone', 'us-central1-a'])
        
        assert exit_code == 0
        mock_cli.describe_instance.assert_called_once_with(name='vm-1', zone='us-central1-a', project=None)
    
    @patch('cli.compute_cli.ComputeCLI')
    def test_unsupported_action(self, mock_cli_class):
        """Test unsupported action"""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        
        exit_code = handle_compute_command('instances', 'reboot', ['vm-1', '--zone', 'us-central1-a'])
        
        assert exit_code == 1


class TestCLIIntegration:
    """Integration tests for CLI (requires running server)"""
    
    @pytest.fixture
    def emulator_url(self):
        """Get emulator URL from environment"""
        return os.environ.get('STORAGE_EMULATOR_HOST', 'http://localhost:8080')
    
    @pytest.mark.integration
    def test_full_instance_lifecycle(self, emulator_url):
        """Test complete instance lifecycle via CLI"""
        cli = ComputeCLI(emulator_host=emulator_url, project='test-project')
        
        # Create instance
        success = cli.create_instance(
            name='test-cli-vm',
            zone='us-central1-a',
            machine_type='e2-micro',
            metadata={'test': 'value'}
        )
        assert success
        
        # List instances
        success = cli.list_instances(zone='us-central1-a')
        assert success
        
        # Describe instance
        success = cli.describe_instance(name='test-cli-vm', zone='us-central1-a')
        assert success
        
        # Stop instance
        success = cli.stop_instance(name='test-cli-vm', zone='us-central1-a')
        assert success
        
        # Start instance
        success = cli.start_instance(name='test-cli-vm', zone='us-central1-a')
        assert success
        
        # Delete instance
        success = cli.delete_instance(name='test-cli-vm', zone='us-central1-a')
        assert success
    
    @pytest.mark.integration
    def test_error_handling_404(self, emulator_url):
        """Test 404 error handling"""
        cli = ComputeCLI(emulator_host=emulator_url, project='test-project')
        
        # Try to describe non-existent instance
        with pytest.raises(SystemExit):
            cli.describe_instance(name='nonexistent-vm', zone='us-central1-a')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
