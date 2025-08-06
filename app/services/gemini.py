import logging
import google.generativeai as genai
from app.core.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

class GeminiClient:
    """A client for interacting with the Google Gemini API."""
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API Key is required for GeminiClient.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_response(self, prompt: str) -> str:
        """
        Generates a text response from Gemini based on the provided prompt.

        Args:
            prompt: The instruction or question for the Gemini model.

        Returns:
            The generated text content as a string.
        """
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"An unexpected error occurred while calling Gemini API: {e}", exc_info=True)
            # Return a safe, generic error message
            return "Dạ, đã có lỗi xảy ra. Xin vui lòng thử lại sau."

gemini_client = GeminiClient(api_key=GEMINI_API_KEY) 