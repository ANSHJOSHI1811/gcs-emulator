# VPC Week 3 Plan - Advanced Networking Features

## Overview
Week 3 focuses on implementing compute instance integration with VPC networking and advanced network management features.

## Completed (Week 1-2)
- ✅ Week 1: Networks, Database Models, Validators, IP Utilities
- ✅ Week 2 Day 1-2: Subnets (create, list, get, delete, expand, patch)
- ✅ Week 2 Day 3: Firewall Rules (CRUD with allowed/denied rules)
- ✅ Week 2 Day 4: Routes (CRUD with multiple next hop types)

## Week 3 Scope

### **Day 1: Network Interfaces & Instance Integration**
**Goal:** Connect compute instances to VPC networks with proper IP allocation

**Tasks:**
1. Create `NetworkInterface` model (already in vpc.py but not active)
2. Create network_interface_handler.py with:
   - Attach network interface to instance
   - Detach network interface from instance
   - List instance network interfaces
   - Update network interface properties
3. Update compute_handler.py to:
   - Accept `networkInterfaces` in instance creation
   - Allocate IPs from subnet CIDR ranges
   - Support custom network/subnet selection
   - Handle instances without explicit network (use default)
4. IP allocation service:
   - Track used IPs per subnet
   - Allocate next available IP from CIDR
   - Handle IP conflicts
   - Release IPs on instance deletion
5. Test instance creation with:
   - Default network (auto-assigned)
   - Custom network + subnet
   - Multiple regions
   - IP allocation from CIDR pools

**Endpoints:**
```
POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/addNetworkInterface
POST /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/removeNetworkInterface
GET  /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/networkInterfaces
```

**Deliverables:**
- network_interface_handler.py (200+ lines)
- IP allocation service update (100+ lines)
- Updated compute_handler.py (50+ lines)
- Migration 013: Add network_interfaces table
- Tests for IP allocation and instance-network integration

---

### **Day 2: External IPs & Access Configs**
**Goal:** Support external IP addresses for instances

**Tasks:**
1. Create `AccessConfig` model (part of NetworkInterface)
   - Type: ONE_TO_ONE_NAT
   - Name: "External NAT"
   - natIP: external IP address
   - networkTier: PREMIUM/STANDARD
2. Create external_ip_handler.py:
   - Allocate static external IP
   - Release external IP
   - List external IPs
   - Attach external IP to instance
   - Detach external IP from instance
3. Update instance creation to support:
   - `accessConfigs` in networkInterfaces
   - Ephemeral external IPs (auto-assigned)
   - Static external IPs (user-provided)
4. External IP pool management:
   - Generate fake public IPs (e.g., 34.x.x.x range)
   - Track allocated vs available
   - Support regional vs global IPs
5. Test scenarios:
   - Instance with no external IP
   - Instance with ephemeral external IP
   - Instance with static external IP
   - Static IP address reservation

**Endpoints:**
```
POST   /compute/v1/projects/{project}/regions/{region}/addresses
GET    /compute/v1/projects/{project}/regions/{region}/addresses
GET    /compute/v1/projects/{project}/regions/{region}/addresses/{address}
DELETE /compute/v1/projects/{project}/regions/{region}/addresses/{address}
POST   /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/addAccessConfig
POST   /compute/v1/projects/{project}/zones/{zone}/instances/{instance}/deleteAccessConfig
```

**Deliverables:**
- external_ip_handler.py (300+ lines)
- AccessConfig model updates
- External IP pool service
- Migration 014: Add addresses table
- Tests for external IP allocation and attachment

---

### **Day 3-4: Cloud Router & NAT Gateway (Simplified)**
**Goal:** Implement basic Cloud Router and Cloud NAT for emulator (metadata only)

**Tasks:**

#### Day 3: Cloud Router
1. Create `Router` model:
   - name, network_id, region
   - bgp settings (ASN, keepalive interval)
   - interfaces (for future VPN/interconnect)
2. Create router_handler.py:
   - Create router
   - List routers (by region)
   - Get router details
   - Update router (BGP settings)
   - Delete router
3. Router validation:
   - Must belong to a network
   - Must be in valid region
   - Unique name per region
4. Test router CRUD operations

