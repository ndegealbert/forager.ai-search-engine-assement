from celery import Celery
from datetime import datetime
import httpx

celery = Celery(
    "search_engine",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

@celery.task(name="recrawl.process_url")
def process_url(url: str):
    """
    Heavy recrawl processing task.
    In production: call crawler engine, update ES index.
    """
    print(f"[Celery] Processing URL: {url}")
    # TODO: Put real crawl logic here

    return {
        "url": url,
        "status": "completed",
        "crawled_at": datetime.utcnow().isoformat(),
    }

@celery.task(name="webhook.send")
def send_webhook(url: str, payload: dict):
    """
    Send webhook notification asynchronously.
    """
    with httpx.Client() as client:
        client.post(url, json=payload)
    return {"status": "sent", "url": url}
