"""
Pytest configuration and fixtures
"""
import pytest
from unittest.mock import patch
from app.factory import create_app, db


@pytest.fixture
def app():
    """Create and configure a new app instance for each test"""
    app = create_app("testing")
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands"""
    return app.test_cli_runner()


@pytest.fixture
def sdk_client(app, client):
    """
    Provides a google.cloud.storage.Client that routes through Flask test client
    
    This fixture patches the SDK's HTTP transport layer to redirect all requests
    to the Flask test client, enabling full SDK integration tests without starting
    a server or making real network calls.
    
    Usage:
        def test_sdk_create_bucket(sdk_client):
            bucket = sdk_client.create_bucket('test-bucket')
            assert bucket.name == 'test-bucket'
    """
    from google.cloud import storage
    from google.auth.credentials import AnonymousCredentials
    from app.testing.sdk_transport import create_mock_session
    
    # Create mock session that routes to Flask test client
    mock_session = create_mock_session(client)
    
    # Patch AuthorizedSession at the module level where SDK imports it
    with patch('google.auth.transport.requests.AuthorizedSession', return_value=mock_session):
        # Create SDK client - it will use our mocked session
        gcs_client = storage.Client(
            project='test-project',
            credentials=AnonymousCredentials()
        )
        
        yield gcs_client
