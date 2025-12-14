# Search Engine API

A **scalable FastAPI-based Search and URL Recrawl API** designed for high-throughput workloads. The system supports asynchronous recrawling using Celery + Redis, in-memory caching, job tracking with SLA enforcement, webhook callbacks, and API-key–based rate limiting.

**Ideal for:** search platforms, crawling pipelines, internal indexing services, and distributed data ingestion systems.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [API Documentation](#api-documentation)
  - [Search API](#search-api)
  - [Recrawl API](#recrawl-api)
- [Webhooks](#webhooks)
- [Rate Limiting](#rate-limiting)
- [Configuration](#configuration)
- [Production Deployment](#production-deployment)

---

## Features

###  Search API
- Full-text search with pagination support
- Advanced filtering options:
  - Language filtering
  - Date range queries
  - Multiple sorting modes (relevance, date, popularity)
  - Safe search filtering
- In-memory query caching for improved performance
- Clean pagination metadata (first, last, next, previous links)

### Recrawl API
- Asynchronous URL recrawling with priority queuing
- Background processing via Celery workers
- Job tracking with SLA deadline enforcement
- Real-time status polling
- Optional webhook callbacks for job completion or failure notifications

### Security & Performance
- API key-based authentication
- Per-key rate limiting (1000 requests/minute)
- Automatic request throttling with HTTP 429 responses

---

## Architecture Overview

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │─────▶│   FastAPI   │─────▶│    Redis    │
└─────────────┘      └─────────────┘      └─────────────┘
                            │                     │
                            │                     │
                            ▼                     ▼
                     ┌─────────────┐      ┌─────────────┐
                     │   Celery    │◀─────│   Workers   │
                     │   Broker    │      └─────────────┘
                     └─────────────┘
```

**Components:**
- **FastAPI** - High-performance HTTP API layer
- **Redis** - Message broker and result backend for Celery
- **Celery Workers** - Distributed task processing for recrawl operations
- **In-Memory Stores** - Job queue, cache, and rate limiting (development)

> **Note:** In-memory storage is used for simplicity in development. For production deployments, migrate to Redis or database-backed persistence for reliability and scalability.

---

## Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern async web framework
- **[Celery](https://docs.celeryq.dev/)** - Distributed task queue
- **[Redis](https://redis.io/)** - In-memory data store and message broker
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Data validation
- **[httpx](https://www.python-httpx.org/)** - Async HTTP client

---

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── routes_search.py      # Search endpoint handlers
│   │   └── routes_recrawl.py     # Recrawl endpoint handlers
│   ├── services/
│   │   ├── search.py             # Search logic implementation
│   │   ├── cache.py              # In-memory caching service
│   │   ├── job_queue.py          # Job tracking and management
│   │   ├── rate_limit.py         # Rate limiting logic
│   │   ├── webhook.py            # Webhook delivery service
│   │   └── celery_tasks.py       # Celery task definitions
│   ├── models/
│   │   └── schemas.py            # Pydantic models
│   ├── utils/
│   │   └── auth.py               # Authentication utilities
│   ├── main.py                   # Application entry point
│   └── __init__.py
├── Dockerfile                     # Container configuration
└── requirements.txt               # Python dependencies
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- Docker (for Redis)
- pip or poetry

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ndegealbert/forager.ai-search-engine-assement.git
   cd search-engine-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Redis**
   ```bash
   docker run -d -p 6379:6379 --name redis redis:latest
   ```

4. **Start the API server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Start Celery worker** (in a separate terminal)
   ```bash
   celery -A app.services.celery_tasks.celery worker --loglevel=info
   ```

6. **Access the API**
   - API: http://127.0.0.1:8000
   - Interactive docs: http://127.0.0.1:8000/docs
   - Alternative docs: http://127.0.0.1:8000/redoc

---

## Authentication

All API requests require Bearer token authentication:

```bash
Authorization: Bearer test_api_key_123
```

**Example:**
```bash
curl "http://127.0.0.1:8000/search?q=fastapi" \
  -H "Authorization: Bearer test_api_key_123"
```

> **Production Note:** Replace `test_api_key_123` with secure, randomly generated API keys. Implement proper key management and rotation policies.

---

## API Documentation

### Search API

#### Endpoint
```
GET /search
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Results per page (default: 10, max: 100) |
| `language` | string | No | Filter by language code (e.g., "en") |
| `date_from` | string | No | Start date (ISO 8601) |
| `date_to` | string | No | End date (ISO 8601) |
| `sort` | string | No | Sort order: `relevance`, `date`, `popularity` |
| `safe_search` | boolean | No | Enable safe search filtering |

#### Example Request
```bash
curl "http://127.0.0.1:8000/search?q=fastapi&page=1&per_page=20&sort=relevance" \
  -H "Authorization: Bearer test_api_key_123"
```

#### Example Response
```json
{
  "query": "fastapi",
  "page": 1,
  "per_page": 20,
  "total_results": 150,
  "total_pages": 8,
  "execution_time_ms": 45,
  "results": [
    {
      "title": "FastAPI Documentation",
      "url": "https://fastapi.tiangolo.com",
      "snippet": "FastAPI is a modern, fast web framework...",
      "date": "2024-12-01",
      "relevance_score": 0.95
    }
  ],
  "pagination": {
    "first": "/search?q=fastapi&page=1",
    "last": "/search?q=fastapi&page=8",
    "next": "/search?q=fastapi&page=2",
    "previous": null
  }
}
```

---

### Recrawl API

#### Submit Recrawl Job

**Endpoint:**
```
POST /recrawl
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "priority": "high",
  "callback_url": "https://your-app.com/webhook",
  "force": false
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | URL to recrawl |
| `priority` | string | No | Priority level: `low`, `medium`, `high` (default: `medium`) |
| `callback_url` | string | No | Webhook URL for notifications |
| `force` | boolean | No | Force recrawl even if recently crawled (default: `false`) |

**Example Request:**
```bash
curl -X POST "http://127.0.0.1:8000/recrawl" \
  -H "Authorization: Bearer test_api_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "priority": "high",
    "callback_url": "https://your-app.com/webhook",
    "force": false
  }'
```

**Example Response:**
```json
{
  "job_id": "d83d8cb5-5631-414a-aac8-3dfc031d755d",
  "status": "queued",
  "url": "https://example.com/",
  "priority": "high",
  "sla_deadline": "2025-12-13T07:10:14.056855",
  "estimated_completion": "2025-12-13T06:55:14.056855",
  "created_at": "2025-12-13T06:10:14.056855",
  "callback_url": "https://your-app.com/webhook",
  "status_url": "/recrawl/d83d8cb5-5631-414a-aac8-3dfc031d755d"
}
```

#### Check Job Status

**Endpoint:**
```
GET /recrawl/{job_id}
```

**Example Request:**
```bash
curl "http://127.0.0.1:8000/recrawl/d83d8cb5-5631-414a-aac8-3dfc031d755d" \
  -H "Authorization: Bearer test_api_key_123"
```

**Example Response:**
```json
{
  "job_id": "d83d8cb5-5631-414a-aac8-3dfc031d755d",
  "status": "completed",
  "url": "https://example.com/",
  "priority": "high",
  "created_at": "2025-12-13T06:10:14.056855",
  "completed_at": "2025-12-13T06:11:12.453939",
  "result": {
    "status": "success",
    "crawled_at": "2025-12-13T06:11:12.453939",
    "content_length": 45672,
    "status_code": 200
  }
}
```

**Status Values:**
- `queued` - Job is waiting in queue
- `processing` - Job is currently being processed
- `completed` - Job finished successfully
- `failed` - Job failed (check result for error details)

---

## Webhooks

When a `callback_url` is provided in the recrawl request, the API will send a POST request to that URL upon job completion or failure.

### Webhook Payload

**Success Event:**
```json
{
  "event": "recrawl.success",
  "timestamp": "2025-12-13T06:11:12.453939Z",
  "job_id": "d83d8cb5-5631-414a-aac8-3dfc031d755d",
  "status": "completed",
  "result": {
    "url": "https://example.com/",
    "status": "success",
    "crawled_at": "2025-12-13T06:11:12.453939",
    "content_length": 45672,
    "status_code": 200
  }
}
```

**Failure Event:**
```json
{
  "event": "recrawl.failure",
  "timestamp": "2025-12-13T06:11:12.453939Z",
  "job_id": "d83d8cb5-5631-414a-aac8-3dfc031d755d",
  "status": "failed",
  "error": {
    "type": "TimeoutError",
    "message": "Request timeout after 30 seconds"
  }
}
```

## Rate Limiting

**Limits:** 1000 requests per minute per API key

When the rate limit is exceeded, the API returns:
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

**HTTP Status:** `429 Too Many Requests`

**Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when limit resets

---

**Docker Deployment**
   ```bash
   docker-compose up -d
   ```

### Celery Tasks Reference

| Task Name | Description | Priority Support |
|-----------|-------------|------------------|
| `recrawl.process_url` | Executes URL crawling logic | Yes |
| `webhook.send` | Delivers webhook notifications | No |

---
