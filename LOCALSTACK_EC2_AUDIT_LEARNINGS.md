# LocalStack EC2 Instance Implementation - Audit & Key Learnings

**Date:** December 9, 2025  
**Purpose:** Understanding LocalStack's EC2 instance lifecycle management to inform our GCS Compute Service implementation  
**Repository Analyzed:** localstack/localstack (main branch)

---

## Executive Summary

LocalStack implements EC2 instance emulation through a sophisticated **CloudFormation resource provider pattern** combined with **Moto backend integration**. Instead of managing actual Docker containers for compute, LocalStack primarily delegates to Moto's in-memory models while adding validation, state management, and AWS parity enhancements.

**Key Insight:** LocalStack does NOT create actual running containers for EC2 instances in most cases - it maintains state in memory via Moto backends and simulates compute behavior.

---

## Architecture Overview

### 1. **Provider Pattern Architecture**

```
User Request (boto3/aws-cli)
    ↓
RequestContext (account_id, region, credentials)
    ↓
Ec2Provider (localstack/services/ec2/provider.py)
    ↓
Handler Methods (@handler decorator)
    ↓
call_moto() or custom implementation
    ↓
Moto EC2Backend (in-memory state)
```

**File:** `localstack-core/localstack/services/ec2/provider.py`

```python
class Ec2Provider(Ec2Api, ABC, ServiceLifecycleHook):
    def on_after_init(self):
        apply_patches()  # Patches moto behavior
    
    def accept_state_visitor(self, visitor: StateVisitor):
        from moto.ec2.models import ec2_backends
        visitor.visit(ec2_backends)
```

### 2. **CloudFormation Resource Provider Integration**

**File:** `localstack-core/localstack/services/ec2/resource_providers/aws_ec2_instance.py`

```python
class EC2InstanceProvider(ResourceProvider[EC2InstanceProperties]):
    TYPE = "AWS::EC2::Instance"
    
    def create(self, request: ResourceRequest[EC2InstanceProperties]) -> ProgressEvent:
        """
        Create-only properties enforced:
          - ImageId, KeyName, SubnetId, AvailabilityZone
          - NetworkInterfaces, CpuOptions, EnclaveOptions
        
        Read-only properties computed:
          - PublicIp, PrivateIp, Id
          - PublicDnsName, PrivateDnsName
        """
        model = request.desired_state
        ec2 = request.aws_client_factory.ec2
        
        if not request.custom_context.get(REPEATED_INVOCATION):
            # First invocation - create instance
            params = util.select_attributes(model, ["InstanceType", "SecurityGroups", "KeyName", "ImageId"])
            params["MaxCount"] = 1
            params["MinCount"] = 1
            
            if model.get("UserData"):
                params["UserData"] = to_str(base64.b64decode(model["UserData"]))
            
            response = ec2.run_instances(**params)
            model["Id"] = response["Instances"][0]["InstanceId"]
            request.custom_context[REPEATED_INVOCATION] = True
            
            # Return IN_PROGRESS - CloudFormation will poll
            return ProgressEvent(status=OperationStatus.IN_PROGRESS, resource_model=model)
        
        # Subsequent invocations - check if running
        response = ec2.describe_instances(InstanceIds=[model["Id"]])
        instance = response["Reservations"][0]["Instances"][0]
        
        if instance["State"]["Name"] != "running":
            return ProgressEvent(status=OperationStatus.IN_PROGRESS, resource_model=model)
        
        # Instance is running
        model.update({
            "PublicIp": instance.get("PublicIpAddress"),
            "PrivateIp": instance.get("PrivateIpAddress"),
            "PublicDnsName": instance.get("PublicDnsName"),
            "PrivateDnsName": instance.get("PrivateDnsName"),
        })
        return ProgressEvent(status=OperationStatus.SUCCESS, resource_model=model)
```

---

## Key Learnings for GCS Compute Service

### Learning #1: State Machine Pattern for Async Operations

**Problem:** Instance creation is async - can't return success immediately  
**LocalStack Solution:** `REPEATED_INVOCATION` pattern with custom_context

