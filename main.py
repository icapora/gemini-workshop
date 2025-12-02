"""
FastAPI application for testing Google GenAI Live API
Real-time audio streaming and transcription application
"""

import logging
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import websocket

# Configure logging with settings
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Real-time conversation",
    description="Application for testing audio streaming and transcriptions with Gemini Live API",
    version="1.0.0",
)

# Include routers
app.include_router(websocket.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    """Serve main HTML page"""
    with open("static/index.html", encoding="utf-8") as f:
        return f.read()


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "gemini-live-api-test",
        "api_key_configured": bool(settings.gemini_api_key),
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting FastAPI server...")
    logger.info(f"📝 Open http://localhost:{settings.port} in your browser")

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
