#!/bin/bash

# Test script to validate GCS Emulator VPC API compatibility
# This simulates what Terraform would do when creating infrastructure

set -e

BASE_URL="http://localhost:8080/compute/v1"
PROJECT="terraform-test"

echo "========================================="
echo "GCS Emulator VPC API Flow Test"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

function test_step() {
    echo -e "${BLUE}>>> $1${NC}"
}

function success() {
    echo -e "${GREEN}✓ $1${NC}"
    echo ""
}

function error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Step 1: Create Network
test_step "Step 1: Create VPC Network (tf-test-network)"
NETWORK_RESPONSE=$(curl -s -X POST \
    "$BASE_URL/projects/$PROJECT/global/networks" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "tf-test-network",
        "autoCreateSubnetworks": false,
        "routingConfig": {"routingMode": "REGIONAL"},
        "mtu": 1460,
        "description": "Test VPC created by test script"
    }')

echo "$NETWORK_RESPONSE" | jq '.'

if echo "$NETWORK_RESPONSE" | jq -e '.kind == "compute#operation"' > /dev/null; then
    success "Network creation returned operation"
    NETWORK_OPERATION=$(echo "$NETWORK_RESPONSE" | jq -r '.name')
    echo "Operation name: $NETWORK_OPERATION"
else
    error "Network creation did not return operation format"
fi

# Step 2: Verify Network exists
test_step "Step 2: Verify Network created"
sleep 1
NETWORK_GET=$(curl -s "$BASE_URL/projects/$PROJECT/global/networks/tf-test-network")
echo "$NETWORK_GET" | jq '.'

if echo "$NETWORK_GET" | jq -e '.name == "tf-test-network"' > /dev/null; then
    success "Network exists and is accessible"
    NETWORK_SELFLINK=$(echo "$NETWORK_GET" | jq -r '.selfLink')
    echo "Network selfLink: $NETWORK_SELFLINK"
else
    error "Network not found or invalid"
fi

# Step 3: Create Subnet
test_step "Step 3: Create Subnet (tf-test-subnet)"
SUBNET_RESPONSE=$(curl -s -X POST \
    "$BASE_URL/projects/$PROJECT/regions/us-central1/subnetworks" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "tf-test-subnet",
        "network": "'"$NETWORK_SELFLINK"'",
        "ipCidrRange": "10.10.0.0/24",
        "region": "us-central1",
        "privateIpGoogleAccess": true,
        "description": "Test subnet created by test script"
    }')

echo "$SUBNET_RESPONSE" | jq '.'

if echo "$SUBNET_RESPONSE" | jq -e '.kind == "compute#operation"' > /dev/null; then
    success "Subnet creation returned operation"
    SUBNET_OPERATION=$(echo "$SUBNET_RESPONSE" | jq -r '.name')
    echo "Operation name: $SUBNET_OPERATION"
elif echo "$SUBNET_RESPONSE" | jq -e '.name == "tf-test-subnet"' > /dev/null; then
    success "Subnet creation returned subnet object (needs operation conversion)"
    echo "Note: Handler should return operation, not subnet object"
else
    error "Subnet creation failed"
fi

# Step 4: Verify Subnet exists
test_step "Step 4: Verify Subnet created"
sleep 1
SUBNET_GET=$(curl -s "$BASE_URL/projects/$PROJECT/regions/us-central1/subnetworks/tf-test-subnet")
echo "$SUBNET_GET" | jq '.'

if echo "$SUBNET_GET" | jq -e '.name == "tf-test-subnet"' > /dev/null; then
    success "Subnet exists and is accessible"
    SUBNET_SELFLINK=$(echo "$SUBNET_GET" | jq -r '.selfLink')
    echo "Subnet selfLink: $SUBNET_SELFLINK"
    echo "Subnet CIDR: $(echo "$SUBNET_GET" | jq -r '.ipCidrRange')"
else
    error "Subnet not found or invalid"
fi

