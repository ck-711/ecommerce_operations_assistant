from celery import Celery
from backend.core.config import settings
from backend.db import SessionLocal
from backend.models import GenerationJob, GenerationJobEvent

celery_app = Celery('ecommerce_assistant', broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(task_serializer='json', accept_content=['json'], result_serializer='json', task_track_started=True, task_acks_late=True, worker_prefetch_multiplier=1)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def execute_generation_job(self, job_id: int, product_id: int, job_kind: str) -> dict:
    """Provider-agnostic task boundary; real AI provider is injected in the next slice."""
    db=SessionLocal(); job=db.get(GenerationJob, job_id)
    if not job: db.close(); raise ValueError('generation job not found')
    job.job_status='running'; job.attempts=(job.attempts or 0)+1; db.add(GenerationJobEvent(job_id=job_id,event_type='running',event_message='worker started')); db.commit()
    try:
        result={'job_id': job_id, 'product_id': product_id, 'job_kind': job_kind, 'status': 'succeeded', 'provider': 'demo'}
        job.job_status='succeeded'; db.add(GenerationJobEvent(job_id=job_id,event_type='succeeded',event_message='demo provider completed')); db.commit(); return result
    except Exception as exc:
        job.job_status='failed'; job.error_message=str(exc); db.add(GenerationJobEvent(job_id=job_id,event_type='failed',event_message=str(exc))); db.commit(); raise
    finally: db.close()

@celery_app.task
def sweep_timeouts() -> dict:
    return {'status': 'ok', 'scanned': 0}
