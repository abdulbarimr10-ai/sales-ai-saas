import os
from celery import Celery
from app.core.config import settings

# Create the celery application instance using the central config setting
redis_url = settings.REDIS_URL

celery_app = Celery(
    'sales_ai_worker',
    broker=redis_url,
    backend=redis_url,
    include=[
        'app.workers.tasks.outreach_tasks',
        'app.workers.tasks.audit_tasks',
        'app.workers.tasks.email_tasks',
        'app.workers.tasks.enrichment_tasks',
        'app.workers.tasks.maintenance_tasks'
    ]
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,       # Hard kill after 1 hour
    task_soft_time_limit=3300,  # Soft limit, raises exception 
    worker_concurrency=4,       # Adjust based on CPU
    task_acks_late=True,        # Only ack after completion (good for retries)
    task_reject_on_worker_lost=True,
    
    # Task routing
    task_routes={
        'app.workers.tasks.outreach_tasks.*': {'queue': 'outreach'},
        'app.workers.tasks.audit_tasks.*': {'queue': 'ai'},
        'app.workers.tasks.email_tasks.*': {'queue': 'emails'},
        'app.workers.tasks.enrichment_tasks.*': {'queue': 'enrichment'},
        'app.workers.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
    }
)

if __name__ == '__main__':
    celery_app.start()
