# app/main.py
import uvicorn
from . import app as fastapi_app

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,   # dev only
        workers=1
    )
