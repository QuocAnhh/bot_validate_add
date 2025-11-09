"""Base agent class with tool support"""
import logging
from typing import AsyncGenerator, Dict, Any, Optional, List
import json

from app.core.agent_config import AgentConfig
from app.services.openai_client import OpenAIClient
from app.prompts.loader import build_prompt_from_config

logger = logging.getLogger("agent")


class BaseAgent:
    """Base agent class with tool support"""
    
    def __init__(self, config: AgentConfig):
        """
        Initialize base agent with configuration
        
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
        
        # Build tools
        self.tools = self._build_tools()
        
        # Conversation history per conversation_id
        self.conversations: Dict[str, List[Dict[str, str]]] = {}
        
        logger.info(f"Initialized base agent: {self.agent_name} with {len(self.tools)} tools")
    
    def _build_system_prompt(self) -> str:
        """
        Build system prompt from config
        
        Returns:
            System prompt string
        """
        config_dict = self.config.model_dump()
        return build_prompt_from_config(config_dict)
    
    def _build_tools(self) -> Optional[List[Dict[str, Any]]]:
        """
        Build tools from config
        
        Returns:
            List of tools in OpenAI format
        """
        if not self.config.tools:
            return None
        
        tools = []
        for tool_config in self.config.tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_config.name,
                    "description": tool_config.description,
                    "parameters": tool_config.parameters
                }
            })
        
        return tools if tools else None
    
    async def get_conversation_state(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get conversation state (can be overridden by subclasses)
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation state dictionary
        """
        return {
            "conversation_id": conversation_id
        }
    
    async def update_conversation_state(
        self,
        conversation_id: str,
        state: Dict[str, Any]
    ):
        """
        Update conversation state (can be overridden by subclasses)
        
        Args:
            conversation_id: Conversation ID
            state: State dictionary to update
        """
        pass
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a tool call (can be overridden by subclasses)
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        logger.warning(f"Tool {tool_name} not implemented, returning empty result")
        return {"result": "Tool not implemented"}
    
    async def process_message(
        self,
        user_message: str,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process user message and generate response (with tool support)
        
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
            
            # Process with tool support (may require multiple rounds)
            max_iterations = self.config.conversation.max_steps
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Build messages for OpenAI
                messages = conversation_history.copy()
                
                # Call OpenAI with tools
                logger.debug(
                    f"Calling OpenAI (iteration {iteration}) - Agent: {self.agent_name}, "
                    f"Conversation: {conversation_id}, "
                    f"History length: {len(messages)}"
                )
                
                response = await self.client.generate_response(
                    prompt=messages,
                    tools=self.tools,
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
                
                # Add assistant message to history
                assistant_message = {
                    "role": "assistant",
                    "content": message.content or None
                }
                
                # Check if tool calls are present
                if message.tool_calls:
                    assistant_message["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                    conversation_history.append(assistant_message)
                    
                    # Execute tool calls
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            # Parse arguments
                            arguments = json.loads(tool_call.function.arguments)
                            
                            # Execute tool
                            tool_result = await self._execute_tool(tool_name, arguments)
                            
                            # Add tool result to history
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })
                            
                            logger.info(
                                f"Executed tool {tool_name} - Agent: {self.agent_name}, "
                                f"Conversation: {conversation_id}"
                            )
                        except Exception as e:
                            logger.error(
                                f"Error executing tool {tool_name}: {e}",
                                exc_info=True
                            )
                            # Add error to history
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps({"error": str(e)}, ensure_ascii=False)
                            })
                    
                    # Continue loop to get final response
                    continue
                else:
                    # No tool calls, final response
                    conversation_history.append(assistant_message)
                    
                    # Log response
                    response_length = len(message.content or "")
                    logger.info(
                        f"OpenAI response - Agent: {self.agent_name}, "
                        f"Conversation: {conversation_id}, "
                        f"Response length: {response_length}"
                    )
                    
                    # Stream response
                    if message.content:
                        yield {"data": json.dumps({"content": message.content})}
                    
                    # Break out of loop
                    break
            
            if iteration >= max_iterations:
                logger.warning(
                    f"Max iterations reached - Agent: {self.agent_name}, "
                    f"Conversation: {conversation_id}"
                )
                yield {"data": json.dumps({"error": "Đã đạt số lần xử lý tối đa. Vui lòng thử lại."})}
            
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

