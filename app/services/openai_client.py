"""OpenAI client for GPT-4.1-mini"""
import logging
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI

from app.core.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client for interacting with GPT models"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4.1-mini-2025-04-14",
        temperature: float = 0.7,
        max_tokens: Optional[int] = 2000
    ):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (defaults to env var)
            model_name: Model name (gpt-4o-mini or gpt-4.1-mini)
            temperature: Temperature for generation
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API Key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def _convert_messages(self, prompt: List) -> List[Dict[str, str]]:
        """
        Convert prompt format to OpenAI messages format
        
        Args:
            prompt: List of messages (can be various formats)
            
        Returns:
            List of OpenAI message dicts
        """
        messages = []
        
        for item in prompt:
            if isinstance(item, dict):
                # Already in OpenAI format
                messages.append(item)
            elif hasattr(item, 'role') and hasattr(item, 'parts'):
                # Gemini format - convert to OpenAI
                role = item.role
                if role == "model":
                    role = "assistant"
                elif role == "user":
                    role = "user"
                elif role == "tool":
                    role = "tool"
                
                # Extract text from parts
                content = ""
                tool_calls = []
                tool_call_id = None
                
                for part in item.parts:
                    if hasattr(part, 'text') and part.text:
                        content += part.text
                    elif hasattr(part, 'function_call'):
                        # Convert function call
                        fc = part.function_call
                        tool_calls.append({
                            "id": f"call_{len(tool_calls)}",
                            "type": "function",
                            "function": {
                                "name": fc.name,
                                "arguments": str(fc.args) if hasattr(fc, 'args') else "{}"
                            }
                        })
                    elif hasattr(part, 'function_response'):
                        # Convert function response
                        fr = part.function_response
                        role = "tool"
                        tool_call_id = fr.name if hasattr(fr, 'name') else None
                        content = str(fr.response) if hasattr(fr, 'response') else ""
                
                if tool_calls:
                    messages.append({
                        "role": role,
                        "content": content or None,
                        "tool_calls": tool_calls
                    })
                elif role == "tool":
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id or f"call_{len(messages)}",
                        "content": content
                    })
                else:
                    if content:
                        messages.append({
                            "role": role,
                            "content": content
                        })
            elif isinstance(item, str):
                # Simple string - assume user message
                messages.append({
                    "role": "user",
                    "content": item
                })
        
        return messages
    
    def _convert_tools(self, tools: Optional[List]) -> Optional[List[Dict[str, Any]]]:
        """
        Convert tools to OpenAI format
        
        Args:
            tools: List of tools (can be various formats)
            
        Returns:
            List of OpenAI tool dicts
        """
        if not tools:
            return None
        
        openai_tools = []
        
        for tool in tools:
            if isinstance(tool, dict):
                # Already in OpenAI format
                openai_tools.append(tool)
            elif hasattr(tool, 'function_declarations'):
                # Gemini Tool format - convert
                for func_decl in tool.function_declarations:
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": func_decl.name,
                            "description": func_decl.description,
                            "parameters": func_decl.parameters if hasattr(func_decl, 'parameters') else {}
                        }
                    })
            elif hasattr(tool, 'name'):
                # FunctionDeclaration format
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description if hasattr(tool, 'description') else "",
                        "parameters": tool.parameters if hasattr(tool, 'parameters') else {}
                    }
                })
        
        return openai_tools if openai_tools else None
    
    async def generate_response(
        self,
        prompt: List,
        tools: Optional[List] = None,
        system_instruction: Optional[str] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Generate response from OpenAI API
        
        Args:
            prompt: List of messages (conversation history)
            tools: List of tools/functions available
            system_instruction: System instruction/prompt
            max_tokens: Maximum tokens in response
            
        Returns:
            OpenAI response object
        """
        try:
            # Convert messages to OpenAI format
            messages = self._convert_messages(prompt)
            
            # Add system instruction if provided
            if system_instruction:
                messages.insert(0, {
                    "role": "system",
                    "content": system_instruction
                })
            
            # Convert tools to OpenAI format
            openai_tools = self._convert_tools(tools)
            
            # Prepare request
            request_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
            }
            
            if max_tokens or self.max_tokens:
                request_params["max_tokens"] = max_tokens or self.max_tokens
            
            if openai_tools:
                request_params["tools"] = openai_tools
                request_params["tool_choice"] = "auto"
            
            # Make API call
            response = await self.client.chat.completions.create(**request_params)
            
            return response
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
            raise


# Default client instance
openai_client = OpenAIClient() if OPENAI_API_KEY else None

