# app/services/rate_limit.py
from datetime import datetime, timedelta
from typing import Dict

class RateLimitService:
    def __init__(self):
        self.buckets: Dict[str, Dict] = {}

    async def check_rate_limit(self, api_key: str, limit: int = 1000) -> bool:
        bucket = self.buckets.get(api_key, {"count": 0, "reset": datetime.utcnow()})
        if datetime.utcnow() > bucket["reset"]:
            bucket = {"count": 0, "reset": datetime.utcnow() + timedelta(minutes=1)}
        if bucket["count"] >= limit:
            return False
        bucket["count"] += 1
        self.buckets[api_key] = bucket
        return True

    def get_rate_limit_headers(self, api_key: str, limit: int = 1000) -> Dict:
        bucket = self.buckets.get(api_key, {"count": 0, "reset": datetime.utcnow()})
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(max(0, limit - bucket["count"])),
            "X-RateLimit-Reset": str(int(bucket["reset"].timestamp()))
        }