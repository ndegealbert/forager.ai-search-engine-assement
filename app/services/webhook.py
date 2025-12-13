# app/services/webhook.py
import hmac
import hashlib
from typing import Dict

class WebhookService:
    async def send_webhook(self, url: str, payload: Dict, secret: str):
        signature = self._generate_signature(payload, secret)
        # In production: use httpx.AsyncClient to post with headers
        print(f"POST {url} payload={payload} signature={signature}")

    def _generate_signature(self, payload: Dict, secret: str) -> str:
        message = str(payload).encode()
        return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()