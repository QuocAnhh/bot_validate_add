from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# --- Enums and Data Classes for State Management ---

class ConversationState(Enum):
    """Defines the possible states in the conversation flow."""
    INITIAL = "initial"
    WAITING_FOR_ADDRESS = "waiting_for_address"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"
    WAITING_FOR_DISTRICT = "waiting_for_district"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"
    CONFIRMING = "confirming"
    COMPLETED = "completed"

@dataclass
class ConversationData:
    """Holds all data for a single conversation session."""
    conversation_id: str
    state: ConversationState = ConversationState.INITIAL
    address_raw: Optional[str] = None
    city_hint: Optional[str] = None
    retry_count: int = 0
    potential_address: Optional[str] = None
    potential_lat: Optional[float] = None
    potential_lng: Optional[float] = None
    potential_addresses: Optional[List[Dict]] = None # To store multiple address candidates
    created_at: datetime = field(default_factory=datetime.now)

# --- In-memory Storage for Conversations ---

# A simple dictionary to store active conversations.
# In a production environment, this should be replaced with a persistent storage like Redis.
conversations: Dict[str, ConversationData] = {}
CONVERSATION_TTL = timedelta(minutes=30)


def cleanup_conversations():
    """
    Removes expired conversations from the in-memory dictionary to prevent memory leaks.
    A conversation is considered expired if it's older than CONVERSATION_TTL.
    """
    current_time = datetime.now()
    expired_ids = [
        conv_id for conv_id, conv_data in conversations.items()
        if current_time - conv_data.created_at > CONVERSATION_TTL
    ]
    for conv_id in expired_ids:
        del conversations[conv_id]

def get_or_create_conversation(conversation_id: str) -> ConversationData:
    """
    Retrieves an existing conversation by its ID or creates a new one if not found.
    Also triggers a cleanup of expired conversations.
    """
    cleanup_conversations()
    if conversation_id not in conversations:
        conversations[conversation_id] = ConversationData(
            conversation_id=conversation_id
        )
    return conversations[conversation_id] 