```python
# First call
if not request.custom_context.get(REPEATED_INVOCATION):
    # Start operation
    request.custom_context[REPEATED_INVOCATION] = True
    return ProgressEvent(status=OperationStatus.IN_PROGRESS)

# Subsequent calls (polling)
# Check if operation complete
if instance["State"]["Name"] != "running":
    return ProgressEvent(status=OperationStatus.IN_PROGRESS)
else:
    return ProgressEvent(status=OperationStatus.SUCCESS)
```

**Application to GCS Compute:**
```python
# app/services/compute_service.py
def create_instance(self, request_id, instance_config):
    if not self.operation_tracker.get(request_id):
        # Start Docker container
        container_id = docker_client.run_container(...)
        self.operation_tracker[request_id] = {"container_id": container_id, "state": "PROVISIONING"}
        return {"status": "PENDING"}
    
    # Check container status
    status = docker_client.inspect_container(self.operation_tracker[request_id]["container_id"])
    if status["State"]["Running"]:
        return {"status": "RUNNING", "metadata": {...}}
    else:
        return {"status": "PENDING"}
```

### Learning #2: Validation Before Moto Delegation

**File:** `localstack-core/localstack/services/ec2/provider.py` (lines 373-388)

```python
@handler("CreateLaunchTemplate", expand=False)
def create_launch_template(self, context: RequestContext, request: CreateLaunchTemplateRequest) -> CreateLaunchTemplateResult:
    # Parameter validation BEFORE calling moto
    if not request["LaunchTemplateData"]:
        raise MissingParameterError(parameter="LaunchTemplateData")
    
    name = request["LaunchTemplateName"]
    if len(name) < 3 or len(name) > 128 or not re.fullmatch(r"[a-zA-Z0-9.\-_()/]*", name):
        raise InvalidLaunchTemplateNameError()
    
    return call_moto(context)  # Delegate to moto only after validation
```

**Application to GCS Compute:**
```python
def create_instance(self, request_context, instance_config):
    # Validate before expensive Docker operations
    if not instance_config.get("machineType"):
        raise InvalidParameterException("machineType is required")
    
    if not re.match(r'^[a-z][-a-z0-9]{0,62}$', instance_config["name"]):
        raise InvalidParameterException("Invalid instance name format")
    
    # Check if name already exists
    if self.instance_exists(instance_config["name"]):
        raise ResourceAlreadyExistsException(f"Instance {instance_config['name']} already exists")
    
    # Now create container
    return self._create_container(instance_config)
```

### Learning #3: Exception Handling & Error Codes

**File:** `localstack-core/localstack/services/ec2/exceptions.py`

```python
class InvalidInstanceIdError(CommonServiceException):
    def __init__(self, instance_id):
        super().__init__(
            code="InvalidInstanceID.NotFound",
            message=f"The instance ID '{instance_id}' does not exist",
        )

class IncorrectInstanceStateError(CommonServiceException):
    def __init__(self, instance_id):
        super().__init__(
            code="IncorrectInstanceState",
            message=f"The instance '{instance_id}' is not in a state from which it can be started",
        )
```

**Application to GCS Compute:**
```python
# app/utils/gcs_errors.py
class InvalidInstanceError(GCSException):
    def __init__(self, instance_name):
        super().__init__(
            code=400,
            reason="Invalid",
            message=f"The instance '{instance_name}' does not exist",
            domain="global",
            location="instance"
        )

class InstanceNotReadyError(GCSException):
    def __init__(self, instance_name, current_state):
        super().__init__(
            code=400,
            reason="OperationNotValid",
            message=f"Instance '{instance_name}' is {current_state}, cannot perform operation",
        )
```

### Learning #4: Network Management Pattern

**File:** `localstack-core/localstack/utils/container_networking.py`

