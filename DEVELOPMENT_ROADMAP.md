# GCP Simulator - Development Roadmap
**Last Updated:** February 11, 2026  
**Current Status:** ~75% Production Ready

---

## Quick Status Overview

### ✅ Fully Implemented (100%)
- ✅ Compute Engine (Zones, Machine Types, Instances, Start/Stop)
- ✅ Cloud Storage (Buckets, Objects, Versioning, Signed URLs, Download)
- ✅ VPC Networks (Networks, Subnets, Routes, VPC Peering)
- ✅ Projects Management
- ✅ UI Navigation & Pages
- ✅ Docker Integration

### ⚠️ Partially Implemented (0-80%)
- ⚠️ Firewall Rules (API exists, no rules created) - 0%
- ⚠️ Service Accounts (API exists, not populated) - 0%
- ⚠️ Load Balancers (not started) - 0%
- ⚠️ Monitoring & Logging (not started) - 0%
- ⚠️ Instance Groups (UI exists, no backend) - 20%
- ⚠️ Disks Management (UI link only) - 10%

---

## Phase 1: Critical Gaps (HIGH PRIORITY) 🔴
**Goal:** Achieve 85% production readiness  
**Timeline:** 1-2 days  
**Impact:** Essential for realistic GCP simulation

### 1.1 Implement Default Firewall Rules
**Priority:** 🔴 CRITICAL  
**Effort:** 4 hours  
**Files to modify:**
- `minimal-backend/api/firewall.py` - Add initialization function
- `minimal-backend/main.py` - Call firewall init on startup

**Tasks:**
```python
# Create these default rules on project creation:
1. allow-ssh (tcp:22, source: 0.0.0.0/0)
2. allow-http (tcp:80, source: 0.0.0.0/0)
3. allow-https (tcp:443, source: 0.0.0.0/0)
4. allow-internal (all protocols, source: 10.0.0.0/8)
5. allow-icmp (icmp, source: 0.0.0.0/0)
```

**Testing:**
- `GET /compute/v1/projects/project-alpha/global/firewalls` should return rules
- UI FirewallsPage should display rules
- Create/Delete operations should work

---

### 1.2 Create Default Service Accounts
**Priority:** 🔴 CRITICAL  
**Effort:** 3 hours  
**Files to modify:**
- `minimal-backend/api/iam.py` - Add initialization function
- `minimal-backend/main.py` - Call service account init on startup

**Tasks:**
```python
# Create these default service accounts:
1. {project-number}-compute@developer.gserviceaccount.com
2. {project-id}@appspot.gserviceaccount.com
3. service-{project-number}@storage-transfer-service.iam.gserviceaccount.com
```

**Testing:**
- `GET /v1/projects/project-alpha/serviceAccounts` should return accounts
- UI IAMDashboardPage should display accounts
- Service account creation should work

---

### 1.3 Add Default Network Subnet
**Priority:** 🟡 HIGH  
**Effort:** 2 hours  
**Files to modify:**
- `minimal-backend/api/vpc.py` - Add default subnet creation

**Tasks:**
```python
# When default network exists, ensure subnet:
1. Name: default-subnet-us-central1
2. CIDR: 10.128.0.0/20
3. Region: us-central1
4. Network: default
```

**Testing:**
- `GET /compute/v1/projects/project-alpha/regions/us-central1/subnetworks` should include default subnet
- Instances in default network should use this subnet
- IP allocation should work correctly

---

## Phase 2: UI Enhancement (MEDIUM PRIORITY) 🟡
**Goal:** Complete missing UI functionality  
**Timeline:** 2-3 days  
**Impact:** Better user experience

### 2.1 Implement Instance Groups Backend
**Priority:** 🟡 MEDIUM  
**Effort:** 8 hours  
**Files to create/modify:**
- `minimal-backend/database.py` - Add InstanceGroup model
- `minimal-backend/api/compute.py` - Add instance group endpoints
- `gcp-stimulator-ui/src/pages/InstanceGroupsPage.tsx` - Connect to API

**Features:**
- Create managed instance groups
- Add/remove instances
- Configure autoscaling (basic)
- Health checks

---

### 2.2 Implement Disks Management
**Priority:** 🟡 MEDIUM  
**Effort:** 6 hours  
**Files to create/modify:**
- `minimal-backend/database.py` - Add Disk model
- `minimal-backend/api/compute.py` - Add disk endpoints
- `gcp-stimulator-ui/src/pages/DisksPage.tsx` - Create page

**Features:**
- Create persistent disks
- Attach/detach to instances
- Disk snapshots
- Resize operations

---

### 2.3 Code-Splitting & Performance
**Priority:** 🟡 MEDIUM  
**Effort:** 4 hours  
**Files to modify:**
- `gcp-stimulator-ui/vite.config.ts` - Configure chunking
- `gcp-stimulator-ui/src/App.tsx` - Add React.lazy()

**Tasks:**
```typescript
// Implement lazy loading for large pages:
const BucketDetails = lazy(() => import('./pages/BucketDetails'));
const ComputeDashboardPage = lazy(() => import('./pages/ComputeDashboardPage'));
```

**Goal:** Reduce bundle from 665 kB to < 400 kB

---

### 2.4 Cleanup Deprecated Code
**Priority:** 🟢 LOW  
**Effort:** 1 hour  
**Files to delete:**
- `gcp-stimulator-ui/src/pages/VPCDashboardPage.old.tsx`
- `gcp-stimulator-ui/src/pages/SubnetsPage.old.tsx`
- `gcp-stimulator-ui/src/pages/ComputeDashboardPage.old.tsx`

