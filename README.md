# Search Engine API

A scalable FastAPI-based web search and URL recrawl system with asynchronous job processing using **Celery + Redis**, in-memory caching, job tracking, webhook callbacks, and rate limiting.

## Features

### Search API
- Full-text search with pagination
- Optional filters (language, date range, sorting, safe search)
- In-memory caching for faster repeated queries
- Per-API-key rate limiting
- Clean pagination metadata

### Recrawl API
- Submit a URL to be re-crawled
- Job queued via Celery
- In-memory job tracking (status, SLA, timestamps)
- Optional webhook callback on completion
- Background async monitor to trigger webhook

### Tech Stack
- FastAPI
- Celery
- Redis
- Uvicorn
- Pydantic

## Project Structure

```
app/
 ├── api/
 │    ├── routes_search.py
 │    ├── routes_recrawl.py
 ├── services/
 │    ├── search.py
 │    ├── cache.py
 │    ├── job_queue.py
 │    ├── rate_limit.py
 │    ├── webhook.py
 ├── models/schemas.py
 ├── utils/auth.py
 ├── __init__.py
celery_tasks.py
Dockerfile
requirements.txt
```

##Getting Started

### Install dependencies
```bash
pip install -r requirements.txt
```

### Start Redis
```bash
docker run -p 6379:6379 redis
```

### Start API server
```bash
uvicorn app:app --reload
```

### Start Celery worker
```bash
celery -A app.services.celery_tasks.celery worker --loglevel=info
```

## Search API — GET /search

Example:
```
GET /search?q=fastapi&page=1
```

## Recrawl API — POST /recrawl

Example:
```json
{
  "url": "https://example.com",
  "priority": "high",
  "callback_url": "https://myapp.com/webhook"
}
```

## Webhooks

Webhook payload:
```json
{
  "event": "recrawl.success",
  "timestamp": "2025-01-01T11:35:00Z",
  "job_id": "c21f969b5f03",
  "status": "SUCCESS"
}
```

## Authentication
Include:
```
x-api-key: YOUR_API_KEY
```

## Rate Limiting
1000 requests/min per API key.

## Docker
```bash
docker build -t search-api .
docker run -p 8000:8000 search-api
```

## Celery Tasks
- process_url(url)
- send_webhook(url, payload)
