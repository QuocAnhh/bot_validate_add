"""Simple agent class - chỉ chat với prompt, không có tools"""
import logging
import time
from typing import AsyncGenerator, Dict, Any, Optional, List
import json

from app.core.agent_config import AgentConfig
from app.services.openai_client import OpenAIClient
from app.prompts.loader import build_prompt_from_config
from app.memory.non_parametric import NonParametricMemory
from app.memory.prompt_builder import build_prompt_from_cases
from app.evaluation.metrics import EvaluationMetrics

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
        
        # Initialize memory if enabled
        self.memory: Optional[NonParametricMemory] = None
        if config.memory.enabled:
            try:
                # Get memory config attributes
                storage_path = config.memory.storage_path or 'memory/cases.jsonl'
                embedding_model = config.memory.embedding_model or 'sentence-transformers/all-MiniLM-L6-v2'
                device = config.memory.device or 'auto'
                
                self.memory = NonParametricMemory(
                    storage_path=storage_path,
                    embedding_model_name=embedding_model,
                    device=device,
                    key_field='user_message',
                    value_field='assistant_response'
                )
                logger.info(f"Memory enabled with {self.memory.get_case_count()} cases")
            except Exception as e:
                logger.warning(f"Failed to initialize memory: {e}, continuing without memory", exc_info=True)
                self.memory = None
        
        # Initialize evaluation metrics (optional)
        self.metrics = EvaluationMetrics()
        
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
        start_time = time.time()
        try:
            # Use default conversation_id if not provided
            if not conversation_id:
                conversation_id = "default"
            
            # Get or create conversation history
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            
            conversation_history = self.conversations[conversation_id]
            
            # Retrieve similar cases from memory if enabled
            memory_prompt = None
            memory_cases_count = 0
            if self.memory and self.config.conversation.enable_memory_injection:
                try:
                    top_k = self.config.memory.top_k
                    filter_negative = self.config.memory.filter_negative
                    
                    # Retrieve cases (filter negative if configured)
                    retrieved_cases = self.memory.retrieve(
                        query=user_message,
                        top_k=top_k,
                        filter_negative=filter_negative
                    )
                    
                    if retrieved_cases:
                        memory_cases_count = len(retrieved_cases)
                        # Build prompt with positive/negative examples
                        memory_prompt = build_prompt_from_cases(
                            query=user_message,
                            retrieved_cases=retrieved_cases,
                            original_cases=self.memory._cases,
                            max_positive=top_k,
                            max_negative=self.config.memory.max_negative_examples,
                            include_negative=(
                                self.config.memory.include_negative_examples 
                                and not filter_negative  # Only if not already filtered
                            )
                        )
                        logger.debug(
                            f"Retrieved {len(retrieved_cases)} cases for query "
                            f"(filter_negative={filter_negative}), "
                            f"memory prompt length: {len(memory_prompt) if memory_prompt else 0}"
                        )
                except Exception as e:
                    logger.warning(f"Memory retrieval failed: {e}", exc_info=True)
            
            # Build user message (with memory if available)
            user_content = user_message
            if memory_prompt:
                user_content = f"{memory_prompt}\n\nCurrent user message: {user_message}"
            
            # Add user message to history
            conversation_history.append({
                "role": "user",
                "content": user_content
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
            
            # Save to memory if enabled (auto-save successful conversations)
            if self.memory and message.content:
                try:
                    # Auto-save successful conversations (can add reward logic later)
                    self.memory.add_case(
                        user_message=user_message,
                        assistant_response=message.content,
                        reward=1  # Default to positive (can add evaluation later)
                    )
                    logger.debug(f"Saved case to memory")
                except Exception as e:
                    logger.warning(f"Failed to save case to memory: {e}")
            
            # Log metrics for evaluation
            response_time = time.time() - start_time
            if message.content:
                try:
                    self.metrics.log_response(
                        query=user_message,
                        response=message.content,
                        has_memory=self.memory is not None and self.config.memory.enabled,
                        memory_cases_used=memory_cases_count,
                        response_time=response_time
                    )
                except Exception as e:
                    logger.debug(f"Failed to log metrics: {e}")
            
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