```python
@lru_cache
def get_main_container_network() -> str | None:
    """
    Gets the main network of the LocalStack container
    If there are multiple networks, choose the first as "main" network
    """
    if config.MAIN_DOCKER_NETWORK:
        if config.is_in_docker:
            networks = DOCKER_CLIENT.get_networks(get_main_container_name())
            if config.MAIN_DOCKER_NETWORK not in networks:
                LOG.warning("Specified network not connected, falling back to %s", networks[0])
                return networks[0]
        return config.MAIN_DOCKER_NETWORK
    
    # Default to bridge network
    return "bridge"

@lru_cache
def get_endpoint_for_network(network: str | None = None) -> str:
    """Get LocalStack endpoint (IP address) on the given network"""
    container_name = get_main_container_name()
    network = network or get_main_container_network()
    
    if config.is_in_docker:
        return DOCKER_CLIENT.get_container_ipv4_for_network(container_name, network)
    else:
        # Host mode - get gateway IP
        if config.is_in_linux:
            return DOCKER_CLIENT.inspect_network(network)["IPAM"]["Config"][0]["Gateway"]
        else:
            # macOS/Windows - use host.docker.internal
            return resolve_host_docker_internal()
```

**Application to GCS Compute:**
```python
# app/services/networking_service.py
class ComputeNetworkManager:
    DEFAULT_NETWORK = "gcs-compute-net"
    
    def __init__(self):
        self._ensure_network_exists()
    
    def _ensure_network_exists(self):
        try:
            DOCKER_CLIENT.inspect_network(self.DEFAULT_NETWORK)
        except NoSuchNetwork:
            DOCKER_CLIENT.create_network(
                self.DEFAULT_NETWORK,
                driver="bridge",
                options={"com.docker.network.bridge.name": "gcs-compute0"}
            )
    
    def get_network_for_instance(self, zone: str) -> str:
        """Return network name for instance based on zone"""
        # Could implement zone-specific networks
        return self.DEFAULT_NETWORK
    
    def get_instance_ip(self, container_id: str) -> str:
        """Get IP address of instance container"""
        return DOCKER_CLIENT.get_container_ipv4_for_network(
            container_id, 
            self.DEFAULT_NETWORK
        )
```

### Learning #5: Port Management for Services

**File:** `localstack-core/localstack/utils/docker_utils.py`

```python
class _DockerPortRange(PortRange):
    """PortRange which checks whether port can be bound on host vs inside container"""
    
    def _port_can_be_bound(self, port: IntOrPort) -> bool:
        return container_ports_can_be_bound(port)

def reserve_available_container_port(duration: int = None, port_start: int = None, port_end: int = None, protocol: str = None) -> int:
    """
    Determine a free port that can be bound by Docker container
    
    :param duration: seconds to reserve the port (default: ~6 seconds)
    :param port_start: start of port range (default: 1024)
    :param port_end: end of port range (default: 65536)
    :return: random available port
    """
    protocol = protocol or "tcp"
    
    def _random_port():
        port = None
        while not port or reserved_docker_ports.is_port_reserved(port):
            port_number = random.randint(
                RANDOM_PORT_START if port_start is None else port_start,
                RANDOM_PORT_END if port_end is None else port_end,
            )
            port = Port(port=port_number, protocol=protocol)
        return port
    
    retries = 10
    for i in range(retries):
        port = _random_port()
        try:
            reserve_container_port(port, duration=duration)
            return port.port
        except PortNotAvailableException as e:
            LOG.debug("Port %s not available, trying next one: %s", port, e)
    
    raise PortNotAvailableException(f"Unable to find available port after {retries} retries")

def container_ports_can_be_bound(ports: IntOrPort | list[IntOrPort], address: str | None = None) -> bool:
    """Determine whether given ports can be bound by Docker containers"""
    port_mappings = PortMappings(bind_host=address or "")
    ports = ensure_list(ports)
    for port in ports:
        port = Port.wrap(port)
        port_mappings.add(port.port, port.port, protocol=port.protocol)
    
    try:
        result = DOCKER_CLIENT.run_container(
            _get_ports_check_docker_image(),
            entrypoint="sh",
            command=["-c", "echo test123"],
            ports=port_mappings,
            remove=True,
        )
        return True
    except Exception as e:
        if "port is already allocated" in str(e) or "address already in use" in str(e):
            return False
        raise
```

