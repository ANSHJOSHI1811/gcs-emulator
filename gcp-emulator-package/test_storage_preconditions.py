"""
Storage Preconditions Verification Harness

Validates GCS-style preconditions against the emulator:
- If-Generation-Match and If-Generation-Not-Match on upload
- If-Metageneration-Match on metadata update

Run: python test_storage_preconditions.py
"""
import json
import sys
import time
from typing import Tuple

import requests


BASE_URL = "http://127.0.0.1:8080"
PROJECT = "test-project"


def create_bucket(bucket: str) -> None:
    url = f"{BASE_URL}/storage/v1/b"
    params = {"project": PROJECT}
    body = {
        "name": bucket,
        "location": "US",
        "storageClass": "STANDARD",
        "versioning": {"enabled": True},
    }
    r = requests.post(url, params=params, json=body)
    if r.status_code == 201:
        print(f"✅ Created bucket: {bucket}")
    elif r.status_code == 409:
        print(f"ℹ️ Bucket already exists: {bucket}")
    else:
        raise RuntimeError(f"Bucket create failed: {r.status_code} {r.text}")


def upload_object(bucket: str, name: str, content: bytes, headers: dict = None, params: dict = None) -> Tuple[int, dict]:
    # Use media upload endpoint for clarity
    url = f"{BASE_URL}/upload/storage/v1/b/{bucket}/o"
    q = {"name": name, "uploadType": "media"}
    if params:
        q.update(params)
    h = {"Content-Type": "text/plain"}
    if headers:
        h.update(headers)
    r = requests.post(url, params=q, data=content, headers=h)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    return r.status_code, data


def get_object_meta(bucket: str, name: str) -> dict:
    url = f"{BASE_URL}/storage/v1/b/{bucket}/o/{name}"
    r = requests.get(url)
    if r.status_code != 200:
        raise RuntimeError(f"Get metadata failed: {r.status_code} {r.text}")
    meta = r.json()
    # Normalize numeric fields
    meta["generation"] = int(meta.get("generation", 0))
    meta["metageneration"] = int(meta.get("metageneration", 0))
    return meta


def patch_object_metadata(bucket: str, name: str, metadata: dict, if_meta_match: int) -> Tuple[int, dict]:
    url = f"{BASE_URL}/storage/v1/b/{bucket}/o/{name}"
    headers = {"Content-Type": "application/json"}
    params = {"ifMetagenerationMatch": str(if_meta_match)}
    r = requests.patch(url, params=params, data=json.dumps({"metadata": metadata}), headers=headers)
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}
    return r.status_code, data


def main():
    bucket = "precond-bucket"
    name = "test.txt"

    # Ensure backend reachable
    try:
        requests.get(f"{BASE_URL}/storage/v1")
    except Exception as e:
        print(f"❌ Backend not reachable at {BASE_URL}: {e}")
        sys.exit(1)

    create_bucket(bucket)

    # 1) Initial upload
    status, data = upload_object(bucket, name, b"v1")
    assert status in (200, 201), f"Upload failed: {status} {data}"
    meta = get_object_meta(bucket, name)
    gen1 = meta["generation"]
    meta1 = meta["metageneration"]
    print(f"✅ Uploaded gen={gen1}, metageneration={meta1}")

    # 2) Upload with mismatched If-Generation-Match → expect 412
    meta = get_object_meta(bucket, name)
    current_gen = meta["generation"]
    bad_match = current_gen + 1
    status, data = upload_object(
        bucket,
        name,
        b"v2-bad",
        headers={"If-Generation-Match": str(bad_match)},
    )
    assert status == 412, f"Expected 412 with header, got {status}: {data} (current_gen={current_gen})"
    print("✅ 412 on mismatched If-Generation-Match (header)")

    # 3) Upload with matching If-Generation-Match → expect success, generation increments
    # Refresh current generation and then use matching precondition
    meta = get_object_meta(bucket, name)
    current_gen = meta["generation"]
    status, data = upload_object(
        bucket,
        name,
        b"v2-good",
        headers={"If-Generation-Match": str(current_gen)},
    )
    assert status in (200, 201), f"Conditional upload failed: {status} {data}"
    meta = get_object_meta(bucket, name)
    gen2 = meta["generation"]
    assert gen2 == gen1 + 1, f"Generation did not increment: {gen2} vs {gen1+1}"
    print(f"✅ Conditional upload succeeded, new gen={gen2}")

    # 4) Metadata update with mismatched If-Metageneration-Match → expect 412
    bad_meta = meta["metageneration"] + 1
    status, data = patch_object_metadata(
        bucket,
        name,
        {"owner": "alice"},
        if_meta_match=bad_meta,
    )
    assert status == 412, f"Expected 412 on bad metageneration, got {status}: {data}"
    print("✅ 412 on mismatched If-Metageneration-Match")

    # 5) Metadata update with matching If-Metageneration-Match → expect success, metageneration increments
    status, data = patch_object_metadata(
        bucket,
        name,
        {"owner": "alice"},
        if_meta_match=meta["metageneration"],
    )
    assert status == 200, f"Metadata update failed: {status} {data}"
    meta2 = get_object_meta(bucket, name)
    assert meta2["metageneration"] == meta["metageneration"] + 1, "Metageneration did not increment"
    print(f"✅ Metadata update succeeded, new metageneration={meta2['metageneration']}")

    print("\n🎉 Preconditions verified successfully.")


if __name__ == "__main__":
    main()
