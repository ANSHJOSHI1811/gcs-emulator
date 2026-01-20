#!/bin/bash
# Quick startup script for Flask backend

cd /mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package

# Set environment
export PYTHONPATH=/mnt/c/Users/ansh.joshi/gcp_emulator/gcp-emulator-package
export FLASK_ENV=development

# Start server
python3 run.py
