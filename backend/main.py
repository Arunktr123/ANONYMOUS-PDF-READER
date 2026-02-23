from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
import os
from app.config import settings
from app.database import init_db
from app.routes import sessions, pdfs, chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup (after middleware is ready)
    init_db()
    yield

app = FastAPI(
    title="Anonymous PDF Reader Chat",
    description="A session-based PDF reader with anonymous chat functionality",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(sessions.router)
app.include_router(pdfs.router)
app.include_router(chat.router)


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    """Serve robots.txt to restrict crawlers"""
    return """User-agent: *
Disallow: /
Disallow: /api/
Disallow: /sessions/
Disallow: /pdfs/
Disallow: /chat/
"""


@app.get("/")
async def root():
    return {
        "message": "Welcome to Anonymous PDF Reader Chat API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
