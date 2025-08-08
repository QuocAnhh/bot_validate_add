import logging
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, Tool
from typing import List

from app.core.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
Bạn là một trợ lý ảo thân thiện, kiên nhẫn và hữu ích cho một dịch vụ giao hàng/nhà xe tại Việt Nam.
Mục tiêu chính của bạn là giúp người dùng xác thực một địa chỉ ở Việt Nam.
Hãy sử dụng công cụ `search_address_in_vietnam` khi bạn có một địa chỉ cụ thể để tìm kiếm.

QUAN TRỌNG: Nếu người dùng không cung cấp địa chỉ mà chỉ đang trò chuyện, yêu cầu chờ đợi hoặc tỏ ra không chắc chắn, hãy phản hồi một cách tự nhiên và kiên nhẫn. Đừng ngay lập tức yêu cầu địa chỉ.
Ví dụ:
- Nếu người dùng nói: "đợi anh chút", bạn nên trả lời: "Dạ vâng, anh cứ xem đi ạ."
- Nếu người dùng nói: "alo", bạn có thể chào lại và hỏi: "Dạ, em nghe ạ. Anh/chị cần em giúp tìm địa chỉ nào không ạ?"

Chỉ hỏi lại địa chỉ khi cuộc trò chuyện có vẻ đã sẵn sàng để tiếp tục.

Nếu công cụ `search_address_in_vietnam` trả về nhiều địa chỉ, đừng liệt kê tất cả. Thay vào đó, hãy thông báo rằng có nhiều kết quả và yêu cầu người dùng làm rõ tỉnh/thành phố. Giữ câu trả lời ngắn gọn.
"""

class GeminiClient:
    """tương tác với api gemini"""
    def __init__(self, api_key: str, system_instruction: str | None = SYSTEM_INSTRUCTION):
        if not api_key:
            raise ValueError("Gemini API Key is required for GeminiClient.")
        genai.configure(api_key=api_key)
        # khởi tạo model với hệ thống instruction
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=system_instruction
        )

    async def generate_response(
        self,
        prompt: List, # prompt là một list của chat history
        tools: List[Tool] | None = None,
        max_output_tokens: int | None = None
    ) -> genai.types.GenerateContentResponse:
        """gọi api gemini"""
        try:
            gen_config = GenerationConfig(max_output_tokens=max_output_tokens) if max_output_tokens else None

            response = await self.model.generate_content_async(
                prompt,
                tools=tools,
                generation_config=gen_config
            )
            return response
        except Exception as e:
            logger.error(f"An unexpected error occurred while calling Gemini API: {e}", exc_info=True)
            # re-raise exception để được xử lý bởi logic chính
            raise

gemini_client = GeminiClient(api_key=GEMINI_API_KEY) 