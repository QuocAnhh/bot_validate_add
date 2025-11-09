from pydantic import BaseModel
from typing import Optional

# Chat request schema
class StreamChatRequest(BaseModel):
    message: str
    conversation_id: str
    agent_name: Optional[str] = None  # Ignored (single agent only)
    config_path: Optional[str] = None  # Full path to config file (overrides agent_name)
    use_tools: Optional[bool] = False  # Whether to use tools
    # Legacy fields (optional)
    customer_phone: Optional[str] = None
    callcenter_phone: Optional[str] = None
    request_from: Optional[str] = None
    index: Optional[int] = None
    bot_id: Optional[str] = None
    model_name: Optional[str] = None 