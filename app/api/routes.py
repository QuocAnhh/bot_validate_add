from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json
from datetime import datetime
import logging

from app.schemas.chat import StreamChatRequest
from app.state.manager import get_or_create_conversation, conversations, ConversationData
from app.logic.chatbot import chatbot_logic_generator

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/chat/stream")
async def stream_chat_handler(request: StreamChatRequest):
    conv_data: ConversationData = get_or_create_conversation(request.conversation_id)
    user_message = request.message.strip()

    async def event_stream():
        """
        Wrapper generator that calls the main logic and ensures the [DONE]
        message is sent when the logic generator is exhausted.
        """
        try:
            async for chunk in chatbot_logic_generator(conv_data, user_message, request.conversation_id):
                yield chunk
            
            conv_data.created_at = datetime.now()
        
        except Exception as e:
            logger.error(f"Error in event_stream wrapper: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': 'An unexpected server error occurred.'})}\n\n"
        finally:
            logger.debug(f"Ending stream for conversation {request.conversation_id}")
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/health")
async def health_check():
    """Health check endpoint to monitor the application's status."""
    return {
        "status": "healthy",
        "active_conversations": len(conversations),
        "timestamp": datetime.now().isoformat()
    } 