from app.workers.celery_app import celery_app
from database.models import supabase
from app.core.logging import logger
from datetime import datetime

@celery_app.task(bind=True, max_retries=2)
def enrich_lead_data_task(self, user_id: int, lead_id: int, lead_data: dict, job_id: str = None):
    """
    Placeholder for async Apollo/LinkedIn enrichment.
    """
    if job_id and supabase:
        supabase.table('job_runs').update({'status': 'running', 'started_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()

    try:
        # Simulate enrichment
        import time
        time.sleep(2)
        
        # In real code: call apollo_tool.py or linkedin_tool.py
        
        if job_id and supabase:
            supabase.table('job_runs').update({'status': 'completed', 'completed_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()
        return True

    except Exception as exc:
        logger.error(f"Enrichment task failed: {exc}")
        if job_id and supabase:
            supabase.table('job_runs').update({'status': 'failed', 'error_message': str(exc), 'completed_at': datetime.utcnow().isoformat()}).eq('id', job_id).execute()
        return False
