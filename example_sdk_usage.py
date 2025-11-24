"""
Quick Example: Using Official GCP SDK with Local Emulator

This is the simplest way to use your emulator with the real GCP SDK.
Just 3 lines of setup, then use SDK normally!
"""
import os
from google.cloud import storage
from google.auth.credentials import AnonymousCredentials

# ============ SETUP (3 lines) ============
os.environ['STORAGE_EMULATOR_HOST'] = 'http://localhost:8080'
client = storage.Client(project='my-project', credentials=AnonymousCredentials())
print("✅ Connected to local emulator at localhost:8080\n")

# ============ USE SDK NORMALLY ============

# Create a bucket
print("Creating bucket...")
bucket = client.create_bucket('my-first-bucket', location='US')
print(f"✅ Created bucket: {bucket.name}\n")

# Upload a file
print("Uploading file...")
blob = bucket.blob('hello.txt')
blob.upload_from_string('Hello from local emulator!')
print(f"✅ Uploaded: {blob.name}\n")

# List files
print("Listing files...")
for blob in bucket.list_blobs():
    print(f"  - {blob.name} ({blob.size} bytes)")

# Download file
print("\nDownloading file...")
content = bucket.blob('hello.txt').download_as_text()
print(f"✅ Content: {content}\n")

# Cleanup
print("Cleaning up...")
bucket.blob('hello.txt').delete()
bucket.delete()
print("✅ Deleted bucket and file\n")

print("="*50)
print("SUCCESS! Your emulator works with the official SDK")
print("="*50)
