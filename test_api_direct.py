#!/usr/bin/env python3
"""
Test script for Cloud Run and Artifact Registry APIs
Uses the backend API directly
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8080"
PROJECT = "test-project"
LOCATION = "us-central1"
REPO_NAME = "test-docker-repo"
SERVICE_NAME = "test-cloud-run-service"
IMAGE = "gcr.io/cloud-builders/docker"

# Colors
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
RED = '\033[0;31m'
NC = '\033[0m'

def print_header(text: str):
    print(f"\n{BLUE}{'='*50}{NC}")
    print(f"{BLUE}{text}{NC}")
    print(f"{BLUE}{'='*50}{NC}\n")

def print_test(text: str):
    print(f"{BLUE}▶ {text}{NC}")

def print_success(text: str):
    print(f"{GREEN}✓ {text}{NC}")

def print_error(text: str):
    print(f"{RED}✗ {text}{NC}")

def print_json(data: Any):
    print(json.dumps(data, indent=2))

def test_artifact_registry():
    """Test Artifact Registry endpoints"""
    print_header("ARTIFACT REGISTRY TESTS")
    
    # Test 1: Create Repository
    print_test(f"Creating Artifact Repository: {REPO_NAME}")
    url = f"{BASE_URL}/v1/projects/{PROJECT}/locations/{LOCATION}/repositories"
    payload = {
        "repositoryId": REPO_NAME,
        "format": "DOCKER",
        "description": "Test Docker repository for Cloud Run"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code in [200, 201]:
            print_success("Repository created successfully")
            print_json(response.json())
        else:
            print(f"Status: {response.status_code}")
            if response.text:
                print_json(response.json())
    except Exception as e:
        print_error(f"Error: {e}")
    print()
    
    # Test 2: List Repositories
    print_test("Listing Artifact Repositories")
    url = f"{BASE_URL}/v1/projects/{PROJECT}/locations/{LOCATION}/repositories"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Found {len(data.get('repositories', []))} repositories")
            for repo in data.get('repositories', []):
                print(f"  - {repo.get('repositoryId', repo.get('name'))}")
            print_json(data)
        else:
            print(f"Status: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")
    print()
    
    # Test 3: Describe Repository
    print_test(f"Describing repository: {REPO_NAME}")
    url = f"{BASE_URL}/v1/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print_success("Repository details retrieved")
            print_json(response.json())
        else:
            print(f"Status: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")
    print()

def test_cloud_run():
    """Test Cloud Run endpoints"""
    print_header("CLOUD RUN TESTS")
    
    # Test 1: Deploy Service
    print_test(f"Deploying Cloud Run Service: {SERVICE_NAME}")
    url = f"{BASE_URL}/v2/projects/{PROJECT}/locations/{LOCATION}/services?serviceId={SERVICE_NAME}"
    payload = {
        "template": {
            "containers": [{
                "image": IMAGE,
                "ports": [{
                    "containerPort": 8080
                }],
                "env": [
                    {"name": "ENV_VAR", "value": "test_value"}
                ]
            }]
        },
        "ingress": "INGRESS_TRAFFIC_ALL"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code in [200, 201]:
            print_success("Service deployed successfully")
            print_json(response.json())
        else:
            print(f"Status: {response.status_code}")
            if response.text:
                try:
                    print_json(response.json())
                except:
                    print(response.text)
    except Exception as e:
        print_error(f"Error: {e}")
    print()
    
    time.sleep(1)  # Brief pause
    
    # Test 2: List Services
    print_test("Listing Cloud Run Services")
    url = f"{BASE_URL}/v2/projects/{PROJECT}/locations/{LOCATION}/services"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            services = data.get('services', [])
            print_success(f"Found {len(services)} services")
            for service in services:
                print(f"  - {service.get('serviceId', service.get('name'))}")
            print_json(data)
        else:
            print(f"Status: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")
    print()
    
    # Test 3: Describe Service
    print_test(f"Describing Cloud Run Service: {SERVICE_NAME}")
    url = f"{BASE_URL}/v2/projects/{PROJECT}/locations/{LOCATION}/services/{SERVICE_NAME}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print_success("Service details retrieved")
            print_json(response.json())
        else:
            print(f"Status: {response.status_code} - {response.text}")
    except Exception as e:
        print_error(f"Error: {e}")
    print()
    
    # Test 4: Get Service URL
    print_test("Retrieving Cloud Run Service URL")
    url = f"{BASE_URL}/v2/projects/{PROJECT}/locations/{LOCATION}/services/{SERVICE_NAME}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            service_url = data.get('uri', data.get('simulatedUrl', 'N/A'))
            print_success(f"Service URL: {service_url}")
        else:
            print(f"Status: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    print()
    
    # Test 5: Update Service (add environment variable)
    print_test("Updating Cloud Run Service")
    url = f"{BASE_URL}/v2/projects/{PROJECT}/locations/{LOCATION}/services/{SERVICE_NAME}"
    payload = {
        "template": {
            "containers": [{
                "image": IMAGE,
                "env": [
                    {"name": "ENV_VAR", "value": "updated_value"},
                    {"name": "NEW_VAR", "value": "new_value"}
                ]
            }]
        }
    }
    try:
        response = requests.patch(url, json=payload)
        if response.status_code in [200, 201]:
            print_success("Service updated successfully")
            print_json(response.json())
        else:
            print(f"Status: {response.status_code}")
            if response.text:
                try:
                    print_json(response.json())
                except:
                    print(response.text)
    except Exception as e:
        print_error(f"Error: {e}")
    print()

def test_integration():
    """Test integration between Artifact Registry and Cloud Run"""
    print_header("INTEGRATION TEST")
    
    print_test("Checking Artifact Registry configuration")
    url = f"{BASE_URL}/v1/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            docker_prefix = data.get('dockerRepositoryPrefix', 'N/A')
            registry_host = data.get('registryHost', 'N/A')
            print_success("Registry configuration retrieved")
            print(f"  Registry Host: {registry_host}")
            print(f"  Docker Prefix: {docker_prefix}")
            print()
            
            print("Docker Commands for CI/CD Pipeline:")
            print("=====================================")
            print(f"1. Build image:")
            print(f"   docker build -t {docker_prefix}/my-app:v1.0.0 .")
            print()
            print(f"2. Push to Artifact Registry:")
            print(f"   docker push {docker_prefix}/my-app:v1.0.0")
            print()
            print(f"3. Deploy to Cloud Run:")
            print(f"   gcloud run deploy my-app \\")
            print(f"     --image={docker_prefix}/my-app:v1.0.0 \\")
            print(f"     --region={LOCATION}")
            print()
            print_success("Integration workflow demonstrated")
        else:
            print(f"Status: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")

def main():
    print(f"\n{GREEN}{'='*50}{NC}")
    print(f"{GREEN}GCP Stimulator - Cloud Run & Artifact Registry Tests{NC}")
    print(f"{GREEN}{'='*50}{NC}")
    print(f"\nBase URL: {BASE_URL}")
    print(f"Project: {PROJECT}")
    print(f"Location: {LOCATION}")
    
    # Run tests
    test_artifact_registry()
    test_cloud_run()
    test_integration()
    
    # Summary
    print_header("TEST SUMMARY")
    print(f"✓ Artifact Registry Tests: COMPLETED")
    print(f"✓ Cloud Run Tests: COMPLETED")
    print(f"✓ Integration Tests: COMPLETED")
    print()
    print(f"Resources Created:")
    print(f"  - Artifact Repository: {REPO_NAME}")
    print(f"  - Cloud Run Service: {SERVICE_NAME}")
    print()

if __name__ == "__main__":
    main()
