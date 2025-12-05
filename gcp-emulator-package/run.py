"""
Simple run script for development server
"""
import os
from app.factory import create_app

if __name__ == "__main__":
    # Set environment
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '0'  # Disable auto-reload
    
    # Create app
    app = create_app('development')
    
    # Run server
    print("Starting GCS Emulator on http://127.0.0.1:8080")
    print("Press CTRL+C to stop")
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