# Step 5: Create Firewall Rule (SSH)
test_step "Step 5: Create Firewall Rule (tf-allow-ssh)"
FIREWALL_RESPONSE=$(curl -s -X POST \
    "$BASE_URL/projects/$PROJECT/global/firewalls" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "tf-allow-ssh",
        "network": "'"$NETWORK_SELFLINK"'",
        "direction": "INGRESS",
        "priority": 1000,
        "sourceRanges": ["0.0.0.0/0"],
        "allowed": [
            {"IPProtocol": "tcp", "ports": ["22"]}
        ],
        "targetTags": ["ssh-enabled"],
        "description": "Allow SSH from anywhere"
    }')

echo "$FIREWALL_RESPONSE" | jq '.'

if echo "$FIREWALL_RESPONSE" | jq -e '.kind == "compute#operation"' > /dev/null; then
    success "Firewall creation returned operation"
elif echo "$FIREWALL_RESPONSE" | jq -e '.name == "tf-allow-ssh"' > /dev/null; then
    success "Firewall creation returned firewall object (needs operation conversion)"
    echo "Note: Handler should return operation, not firewall object"
else
    error "Firewall creation failed"
fi

# Step 6: Create Compute Instance
test_step "Step 6: Create Compute Instance (tf-test-vm)"
INSTANCE_RESPONSE=$(curl -s -X POST \
    "$BASE_URL/projects/$PROJECT/zones/us-central1-a/instances" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "tf-test-vm",
        "machineType": "zones/us-central1-a/machineTypes/e2-micro",
        "disks": [
            {
                "boot": true,
                "autoDelete": true,
                "initializeParams": {
                    "sourceImage": "debian-11",
                    "diskSizeGb": "10"
                }
            }
        ],
        "networkInterfaces": [
            {
                "network": "'"$NETWORK_SELFLINK"'",
                "subnetwork": "'"$SUBNET_SELFLINK"'",
                "accessConfigs": [
                    {
                        "name": "External NAT",
                        "type": "ONE_TO_ONE_NAT"
                    }
                ]
            }
        ],
        "tags": {
            "items": ["ssh-enabled", "web-server"]
        },
        "metadata": {
            "items": [
                {
                    "key": "startup-script",
                    "value": "#!/bin/bash\necho Hello from test VM"
                }
            ]
        }
    }')

echo "$INSTANCE_RESPONSE" | jq '.'

if echo "$INSTANCE_RESPONSE" | jq -e '.kind == "compute#operation"' > /dev/null; then
    success "Instance creation returned operation"
    INSTANCE_OPERATION=$(echo "$INSTANCE_RESPONSE" | jq -r '.name')
    echo "Operation name: $INSTANCE_OPERATION"
elif echo "$INSTANCE_RESPONSE" | jq -e '.name == "tf-test-vm"' > /dev/null; then
    success "Instance creation returned instance object (needs operation conversion)"
    echo "Note: Handler should return operation, not instance object"
else
    echo "Warning: Instance creation may have failed (check response above)"
fi

# Step 7: Verify Instance exists
test_step "Step 7: Verify Instance created"
sleep 2
INSTANCE_GET=$(curl -s "$BASE_URL/projects/$PROJECT/zones/us-central1-a/instances/tf-test-vm")
echo "$INSTANCE_GET" | jq '.'

if echo "$INSTANCE_GET" | jq -e '.name == "tf-test-vm"' > /dev/null; then
    success "Instance exists and is accessible"
    echo "Instance status: $(echo "$INSTANCE_GET" | jq -r '.status')"
    echo "Internal IP: $(echo "$INSTANCE_GET" | jq -r '.networkInterfaces[0].networkIP // "N/A"')"
    echo "External IP: $(echo "$INSTANCE_GET" | jq -r '.networkInterfaces[0].accessConfigs[0].natIP // "N/A"')"
else
    error "Instance not found or invalid"
fi

# Summary
echo ""
echo "========================================="
echo -e "${GREEN}✓ API Flow Test Complete${NC}"
echo "========================================="
echo ""
echo "Summary:"
echo "- Network: tf-test-network (Created)"
echo "- Subnet: tf-test-subnet (10.10.0.0/24)"
echo "- Firewall: tf-allow-ssh (TCP:22)"
echo "- Instance: tf-test-vm (e2-micro)"
echo ""
echo "Notes:"
echo "- Check which handlers need to return operations instead of objects"
echo "- Operations should have: kind, name, operationType, status, targetLink"
echo ""