**Application to GCS Compute:**
```python
# app/services/port_pool_service.py
class ComputePortPool:
    """Manages port allocation for compute instances"""
    
    def __init__(self, start_port=config.COMPUTE_PORT_MIN, end_port=config.COMPUTE_PORT_MAX):
        self.start_port = start_port
        self.end_port = end_port
        self.allocated = {}  # {port: (instance_id, timestamp)}
        self.lock = threading.Lock()
    
    def allocate_ports(self, instance_id: str, num_ports: int = 1) -> list[int]:
        """Allocate ports for instance"""
        with self.lock:
            ports = []
            for _ in range(num_ports):
                port = self._find_free_port()
                self.allocated[port] = (instance_id, time.time())
                ports.append(port)
            return ports
    
    def _find_free_port(self) -> int:
        """Find a port that's not allocated and can actually bind"""
        for attempt in range(100):
            port = random.randint(self.start_port, self.end_port)
            if port not in self.allocated:
                # Verify port can bind
                if self._can_bind(port):
                    return port
        raise PortNotAvailableException("No free ports in pool")
    
    def _can_bind(self, port: int) -> bool:
        """Test if port can be bound by creating temp container"""
        try:
            DOCKER_CLIENT.run_container(
                "alpine",
                command=["echo", "test"],
                ports=PortMappings().add(port, port),
                remove=True
            )
            return True
        except ContainerException:
            return False
    
    def release_ports(self, instance_id: str):
        """Release all ports allocated to instance"""
        with self.lock:
            self.allocated = {
                p: (iid, ts) for p, (iid, ts) in self.allocated.items() 
                if iid != instance_id
            }
    
    def cleanup_stale_allocations(self, max_age_seconds=3600):
        """Remove allocations older than max_age_seconds"""
        with self.lock:
            cutoff = time.time() - max_age_seconds
            self.allocated = {
                p: (iid, ts) for p, (iid, ts) in self.allocated.items()
                if ts > cutoff
            }
```

### Learning #6: Container Lifecycle State Management

**File:** `localstack-core/localstack/utils/bootstrap.py`

```python
class Container:
    """Encapsulates container lifecycle"""
    
    def start(self, attach: bool = False) -> RunningContainer:
        cfg = copy.deepcopy(self.config)
        
        # Ensure network exists
        self._ensure_container_network(cfg.network)
        
        try:
            # Start container
            container_id = DOCKER_CLIENT.create_container(
                image_name=cfg.image_name,
                name=cfg.name,
                entrypoint=cfg.entrypoint,
                command=cfg.command,
                volumes=cfg.volumes.to_list(),
                ports=cfg.ports,
                env_vars=cfg.env_vars,
                network=cfg.network,
                privileged=cfg.privileged,
                remove=cfg.remove,
            )
            
            DOCKER_CLIENT.start_container(container_id)
            
            # Wait for container to be ready
            if not attach:
                self._wait_for_logs(container_id, timeout=30)
            
            return RunningContainer(container_id, self.config)
        
        except ContainerException as e:
            LOG.error("Failed to start container: %s", e)
            raise
    
    def stop(self, timeout: int = 10):
        """Stop the container"""
        try:
            DOCKER_CLIENT.stop_container(self.container_id, timeout=timeout)
        except NoSuchContainer:
            LOG.warning("Container %s does not exist", self.container_id)
```

