"""Main API routes"""
from fastapi import APIRouter
from app.api.chat import router as chat_router
from app.api.evaluation import router as evaluation_router
from app.ui.routes import router as ui_router

router = APIRouter()

# Include chat routes
router.include_router(chat_router, prefix="/api", tags=["chat"])

# Include evaluation routes
router.include_router(evaluation_router, tags=["evaluation"])

# Include UI routes
router.include_router(ui_router, tags=["ui"])


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "bot_nhaXe"}


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "bot_nhaXe API - Single Agent",
        "version": "1.0.0",
        "endpoints": {
            "ui": "/ui",
            "chat": "/api/chat/stream",
            "agent_info": "/api/agents/agent",
            "health": "/health"
        }
    }
