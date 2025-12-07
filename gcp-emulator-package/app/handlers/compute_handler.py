"""
Compute Engine handlers - HTTP request/response logic
Phase 2: GCE-compliant API responses with proper error handling
"""
import time
from flask import jsonify, request
from app.services.compute_service import (
    ComputeService,
    InvalidStateError,
    InstanceNotFoundError,
    InstanceAlreadyExistsError,
    DockerExecutionError
)
from app.utils.gcs_errors import (
    invalid_argument_error,
    not_found_error,
    conflict_error,
    internal_error
)
from app.logging import log_handler_stage


def handle_create_instance(project, zone):
    """
    Handle POST /compute/v1/projects/{project}/zones/{zone}/instances
    Create a new instance
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handling create instance request",
        details={"project": project, "zone": zone}
    )
    
    try:
        data = request.get_json()
        if not data:
            return invalid_argument_error("Request body is required")
        
        # Extract instance name
        name = data.get("name")
        if not name:
            return invalid_argument_error("Instance name is required")
        
        # Extract machine type (may be full path or just type name)
        machine_type_raw = data.get("machineType")
        if not machine_type_raw:
            return invalid_argument_error("machineType is required")
        
        # Extract just the machine type name from full path if needed
        # GCE format: zones/{zone}/machineTypes/{type}
        if "/" in machine_type_raw:
            machine_type = machine_type_raw.split("/")[-1]
        else:
            machine_type = machine_type_raw
        
        # Extract metadata (GCE format: {items: [{key, value}]})
        metadata_dict = {}
        if "metadata" in data and "items" in data["metadata"]:
            for item in data["metadata"]["items"]:
                if "key" in item and "value" in item:
                    metadata_dict[item["key"]] = item["value"]
        
        # Extract labels
        labels = data.get("labels", {})
        
        # Extract tags (GCE format: {items: [...]})
        tags = []
        if "tags" in data and "items" in data["tags"]:
            tags = data["tags"]["items"]
        
        # Create instance
        instance = ComputeService.create_instance(
            project_id=project,
            zone=zone,
            name=name,
            machine_type=machine_type,
            metadata=metadata_dict,
            labels=labels,
            tags=tags,
            network_interfaces=data.get("networkInterfaces", []),
            disks=data.get("disks", [])
        )
        
        # Return GCE operation response
        operation = {
            "kind": "compute#operation",
            "id": instance.id,
            "name": f"operation-create-{instance.name}",
            "zone": f"projects/{project}/zones/{zone}",
            "operationType": "insert",
            "targetLink": f"projects/{project}/zones/{zone}/instances/{instance.name}",
            "status": "DONE",
            "progress": 100,
            "insertTime": instance.creation_timestamp.isoformat() + "Z",
            "startTime": instance.creation_timestamp.isoformat() + "Z",
            "endTime": instance.creation_timestamp.isoformat() + "Z",
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/operation-create-{instance.name}"
        }
        
        log_handler_stage(
            message="Instance created successfully",
            details={
                "instance_id": instance.id,
                "instance_name": instance.name,
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return jsonify(operation), 200
        
    except InstanceAlreadyExistsError as e:
        log_handler_stage(
            message="Instance already exists",
            details={"error": str(e)},
            level="WARNING"
        )
        return conflict_error(str(e))
        
    except ValueError as e:
        log_handler_stage(
            message="Invalid request parameters",
            details={"error": str(e)},
            level="WARNING"
        )
        return invalid_argument_error(str(e))
    
    except DockerExecutionError as e:
        log_handler_stage(
            message="Docker operation failed during instance creation",
            details={"error": str(e)},
            level="ERROR"
        )
        return internal_error(f"Docker operation failed: {str(e)}")
        
    except Exception as e:
        log_handler_stage(
            message="Unexpected error creating instance",
            details={"error": str(e)},
            level="ERROR"
        )
        return internal_error(str(e))


def handle_list_instances(project, zone):
    """
    Handle GET /compute/v1/projects/{project}/zones/{zone}/instances
    List instances
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handling list instances request",
        details={"project": project, "zone": zone}
    )
    
    try:
        # List instances
        instances = ComputeService.list_instances(project, zone)
        
        # Convert to GCE format
        items = [instance.to_dict() for instance in instances]
        
        response = {
            "kind": "compute#instanceList",
            "id": f"projects/{project}/zones/{zone}/instances",
            "items": items,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances"
        }
        
        log_handler_stage(
            message="Instances listed successfully",
            details={
                "count": len(items),
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return jsonify(response), 200
        
    except Exception as e:
        log_handler_stage(
            message="Unexpected error listing instances",
            details={"error": str(e)},
            level="ERROR"
        )
        return internal_error(str(e))


def handle_get_instance(project, zone, name):
    """
    Handle GET /compute/v1/projects/{project}/zones/{zone}/instances/{name}
    Get instance details
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handling get instance request",
        details={"project": project, "zone": zone, "name": name}
    )
    
    try:
        instance = ComputeService.get_instance(project, zone, name)
        
        log_handler_stage(
            message="Instance retrieved successfully",
            details={
                "instance_id": instance.id,
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return jsonify(instance.to_dict()), 200
        
    except InstanceNotFoundError as e:
        log_handler_stage(
            message="Instance not found",
            details={"error": str(e)},
            level="WARNING"
        )
        return not_found_error(str(e))
        
    except Exception as e:
        log_handler_stage(
            message="Unexpected error getting instance",
            details={"error": str(e)},
            level="ERROR"
        )
        return internal_error(str(e))


def handle_start_instance(project, zone, name):
    """
    Handle POST /compute/v1/projects/{project}/zones/{zone}/instances/{name}/start
    Start an instance
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handling start instance request",
        details={"project": project, "zone": zone, "name": name}
    )
    
    try:
        instance = ComputeService.start_instance(project, zone, name)
        
        # Return GCE operation response
        operation = {
            "kind": "compute#operation",
            "id": instance.id,
            "name": f"operation-start-{instance.name}",
            "zone": f"projects/{project}/zones/{zone}",
            "operationType": "start",
            "targetLink": f"projects/{project}/zones/{zone}/instances/{instance.name}",
            "status": "DONE",
            "progress": 100,
            "insertTime": instance.last_start_timestamp.isoformat() + "Z" if instance.last_start_timestamp else None,
            "startTime": instance.last_start_timestamp.isoformat() + "Z" if instance.last_start_timestamp else None,
            "endTime": instance.last_start_timestamp.isoformat() + "Z" if instance.last_start_timestamp else None,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/operation-start-{instance.name}"
        }
        
        log_handler_stage(
            message="Instance started successfully",
            details={
                "instance_id": instance.id,
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return jsonify(operation), 200
        
    except InstanceNotFoundError as e:
        log_handler_stage(
            message="Instance not found",
            details={"error": str(e)},
            level="WARNING"
        )
        return not_found_error(str(e))
        
    except InvalidStateError as e:
        log_handler_stage(
            message="Invalid state for start operation",
            details={"error": str(e)},
            level="WARNING"
        )
        return invalid_argument_error(str(e))
    
    except DockerExecutionError as e:
        log_handler_stage(
            message="Docker operation failed during instance start",
            details={"error": str(e)},
            level="ERROR"
        )
        return internal_error(f"Docker operation failed: {str(e)}")
        
    except Exception as e:
        log_handler_stage(
            message="Unexpected error starting instance",
            details={"error": str(e)},
            level="ERROR"
        )
        return internal_error(str(e))


def handle_stop_instance(project, zone, name):
    """
    Handle POST /compute/v1/projects/{project}/zones/{zone}/instances/{name}/stop
    Stop an instance
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handling stop instance request",
        details={"project": project, "zone": zone, "name": name}
    )
    
    try:
        instance = ComputeService.stop_instance(project, zone, name)
        
        # Return GCE operation response
        operation = {
            "kind": "compute#operation",
            "id": instance.id,
            "name": f"operation-stop-{instance.name}",
            "zone": f"projects/{project}/zones/{zone}",
            "operationType": "stop",
            "targetLink": f"projects/{project}/zones/{zone}/instances/{instance.name}",
            "status": "DONE",
            "progress": 100,
            "insertTime": instance.last_stop_timestamp.isoformat() + "Z" if instance.last_stop_timestamp else None,
            "startTime": instance.last_stop_timestamp.isoformat() + "Z" if instance.last_stop_timestamp else None,
            "endTime": instance.last_stop_timestamp.isoformat() + "Z" if instance.last_stop_timestamp else None,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/operation-stop-{instance.name}"
        }
        
        log_handler_stage(
            message="Instance stopped successfully",
            details={
                "instance_id": instance.id,
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return jsonify(operation), 200
        
    except InstanceNotFoundError as e:
        log_handler_stage(
            message="Instance not found",
            details={"error": str(e)},
            level="WARNING"
        )
        return not_found_error(str(e))
        
    except InvalidStateError as e:
        log_handler_stage(
            message="Invalid state for stop operation",
            details={"error": str(e)},
            level="WARNING"
        )
        return invalid_argument_error(str(e))
    
    except DockerExecutionError as e:
        log_handler_stage(
            message="Docker operation failed during instance stop",
            details={"error": str(e)},
            level="ERROR"
        )
        return internal_error(f"Docker operation failed: {str(e)}")
        
    except Exception as e:
        log_handler_stage(
            message="Unexpected error stopping instance",
            details={"error": str(e)},
            level="ERROR"
        )
        return internal_error(str(e))


def handle_delete_instance(project, zone, name):
    """
    Handle DELETE /compute/v1/projects/{project}/zones/{zone}/instances/{name}
    Delete an instance
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handling delete instance request",
        details={"project": project, "zone": zone, "name": name}
    )
    
    try:
        instance = ComputeService.delete_instance(project, zone, name)
        
        # Return GCE operation response
        operation = {
            "kind": "compute#operation",
            "id": instance.id,
            "name": f"operation-delete-{instance.name}",
            "zone": f"projects/{project}/zones/{zone}",
            "operationType": "delete",
            "targetLink": f"projects/{project}/zones/{zone}/instances/{instance.name}",
            "status": "DONE",
            "progress": 100,
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/operation-delete-{instance.name}"
        }
        
        log_handler_stage(
            message="Instance deleted successfully",
            details={
                "instance_id": instance.id,
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return jsonify(operation), 200
        
    except InstanceNotFoundError as e:
        log_handler_stage(
            message="Instance not found",
            details={"error": str(e)},
            level="WARNING"
        )
        return not_found_error(str(e))
    
    except DockerExecutionError as e:
        log_handler_stage(
            message="Docker operation failed during instance deletion",
            details={"error": str(e)},
            level="ERROR"
        )
        return internal_error(f"Docker operation failed: {str(e)}")
        
    except Exception as e:
        log_handler_stage(
            message="Unexpected error deleting instance",
            details={"error": str(e)},
            level="ERROR"
        )
        return internal_error(str(e))


def handle_get_serial_port_output(project, zone, name):
    """
    Handle GET /compute/v1/projects/{project}/zones/{zone}/instances/{name}/serialPort
    Get serial port output
    """
    start_time = time.time()
    
    log_handler_stage(
        message="Handling get serial port output request",
        details={"project": project, "zone": zone, "name": name}
    )
    
    try:
        port = request.args.get("port", 1, type=int)
        start_pos = request.args.get("start", 0, type=int)
        
        output = ComputeService.get_instance_serial_port_output(
            project, zone, name, port, start_pos
        )
        
        response = {
            "kind": "compute#serialPortOutput",
            "contents": output,
            "start": start_pos,
            "next": start_pos + len(output),
            "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{name}/serialPort?port={port}&start={start_pos}"
        }
        
        log_handler_stage(
            message="Serial port output retrieved",
            details={
                "duration_ms": (time.time() - start_time) * 1000
            }
        )
        
        return jsonify(response), 200
        
    except InstanceNotFoundError as e:
        return not_found_error(str(e))
        
    except Exception as e:
        return internal_error(str(e))
