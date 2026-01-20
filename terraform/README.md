# Terraform Testing for GCS Emulator VPC

This directory contains Terraform configurations to test the GCS Emulator's VPC networking capabilities.

## Prerequisites

1. **Terraform installed** (version >= 1.0)
   ```bash
   # Check if installed
   terraform version
   
   # Install on Ubuntu
   wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
   echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
   sudo apt update && sudo apt install terraform
   ```

2. **GCS Emulator backend running** on http://localhost:8080

3. **terraform-test project** created in the emulator database

## Setup

1. **Set environment variables** to point Terraform at the emulator:

   ```bash
   # Point to fake credentials
   export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/fake-gcp-credentials.json"
   
   # Override GCP API endpoints to use emulator
   export CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE="http://localhost:8080/compute/v1/"
   
   # Disable SSL verification (local testing only)
   export CLOUDSDK_CORE_CUSTOM_CA_CERTS_FILE=""
   ```

2. **Initialize Terraform**:

   ```bash
   terraform init
   ```

## Usage

### Create Resources

```bash
# Preview changes
terraform plan

# Create all resources (network, subnet, firewall, VM)
terraform apply

# Auto-approve (skip confirmation)
terraform apply -auto-approve
```

### View Outputs

```bash
# Show all outputs
terraform output

# Specific output
terraform output vm_internal_ip
```

### Verify in Emulator

```bash
# Check network
curl http://localhost:8080/compute/v1/projects/terraform-test/global/networks/tf-test-network | jq

# Check subnet
curl http://localhost:8080/compute/v1/projects/terraform-test/regions/us-central1/subnetworks/tf-test-subnet | jq

# Check firewall rules
curl http://localhost:8080/compute/v1/projects/terraform-test/global/firewalls | jq

# Check VM instance
curl http://localhost:8080/compute/v1/projects/terraform-test/zones/us-central1-a/instances/tf-test-vm | jq
```

### Destroy Resources

```bash
# Destroy all resources
terraform destroy

# Auto-approve
terraform destroy -auto-approve
```

## What Gets Created

1. **VPC Network** (`tf-test-network`)
   - Custom mode (no auto-created subnets)
   - MTU: 1460
   - Regional routing

2. **Subnet** (`tf-test-subnet`)
   - CIDR: 10.10.0.0/24
   - Region: us-central1
   - Private Google Access enabled

3. **Firewall Rules**
   - `tf-allow-ssh`: Allow TCP:22 from anywhere
   - `tf-allow-web`: Allow TCP:80,443 from anywhere

4. **VM Instance** (`tf-test-vm`)
   - Machine type: e2-micro
   - Zone: us-central1-a
   - Internal IP: from subnet (10.10.0.x)
   - External IP: ephemeral (34.x.x.x)
   - Tags: ssh-enabled, web-server
   - Docker container running Debian 11

## Expected Outputs

```
network_name = "tf-test-network"
network_self_link = "http://127.0.0.1:8080/compute/v1/projects/terraform-test/global/networks/tf-test-network"
subnet_name = "tf-test-subnet"
subnet_cidr = "10.10.0.0/24"
vm_name = "tf-test-vm"
vm_internal_ip = "10.10.0.2"  # First IP in subnet (after gateway .1)
vm_external_ip = "34.123.45.67"  # Random external IP
vm_status = "RUNNING"
```

## Troubleshooting

### Error: Network not found
- Ensure backend is running: `curl http://localhost:8080/health`
- Check project exists: `curl http://localhost:8080/compute/v1/projects/terraform-test`

### Error: Authentication failed
- Verify environment variables are set: `echo $GOOGLE_APPLICATION_CREDENTIALS`
- Check fake credentials file exists: `ls -l fake-gcp-credentials.json`

### Error: API endpoint not found
- Verify CLOUDSDK_API_ENDPOINT_OVERRIDES_COMPUTE is set correctly
- Must include trailing slash: `http://localhost:8080/compute/v1/`

### View backend logs
```bash
tail -f /tmp/backend_vpc.log
```

## Testing Checklist

- [ ] `terraform init` succeeds
- [ ] `terraform plan` shows 6 resources to create
- [ ] `terraform apply` creates all resources
- [ ] VM gets internal IP from subnet (10.10.0.x)
- [ ] VM gets external IP (34.x.x.x)
- [ ] Docker container is created for VM
- [ ] Firewall rules are created
- [ ] `terraform destroy` removes all resources
- [ ] Database is clean after destroy

## Notes

- The emulator uses **instant operations** (status = DONE immediately)
- Real GCP would have PENDING/RUNNING states that Terraform polls
- External IPs are generated from fake 34.x.x.x range
- Docker containers use simple images (debian:11, ubuntu:22.04, etc.)
- This validates the **API compatibility** not actual networking functionality