**Endpoints:**
```
POST   /compute/v1/projects/{project}/regions/{region}/routers
GET    /compute/v1/projects/{project}/regions/{region}/routers
GET    /compute/v1/projects/{project}/regions/{region}/routers/{router}
PATCH  /compute/v1/projects/{project}/regions/{region}/routers/{router}
DELETE /compute/v1/projects/{project}/regions/{region}/routers/{router}
```

#### Day 4: Cloud NAT
1. Create `CloudNAT` model:
   - name, router_id
   - natIpAllocateOption (AUTO_ONLY, MANUAL_ONLY)
   - sourceSubnetworkIpRangesToNat (ALL_SUBNETWORKS, LIST_OF_SUBNETWORKS)
   - natIps (list of external IP addresses)
   - minPortsPerVm, maxPortsPerVm
2. Create nat_handler.py:
   - Create NAT configuration on router
   - List NAT configs for router
   - Get NAT config details
   - Update NAT config
   - Delete NAT config
3. NAT configuration validation:
   - Must attach to existing router
   - Validate IP allocation options
   - Validate port ranges
4. Test NAT CRUD operations

**Endpoints:**
```
POST   /compute/v1/projects/{project}/regions/{region}/routers/{router}/nats
GET    /compute/v1/projects/{project}/regions/{region}/routers/{router}/nats
GET    /compute/v1/projects/{project}/regions/{region}/routers/{router}/nats/{nat}
PATCH  /compute/v1/projects/{project}/regions/{region}/routers/{router}/nats/{nat}
DELETE /compute/v1/projects/{project}/regions/{region}/routers/{router}/nats/{nat}
```

**Note:** Cloud Router and NAT are metadata-only in the emulator. No actual packet routing or NAT translation occurs.

**Deliverables:**
- router_handler.py (250+ lines)
- nat_handler.py (250+ lines)
- Router and CloudNAT models
- Migration 015: Add routers table
- Migration 016: Add cloud_nat table
- Tests for router and NAT CRUD

---

## Week 3 Success Criteria

### Day 1 ✅ Checklist
- [ ] NetworkInterface model operational
- [ ] IP allocation from subnet CIDR works
- [ ] Instances can specify custom network/subnet
- [ ] Default network attachment works
- [ ] IP addresses tracked per subnet
- [ ] Tests pass for instance-network integration

### Day 2 ✅ Checklist
- [ ] AccessConfig model implemented
- [ ] External IP pool management works
- [ ] Static IP reservation functional
- [ ] Ephemeral IP auto-assignment works
- [ ] External IPs can attach/detach from instances
- [ ] Tests pass for external IP operations

### Day 3-4 ✅ Checklist
- [ ] Cloud Router CRUD complete
- [ ] Cloud NAT CRUD complete
- [ ] Routers belong to networks
- [ ] NAT configs attach to routers
- [ ] BGP settings configurable
- [ ] Tests pass for router and NAT

---

## Architecture Notes

### IP Allocation Strategy
```
Subnet CIDR: 10.128.0.0/20 (4096 IPs)
- 10.128.0.0: Network address (reserved)
- 10.128.0.1: Gateway (reserved)
- 10.128.0.2 - 10.128.15.253: Allocatable (4094 IPs)
- 10.128.15.254: Broadcast (reserved)
```

**Allocation:**
- Track `next_ip_index` per subnet (starts at 2)
- Increment on each allocation
- Simple, sequential, no fragmentation in Phase 1

### External IP Pool
```
Range: 34.0.0.0 - 34.255.255.255 (fake GCP range)
- Generate random IPs from this range
- Track allocated vs available
- Support regional (cheaper) and global (more expensive) tiers
```

### Network Tier
- **PREMIUM**: Global anycast, higher cost
- **STANDARD**: Regional, lower cost
- Affects external IP and access config

---

## Database Schema Updates

