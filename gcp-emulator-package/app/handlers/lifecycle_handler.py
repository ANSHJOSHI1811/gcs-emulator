"""
Lifecycle Handler - Phase 4

Endpoints for lifecycle rule management and evaluation.
"""
from flask import Blueprint, jsonify, request
from app.services.lifecycle_service import LifecycleService

lifecycle_bp = Blueprint("lifecycle", __name__, url_prefix="/internal/lifecycle")


@lifecycle_bp.route("/rules", methods=["POST"])
def create_lifecycle_rule():
    """
    Create lifecycle rule
    
    POST /internal/lifecycle/rules
    Body: {
        "bucket": "bucket-name",
        "action": "Delete" | "Archive",
        "ageDays": 30
    }
    """
    data = request.get_json()
    
    bucket_name = data.get("bucket")
    action = data.get("action")
    age_days = data.get("ageDays")
    
    if not all([bucket_name, action, age_days is not None]):
        return jsonify({"error": "Missing required fields: bucket, action, ageDays"}), 400
    
    try:
        rule = LifecycleService.create_rule(bucket_name, action, age_days)
        return jsonify({
            "kind": "storage#lifecycleRule",
            "ruleId": rule.rule_id,
            "bucket": bucket_name,
            "action": rule.action,
            "ageDays": rule.age_days,
            "createdAt": rule.created_at.isoformat() + "Z"
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@lifecycle_bp.route("/rules", methods=["GET"])
def list_lifecycle_rules():
    """
    List lifecycle rules
    
    GET /internal/lifecycle/rules?bucket=bucket-name (optional)
    """
    bucket_name = request.args.get("bucket")
    
    try:
        rules = LifecycleService.list_rules(bucket_name)
        
        return jsonify({
            "kind": "storage#lifecycleRules",
            "items": [
                {
                    "ruleId": rule.rule_id,
                    "bucket": bucket_name or rule.bucket.name,
                    "action": rule.action,
                    "ageDays": rule.age_days,
                    "createdAt": rule.created_at.isoformat() + "Z"
                }
                for rule in rules
            ]
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@lifecycle_bp.route("/rules/<rule_id>", methods=["DELETE"])
def delete_lifecycle_rule(rule_id):
    """
    Delete lifecycle rule
    
    DELETE /internal/lifecycle/rules/{ruleId}
    """
    try:
        LifecycleService.delete_rule(rule_id)
        return jsonify({"message": "Rule deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@lifecycle_bp.route("/evaluate", methods=["POST"])
def evaluate_lifecycle():
    """
    Evaluate lifecycle rules (manual trigger)
    
    POST /internal/lifecycle/evaluate
    
    Returns:
        Summary of actions taken
    """
    try:
        results = LifecycleService.evaluate_all_rules()
        
        return jsonify({
            "kind": "storage#lifecycleEvaluation",
            "rulesEvaluated": results["rulesEvaluated"],
            "objectsDeleted": results["objectsDeleted"],
            "objectsArchived": results["objectsArchived"],
            "timestamp": request.environ.get("request_start_time", "").isoformat() + "Z" if hasattr(request.environ.get("request_start_time", ""), "isoformat") else None,
            "details": results["details"]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
