# app/services/job_queue.py
from typing import Dict, Optional, Any
from uuid import uuid4
from datetime import datetime, timedelta

class JobQueueService:
    def __init__(self):
        self.queue = []
        self.jobs: Dict[str, Dict[str, Any]] = {}

    async def submit_job(self, job_data: Dict) -> str:
        # lazy import to avoid circular imports at module import time
        from app.models import schemas

        job_id = f"recrawl_{uuid4().hex}"
        sla_deadline = datetime.utcnow() + timedelta(hours=1)
        job = {
            "job_id": job_id,
            "status": schemas.JobStatus.QUEUED,
            "url": job_data["url"],
            "priority": job_data.get("priority"),
            "sla_deadline": sla_deadline,
            "created_at": datetime.utcnow(),
            "callback_url": job_data.get("callback_url")
        }
        self.jobs[job_id] = job
        self.queue.append(job_id)
        return job_id

    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        return self.jobs.get(job_id)

    async def cancel_job(self, job_id: str) -> bool:
        # lazy import for the same reason
        from app.models import schemas

        job = self.jobs.get(job_id)
        if not job:
            return False
        if job["status"] in [schemas.JobStatus.COMPLETED, schemas.JobStatus.FAILED]:
            return False
        job["status"] = schemas.JobStatus.CANCELLED
        job["cancelled_at"] = datetime.utcnow()
        return True

