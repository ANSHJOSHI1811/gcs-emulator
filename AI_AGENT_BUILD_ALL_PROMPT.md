# 🏗️ PROMPT FOR AI AGENT: Build All Possible GCP Services & Features

Copy this entire prompt and give it to Claude after initialization is complete.

---

## 📋 TASK: Implement All Possible GCP Services in GCS Emulator

**Objective**: Build out the complete GCS Emulator with all major GCP services fully implemented, tested, and working end-to-end.

**Current Status**: 
- ✅ Repo is clean and organized
- ✅ Backend and frontend running
- ✅ Seed data created and verified
- ⏳ Some services are partial (Autoscaling, GKE, Firewall)
- ⏳ Need to implement remaining services completely

**Expected Outcome**:
- ✅ All major GCP services implemented (99%+ coverage)
- ✅ All services have gcloud CLI compatibility (95%+)
- ✅ All services have complete API endpoints
- ✅ All services have React UI pages
- ✅ All services have comprehensive tests (85%+ coverage)
- ✅ All services have end-to-end workflows working
- ✅ Entire system tested and verified
- ✅ Documentation updated

---

## 🎯 YOUR ROLE (AI Agent)

You are building out the complete GCS Emulator. Your tasks:

1. **Review current status** of each service
2. **Implement missing features** for partial services
3. **Add complete tests** for all services
4. **Create frontend pages** for all services
5. **Verify end-to-end workflows**
6. **Update documentation**
7. **Report completion status**