**Application to GCS Compute:**
```python
# app/models/compute_instance.py
class ComputeInstance:
    """Model for compute instance state"""
    
    def __init__(self, name, zone, machine_type, account_id, project_id):
        self.name = name
        self.zone = zone
        self.machine_type = machine_type
        self.account_id = account_id
        self.project_id = project_id
        self.status = "PROVISIONING"  # PROVISIONING, STAGING, RUNNING, STOPPING, TERMINATED
        self.container_id = None
        self.creation_timestamp = datetime.utcnow()
        self.ports = []
        self.network_interfaces = []
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "zone": f"projects/{self.project_id}/zones/{self.zone}",
            "machineType": f"projects/{self.project_id}/zones/{self.zone}/machineTypes/{self.machine_type}",
            "status": self.status,
            "creationTimestamp": self.creation_timestamp.isoformat() + "Z",
            "networkInterfaces": self.network_interfaces,
        }

# app/services/compute_lifecycle_service.py
class ComputeLifecycleService:
    def __init__(self):
        self.instances = {}  # {instance_id: ComputeInstance}
        self.port_pool = ComputePortPool()
        self.network_mgr = ComputeNetworkManager()
    
    def create_instance(self, config):
        instance = ComputeInstance(
            name=config["name"],
            zone=config["zone"],
            machine_type=config["machineType"],
            account_id=config["account_id"],
            project_id=config["project_id"]
        )
        
        # Allocate ports
        instance.ports = self.port_pool.allocate_ports(instance.id, num_ports=2)
        
        # Create container
        container_config = self._build_container_config(instance)
        container_id = DOCKER_CLIENT.create_container(**container_config)
        instance.container_id = container_id
        instance.status = "STAGING"
        
        # Start container
        DOCKER_CLIENT.start_container(container_id)
        
        # Wait for ready (async in real implementation)
        if self._wait_for_container_ready(container_id, timeout=30):
            instance.status = "RUNNING"
            instance.network_interfaces = self._get_network_interfaces(container_id)
        
        self.instances[instance.id] = instance
        return instance
    
    def stop_instance(self, instance_id):
        instance = self.instances.get(instance_id)
        if not instance:
            raise InvalidInstanceError(instance_id)
        
        if instance.status != "RUNNING":
            raise InstanceNotReadyError(instance_id, instance.status)
        
        instance.status = "STOPPING"
        DOCKER_CLIENT.stop_container(instance.container_id, timeout=10)
        instance.status = "TERMINATED"
    
    def delete_instance(self, instance_id):
        instance = self.instances.get(instance_id)
        if not instance:
            raise InvalidInstanceError(instance_id)
        
        # Stop if running
        if instance.status == "RUNNING":
            self.stop_instance(instance_id)
        
        # Remove container
        try:
            DOCKER_CLIENT.remove_container(instance.container_id, force=True)
        except NoSuchContainer:
            pass
        
        # Release ports
        self.port_pool.release_ports(instance_id)
        
        # Remove from tracking
        del self.instances[instance_id]
```

### Learning #7: State Persistence & Recovery

**File:** `localstack-core/localstack/services/opensearch/provider.py`

```python
class OpensearchProvider(OpensearchApi, ServiceLifecycleHook):
    @staticmethod
    def get_store(account_id: str, region_name: str) -> OpenSearchStore:
        return opensearch_stores[account_id][region_name]
    
    def accept_state_visitor(self, visitor: StateVisitor):
        visitor.visit(opensearch_stores)
        visitor.visit(AssetDirectory(self.service, os.path.join(config.dirs.data, self.service)))
    
    def on_after_state_load(self):
        """Starts clusters whose metadata has been restored"""
        for account_id, region, store in opensearch_stores.iter_stores():
            for domain_name, domain_status in store.opensearch_domains.items():
                if domain_status.get("Processing"):
                    # Restart cluster after state load
                    self._start_cluster(domain_name, domain_status)
    
    def on_before_state_reset(self):
        self._stop_clusters()
    
    def _stop_clusters(self):
        for account_id, region, store in opensearch_stores.iter_stores():
            for domain_name in store.opensearch_domains.keys():
                cluster_manager().remove(DomainKey(domain_name, region, account_id).arn)
```

**Application to GCS Compute:**
```python
# app/services/compute_state_service.py
class ComputeStateManager:
    """Handles state persistence and recovery for compute instances"""
    
    def save_state(self):
        """Serialize all instance state to disk"""
        state = {
            "instances": {
                iid: instance.to_dict() 
                for iid, instance in self.lifecycle.instances.items()
            },
            "port_allocations": self.lifecycle.port_pool.allocated,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        state_file = os.path.join(config.STATE_DIR, "compute_instances.json")
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """Restore instance state from disk"""
        state_file = os.path.join(config.STATE_DIR, "compute_instances.json")
        if not os.path.exists(state_file):
            return
        
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        # Restore instances
        for iid, instance_data in state["instances"].items():
            instance = ComputeInstance.from_dict(instance_data)
            
            # Check if container still exists
            try:
                status = DOCKER_CLIENT.inspect_container(instance.container_id)
                if status["State"]["Running"]:
                    instance.status = "RUNNING"
                else:
                    # Container stopped - restart it
                    DOCKER_CLIENT.start_container(instance.container_id)
            except NoSuchContainer:
                # Container lost - recreate
                LOG.warning("Container %s lost, recreating instance %s", instance.container_id, iid)
                instance.status = "PROVISIONING"
                self.lifecycle._recreate_container(instance)
            
            self.lifecycle.instances[iid] = instance
        
        # Restore port allocations
        self.lifecycle.port_pool.allocated = state["port_allocations"]
    
    def on_shutdown(self):
        """Save state before shutdown"""
        self.save_state()
        
        # Optionally stop all containers
        for instance in self.lifecycle.instances.values():
            try:
                DOCKER_CLIENT.stop_container(instance.container_id)
            except Exception as e:
                LOG.error("Failed to stop container %s: %s", instance.container_id, e)
```

