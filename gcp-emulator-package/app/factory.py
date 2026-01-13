"""
Flask app factory and configuration
"""
import os
import logging
from flask import Flask
from dotenv import load_dotenv
from app.logging.middleware import setup_request_logging
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Initialize SQLAlchemy (moved to avoid circular import)
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config_name: str = None) -> Flask:
    """
    Create and configure Flask application
    
    Args:
        config_name: Configuration environment (development, testing, production)
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    
    from app.config import config
    app.config.from_object(config.get(config_name, config["development"]))
    
    # Enable CORS
    CORS(app)
    
    # Initialize database
    db.init_app(app)
    
    # Set up logging
    setup_logging(app)
    
    # Setup request logging middleware
    setup_request_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    # Create application context and initialize database
    with app.app_context():
        db.create_all()
    
    # Start lifecycle executor background service
    lifecycle_interval = int(os.getenv("LIFECYCLE_INTERVAL_MINUTES", "5"))
    from app.services.lifecycle_executor import start_lifecycle_executor
    start_lifecycle_executor(app, interval_minutes=lifecycle_interval)
    
    return app


def setup_logging(app: Flask) -> None:
    """Configure logging"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(getattr(logging, log_level))


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints"""
    from app.routes.bucket_routes import buckets_bp
    from app.handlers.objects import objects_bp
    from app.handlers.health import health_bp
    from app.handlers.upload import upload_bp, resumable_bp
    from app.handlers.download import download_bp
    from app.handlers.signed_url_handler import signed_bp
    from app.handlers.acl_handler import acl_bp
    from app.handlers.lifecycle_handler import lifecycle_bp
    from app.handlers.events_handler import events_bp
    from app.handlers.dashboard_handler import dashboard_bp
    from app.handlers.cors_handler import cors_bp
    from app.handlers.notification_handler import notifications_bp
    from app.handlers.lifecycle_config_handler import lifecycle_config_bp
    from app.handlers.auth_handler import auth_bp
    from app.handlers.iam_handler import iam_bp
    from app.handlers.compute_handler import compute_bp
    from app.routes.network_routes import network_bp
    from app.routes.subnet_routes import subnet_bp
    from app.routes.firewall_routes import firewall_bp
    from app.routes.route_routes import route_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(buckets_bp, url_prefix="/storage/v1/b")
    app.register_blueprint(objects_bp, url_prefix="/storage/v1/b")
    app.register_blueprint(upload_bp, url_prefix="/upload")
    app.register_blueprint(resumable_bp)  # Has its own URL prefix
    app.register_blueprint(download_bp, url_prefix="/download")
    app.register_blueprint(signed_bp)  # Signed URL handler
    app.register_blueprint(acl_bp)  # Phase 4: ACL endpoints
    app.register_blueprint(lifecycle_bp)  # Phase 4: Lifecycle rules (legacy)
    app.register_blueprint(events_bp)  # Phase 4: Object events
    app.register_blueprint(dashboard_bp)  # Dashboard stats aggregation
    app.register_blueprint(cors_bp, url_prefix="/storage/v1")  # CORS configuration
    app.register_blueprint(notifications_bp, url_prefix="/storage/v1")  # Notification webhooks
    app.register_blueprint(lifecycle_config_bp, url_prefix="/storage/v1")  # Lifecycle configuration
    
    # New: IAM and Compute Engine
    app.register_blueprint(auth_bp)  # OAuth2 mock endpoints
    app.register_blueprint(iam_bp)  # IAM service accounts and policies
    app.register_blueprint(compute_bp)  # Compute Engine instances
    
    # VPC Networking
    app.register_blueprint(network_bp)  # VPC networks
    app.register_blueprint(subnet_bp)  # VPC subnetworks
    app.register_blueprint(firewall_bp)  # VPC firewall rules
    app.register_blueprint(route_bp)  # VPC routes
    
    # Register SDK compatibility middleware
    register_sdk_middleware(app)


def register_sdk_middleware(app: Flask) -> None:
    """Register SDK compatibility middleware"""
    from flask import request, jsonify
    
    @app.before_request
    def handle_sdk_auth():
        """Handle SDK authentication headers in mock mode"""
        if app.config.get('MOCK_AUTH_ENABLED', True):
            # Log SDK authentication attempts (for debugging)
            auth_header = request.headers.get('Authorization')
            if auth_header:
                app.logger.debug(f"SDK Auth header detected: {auth_header[:20]}...")
            
            # Accept any authorization (emulator mode)
            # In real GCS, this would validate OAuth2 tokens
            pass
    
    @app.route('/storage/v1')
    def sdk_info():
        """SDK discovery endpoint - helps verify emulator is running"""
        return jsonify({
            "kind": "storage#serviceAccount",
            "emulator": True,
            "version": "v1",
            "endpoints": {
                "buckets": "/storage/v1/b",
                "objects": "/storage/v1/b/{bucket}/o"
            },
            "features": {
                "mockAuth": app.config.get('MOCK_AUTH_ENABLED', True),
                "sdkCompatible": app.config.get('SDK_COMPATIBLE_MODE', True)
            }
        }), 200


def register_error_handlers(app: Flask) -> None:
    """Register error handlers"""
    from app.handlers.errors import handle_not_found, handle_bad_request, handle_internal_error
    
    app.register_error_handler(404, handle_not_found)
    app.register_error_handler(400, handle_bad_request)
    app.register_error_handler(500, handle_internal_error)


def register_cli_commands(app: Flask) -> None:
    """Register Flask CLI commands"""
    from app.cli import cli
    cli(app)
