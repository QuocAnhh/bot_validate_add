import logging
from typing import Dict, List, Any

from google.generativeai.protos import Content, Part
from app.state.booking import BookingState

logger = logging.getLogger(__name__)

class ConversationData:
    """lưu trữ dữ liệu cuộc trò chuyện"""
    def __init__(self):
        self.history: List[Content] = []
        self.context: Dict[str, Any] = {}
        self.booking_state = BookingState()
        logger.debug("khởi tạo ConversationData")

    def add_message(self, role: str, content: str):
        """thêm tin nhắn vào lịch sử cuộc trò chuyện"""
        api_role = "model" if role == "assistant" else role
        self.history.append(Content(role=api_role, parts=[Part(text=content)]))

    def reset(self):
        """reset lịch sử cuộc trò chuyện"""
        self.history.clear()
        self.context.clear()
        self.booking_state = BookingState()
        logger.info("ConversationData đã được reset")

class ConversationManager:
    """quản lý tất cả cuộc trò chuyện đang diễn ra"""
    def __init__(self):
        self._conversations: Dict[str, ConversationData] = {}
        logger.info("ConversationManager đã được khởi tạo")

    def get_or_create_conversation(self, conversation_id: str) -> ConversationData:
        """lấy hoặc tạo cuộc trò chuyện"""
        if conversation_id not in self._conversations:
            logger.info(f"tạo cuộc trò chuyện mới với ID: {conversation_id}")
            self._conversations[conversation_id] = ConversationData()
        return self._conversations[conversation_id]

# singleton instance
conversation_manager = ConversationManager() 