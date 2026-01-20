"""
PHASE 1: Compute Sync Worker
Background thread to synchronize instance states with Docker (runs every 5 seconds)
"""
import threading
import time
import logging
from typing import Optional

from app.models.instance import Instance

logger = logging.getLogger(__name__)

# Global worker state
_sync_worker_thread: Optional[threading.Thread] = None
_sync_worker_running = False


def start_compute_sync_worker(app, compute_service, interval: int = 5):
    """
    Start the background sync worker thread (PHASE 1)
    
    Args:
        app: Flask application instance
        compute_service: ComputeService instance
        interval: Sync interval in seconds (default: 5)
    """
    global _sync_worker_thread, _sync_worker_running
    
    if _sync_worker_running:
        logger.warning("Compute sync worker already running")
        return
    
    _sync_worker_running = True
    _sync_worker_thread = threading.Thread(
        target=_sync_worker_loop,
        args=(app, compute_service, interval),
        daemon=True,
        name="ComputeSyncWorker"
    )
    _sync_worker_thread.start()
    logger.info(f"PHASE 1: Started compute sync worker (interval: {interval}s)")


def stop_compute_sync_worker():
    """
    Stop the background sync worker thread
    """
    global _sync_worker_running
    
    if not _sync_worker_running:
        return
    
    _sync_worker_running = False
    logger.info("Stopping compute sync worker...")
    
    # Wait for thread to finish (with timeout)
    if _sync_worker_thread and _sync_worker_thread.is_alive():
        _sync_worker_thread.join(timeout=5)
    
    logger.info("Compute sync worker stopped")


def is_worker_running() -> bool:
    """
    Check if worker is running
    
    Returns:
        True if running, False otherwise
    """
    return _sync_worker_running


def _sync_worker_loop(app, compute_service, interval: int):
    """
    Main loop for sync worker (PHASE 1)
    
    Args:
        app: Flask application instance
        compute_service: ComputeService instance
        interval: Sync interval in seconds
    """
    logger.info("Compute sync worker loop started")
    
    while _sync_worker_running:
        try:
            with app.app_context():
                _sync_all_instances(compute_service)
        except Exception as e:
            logger.error(f"Error in compute sync worker: {e}", exc_info=True)
        
        # Sleep in small increments to allow quick shutdown
        for _ in range(interval):
            if not _sync_worker_running:
                break
            time.sleep(1)
    
    logger.info("Compute sync worker loop exited")


def _sync_all_instances(compute_service):
    """
    Synchronize all non-terminated instances with Docker container states
    
    Args:
        compute_service: ComputeService instance
    """
    try:
        # Get all instances that are running or pending
        instances = Instance.query.filter(
            Instance.state.in_(['pending', 'running', 'stopping', 'stopped'])
        ).all()
        
        if not instances:
            return
        
        logger.debug(f"Syncing {len(instances)} instances...")
        
        synced_count = 0
        for instance in instances:
            try:
                if compute_service.sync_instance_state(instance):
                    synced_count += 1
            except Exception as e:
                logger.error(f"Failed to sync instance {instance.id}: {e}")
        
        if synced_count > 0:
            logger.info(f"Synced {synced_count} instance states")
            
    except Exception as e:
        logger.error(f"Error in _sync_all_instances: {e}", exc_info=True)