**Files to modify:**
- `minimal-backend/database.py` - Remove RouteTable models if not needed

---

## Phase 3: Advanced Features (LOW PRIORITY) 🟢
**Goal:** Production-grade simulator  
**Timeline:** 1-2 weeks  
**Impact:** Advanced use cases

### 3.1 Load Balancers
**Priority:** 🟢 LOW  
**Effort:** 12 hours  

**Features:**
- HTTP(S) load balancer
- Network load balancer
- Backend services
- Health checks
- URL maps
- Target pools

**Files to create:**
- `minimal-backend/database.py` - LoadBalancer, BackendService models
- `minimal-backend/api/loadbalancing.py` - New API module
- `gcp-stimulator-ui/src/pages/LoadBalancersPage.tsx` - New page

---

### 3.2 Monitoring & Logging
**Priority:** 🟢 LOW  
**Effort:** 16 hours  

**Features:**
- Instance CPU metrics (simulated)
- Network traffic metrics
- Storage usage metrics
- Event logs
- Audit logs
- Metrics visualization

**Files to create:**
- `minimal-backend/database.py` - Metric, LogEntry models
- `minimal-backend/api/monitoring.py` - Metrics API
- `minimal-backend/api/logging.py` - Logging API
- `gcp-stimulator-ui/src/pages/MonitoringPage.tsx` - Dashboard

---

### 3.3 Cloud DNS
**Priority:** 🟢 LOW  
**Effort:** 10 hours  

**Features:**
- DNS zones
- DNS records (A, AAAA, CNAME, MX, TXT)
- DNS policies
- DNSSEC

**Files to create:**
- `minimal-backend/database.py` - DNSZone, DNSRecord models
- `minimal-backend/api/dns.py` - DNS API
- `gcp-stimulator-ui/src/pages/DNSPage.tsx` - Management UI

---

### 3.4 Cloud SQL (Database Service)
**Priority:** 🟢 LOW  
**Effort:** 20 hours  

**Features:**
- MySQL instances (Docker containers)
- PostgreSQL instances
- Instance management (start/stop/restart)
- Database users
- Backups

**Files to create:**
- `minimal-backend/database.py` - CloudSQLInstance model
- `minimal-backend/api/sql.py` - Cloud SQL API
- `gcp-stimulator-ui/src/pages/CloudSQLPage.tsx` - Management UI

---

## Phase 4: Polish & Testing (PRODUCTION READY) 🎯
**Goal:** 95%+ production readiness  
**Timeline:** 1 week  
**Impact:** Deployment ready

### 4.1 End-to-End Testing
**Priority:** 🟡 MEDIUM  
**Effort:** 12 hours  

**Tools:**
- Playwright for UI testing
- Pytest for backend testing
- K6 for load testing

**Coverage:**
- All API endpoints
- All UI pages
- Error scenarios
- Performance benchmarks

---

### 4.2 Documentation
**Priority:** 🟡 MEDIUM  
**Effort:** 8 hours  

**Documents to create:**
- API Reference Guide
- User Guide (screenshots)
- Developer Guide (architecture)
- Deployment Guide
- Troubleshooting Guide

---

### 4.3 Security & Auth
**Priority:** 🟡 MEDIUM  
**Effort:** 16 hours  

**Features:**
- User authentication (OAuth2)
- API key management
- IAM role enforcement
- Audit logging
- Rate limiting

---

## Quick Win Tasks (Can Be Done Anytime) ⚡

### Small Improvements (< 1 hour each)
1. ✅ Add favicon to UI
2. ✅ Add loading spinners to all pages
3. ✅ Add error boundaries
4. ✅ Add toast notifications
5. ✅ Improve error messages
6. ✅ Add keyboard shortcuts
7. ✅ Add dark mode toggle
8. ✅ Add search/filter to instance list
9. ✅ Add bulk operations (select multiple instances)
10. ✅ Add instance templates

---

## Suggested Order of Implementation

### Week 1: Critical Gaps
1. **Day 1-2:** Firewall rules + Service accounts + Default subnet (Phase 1)
2. **Day 3-4:** Testing and bug fixes
3. **Day 5:** Documentation updates

### Week 2: UI Enhancement
1. **Day 1-2:** Instance Groups backend
2. **Day 3:** Disks management
3. **Day 4:** Code-splitting & performance
4. **Day 5:** Cleanup & testing

### Week 3-4: Advanced Features
1. **Week 3:** Load Balancers + Monitoring basics
2. **Week 4:** Cloud DNS + Advanced monitoring

### Week 5: Polish
1. **Day 1-3:** End-to-end testing
2. **Day 4:** Documentation
3. **Day 5:** Security improvements

---

## Success Metrics

### Phase 1 Complete (85% Ready)
- ✅ Firewall rules working
- ✅ Service accounts populated
- ✅ All networks have subnets
- ✅ No critical gaps

### Phase 2 Complete (90% Ready)
- ✅ All UI pages functional
- ✅ Bundle size < 400 kB
- ✅ No deprecated code

### Phase 3 Complete (95% Ready)
- ✅ Load balancers working
- ✅ Basic monitoring available
- ✅ DNS service operational

### Phase 4 Complete (95%+ Ready)
- ✅ 80%+ test coverage
- ✅ Complete documentation
- ✅ Security features enabled
- ✅ Production deployment ready

---

## Current Focus 🎯

**IMMEDIATE NEXT TASK:**
Start with **Phase 1.1 - Implement Default Firewall Rules**

This is the most visible gap and will immediately improve the simulator's realism and functionality.

---

**Roadmap Prepared:** February 11, 2026  
**Maintainer:** DevOps Team  
**Review Schedule:** Every sprint (2 weeks)