Reference documents:
- CLAUDE.md (current service status)
- DEVELOPMENT_RULES.md (workflow & standards)
- SKILLS_ROADMAP.md (service knowledge)
- IMPLEMENTATION_TRACKER.md (what's done)

---

## 📊 SERVICE COMPLETION MATRIX

Use this to track progress. Your goal: **All ✅ COMPLETE**

| Service | gcloud | API | Frontend | Tests | Docker | Status | Priority |
|---------|--------|-----|----------|-------|--------|--------|----------|
| **Storage** | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ | COMPLETE | — |
| **Compute** | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ | COMPLETE | — |
| **VPC** | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ | COMPLETE | — |
| **IAM** | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | N/A | COMPLETE | — |
| **Monitoring** | ⚠️ 60% | ✅ 100% | ✅ 100% | ⚠️ 60% | N/A | PARTIAL | 🔴 HIGH |
| **Firewall** | ⚠️ 75% | ⚠️ 75% | ⚠️ 75% | ❌ 0% | ⚠️ | PARTIAL | 🔴 HIGH |
| **Autoscaling** | ⚠️ 50% | ⚠️ 50% | ⚠️ 50% | ❌ 0% | ⚠️ | PARTIAL | 🔴 HIGH |
| **GKE** | ❌ 0% | ⚠️ 50% | ⚠️ 50% | ❌ 0% | ⚠️ | PARTIAL | 🟡 MEDIUM |
| **Routes** | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | N/A | COMPLETE | — |
| **Pub/Sub** | ❌ 0% | ❌ 0% | ❌ 0% | ❌ 0% | N/A | MISSING | 🟡 MEDIUM |
| **Secrets Manager** | ❌ 0% | ❌ 0% | ❌ 0% | ❌ 0% | N/A | MISSING | 🟡 MEDIUM |
| **Cloud SQL** | ❌ 0% | ❌ 0% | ❌ 0% | ❌ 0% | ⚠️ | MISSING | 🟢 LOW |
| **BigQuery** | ❌ 0% | ❌ 0% | ❌ 0% | ❌ 0% | N/A | MISSING | 🟢 LOW |

---

## 🔴 PRIORITY 1: Complete Partial Services

### Service 1: Firewall Rules (⚠️ PARTIAL)

**Current State**: 75% gcloud, 75% API, 75% Frontend  
**Missing**: Tests, some edge cases, integration

**What to implement**:

#### 1.1: Complete gcloud CLI Wrappers
```
File: tests/gcloud_wrappers/firewall.py

Commands to wrap:
  ✅ gcloud compute firewall-rules create
  ✅ gcloud compute firewall-rules list
  ✅ gcloud compute firewall-rules delete
  ⚠️ gcloud compute firewall-rules update (add/remove rules)
  ⚠️ gcloud compute firewall-rules describe
  ❌ gcloud compute firewall-rules rules {list,add,remove}

Checklist:
  [ ] All commands return proper JSON
  [ ] Error messages match GCP format
  [ ] 85%+ test coverage
  [ ] Test passes: pytest tests/gcloud_wrappers/firewall.py -v
```

**Example implementation**:
```python
# tests/gcloud_wrappers/firewall.py

def create_firewall_rule(network, name, direction, priority, source_ranges=None, 
                        target_tags=None, allow_rules=None):
    """Wrapper for: gcloud compute firewall-rules create"""
    # Validate inputs
    if direction not in ["INGRESS", "EGRESS"]:
        raise ValueError("Invalid direction")
    if not (0 <= priority <= 65535):
        raise ValueError("Priority must be 0-65535")
    
    # Return formatted output matching gcloud
    return {
        "name": name,
        "network": network,
        "direction": direction,
        "priority": priority,
        "sourceRanges": source_ranges or ["0.0.0.0/0"],
        "targetTags": target_tags or [],
        "allowed": allow_rules or [{"IPProtocol": "tcp", "ports": ["22"]}]
    }

def delete_firewall_rule(name):
    """Wrapper for: gcloud compute firewall-rules delete"""
    # Verify rule exists
    # Delete via API or database
    return {"message": f"Firewall rule {name} deleted"}

def list_firewall_rules(network=None):
    """Wrapper for: gcloud compute firewall-rules list"""
    # Return array of firewall rules
    return [
        {"name": "default-allow-ssh", "network": "default", ...},
        # ... more rules
    ]

# Write tests for each command
def test_create_firewall_rule():
    result = create_firewall_rule(
        network="default",
        name="allow-http",
        direction="INGRESS",
        priority=1000,
        allow_rules=[{"IPProtocol": "tcp", "ports": ["80", "443"]}]
    )
    assert result["name"] == "allow-http"
    assert result["priority"] == 1000
```

#### 1.2: Complete API Endpoints
```
File: minimal-backend/app/api/firewall.py

Endpoints needed:
  ✅ POST /api/v1/firewall/rules (create)
  ✅ GET /api/v1/firewall/rules (list)
  ✅ DELETE /api/v1/firewall/rules/{rule_id} (delete)
  ⚠️ PATCH /api/v1/firewall/rules/{rule_id} (update)
  ⚠️ GET /api/v1/firewall/rules/{rule_id} (describe)

Validation needed:
  [ ] Direction is INGRESS or EGRESS
  [ ] Priority is 0-65535
  [ ] Source ranges are valid CIDR blocks
  [ ] Allow/deny rules have proper structure
  [ ] Network exists before creating rules

Database integration:
  [ ] Firewall rules stored in database
  [ ] State synchronized with Docker networks (if applicable)
  [ ] Proper error handling (rule not found, network not found, etc)

Tests:
  [ ] test_create_firewall_rule_valid
  [ ] test_create_firewall_rule_invalid_priority
  [ ] test_create_firewall_rule_invalid_direction
  [ ] test_delete_firewall_rule_not_found
  [ ] test_firewall_rules_list_by_network
```

#### 1.3: Complete Frontend Page
```
File: gcp-stimulator-ui/src/pages/Firewall.tsx

Features needed:
  ✅ List firewall rules in table
  ✅ Create new firewall rule form
  ✅ Delete firewall rule
  ⚠️ Edit firewall rule
  ⚠️ Filter rules by network
  ⚠️ Visualize rule priority

Form fields:
  - Rule name (required)
  - Network (dropdown)
  - Direction (INGRESS/EGRESS)
  - Priority (0-65535)
  - Source ranges (multi-input)
  - Target tags (multi-input)
  - Allow rules (protocol + ports)
  - Deny rules (if applicable)

Validation:
  [ ] Rule name not empty
  [ ] Priority 0-65535
  [ ] At least one source range
  [ ] At least one allow/deny rule

Tests:
  [ ] Can create firewall rule via UI
  [ ] Can delete firewall rule via UI
  [ ] Can filter rules by network
  [ ] Form validation works
```

#### 1.4: Complete Tests
```
File: tests/integration/firewall/test_api.py
File: tests/integration/firewall/test_integration.py

Test coverage needed:
  [ ] Create firewall rule (valid)
  [ ] Create firewall rule (invalid priority)
  [ ] Create firewall rule (invalid direction)
  [ ] Create firewall rule (network not found)
  [ ] List firewall rules
  [ ] List firewall rules by network
  [ ] Delete firewall rule
  [ ] Delete firewall rule (not found)
  [ ] Update firewall rule priority
  [ ] Add allow rule to existing firewall rule
  [ ] Remove rule from existing firewall rule

Integration tests:
  [ ] Create network → Create firewall rule → Verify rule in network
  [ ] Create instance → Apply firewall rule → Verify traffic rules
  [ ] End-to-end: gcloud create → API verify → Frontend display

Coverage target: 90%+
```

---

### Service 2: Autoscaling (⚠️ PARTIAL)

**Current State**: 50% gcloud, 50% API, 50% Frontend  
**Missing**: Tests, actual scaling logic, Docker integration

**What to implement**:

#### 2.1: Complete gcloud CLI Wrappers
```
File: tests/gcloud_wrappers/autoscaling.py

Commands to wrap:
  ⚠️ gcloud compute instance-groups managed create
  ⚠️ gcloud compute instance-groups managed list
  ⚠️ gcloud compute instance-groups managed delete
  ⚠️ gcloud compute instance-groups managed set-autoscaling
  ⚠️ gcloud compute instance-groups managed describe
  ❌ gcloud compute instance-groups managed update-instances

Key features:
  [ ] Instance group templates
  [ ] Min/max size limits
  [ ] Autoscaling metrics (CPU, memory)
  [ ] Target values for scaling
  [ ] Scale-up/down policies
  [ ] Cooldown periods

Tests:
  [ ] Create instance group with template
  [ ] List instance groups
  [ ] Set autoscaling policy
  [ ] Describe autoscaling details
  [ ] Delete instance group
```

#### 2.2: Complete API Endpoints & Scaling Logic
```
File: minimal-backend/app/api/autoscaling.py
File: minimal-backend/app/services/autoscaling/operations.py

Endpoints:
  [ ] POST /api/v1/autoscaling/groups (create)
  [ ] GET /api/v1/autoscaling/groups (list)
  [ ] DELETE /api/v1/autoscaling/groups/{group_id} (delete)
  [ ] POST /api/v1/autoscaling/groups/{group_id}/set-policy (set scaling policy)
  [ ] GET /api/v1/autoscaling/groups/{group_id}/policy (get policy)

Scaling logic:
  [ ] Monitor metric values (CPU, memory)
  [ ] Compare against target value
  [ ] Calculate number of instances to add/remove
  [ ] Create/delete instances based on scaling decision
  [ ] Apply cooldown period between scaling actions
  [ ] Update instance group size

Database:
  [ ] instance_groups table
  [ ] autoscaling_policies table
  [ ] scaling_history table (for audit)

Integration with Compute:
  [ ] Create instances from template
  [ ] Delete instances when scaling down
  [ ] Update instance group "size" field
  [ ] Synchronize with Docker containers
```

#### 2.3: Complete Frontend Page
```
File: gcp-stimulator-ui/src/pages/Autoscaling.tsx

Features:
  [ ] List instance groups with current size
  [ ] Create new instance group (select template, min, max)
  [ ] Set autoscaling policy (select metric, target value)
  [ ] View scaling history (when instances added/removed)
  [ ] Manual scale (adjust current size)
  [ ] Delete instance group

Dashboard:
  [ ] Current instance count vs min/max
  [ ] Scaling metrics graph (CPU, memory)
  [ ] Recent scaling actions
  [ ] Cooldown status

Tests:
  [ ] Can create instance group
  [ ] Can set autoscaling policy
  [ ] Can scale up manually
  [ ] Can scale down manually
  [ ] Scaling triggered by metrics
```

#### 2.4: Complete Tests
```
File: tests/integration/autoscaling/test_api.py
File: tests/integration/autoscaling/test_scaling_logic.py

Test coverage:
  [ ] Create instance group (valid)
  [ ] Create instance group (template not found)
  [ ] Set autoscaling policy (valid)
  [ ] Set autoscaling policy (invalid target)
  [ ] Scale up (metric exceeds target)
  [ ] Scale down (metric below target)
  [ ] Respect min/max limits
  [ ] Cooldown period enforced
  [ ] Manual scaling works
  [ ] Scaling creates/deletes instances
  [ ] Scaling creates/deletes Docker containers
  [ ] Scaling history recorded

Coverage target: 85%+
```

---

### Service 3: GKE (⚠️ PARTIAL / ❌ MISSING)

**Current State**: 0% gcloud, 50% API, 50% Frontend  
**Missing**: gcloud wrappers, complete API, tests

**What to implement**:

#### 3.1: gcloud CLI Wrappers (FROM SCRATCH)
```
File: tests/gcloud_wrappers/gke.py

Commands to implement:
  [ ] gcloud container clusters create
  [ ] gcloud container clusters list
  [ ] gcloud container clusters delete
  [ ] gcloud container clusters describe
  [ ] gcloud container node-pools create
  [ ] gcloud container node-pools list
  [ ] gcloud container node-pools delete

Output format:
```json
{
  "name": "production-cluster",
  "zone": "us-central1-a",
  "status": "RUNNING",
  "numNodes": 3,
  "machineType": "n1-standard-1",
  "clusterVersion": "1.27.0",
  "nodePools": [
    {
      "name": "default-pool",
      "nodeCount": 3,
      "machineType": "n1-standard-1"
    }
  ]
}
```

Tests:
  [ ] Create cluster
  [ ] List clusters
  [ ] Describe cluster
  [ ] Create node pool
  [ ] Delete cluster
  [ ] Error when cluster exists
```

#### 3.2: Complete API Implementation
```
File: minimal-backend/app/api/gke.py
File: minimal-backend/app/services/gke/operations.py

Endpoints:
  [ ] POST /api/v1/gke/clusters (create)
  [ ] GET /api/v1/gke/clusters (list)
  [ ] GET /api/v1/gke/clusters/{cluster_id} (describe)
  [ ] DELETE /api/v1/gke/clusters/{cluster_id} (delete)
  [ ] POST /api/v1/gke/clusters/{cluster_id}/node-pools (create pool)
  [ ] GET /api/v1/gke/clusters/{cluster_id}/node-pools (list pools)
  [ ] DELETE /api/v1/gke/clusters/{cluster_id}/node-pools/{pool_id} (delete pool)

Database:
  [ ] gke_clusters table
  [ ] gke_node_pools table
  [ ] gke_nodes table

Docker Integration:
  [ ] Each node = Docker container
  [ ] Node pool = group of containers
  [ ] Cluster = Docker network + containers
  [ ] Nodes can be created/deleted
```

#### 3.3: Complete Frontend Page
```
File: gcp-stimulator-ui/src/pages/GKE.tsx

Features:
  [ ] List clusters with status
  [ ] Create new cluster form
  [ ] View cluster details
  [ ] List node pools per cluster
  [ ] Create node pool
  [ ] Delete cluster
  [ ] Delete node pool
  [ ] Scale node pool (change node count)

Dashboard:
  [ ] Cluster status (PROVISIONING, RUNNING, STOPPING)
  [ ] Node count per pool
  [ ] Machine type per pool
  [ ] Cluster version
```

#### 3.4: Complete Tests
```
Test coverage:
  [ ] Create cluster (valid)
  [ ] Create cluster (zone not found)
  [ ] List clusters
  [ ] Describe cluster
  [ ] Delete cluster
  [ ] Create node pool (valid)
  [ ] Create node pool (cluster not found)
  [ ] Delete node pool
  [ ] Scale node pool
  [ ] Nodes created as Docker containers
  [ ] Cluster created as Docker network

Coverage target: 85%+
```

---

## 🟡 PRIORITY 2: Implement Missing Services

### Service 4: Pub/Sub (❌ MISSING)

**What to implement**: Messaging/event system

#### 4.1: Design Database Schema
```sql
CREATE TABLE pubsub_topics (
  id UUID PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  project_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pubsub_subscriptions (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  topic_id UUID REFERENCES pubsub_topics(id),
  project_id VARCHAR(255),
  ack_deadline_seconds INTEGER DEFAULT 60,
  created_at TIMESTAMP
);

CREATE TABLE pubsub_messages (
  id UUID PRIMARY KEY,
  topic_id UUID REFERENCES pubsub_topics(id),
  data TEXT,
  attributes JSONB,
  published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subscription_messages (
  id UUID PRIMARY KEY,
  subscription_id UUID REFERENCES pubsub_subscriptions(id),
  message_id UUID REFERENCES pubsub_messages(id),
  ack_id VARCHAR(255),
  acked BOOLEAN DEFAULT FALSE
);
```

#### 4.2: gcloud CLI Wrappers
```
Commands to implement:
  [ ] gcloud pubsub topics create
  [ ] gcloud pubsub topics list
  [ ] gcloud pubsub topics publish
  [ ] gcloud pubsub topics delete
  [ ] gcloud pubsub subscriptions create
  [ ] gcloud pubsub subscriptions list
  [ ] gcloud pubsub subscriptions pull
  [ ] gcloud pubsub subscriptions ack
```

#### 4.3: API Endpoints
```
POST   /api/v1/pubsub/topics
GET    /api/v1/pubsub/topics
DELETE /api/v1/pubsub/topics/{topic_id}
POST   /api/v1/pubsub/topics/{topic_id}/publish
POST   /api/v1/pubsub/subscriptions
GET    /api/v1/pubsub/subscriptions
DELETE /api/v1/pubsub/subscriptions/{sub_id}
GET    /api/v1/pubsub/subscriptions/{sub_id}/pull
POST   /api/v1/pubsub/subscriptions/{sub_id}/ack
```

#### 4.4: Frontend Page
```
Features:
  [ ] List topics
  [ ] Create topic
  [ ] Publish message to topic
  [ ] List subscriptions
  [ ] Create subscription
  [ ] Pull messages from subscription
  [ ] View message content
```

#### 4.5: Tests
```
Test coverage: 85%+
  [ ] Create topic
  [ ] Publish message
  [ ] Create subscription
  [ ] Pull message
  [ ] Acknowledge message
  [ ] Message ordering
  [ ] Subscription filtering
```

---

### Service 5: Secrets Manager (❌ MISSING)

**What to implement**: Secret storage and retrieval

#### 5.1: Database Schema
```sql
CREATE TABLE secrets (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  project_id VARCHAR(255),
  labels JSONB,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE secret_versions (
  id UUID PRIMARY KEY,
  secret_id UUID REFERENCES secrets(id),
  version_id INTEGER,
  secret_value TEXT,
  created_at TIMESTAMP,
  destroyed_at TIMESTAMP
);
```

#### 5.2: gcloud CLI Wrappers
```
Commands:
  [ ] gcloud secrets create
  [ ] gcloud secrets list
  [ ] gcloud secrets describe
  [ ] gcloud secrets add-iam-policy-binding
  [ ] gcloud secrets versions add
  [ ] gcloud secrets versions list
  [ ] gcloud secrets versions access
  [ ] gcloud secrets delete
```

#### 5.3: API Endpoints
```
POST   /api/v1/secrets
GET    /api/v1/secrets
GET    /api/v1/secrets/{secret_id}
DELETE /api/v1/secrets/{secret_id}
POST   /api/v1/secrets/{secret_id}/versions
GET    /api/v1/secrets/{secret_id}/versions
GET    /api/v1/secrets/{secret_id}/versions/{version_id}/access
```

#### 5.4: Frontend Page
```
Features:
  [ ] List secrets with masking
  [ ] Create secret
  [ ] View secret versions
  [ ] Add new secret version
  [ ] Set secret labels
  [ ] Delete secret
```

#### 5.5: Tests
```
Test coverage: 85%+
  [ ] Create secret
  [ ] Add version
  [ ] Access version
  [ ] Version history
  [ ] Secret rotation
  [ ] Access control
```

---

### Service 6: Cloud SQL (❌ MISSING) [OPTIONAL]

**What to implement**: Managed SQL database instances

#### 6.1: Key Features
```
[ ] Create database instance (MySQL, PostgreSQL)
[ ] List instances
[ ] Delete instances
[ ] Create databases in instance
[ ] Create users/passwords
[ ] Backup scheduling
[ ] Point-in-time recovery
```

---

### Service 7: BigQuery (❌ MISSING) [OPTIONAL]

**What to implement**: Data warehouse

#### 7.1: Key Features
```
[ ] Create datasets
[ ] Create tables
[ ] Load data
[ ] Query tables
[ ] List results
[ ] Job tracking
```

---

## ✅ PRIORITY 3: Enhance Completed Services

For all ✅ COMPLETE services:

### Testing Enhancement
```
Goal: Increase coverage from current to 95%+

For each service:
  [ ] Add edge case tests
  [ ] Add error condition tests
  [ ] Add load/stress tests
  [ ] Add performance tests
  [ ] Run coverage report: pytest tests/integration/{service}/ --cov
```

### Documentation Enhancement
```
For each service in CLAUDE.md:
  [ ] Update status to ✅ 100%
  [ ] Document all API endpoints
  [ ] Document all gcloud commands
  [ ] Document Docker integration
  [ ] Add troubleshooting section
```

### Frontend Enhancement
```
For each service page:
  [ ] Add data export (CSV, JSON)
  [ ] Add data import (bulk operations)
  [ ] Add advanced filters
  [ ] Add sorting options
  [ ] Add pagination
  [ ] Add error notifications
  [ ] Add loading states
```

---

## 🎯 IMPLEMENTATION WORKFLOW

For EACH service you implement, follow this strict process:

### Phase 1: gcloud CLI (ALWAYS FIRST)
```
1. Create: tests/gcloud_wrappers/{service}.py
2. Write wrapper functions (alphabetically)
3. Create: tests/integration/{service}/test_gcloud_cli.py
4. Write tests for each wrapper
5. Run: pytest tests/gcloud_wrappers/{service}.py -v
6. Verify: Coverage ≥ 80%
```

### Phase 2: Backend API
```
1. Update: minimal-backend/app/models/database.py (add tables)
2. Create: minimal-backend/app/api/{service}.py (routes)
3. Create: minimal-backend/app/services/{service}/ (logic)
4. Create: tests/integration/{service}/test_api.py
5. Run: pytest tests/integration/{service}/test_api.py -v
6. Verify: Coverage ≥ 85%
```

### Phase 3: Frontend UI
```
1. Create: gcp-stimulator-ui/src/pages/{ServiceName}.tsx
2. Create: gcp-stimulator-ui/src/api/{service}.ts
3. Create: gcp-stimulator-ui/src/types/{service}.ts
4. Update: gcp-stimulator-ui/src/App.tsx (add route)
5. Test in browser: Manually verify CRUD operations
6. Verify: No console errors
```

### Phase 4: Integration Tests
```
1. Create: tests/integration/{service}/test_integration.py
2. Write end-to-end workflows
3. Run: pytest tests/integration/{service}/ -v --cov
4. Verify: Coverage ≥ 85%
```

### Phase 5: Commit
```
1. Update: IMPLEMENTATION_TRACKER.md
2. Update: CLAUDE.md with new status
3. Git commit with proper message
4. Git push
```

---

## 📋 IMPLEMENTATION CHECKLIST

Track completion with this checklist:

### Firewall Rules
- [ ] gcloud wrappers (80%+)
- [ ] API endpoints (90%+)
- [ ] Frontend page
- [ ] Integration tests (85%+)
- [ ] Tests pass
- [ ] Documented

### Autoscaling
- [ ] gcloud wrappers (80%+)
- [ ] API endpoints (90%+)
- [ ] Scaling logic working
- [ ] Frontend page
- [ ] Integration tests (85%+)
- [ ] Tests pass
- [ ] Documented

### GKE
- [ ] gcloud wrappers (80%+)
- [ ] API endpoints (90%+)
- [ ] Docker integration (nodes as containers)
- [ ] Frontend page
- [ ] Integration tests (85%+)
- [ ] Tests pass
- [ ] Documented

### Pub/Sub
- [ ] gcloud wrappers (80%+)
- [ ] API endpoints (90%+)
- [ ] Message queue working
- [ ] Frontend page
- [ ] Integration tests (85%+)
- [ ] Tests pass
- [ ] Documented

### Secrets Manager
- [ ] gcloud wrappers (80%+)
- [ ] API endpoints (90%+)
- [ ] Secret encryption (basic)
- [ ] Frontend page
- [ ] Integration tests (85%+)
- [ ] Tests pass
- [ ] Documented

### Cloud SQL [OPTIONAL]
- [ ] gcloud wrappers (80%+)
- [ ] API endpoints (90%+)
- [ ] Database creation
- [ ] Frontend page
- [ ] Integration tests (85%+)
- [ ] Tests pass
- [ ] Documented

### BigQuery [OPTIONAL]
- [ ] gcloud wrappers (80%+)
- [ ] API endpoints (90%+)
- [ ] Data loading
- [ ] Frontend page
- [ ] Integration tests (85%+)
- [ ] Tests pass
- [ ] Documented

---

## 🎯 DELIVERY PHASES

### Phase 1: Priority 1 Services (1-2 weeks)
Complete all partial services:
- [ ] Firewall Rules (complete)
- [ ] Autoscaling (complete)
- [ ] GKE (complete)
- All tests passing
- All documented

### Phase 2: Priority 2 Services (1-2 weeks)
Implement missing services:
- [ ] Pub/Sub (complete)
- [ ] Secrets Manager (complete)
- All tests passing
- All documented

### Phase 3: Priority 3 Services (1-2 weeks) [OPTIONAL]
Implement optional services:
- [ ] Cloud SQL (complete)
- [ ] BigQuery (complete)
- All tests passing
- All documented

### Phase 4: Polish & Enhancement (1 week)
- [ ] Increase all test coverage to 95%+
- [ ] Add advanced UI features
- [ ] Performance optimization
- [ ] Documentation complete
- [ ] Final verification

---

## 📊 FINAL DELIVERABLE

When complete, you'll have:

```
═════════════════════════════════════════════════════════════════
 GCS EMULATOR - COMPLETE IMPLEMENTATION
═════════════════════════════════════════════════════════════════

SERVICES IMPLEMENTED: 12/12 (100%)

✅ Storage          (100% - gcloud, API, Frontend, Tests)
✅ Compute          (100% - gcloud, API, Frontend, Tests)
✅ VPC              (100% - gcloud, API, Frontend, Tests)
✅ Routes           (100% - gcloud, API, Frontend, Tests)
✅ Firewall         (100% - gcloud, API, Frontend, Tests)
✅ IAM              (100% - gcloud, API, Frontend, Tests)
✅ Monitoring       (100% - gcloud, API, Frontend, Tests)
✅ Autoscaling      (100% - gcloud, API, Frontend, Tests)
✅ GKE              (100% - gcloud, API, Frontend, Tests)
✅ Pub/Sub          (100% - gcloud, API, Frontend, Tests)
✅ Secrets Manager  (100% - gcloud, API, Frontend, Tests)
✅ Cloud SQL        (100% - gcloud, API, Frontend, Tests) [OPTIONAL]
✅ BigQuery         (100% - gcloud, API, Frontend, Tests) [OPTIONAL]

COVERAGE METRICS:
  - gcloud CLI: 95%+ compatibility
  - API: 95%+ endpoint coverage
  - Frontend: 100% page coverage
  - Tests: 95%+ code coverage

FEATURES:
  - 150+ API endpoints
  - 100+ gcloud CLI commands
  - 15+ React pages
  - 500+ unit & integration tests
  - Complete end-to-end workflows
  - Docker container integration
  - Real-time state synchronization
  - Comprehensive error handling
  - Full documentation

READY FOR:
  ✅ Production-like testing
  ✅ Feature development
  ✅ Team collaboration
  ✅ Educational use
  ✅ GCP simulation

═════════════════════════════════════════════════════════════════
```

---

## 🚀 HOW TO USE THIS PROMPT

### If implementing ALL services:
1. Follow Priority 1 → 2 → 3 in order
2. Complete each service fully before moving to next
3. Use strict DEVELOPMENT_RULES.md for every change
4. Run tests after each service
5. Update IMPLEMENTATION_TRACKER.md after each service

### If implementing PARTIAL services only:
1. Skip Priority 1 services you don't need
2. Focus on Firewall, Autoscaling, GKE first
3. Add optional services later

### If implementing SPECIFIC services:
1. Tell me which services you want
2. I'll implement them following the exact same workflow
3. All tests, docs, UI included

---

## 📝 PROGRESS TRACKING

After each service, update IMPLEMENTATION_TRACKER.md:

```markdown
| Service | gcloud | API | Frontend | Tests | Status |
|---------|--------|-----|----------|-------|--------|
| Firewall | ✅ 90% | ✅ 90% | ✅ 100% | ✅ 90% | ✅ COMPLETE |
| Autoscaling | ✅ 90% | ✅ 90% | ✅ 100% | ✅ 90% | ✅ COMPLETE |
| ... | ... | ... | ... | ... | ... |
```

---

## ⏱️ TIME ESTIMATES

| Service | Time | Difficulty |
|---------|------|------------|
| Firewall | 12 hours | Medium |
| Autoscaling | 16 hours | Medium-Hard |
| GKE | 20 hours | Hard |
| Pub/Sub | 16 hours | Medium |
| Secrets Manager | 12 hours | Medium |
| Cloud SQL | 16 hours | Hard |
| BigQuery | 20 hours | Hard |
| Polish | 20 hours | Easy |
| **TOTAL** | **132 hours** | **~3 weeks** |

---

## ✅ SUCCESS CRITERIA

Implementation is complete when:

- [ ] All 12 services have gcloud wrappers (90%+ coverage)
- [ ] All services have complete API endpoints (90%+ coverage)
- [ ] All services have React UI pages
- [ ] All services have integration tests (85%+ coverage)
- [ ] All tests pass (0 failures)
- [ ] Frontend loads all seed data
- [ ] End-to-end workflows work (create → list → delete)
- [ ] Docker containers sync with instances
- [ ] IMPLEMENTATION_TRACKER.md shows all ✅ COMPLETE
- [ ] CLAUDE.md updated with 100% status
- [ ] All services documented

---

## 🎉 READY?

Give this prompt to your AI agent and watch it build out the complete GCS Emulator!

**Expected outcome**: Fully functional, well-tested GCP emulator with 12+ services.

**Time frame**: 2-4 weeks depending on parallelization.

**Quality**: Production-ready code with 95%+ test coverage.

Let's build! 🚀

