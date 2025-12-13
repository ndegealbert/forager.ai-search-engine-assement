 # app/utils/auth.py
from fastapi import Header, HTTPException

async def verify_api_key(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    api_key = authorization.replace("Bearer ", "")
    if len(api_key) < 10:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
