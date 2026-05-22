from app.workers.celery_app import celery_app
from database.models import supabase
from app.core.logging import logger
from datetime import datetime
from tools.auto_outreach import generate_and_send_email
from app.services.llm.exceptions import ProviderTimeoutError, ProviderRateLimitError

@celery_app.task(bind=True, max_retries=2)
def run_outreach_campaign_task(self, user_id: int, lead_id: int, lead_data: dict, job_id: str = None):
    if job_id and supabase:
        supabase.table('job_runs').update({'status': 'running', 'started_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()

    try:
        # Re-use existing outreach pipeline logic, passing user_id down
        success = generate_and_send_email(lead_data, user_id=user_id)
        
        if success and supabase:
            supabase.table('leads').update({'status': 'Outreached'}).eq('id', lead_id).execute()
            if job_id:
                supabase.table('job_runs').update({'status': 'completed', 'completed_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()
            return True
        else:
            raise Exception("generate_and_send_email returned False")

    except (ProviderTimeoutError, ProviderRateLimitError) as exc:
        logger.warning(f"AI transient error during outreach generation, retrying: {exc}")
        if job_id and supabase:
            supabase.table('job_runs').update({'status': 'retrying', 'retry_count': self.request.retries + 1}).eq('id', job_id).execute()
        countdown = 30 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)
    except Exception as exc:
        logger.error(f"Outreach task failed: {exc}")
        if job_id and supabase:
            supabase.table('job_runs').update({'status': 'failed', 'error_message': str(exc), 'completed_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()
        return False
