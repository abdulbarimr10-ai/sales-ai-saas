from app.workers.celery_app import celery_app
from database.models import supabase
from app.core.logging import logger
from datetime import datetime
from pipeline.audit_flow import execute_universal_audit
from app.services.llm.exceptions import ProviderTimeoutError, ProviderRateLimitError

@celery_app.task(bind=True, max_retries=2)
def run_ai_audit_task(self, user_id: int, lead_id: int, lead_data: dict, job_id: str = None):
    if job_id and supabase:
        supabase.table('job_runs').update({'status': 'running', 'started_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()

    try:
        # Re-use the existing core logic, passing user_id so LLM factory uses correct keys
        result = execute_universal_audit(lead_id, user_id)
        analysis_result = result.get('analysis') if result else "Audit failed"
        
        # Save to DB
        if supabase:
            supabase.table('leads').update({
                'pain_points': analysis_result,
                'status': 'Audited'
            }).eq('id', lead_id).execute()
            
            if job_id:
                supabase.table('job_runs').update({'status': 'completed', 'completed_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()
        return True

    except (ProviderTimeoutError, ProviderRateLimitError) as exc:
        logger.warning(f"AI transient error during audit, retrying: {exc}")
        if job_id and supabase:
            supabase.table('job_runs').update({'status': 'retrying', 'retry_count': self.request.retries + 1}).eq('id', job_id).execute()
        countdown = 20 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)
    except Exception as exc:
        logger.error(f"Audit task failed: {exc}")
        if job_id and supabase:
            supabase.table('job_runs').update({'status': 'failed', 'error_message': str(exc), 'completed_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()
        return False
