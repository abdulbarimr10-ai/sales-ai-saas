from app.workers.celery_app import celery_app
from app.services.email_service import email_service
from database.models import supabase
from app.core.logging import logger
from datetime import datetime

@celery_app.task(bind=True, max_retries=3)
def send_email_task(self, user_id: int, to_email: str, subject: str, body: str, job_id: str = None):
    """
    Sends an email using the user's secure Gmail credentials.
    Retries transient errors up to 3 times with exponential backoff.
    """
    if job_id and supabase:
        supabase.table('job_runs').update({'status': 'running', 'started_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()

    try:
        success = email_service.send_user_email(user_id, to_email, subject, body)
        if not success:
            raise Exception("Email service returned false")
            
        if job_id and supabase:
            supabase.table('job_runs').update({'status': 'completed', 'completed_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()
        return True

    except Exception as exc:
        logger.error(f"Email task failed: {exc}")
        
        # Determine if it's a transient failure (e.g., Timeout) vs Hard (e.g., Auth failure)
        # For simplicity, we assume we retry most network/API exceptions
        error_msg = str(exc)
        if "invalid_grant" in error_msg or "unauthorized" in error_msg.lower():
            # Hard failure - token revoked, don't retry
            if job_id and supabase:
                supabase.table('job_runs').update({'status': 'failed', 'error_message': 'Authentication revoked. Please reconnect Gmail.', 'completed_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()
            return False
            
        # Transient failure, trigger retry
        if job_id and supabase:
            supabase.table('job_runs').update({'status': 'retrying', 'retry_count': self.request.retries + 1}).eq('id', job_id).execute()
            
        # Exponential backoff: 10s, 30s, 90s
        countdown = 10 * (3 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)
