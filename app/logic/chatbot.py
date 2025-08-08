import logging
import json
from typing import AsyncGenerator

from app.state.manager import ConversationData
from app.services.goong import goong_client
from app.services.gemini import gemini_client
from app.logic.tools import address_validation_tool

from google.generativeai.protos import Content, Part

logger = logging.getLogger(__name__)


async def stream_message(content: str) -> AsyncGenerator[dict, None]:
    """gửi message đến người dùng"""
    yield {"data": json.dumps({"content": content})}


async def chatbot_logic_generator(conv_data: ConversationData, user_message: str, conversation_id: str) -> AsyncGenerator[dict, None]:
    """logic chatbot """
    try:
        # 1. append tin nhan moi vao history
        conv_data.add_message("user", user_message)

        # 2. call gemini API với full history và available tools
        initial_response = await gemini_client.generate_response(
            prompt=conv_data.history,
            tools=[address_validation_tool]
        )

        response_part = initial_response.candidates[0].content.parts[0]

        # 3. check if the model decided to call a tool
        if response_part.function_call:
            function_call = response_part.function_call
            
            # currently, we only have one tool. In the future, a dispatcher could be used.
            if function_call.name == "search_address_in_vietnam":
                # 3a. acknowledge and execute the tool call
                query = function_call.args.get("query", "")
                
                # let the user know what the bot is doing
                async for chunk in stream_message(f"Đang tìm kiếm địa chỉ: '{query}'..."):
                    yield chunk

                tool_results = await goong_client.autocomplete(query)

                # 3b. Send the tool's result back to the model
                # The LLM will now analyze the tool results in the context of the conversation.
                tool_response_prompt = conv_data.history + [
                    Content(
                        parts=[
                            Part(function_call=function_call),
                            Part(
                                function_response={
                                    "name": "search_address_in_vietnam",
                                    "response": {"predictions": tool_results},
                                }
                            ),
                        ],
                    )
                ]

                # Call Gemini again with the tool's output
                final_response_obj = await gemini_client.generate_response(
                    prompt=tool_response_prompt
                )
                final_response_text = final_response_obj.text
                
                # 3c. Stream the final, synthesized response to the user
                conv_data.add_message("assistant", final_response_text)
                async for chunk in stream_message(final_response_text):
                    yield chunk

            else:
                # handle cases where an unknown tool is called
                async for chunk in stream_message("Lỗi: Bot đã cố gắng gọi một công cụ không xác định."):
                    yield chunk
        
        else:
            # 4. If no tool is called, it's a direct text response
            # We also limit this response to keep it concise.
            direct_response_text = initial_response.text
            conv_data.add_message("assistant", direct_response_text)
            async for chunk in stream_message(direct_response_text):
                yield chunk

    except Exception as e:
        logger.error(f"Error in chatbot logic for conv {conversation_id}: {e}", exc_info=True)
        error_payload = {"error": "An internal server error occurred."}
        yield {"data": json.dumps(error_payload)} 