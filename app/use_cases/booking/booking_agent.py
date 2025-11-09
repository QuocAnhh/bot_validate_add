"""Booking agent implementation"""
import logging
from typing import Dict, Any
from datetime import datetime
from zoneinfo import ZoneInfo
import json
from dataclasses import asdict

from app.use_cases.base.base_agent import BaseAgent
from app.core.agent_config import AgentConfig
from app.state.manager import conversation_manager
from app.state.booking import BookingState

logger = logging.getLogger(__name__)


class BookingAgent(BaseAgent):
    """Booking agent for trip booking"""
    
    async def get_conversation_state(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation state
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation state dictionary
        """
        conv_data = conversation_manager.get_or_create_conversation(conversation_id)
        
        # Build state dictionary
        state = {
            "conversation_id": conversation_id,
            "booking_state": asdict(conv_data.booking_state),
            "context": conv_data.context.copy()
        }
        
        # Add current time context
        now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        state["current_time"] = now_vn.strftime('%Y-%m-%d %H:%M')
        state["timezone"] = "Asia/Ho_Chi_Minh"
        
        return state
    
    async def update_conversation_state(
        self,
        conversation_id: str,
        state: Dict[str, Any]
    ):
        """
        Update conversation state
        
        Args:
            conversation_id: Conversation ID
            state: State dictionary to update
        """
        conv_data = conversation_manager.get_or_create_conversation(conversation_id)
        
        # Update booking state if present
        if "booking_state" in state:
            booking_state_dict = state["booking_state"]
            conv_data.booking_state.origin = booking_state_dict.get("origin")
            conv_data.booking_state.destination = booking_state_dict.get("destination")
            conv_data.booking_state.departure_time = booking_state_dict.get("departure_time")
            conv_data.booking_state.available_trips = booking_state_dict.get("available_trips", [])
            conv_data.booking_state.selected_trip_id = booking_state_dict.get("selected_trip_id")
            conv_data.booking_state.status = booking_state_dict.get("status", "pending")
        
        # Update context
        if "context" in state:
            conv_data.context.update(state["context"])
    
    async def process_message(
        self,
        user_message: str,
        conversation_id: str
    ):
        """
        Process user message with booking-specific context
        
        Args:
            user_message: User message
            conversation_id: Conversation ID
            
        Yields:
            Response chunks
        """
        # Get conversation state
        conversation_state = await self.get_conversation_state(conversation_id)
        
        # Build context message with current time and booking state
        now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        now_context = (
            f"Thời gian hiện tại (giờ Việt Nam): {now_vn.strftime('%Y-%m-%d %H:%M')}\n"
            f"Nếu người dùng nói các cụm như 'hôm nay', 'ngày mai', 'tối mai', hãy hiểu theo thời gian hiện tại này.\n"
            f"Nếu đã có 'departure_time' trong trạng thái, đừng hỏi lại thời gian, chỉ xác nhận ngắn gọn nếu cần."
        )
        
        booking_state = conversation_state.get("booking_state", {})
        context_message = (
            f"{now_context}\n"
            f"Người dùng nói: '{user_message}'.\n"
            f"Trạng thái đặt vé hiện tại là: {json.dumps(booking_state, ensure_ascii=False)}.\n"
            "Dựa trên lịch sử hội thoại và trạng thái này, hãy quyết định bước đi tiếp theo một cách hợp lý."
        )
        
        # Process with base agent - use context message instead of original
        # The base agent will add the message to history
        async for chunk in super().process_message(context_message, conversation_id):
            yield chunk