---

## Critical Implementation Patterns

### Pattern 1: Resource Provider State Machine

```
┌─────────────┐
│   CREATE    │ ── First Call ──► Start Operation
│   Request   │                   (return IN_PROGRESS)
└─────────────┘                          │
       │                                 │
       │                                 ▼
       │                        ┌──────────────┐
       └──── Poll ─────────────►│ Check Status │
                                 └──────────────┘
                                        │
                         ┌──────────────┴──────────────┐
                         │                             │
                    Still Pending              Operation Complete
                         │                             │
                         ▼                             ▼
                return IN_PROGRESS            return SUCCESS
                         │                             │
                         └──────────► Poll ◄───────────┘
```

### Pattern 2: Docker Container Management

```
Instance Request
    │
    ├── Validate Parameters
    │
    ├── Allocate Ports
    │
    ├── Create Container Config
    │       └── Image, Network, Volumes, Env Vars
    │
    ├── Create Container (PROVISIONING)
    │
    ├── Start Container (STAGING)
    │
    ├── Wait for Ready (health check)
    │
    └── Update Status (RUNNING)
```

### Pattern 3: Cleanup & Resource Tracking

```python
# LocalStack pattern for cleanup
class ServiceLifecycleHook:
    def on_before_stop(self):
        """Cleanup before service stops"""
        self._stop_all_containers()
    
    def on_before_state_reset(self):
        """Cleanup before state reset"""
        self._stop_all_containers()
        self._release_all_ports()
    
    def _stop_all_containers(self):
        for account_id, region, store in compute_stores.iter_stores():
            for instance in store.instances.values():
                try:
                    DOCKER_CLIENT.remove_container(instance.container_id, force=True)
                except Exception as e:
                    LOG.error("Failed to remove container: %s", e)
```

---

## Recommendations for GCS Compute Service

### 1. **Adopt Resource Provider Pattern**
- Implement `ComputeInstanceProvider` similar to `EC2InstanceProvider`
- Use state machine pattern for async operations
- Support CloudFormation-style progress tracking

### 2. **Implement Robust Port Management**
- Create dedicated `ComputePortPool` service
- Test port availability before allocation
- Implement stale allocation cleanup
- Reserve ports for lifecycle (not just creation)

### 3. **Network Isolation**
- Create dedicated `gcs-compute-net` Docker network
- Isolate compute instances from main GCS backend
- Implement proper DNS resolution for compute instances

### 4. **State Persistence**
- Persist instance metadata to disk/database
- Implement state recovery on restart
- Handle container loss gracefully (recreate vs mark failed)

### 5. **Lifecycle Hooks**
- Implement `on_before_stop()` for graceful shutdown
- Implement `on_before_state_reset()` for cleanup
- Support state snapshots for backups

### 6. **Error Handling**
- Define GCS-specific exception classes
- Return proper HTTP error codes
- Provide detailed error messages with context

### 7. **Container Health Monitoring**
- Implement health check endpoints
- Monitor container resource usage
- Auto-restart failed containers (with backoff)

---

## Testing Recommendations

