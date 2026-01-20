"""
Operation Routes

Routes for operation polling (required for Terraform).
"""

from flask import Blueprint
from app.handlers import operation_handler

operations_bp = Blueprint("operations", __name__)


# Global operations
@operations_bp.route("/compute/v1/projects/<project>/global/operations/<operation>", methods=["GET"])
def get_global_operation(project, operation):
    """Get global operation details"""
    return operation_handler.get_global_operation(project, operation)


@operations_bp.route("/compute/v1/projects/<project>/global/operations", methods=["GET"])
def list_global_operations(project):
    """List all global operations"""
    return operation_handler.list_global_operations(project)


# Regional operations
@operations_bp.route("/compute/v1/projects/<project>/regions/<region>/operations/<operation>", methods=["GET"])
def get_regional_operation(project, region, operation):
    """Get regional operation details"""
    return operation_handler.get_regional_operation(project, region, operation)


@operations_bp.route("/compute/v1/projects/<project>/regions/<region>/operations", methods=["GET"])
def list_regional_operations(project, region):
    """List all regional operations"""
    return operation_handler.list_regional_operations(project, region)


# Zonal operations
@operations_bp.route("/compute/v1/projects/<project>/zones/<zone>/operations/<operation>", methods=["GET"])
def get_zonal_operation(project, zone, operation):
    """Get zonal operation details"""
    return operation_handler.get_zonal_operation(project, zone, operation)


@operations_bp.route("/compute/v1/projects/<project>/zones/<zone>/operations", methods=["GET"])
def list_zonal_operations(project, zone):
    """List all zonal operations"""
    return operation_handler.list_zonal_operations(project, zone)
