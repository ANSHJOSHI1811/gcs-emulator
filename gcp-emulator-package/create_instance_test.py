import requests
import json

# Create instance
url = 'http://127.0.0.1:8080/compute/v1/projects/test-project/zones/us-central1-a/instances'
payload = {
    'name': 'test-instance-1',
    'machineType': 'e2-medium',
    'metadata': {
        'items': [
            {'key': 'startup-script', 'value': 'echo "Hello from compute instance!"'}
        ]
    },
    'labels': {
        'environment': 'test',
        'created-by': 'api-test'
    }
}

print("Creating instance...")
response = requests.post(url, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")
