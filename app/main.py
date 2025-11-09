"""Main FastAPI application"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.middleware import RequestLoggingMiddleware
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="bot_nhaXe - Single Agent",
    description="Simple AI agent with prompt-only configuration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include API routes
app.include_router(api_router)

logger.info("FastAPI application initialized") 