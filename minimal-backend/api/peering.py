"""VPC Peering API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime
from database import get_db, VPCPeering, Network, Route
from peering_manager import get_peering_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def get_docker_network_name(project_id: str, network_name: str) -> str:
    """Generate Docker network name"""
    name = f"{project_id}-{network_name}".lower().replace("_", "-")
    return name[:63]


def format_peering_response(peering: VPCPeering, project_id: str) -> Dict[str, Any]:
    """Format VPC peering as GCP API response"""
    return {
        "kind": "compute#networkPeering",
        "id": str(peering.id),
        "name": peering.name,
        "network": f"https://www.googleapis.com/compute/v1/projects/{project_id}/global/networks/{peering.local_network}",
        "peeredNetwork": f"https://www.googleapis.com/compute/v1/projects/{peering.peer_project_id}/global/networks/{peering.peer_network}",
        "state": peering.state,
        "stateDetails": peering.state_details,
        "autoCreateRoutes": peering.auto_create_routes,
        "exportCustomRoutes": peering.export_custom_routes,
        "importCustomRoutes": peering.import_custom_routes,
        "exportSubnetRoutesWithPublicIp": peering.export_subnet_routes_with_public_ip,
        "importSubnetRoutesWithPublicIp": peering.import_subnet_routes_with_public_ip,
        "creationTimestamp": peering.created_at.isoformat() + "Z" if peering.created_at else "",
        "selfLink": f"https://www.googleapis.com/compute/v1/projects/{project_id}/global/networks/{peering.local_network}/peerings/{peering.name}"
    }


@router.post("/compute/v1/projects/{project}/global/networks/{network}/peerings")
def create_peering(
    project: str,
    network: str,
    db: Session = Depends(get_db),
    peering_data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """
    Create a new VPC peering connection
    
    Expected body:
    {
        "name": "peering-name",
        "targetNetwork": "projects/target-project/global/networks/peer-network",
        "autoCreateRoutes": true
    }
    """
    try:
        # Validate source network exists
        source_net = db.query(Network).filter(
            Network.project_id == project,
            Network.name == network
        ).first()
        
        if not source_net:
            raise HTTPException(status_code=404, detail=f"Network '{network}' not found in project '{project}'")
        
        # Parse target network
        target_network = peering_data.get("targetNetwork", "")
        # Extract target project and network from format: "projects/target-project/global/networks/peer-network"
        parts = target_network.split("/")
        if len(parts) != 5:
            raise HTTPException(status_code=400, detail="Invalid targetNetwork format")
        
        target_project = parts[1]
        target_net_name = parts[4]
        
        # Validate target network exists
        target_net = db.query(Network).filter(
            Network.project_id == target_project,
            Network.name == target_net_name
        ).first()
        
        if not target_net:
            raise HTTPException(
                status_code=404,
                detail=f"Target network '{target_net_name}' not found in project '{target_project}'"
            )
        
        # Validate CIDRs don't overlap
        peering_manager = get_peering_manager()
        if not peering_manager.validate_cidrs_dont_overlap(source_net.cidr_range, target_net.cidr_range):
            raise HTTPException(
                status_code=409,
                detail=f"Network CIDRs overlap: {source_net.cidr_range} and {target_net.cidr_range}"
            )
        
        peering_name = peering_data.get("name", f"{network}-{target_net_name}")
        auto_create_routes = peering_data.get("autoCreateRoutes", True)
        
        # Check if peering already exists
        existing = db.query(VPCPeering).filter(
            VPCPeering.project_id == project,
            VPCPeering.local_network == network,
            VPCPeering.peer_network == target_net_name,
            VPCPeering.peer_project_id == target_project
        ).first()
        
        if existing:
            raise HTTPException(status_code=409, detail="Peering already exists between these networks")
        
        # Create bidirectional peering records
        peering_forward = VPCPeering(
            name=peering_name,
            project_id=project,
            local_network=network,
            peer_network=target_net_name,
            peer_project_id=target_project,
            state="ACTIVE",
            auto_create_routes=auto_create_routes
        )
        
        peering_reverse = VPCPeering(
            name=f"{target_net_name}-{network}",
            project_id=target_project,
            local_network=target_net_name,
            peer_network=network,
            peer_project_id=project,
            state="ACTIVE",
            auto_create_routes=auto_create_routes
        )
        
        db.add(peering_forward)
        db.add(peering_reverse)
        db.flush()
        
        # Create auto routes if enabled
        if auto_create_routes:
            # Route from source network to target network
            route_forward = Route(
                name=f"{peering_name}-route",
                network=network,
                project_id=project,
                description=f"Auto-created route for peering {peering_name}",
                dest_range=target_net.cidr_range,
                next_hop_network=target_net_name,
                priority=1000
            )
            
            # Route from target network to source network
            route_reverse = Route(
                name=f"{target_net_name}-{network}-route",
                network=target_net_name,
                project_id=target_project,
                description=f"Auto-created route for peering {peering_reverse.name}",
                dest_range=source_net.cidr_range,
                next_hop_network=network,
                priority=1000
            )
            
            db.add(route_forward)
            db.add(route_reverse)
        
        db.commit()
        
        # Establish Docker network connections
        local_docker_net = get_docker_network_name(project, network)
        peer_docker_net = get_docker_network_name(target_project, target_net_name)
        
        if not peering_manager.connect_docker_networks(local_docker_net, peer_docker_net):
            logger.warning(f"Failed to establish Docker network connections for peering {peering_name}")
            # Continue anyway - DB is already updated
        
        logger.info(f"✅ Created VPC peering: {peering_name}")
        return {
            "kind": "compute#operation",
            "id": f"peering-{peering_forward.id}",
            "name": f"operation-peering-{peering_forward.id}",
            "status": "DONE",
            "operationType": "compute.networkPeerings.create",
            "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{network}/peerings/{peering_name}",
            "insertTime": datetime.utcnow().isoformat() + "Z",
            "startTime": datetime.utcnow().isoformat() + "Z",
            "endTime": datetime.utcnow().isoformat() + "Z",
            "progress": 100
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating peering: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compute/v1/projects/{project}/global/networks/{network}/peerings")
def list_peerings(project: str, network: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """List all peering connections for a network"""
    try:
        # Validate network exists
        net = db.query(Network).filter(
            Network.project_id == project,
            Network.name == network
        ).first()
        
        if not net:
            raise HTTPException(status_code=404, detail=f"Network '{network}' not found")
        
        # Get all peerings for this network
        peerings = db.query(VPCPeering).filter(
            VPCPeering.project_id == project,
            VPCPeering.local_network == network
        ).all()
        
        return {
            "kind": "compute#networkPeeringList",
            "id": f"projects/{project}/global/networks/{network}/peerings",
            "items": [format_peering_response(p, project) for p in peerings]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing peerings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compute/v1/projects/{project}/global/networks/{network}/peerings/{peering_name}")
def get_peering(
    project: str,
    network: str,
    peering_name: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get a specific peering connection"""
    try:
        peering = db.query(VPCPeering).filter(
            VPCPeering.project_id == project,
            VPCPeering.local_network == network,
            VPCPeering.name == peering_name
        ).first()
        
        if not peering:
            raise HTTPException(status_code=404, detail=f"Peering '{peering_name}' not found")
        
        # Get routes for this peering
        routes = db.query(Route).filter(
            Route.project_id == project,
            Route.network == network,
            Route.next_hop_network == peering.peer_network
        ).all()
        
        response = format_peering_response(peering, project)
        response["routes"] = [
            {
                "name": r.name,
                "destRange": r.dest_range,
                "nextHopNetwork": r.next_hop_network,
                "priority": r.priority
            }
            for r in routes
        ]
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting peering: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/compute/v1/projects/{project}/global/networks/{network}/peerings/{peering_name}")
def delete_peering(
    project: str,
    network: str,
    peering_name: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Delete a peering connection"""
    try:
        peering = db.query(VPCPeering).filter(
            VPCPeering.project_id == project,
            VPCPeering.local_network == network,
            VPCPeering.name == peering_name
        ).first()
        
        if not peering:
            raise HTTPException(status_code=404, detail=f"Peering '{peering_name}' not found")
        
        peer_network = peering.peer_network
        peer_project = peering.peer_project_id
        
        # Delete routes associated with this peering
        db.query(Route).filter(
            Route.project_id == project,
            Route.network == network,
            Route.next_hop_network == peer_network
        ).delete()
        
        # Delete reverse routes
        db.query(Route).filter(
            Route.project_id == peer_project,
            Route.network == peer_network,
            Route.next_hop_network == network
        ).delete()
        
        # Delete the reverse peering record
        reverse_peering = db.query(VPCPeering).filter(
            VPCPeering.project_id == peer_project,
            VPCPeering.local_network == peer_network,
            VPCPeering.peer_network == network
        ).first()
        
        if reverse_peering:
            db.delete(reverse_peering)
        
        # Delete the peering
        db.delete(peering)
        db.commit()
        
        # Disconnect Docker networks
        peering_manager = get_peering_manager()
        local_docker_net = get_docker_network_name(project, network)
        peer_docker_net = get_docker_network_name(peer_project, peer_network)
        
        if not peering_manager.disconnect_docker_networks(local_docker_net, peer_docker_net):
            logger.warning(f"Failed to disconnect Docker networks for deleted peering {peering_name}")
        
        logger.info(f"✅ Deleted VPC peering: {peering_name}")
        return {
            "kind": "compute#operation",
            "id": f"peering-delete-{peering.id}",
            "name": f"operation-peering-delete-{peering.id}",
            "status": "DONE",
            "operationType": "compute.networkPeerings.delete",
            "targetLink": f"https://www.googleapis.com/compute/v1/projects/{project}/global/networks/{network}/peerings/{peering_name}",
            "insertTime": datetime.utcnow().isoformat() + "Z",
            "startTime": datetime.utcnow().isoformat() + "Z",
            "endTime": datetime.utcnow().isoformat() + "Z",
            "progress": 100
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting peering: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/compute/v1/projects/{project}/global/networks/{network}/peerings/{peering_name}")
def update_peering(
    project: str,
    network: str,
    peering_name: str,
    db: Session = Depends(get_db),
    update_data: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Update peering settings (import/export routes)"""
    try:
        peering = db.query(VPCPeering).filter(
            VPCPeering.project_id == project,
            VPCPeering.local_network == network,
            VPCPeering.name == peering_name
        ).first()
        
        if not peering:
            raise HTTPException(status_code=404, detail=f"Peering '{peering_name}' not found")
        
        # Update configurable fields
        if "exportCustomRoutes" in update_data:
            peering.export_custom_routes = update_data["exportCustomRoutes"]
        if "importCustomRoutes" in update_data:
            peering.import_custom_routes = update_data["importCustomRoutes"]
        if "exportSubnetRoutesWithPublicIp" in update_data:
            peering.export_subnet_routes_with_public_ip = update_data["exportSubnetRoutesWithPublicIp"]
        if "importSubnetRoutesWithPublicIp" in update_data:
            peering.import_subnet_routes_with_public_ip = update_data["importSubnetRoutesWithPublicIp"]
        
        db.commit()
        
        logger.info(f"✅ Updated VPC peering: {peering_name}")
        return format_peering_response(peering, project)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating peering: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
