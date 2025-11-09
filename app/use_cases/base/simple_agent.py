"""Simple agent class - chỉ chat với prompt, không có tools"""
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List
import json

from app.core.agent_config import AgentConfig
from app.services.openai_client import OpenAIClient
from app.prompts.loader import build_prompt_from_config

logger = logging.getLogger("agent")


class SimpleAgent:
    """Simple agent - chỉ chat với prompt, không có tools"""
    
    def __init__(self, config: AgentConfig):
        """
        Initialize simple agent with configuration
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.agent_name = config.agent.get('name', 'Assistant')
        self.agent_description = config.agent.get('description', '')
        
        # Initialize OpenAI client
        model_config = config.model
        self.client = OpenAIClient(
            model_name=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens
        )
        
        # Build system prompt
        self.system_prompt = self._build_system_prompt()
        
        # Conversation history per conversation_id
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        
        logger.info(f"Initialized simple agent: {self.agent_name}")
    
    def _build_system_prompt(self) -> str:
        """
        Build system prompt from config
        
        Returns:
            System prompt string
        """
        config_dict = self.config.model_dump()
        return build_prompt_from_config(config_dict)
    
    async def process_message(
        self,
        user_message: str,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process user message and generate response (simple - no tools)
        
        Args:
            user_message: User message
            conversation_id: Conversation ID (optional, defaults to "default")
            
        Yields:
            Response chunks
        """
        try:
            # Use default conversation_id if not provided
            if not conversation_id:
                conversation_id = "default"
            
            # Get or create conversation history
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            
            conversation_history = self.conversations[conversation_id]
            
            # Add user message to history
            conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Build messages for OpenAI
            messages = conversation_history.copy()
            
            # Call OpenAI (no tools)
            logger.debug(
                f"Calling OpenAI - Agent: {self.agent_name}, "
                f"Conversation: {conversation_id}, "
                f"History length: {len(messages)}"
            )
            
            response = await self.client.generate_response(
                prompt=messages,
                tools=None,  # No tools for simple agent
                system_instruction=self.system_prompt
            )
            
            if not response.choices:
                logger.warning(
                    f"No response from OpenAI - Agent: {self.agent_name}, "
                    f"Conversation: {conversation_id}"
                )
                yield {"data": json.dumps({"error": "Không thể xử lý yêu cầu này. Vui lòng thử lại."})}
                return
            
            choice = response.choices[0]
            message = choice.message
            
            # Log response
            response_length = len(message.content or "")
            logger.info(
                f"OpenAI response - Agent: {self.agent_name}, "
                f"Conversation: {conversation_id}, "
                f"Response length: {response_length}"
            )
            
            # Add assistant message to history
            assistant_message = {
                "role": "assistant",
                "content": message.content or ""
            }
            conversation_history.append(assistant_message)
            
            # Stream response
            if message.content:
                yield {"data": json.dumps({"content": message.content})}
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            yield {"data": json.dumps({"error": "Đã xảy ra lỗi khi xử lý yêu cầu."})}
    
    def reset_conversation(self, conversation_id: Optional[str] = None):
        """
        Reset conversation history
        
        Args:
            conversation_id: Conversation ID to reset (if None, resets all)
        """
        if conversation_id:
            if conversation_id in self.conversations:
                self.conversations[conversation_id].clear()
                logger.info(f"Reset conversation {conversation_id} for agent: {self.agent_name}")
        else:
            self.conversations.clear()
            logger.info(f"Reset all conversations for agent: {self.agent_name}")