### Migration 013: network_interfaces
```sql
CREATE TABLE network_interfaces (
    id UUID PRIMARY KEY,
    instance_id UUID REFERENCES instances(id) ON DELETE CASCADE,
    network_id UUID REFERENCES networks(id) ON DELETE CASCADE,
    subnetwork_id UUID REFERENCES subnetworks(id) ON DELETE SET NULL,
    name VARCHAR(63) NOT NULL,
    ip_address VARCHAR(50) NOT NULL,
    network_tier VARCHAR(20) DEFAULT 'PREMIUM',
    nic_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Migration 014: addresses (External IPs)
```sql
CREATE TABLE addresses (
    id UUID PRIMARY KEY,
    name VARCHAR(63) NOT NULL,
    project_id VARCHAR(255) NOT NULL,
    region VARCHAR(50) NOT NULL,
    address VARCHAR(50) NOT NULL,
    address_type VARCHAR(20) DEFAULT 'EXTERNAL', -- INTERNAL or EXTERNAL
    status VARCHAR(20) DEFAULT 'RESERVED', -- RESERVED, IN_USE
    network_tier VARCHAR(20) DEFAULT 'PREMIUM',
    purpose VARCHAR(50), -- GCE_ENDPOINT, NAT_AUTO, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, region, name)
);
```

### Migration 015: routers
```sql
CREATE TABLE routers (
    id UUID PRIMARY KEY,
    name VARCHAR(63) NOT NULL,
    network_id UUID REFERENCES networks(id) ON DELETE CASCADE,
    region VARCHAR(50) NOT NULL,
    description TEXT,
    bgp_asn INTEGER,
    bgp_keepalive_interval INTEGER DEFAULT 20,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(network_id, region, name)
);
```

### Migration 016: cloud_nat
```sql
CREATE TABLE cloud_nat (
    id UUID PRIMARY KEY,
    name VARCHAR(63) NOT NULL,
    router_id UUID REFERENCES routers(id) ON DELETE CASCADE,
    nat_ip_allocate_option VARCHAR(50) DEFAULT 'AUTO_ONLY',
    source_subnet_ip_ranges_to_nat VARCHAR(50) DEFAULT 'ALL_SUBNETWORKS',
    nat_ips TEXT[], -- Array of external IP addresses
    min_ports_per_vm INTEGER DEFAULT 64,
    max_ports_per_vm INTEGER DEFAULT 65536,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(router_id, name)
);
```

---

## Testing Strategy

### Unit Tests
- IP allocation logic (allocate, deallocate, conflict detection)
- External IP pool management
- Model validations (network tier, address types)

### Integration Tests
- Instance creation with custom network
- Instance with external IP
- External IP reservation and attachment
- Router and NAT CRUD workflows

### E2E Tests
```bash
# Create network
curl -X POST .../networks -d '{"name":"vpc-test","autoCreateSubnetworks":false}'

# Create subnet
curl -X POST .../subnetworks -d '{"name":"subnet-test","ipCidrRange":"10.0.0.0/24"}'

# Reserve external IP
curl -X POST .../addresses -d '{"name":"static-ip-1","networkTier":"PREMIUM"}'

# Create instance with custom network + external IP
curl -X POST .../instances -d '{
  "name": "vm-test",
  "machineType": "e2-medium",
  "networkInterfaces": [{
    "network": "vpc-test",
    "subnetwork": "subnet-test",
    "accessConfigs": [{"type":"ONE_TO_ONE_NAT","natIP":"static-ip-1"}]
  }]
}'

# Verify IP allocation
curl .../instances/vm-test | jq '.networkInterfaces[0]'
```

---

## Estimated Effort

| Day | Task | Lines of Code | Complexity |
|-----|------|---------------|------------|
| 1 | Network Interfaces & IP Allocation | ~350 | Medium |
| 2 | External IPs & Access Configs | ~400 | Medium |
| 3 | Cloud Router | ~300 | Low |
| 4 | Cloud NAT | ~300 | Low |
| **Total** | **Week 3** | **~1,350** | **Medium** |

---

## Success Metrics
- All 4 days completed
- All migrations applied successfully
- All tests passing
- All endpoints tested with curl
- Instance-network integration working
- External IP allocation functional
- Router and NAT CRUD operational

---

## Next Steps (Week 4+)
- VPC Peering
- VPN Tunnels
- Cloud Interconnect
- Private Google Access
- Shared VPC
- Firewall Rules enforcement (if implementing packet filtering)
- Load Balancers (HTTP/S, TCP/UDP, Internal)

---

**Ready to start Week 3 Day 1!** 🚀
