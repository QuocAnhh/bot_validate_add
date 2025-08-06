from pydantic import BaseModel
from typing import Optional

# payload gửi lên live-demo
class StreamChatRequest(BaseModel):
    message: str
    conversation_id: str
    customer_phone: Optional[str] = None
    callcenter_phone: Optional[str] = None
    request_from: Optional[str] = None
    index: Optional[int] = None
    bot_id: Optional[str] = None
    model_name: Optional[str] = None 