from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json
from datetime import datetime
import logging

from app.schemas.chat import StreamChatRequest
from app.logic.chatbot import chatbot_logic_generator
from app.state.manager import conversation_manager
from sse_starlette.sse import EventSourceResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat/stream")
async def stream_chat_handler(request: StreamChatRequest):
    """
    Endpoint to handle streaming chat requests.
    It retrieves or creates a conversation, then returns an EventSourceResponse
    that streams the chatbot's responses.
    """
    # Get or create the conversation from the manager
    conv_data = conversation_manager.get_or_create_conversation(request.conversation_id)

    # Return a streaming response that runs the chatbot logic
    # Error handling is managed inside the generator itself.
    return EventSourceResponse(
        chatbot_logic_generator(
            conv_data=conv_data,
            user_message=request.message,
            conversation_id=request.conversation_id
        )
    )

@router.get("/health")
async def health_check():
    return {"status": "ok"} 