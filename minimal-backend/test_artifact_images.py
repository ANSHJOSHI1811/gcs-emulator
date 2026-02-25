"""
Integration tests for Artifact Registry image management.
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8080"
PROJECT = "test-artifact-project"
LOCATION = "us-central1"
REPO_NAME = f"test-repo-{int(time.time())}"  # Use timestamp for unique repo name

# Base API prefix
API_PREFIX = "/v1"


def print_test(msg: str):
    print(f"\n{'='*60}")
    print(f"TEST: {msg}")
    print(f"{'='*60}")


def print_success(msg: str):
    print(f"✅ {msg}")


def print_error(msg: str):
    print(f"❌ {msg}")


def print_json(data):
    print(json.dumps(data, indent=2, default=str))


def test_artifact_registry_images():
    """Test Artifact Registry image management."""
    
    # Setup: Create repository
    print_test("Setup: Create repository")
    repo_url = f"{BASE_URL}{API_PREFIX}/projects/{PROJECT}/locations/{LOCATION}/repositories"
    
    r = requests.post(
        repo_url,
        json={
            "repositoryId": REPO_NAME,
            "format": "DOCKER",
            "description": "Test repository for images"
        }
    )
    
    if r.status_code != 200:
        print_error(f"Failed to create repository: {r.status_code} - {r.text}")
        return False
    
    print_success("Repository created")
    
    # Test 1: Push an image
    print_test("Push image")
    
    image_digest = "sha256:abcd1234ef5678"
    config = {
        "architecture": "amd64",
        "os": "linux",
        "config": {
            "Env": ["PATH=/usr/bin:/bin"],
            "Cmd": ["/bin/sh"],
        }
    }
    
    push_url = f"{BASE_URL}{API_PREFIX}/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}/docker/v2/images"
    r = requests.put(
        push_url,
        json={
            "imageDigest": image_digest,
            "config": config,
            "tags": ["latest", "v1.0", "stable"]
        }
    )
    
    if r.status_code != 200:
        print_error(f"Push failed: {r.status_code} - {r.text}")
        return False
    
    print_success("Image pushed")
    print_json(r.json())
    
    # Test 2: List images
    print_test("List images")
    
    list_url = f"{BASE_URL}{API_PREFIX}/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}/docker/v2/images"
    r = requests.get(list_url)
    
    if r.status_code != 200:
        print_error(f"List failed: {r.status_code} - {r.text}")
        return False
    
    data = r.json()
    print_success(f"Found {len(data.get('images', []))} images")
    print_json(data)
    
    # Test 3: Get image by digest
    print_test("Get image details")
    
    get_url = f"{BASE_URL}{API_PREFIX}/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}/docker/v2/images/{image_digest}"
    r = requests.get(get_url)
    
    if r.status_code != 200:
        print_error(f"Get failed: {r.status_code} - {r.text}")
        return False
    
    print_success("Image details retrieved")
    print_json(r.json())
    
    # Test 4: List tags
    print_test("List tags")
    
    tags_url = f"{BASE_URL}{API_PREFIX}/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}/docker/v2/tags"
    r = requests.get(tags_url)
    
    if r.status_code != 200:
        print_error(f"List tags failed: {r.status_code} - {r.text}")
        return False
    
    data = r.json()
    print_success(f"Found {len(data.get('tags', []))} tags")
    print_json(data)
    
    # Test 5: Create additional tag
    print_test("Create additional tag")
    
    create_tag_url = f"{BASE_URL}{API_PREFIX}/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}/docker/v2/tags"
    r = requests.post(
        create_tag_url,
        json={
            "tag": "canary",
            "imageDigest": image_digest
        }
    )
    
    if r.status_code != 200:
        print_error(f"Create tag failed: {r.status_code} - {r.text}")
        return False
    
    print_success("Tag 'canary' created")
    print_json(r.json())
    
    # Test 6: Pull image by tag
    print_test("Pull image by tag")
    
    pull_url = f"{BASE_URL}{API_PREFIX}/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}/docker/v2/:pull"
    r = requests.post(
        pull_url,
        json={"imageReference": "latest"}
    )
    
    if r.status_code != 200:
        print_error(f"Pull failed: {r.status_code} - {r.text}")
        return False
    
    print_success("Image pulled successfully")
    print_json(r.json())
    
    # Test 7: Pull image by digest
    print_test("Pull image by digest")
    
    r = requests.post(
        pull_url,
        json={"imageReference": image_digest}
    )
    
    if r.status_code != 200:
        print_error(f"Pull by digest failed: {r.status_code} - {r.text}")
        return False
    
    print_success("Image pulled by digest")
    
    # Test 8: Push another image with different digest
    print_test("Push second image")
    
    image_digest_2 = "sha256:xyz9876543210abc"
    r = requests.put(
        push_url,
        json={
            "imageDigest": image_digest_2,
            "config": config,
            "tags": ["v2.0"]
        }
    )
    
    if r.status_code != 200:
        print_error(f"Push second image failed: {r.status_code} - {r.text}")
        return False
    
    print_success("Second image pushed")
    
    # Test 9: List all images (should be 2)
    print_test("List all images (verify 2 images)")
    
    r = requests.get(list_url)
    if r.status_code != 200:
        print_error(f"List failed: {r.status_code}")
        return False
    
    data = r.json()
    if len(data.get('images', [])) != 2:
        print_error(f"Expected 2 images, got {len(data.get('images', []))}")
        return False
    
    print_success(f"Confirmed {len(data.get('images', []))} images in repository")
    
    # Test 10: Get stats
    print_test("Get image statistics")
    
    stats_url = f"{BASE_URL}{API_PREFIX}/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}/images:stats"
    r = requests.get(stats_url)
    
    if r.status_code != 200:
        print_error(f"Stats failed: {r.status_code} - {r.text}")
        return False
    
    data = r.json()
    print_success("Statistics retrieved")
    print_json(data)
    
    # Test 11: Delete tag
    print_test("Delete tag 'canary'")
    
    delete_tag_url = f"{BASE_URL}{API_PREFIX}/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}/docker/v2/tags/canary"
    r = requests.delete(delete_tag_url)
    
    if r.status_code != 200:
        print_error(f"Delete tag failed: {r.status_code} - {r.text}")
        return False
    
    print_success("Tag deleted")
    
    # Test 12: Delete image
    print_test("Delete second image")
    
    delete_url = f"{BASE_URL}{API_PREFIX}/projects/{PROJECT}/locations/{LOCATION}/repositories/{REPO_NAME}/docker/v2/images/{image_digest_2}"
    r = requests.delete(delete_url)
    
    if r.status_code != 200:
        print_error(f"Delete image failed: {r.status_code} - {r.text}")
        return False
    
    print_success("Image deleted")
    
    # Final verification: List images (should be 1)
    print_test("Final verification: List images")
    
    r = requests.get(list_url)
    data = r.json()
    
    if len(data.get('images', [])) != 1:
        print_error(f"Expected 1 image after deletion, got {len(data.get('images', []))}")
        return False
    
    print_success(f"Final count: {len(data.get('images', []))} image(s)")
    
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("ARTIFACT REGISTRY IMAGE MANAGEMENT TESTS")
    print("="*60)
    
    success = test_artifact_registry_images()
    
    print("\n" + "="*60)
    if success:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("="*60 + "\n")
