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
    endpoint xử lý yêu cầu chat và stream response
    """
    try:
        # lấy hoặc tạo session
        conv_data = conversation_manager.get_or_create_conversation(request.conversation_id)

        # logic chatbot
        return EventSourceResponse(
            chatbot_logic_generator(
                conv_data=conv_data,
                user_message=request.message,
                conversation_id=request.conversation_id
            )
        )
    except Exception as e:
        logger.error(f"Error in stream_chat_handler: {e}", exc_info=True)
        # trả về JSON response cho lỗi
        error_msg = {"error": "An unexpected server error occurred."}
        return StreamingResponse(
            iter([f"data: {json.dumps(error_msg)}\n\n"]),
            status_code=500,
            media_type="text/event-stream"
        )

@router.get("/health")
async def health_check():
    return {"status": "ok"} 