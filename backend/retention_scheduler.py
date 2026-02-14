"""
Retention Policy Scheduler
Runs hourly cleanup of old logs based on retention policies
"""

import threading
import time
import schedule
import logging
from database import (
    apply_retention_policies,
    create_retention_run,
    update_retention_run,
)

logger = logging.getLogger(__name__)

# Global flag to track if scheduler is running
_scheduler_running = False
_scheduler_thread = None


def run_retention_cleanup():
    """Execute retention cleanup - called by scheduler"""
    global _scheduler_running

    if _scheduler_running:
        logger.warning("Retention cleanup already running, skipping this run")
        return

    _scheduler_running = True
    run_id = None

    try:
        logger.info("Starting automatic retention cleanup")
        run_id = create_retention_run(trigger_type="automatic", user_id=None)

        # Apply all retention policies
        results = apply_retention_policies()
        total_deleted = sum(results.values())

        logger.info(f"Retention cleanup completed: {total_deleted} logs deleted")
        logger.debug(f"Cleanup results: {results}")

        update_retention_run(run_id, "completed", total_deleted, None)

    except Exception as e:
        error_msg = f"Retention cleanup failed: {str(e)}"
        logger.error(error_msg, exc_info=True)

        if run_id:
            update_retention_run(run_id, "failed", 0, error_msg)

    finally:
        _scheduler_running = False


def run_scheduler_loop():
    """Background thread that runs the scheduler"""
    logger.info("Retention scheduler thread started")

    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            time.sleep(60)


def start_retention_scheduler():
    """Start the retention policy scheduler"""
    global _scheduler_thread

    if _scheduler_thread and _scheduler_thread.is_alive():
        logger.warning("Retention scheduler already running")
        return

    # Schedule hourly cleanup at the top of each hour
    schedule.every().hour.at(":00").do(run_retention_cleanup)

    logger.info("Scheduling retention cleanup to run every hour")

    # Start background thread
    _scheduler_thread = threading.Thread(
        target=run_scheduler_loop, daemon=True, name="RetentionScheduler"
    )
    _scheduler_thread.start()

    logger.info("Retention scheduler started successfully")


def stop_retention_scheduler():
    """Stop the retention scheduler (mainly for testing)"""
    global _scheduler_thread

    schedule.clear()
    logger.info("Retention scheduler stopped")

    if _scheduler_thread:
        _scheduler_thread = None
