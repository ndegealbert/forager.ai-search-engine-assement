# app/api/routes_recrawl.py
from fastapi import APIRouter, BackgroundTasks, Path, Depends, HTTPException
from datetime import datetime, timedelta
from app.models import schemas
from app.services.job_queue import JobQueueService
from app.services.webhook import WebhookService
from app.services.celery_tasks import process_url, send_webhook, celery
from app.utils.auth import verify_api_key
import asyncio

router = APIRouter()

job_queue_service = JobQueueService()
webhook_service = WebhookService()




@router.post("/recrawl", response_model=schemas.RecrawlResponse, status_code=202)
async def submit_recrawl(
    request: schemas.RecrawlRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    # Submit Celery task
    celery_job = process_url.delay(str(request.url))

    # store metadata in our in-memory job store so status endpoint can return full data
    created_at = datetime.utcnow()
    job_record = {
        "job_id": celery_job.id,
        "status": schemas.JobStatus.QUEUED,
        "url": str(request.url),
        "priority": request.priority,
        "sla_deadline": created_at + timedelta(hours=1),
        "created_at": created_at,
        "callback_url": str(request.callback_url) if request.callback_url else None,
    }
    # persist in in-memory store (JobQueueService)
    job_queue_service.jobs[celery_job.id] = job_record
    job_queue_service.queue.append(celery_job.id)

    # Monitor and trigger webhook after completion (non-blocking)
    if request.callback_url:
        background_tasks.add_task(_monitor_and_send, celery_job.id, str(request.callback_url))

    return schemas.RecrawlResponse(
        job_id=celery_job.id,
        status=schemas.JobStatus.QUEUED,
        url=str(request.url),
        priority=request.priority,
        sla_deadline=job_record["sla_deadline"],
        estimated_completion=created_at + timedelta(minutes=45),
        created_at=created_at,
        callback_url=job_record["callback_url"],
        status_url=f"/recrawl/{celery_job.id}"
    )


async def _monitor_and_send(job_id: str, callback_url: str):
    """Lightweight monitor that polls Celery for task result and then sends webhook via Celery task."""
    while True:
        res = celery.AsyncResult(job_id)
        if res.status in ["SUCCESS", "FAILURE"]:
            payload = {
                "event": f"recrawl.{res.status.lower()}",
                "timestamp": datetime.utcnow().isoformat(),
                "job_id": job_id,
                "status": res.status,
                "result": res.result
            }
            send_webhook.delay(callback_url, payload)
            break
        await asyncio.sleep(2)

@router.get("/recrawl/{job_id}", response_model=schemas.JobStatusResponse)
async def get_recrawl_status(
    job_id: str = Path(...),
    api_key: str = Depends(verify_api_key)
):
    # First, try to read from our in-memory job store
    job = await job_queue_service.get_job_status(job_id)
    if job:
        # If task finished in Celery, try enriching job with Celery result
        try:
            res = celery.AsyncResult(job_id)
            if res.status == "SUCCESS" and isinstance(res.result, dict):
                job["status"] = schemas.JobStatus.COMPLETED
                job["result"] = res.result
                job["completed_at"] = job.get("completed_at") or datetime.utcnow()
            elif res.status == "FAILURE":
                job["status"] = schemas.JobStatus.FAILED
                job["completed_at"] = job.get("completed_at") or datetime.utcnow()
            elif res.status in ("PENDING", "RETRY"):
                job["status"] = schemas.JobStatus.PROCESSING
        except Exception:
            # ignore celery lookup failures and return stored job
            pass

        sla_met = None
        if job["status"] in [schemas.JobStatus.COMPLETED, schemas.JobStatus.FAILED]:
            completed_at = job.get("completed_at", datetime.utcnow())
            sla_met = completed_at <= job["sla_deadline"]

        return schemas.JobStatusResponse(
            job_id=job["job_id"],
            status=job["status"],
            url=job.get("url", ""),
            priority=job.get("priority", schemas.Priority.HIGH),
            sla_deadline=job.get("sla_deadline"),
            sla_met=sla_met,
            created_at=job.get("created_at"),
            started_at=job.get("started_at"),
            completed_at=job.get("completed_at"),
            result=job.get("result")
        )

    # Fallback: no stored job record — try Celery AsyncResult
    res = celery.AsyncResult(job_id)
    status = res.status
    result = res.result if res.ready() else None

    # Map Celery states to our JobStatus
    if status == "SUCCESS":
        mapped_status = schemas.JobStatus.COMPLETED
    elif status == "FAILURE":
        mapped_status = schemas.JobStatus.FAILED
    else:
        mapped_status = schemas.JobStatus.PROCESSING

    return schemas.JobStatusResponse(
        job_id=job_id,
        status=mapped_status,
        url=(result.get("url") if isinstance(result, dict) else ""),
        priority=schemas.Priority.HIGH,
        sla_deadline=datetime.utcnow() + timedelta(hours=1),
        sla_met=None,
        created_at=datetime.utcnow(),
        started_at=None,
        completed_at=(datetime.utcnow() if status in ("SUCCESS", "FAILURE") else None),
        result=result if result else None
    )
