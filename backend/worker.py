from celery import Celery
from backend.core.config import settings

celery_app = Celery('ecommerce_assistant', broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(task_serializer='json', accept_content=['json'], result_serializer='json', task_track_started=True, task_acks_late=True, worker_prefetch_multiplier=1)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def execute_generation_job(self, job_id: int, product_id: int, job_kind: str) -> dict:
    """Provider-agnostic task boundary; real AI provider is injected in the next slice."""
    return {'job_id': job_id, 'product_id': product_id, 'job_kind': job_kind, 'status': 'succeeded', 'provider': 'demo'}

@celery_app.task
def sweep_timeouts() -> dict:
    return {'status': 'ok', 'scanned': 0}
