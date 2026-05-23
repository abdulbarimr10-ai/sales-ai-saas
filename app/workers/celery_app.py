import os
import redis
import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

# Test Redis connection
redis_url = settings.REDIS_URL
use_redis = False

if redis_url and not redis_url.startswith("memory://"):
    try:
        test_client = redis.Redis.from_url(redis_url)
        test_client.ping()
        use_redis = True
        logger.info("Celery: Connected to Redis successfully.")
    except Exception as e:
        logger.warning(f"Celery: Could not connect to Redis at {redis_url}: {e}. Falling back to inline synchronous mode.")

if use_redis:
    broker_url = redis_url
    backend_url = redis_url
    task_always_eager = False
    task_eager_propagates = False
else:
    # Use memory broker and execute tasks synchronously inline
    broker_url = "memory://"
    backend_url = "memory://"
    task_always_eager = True
    task_eager_propagates = True

# Create the celery application instance using the central config setting
celery_app = Celery(
    'sales_ai_worker',
    broker=broker_url,
    backend=backend_url,
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
    task_always_eager=task_always_eager,
    task_eager_propagates=task_eager_propagates,
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