### Unit Tests
```python
def test_instance_creation_state_machine():
    """Test that instance creation follows proper state transitions"""
    provider = ComputeInstanceProvider()
    
    # First call - should start creation
    result1 = provider.create_instance(config)
    assert result1["status"] == "PENDING"
    assert result1["operation_id"] is not None
    
    # Poll - should still be pending
    result2 = provider.get_operation(result1["operation_id"])
    assert result2["status"] in ["PENDING", "RUNNING"]
    
    # Wait for completion
    result3 = wait_for_operation(result1["operation_id"], timeout=30)
    assert result3["status"] == "RUNNING"
```

### Integration Tests
```python
def test_container_port_allocation():
    """Test that ports are properly allocated and released"""
    port_pool = ComputePortPool(start_port=50000, end_port=50100)
    
    # Allocate ports for instance 1
    ports1 = port_pool.allocate_ports("instance-1", num_ports=2)
    assert len(ports1) == 2
    assert all(50000 <= p <= 50100 for p in ports1)
    
    # Allocate ports for instance 2
    ports2 = port_pool.allocate_ports("instance-2", num_ports=2)
    assert len(ports2) == 2
    assert not set(ports1).intersection(set(ports2))  # No overlap
    
    # Release ports
    port_pool.release_ports("instance-1")
    
    # Should be able to reallocate released ports
    ports3 = port_pool.allocate_ports("instance-3", num_ports=2)
    assert len(ports3) == 2
```

### End-to-End Tests
```python
def test_full_instance_lifecycle():
    """Test complete lifecycle: create → start → stop → delete"""
    compute = ComputeService()
    
    # Create instance
    instance = compute.create_instance({
        "name": "test-instance",
        "zone": "us-central1-a",
        "machineType": "n1-standard-1"
    })
    assert instance["status"] == "RUNNING"
    
    # Verify container exists
    container_id = instance["container_id"]
    status = docker_client.inspect_container(container_id)
    assert status["State"]["Running"] is True
    
    # Stop instance
    compute.stop_instance(instance["id"])
    assert instance["status"] == "TERMINATED"
    
    # Delete instance
    compute.delete_instance(instance["id"])
    
    # Verify cleanup
    with pytest.raises(NoSuchContainer):
        docker_client.inspect_container(container_id)
```

---

## Risk Mitigation

### Risk #1: Port Exhaustion
**Mitigation:**
- Implement port recycling with age-based cleanup
- Monitor port pool usage (alert at 80% capacity)
- Support dynamic port range expansion

### Risk #2: Orphaned Containers
**Mitigation:**
- Background sync process (every 60s) to detect orphans
- Tag containers with metadata (instance_id, creation_time)
- Implement force-cleanup API endpoint

### Risk #3: Container Startup Failures
**Mitigation:**
- Implement retry logic with exponential backoff
- Capture container logs on failure
- Return detailed error messages to client

### Risk #4: Network Isolation Issues
**Mitigation:**
- Test network connectivity before marking instance as RUNNING
- Implement health check endpoints in compute containers
- Support custom DNS resolution

### Risk #5: State Inconsistency
**Mitigation:**
- Use database transactions for state updates
- Implement write-ahead logging for critical operations
- Support manual reconciliation via admin API

---

## Next Steps

1. **Create Database Schema** for compute instances
2. **Implement Port Pool Service** with allocation tracking
3. **Build Container Configuration Builder** with validation
4. **Implement State Machine** for async operations
5. **Add Lifecycle Hooks** for cleanup
6. **Write Comprehensive Tests** (unit, integration, e2e)
7. **Document API** with OpenAPI spec
8. **Performance Testing** (concurrent instance creation)

---

## Conclusion

LocalStack's EC2 implementation demonstrates that **you don't need actual compute emulation** for most use cases - state management and API compliance are sufficient. However, for GCS Compute, we want **real containers** to enable:

1. **Shared Storage Testing** - Verify actual file access patterns
2. **Networking Testing** - Test container-to-container communication
3. **Resource Constraints** - Simulate machine types with CPU/memory limits
4. **Real Workloads** - Support actual application deployment

The key is combining LocalStack's **state management patterns** with **actual Docker container orchestration** - best of both worlds.

---

**Generated:** December 9, 2025  
**Author:** GitHub Copilot (Claude Sonnet 4.5)  
**Reference Repository:** localstack/localstack (main)
