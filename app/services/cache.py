import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta

class CacheService:
    def __init__(self):
        self.cache = {}

    async def get(self, key: str) -> Optional[Dict]:
        entry = self.cache.get(key)
        if not entry:
            return None
        value, expiry = entry
        if expiry and datetime.utcnow() > expiry:
            del self.cache[key]
            return None
        return value

    async def set(self, key: str, value: Dict, ttl: int = 3600):
        expiry = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None
        self.cache[key] = (value, expiry)

    def generate_key(self, query: str, filters: Dict) -> str:
        data = f"{query}:{str(sorted(filters.items()))}"
        return hashlib.md5(data.encode()).hexdigest()