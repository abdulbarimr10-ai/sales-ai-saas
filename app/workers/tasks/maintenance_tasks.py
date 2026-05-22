from app.workers.celery_app import celery_app
from database.models import supabase
from app.core.logging import logger
from datetime import datetime, timedelta

@celery_app.task
def cleanup_expired_sessions_task():
    """Runs daily to remove old sessions from PostgreSQL"""
    if not supabase:
        return False
    try:
        now = datetime.utcnow().isoformat()
        # Delete sessions expired more than 1 day ago
        supabase.table('sessions').delete().lt('expires_at', now).execute()
        logger.info("Cleaned up expired sessions")
        return True
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return False

# Setup Periodic Tasks (Beat)
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run every day at midnight
    sender.add_periodic_task(
        86400.0,
        cleanup_expired_sessions_task.s(),
        name='cleanup_sessions_daily'
    )
