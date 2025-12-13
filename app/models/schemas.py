from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

class SortOrder(str, Enum):
    RELEVANCE = "relevance"
    DATE = "date"
    POPULARITY = "popularity"

class Priority(str, Enum):
    STANDARD = "standard"
    HIGH = "high"
    URGENT = "urgent"

class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SearchRequest(BaseModel):
    q: str = Field(..., max_length=500)
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)
    language: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    sort: SortOrder = SortOrder.RELEVANCE
    safe_search: bool = False
    fields: Optional[str] = None

class SearchResult(BaseModel):
    id: str
    url: str
    title: str
    snippet: str
    crawled_at: datetime
    last_modified: datetime
    language: str
    score: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    query: str
    total_results: int
    page: int
    per_page: int
    total_pages: int
    search_time_ms: int
    results: List[SearchResult]
    pagination: Dict[str, Optional[str]]

class RecrawlRequest(BaseModel):
    url: HttpUrl
    priority: Priority = Priority.HIGH
    callback_url: Optional[HttpUrl] = None
    force: bool = False

class RecrawlResponse(BaseModel):
    job_id: str
    status: JobStatus
    url: str
    priority: Priority
    sla_deadline: datetime
    estimated_completion: datetime
    created_at: datetime
    callback_url: Optional[str]
    status_url: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    url: str
    priority: Priority
    sla_deadline: datetime
    sla_met: Optional[bool]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]