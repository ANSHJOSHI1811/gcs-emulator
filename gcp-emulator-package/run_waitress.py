"""
Production run script using Waitress WSGI server
"""
import os
from waitress import serve
from app.factory import create_app

if __name__ == "__main__":
    # Set environment
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '0'
    
    # Create app
    print("Creating GCP Emulator app...")
    app = create_app('development')
    
    # Run with Waitress (production WSGI server)
    print("=" * 60)
    print("Starting GCS Emulator on http://127.0.0.1:8080")
    print("Using Waitress WSGI Server")
    print("Press CTRL+C to stop")
    print("=" * 60)
    
    serve(app, host='0.0.0.0', port=8080, threads=4)
