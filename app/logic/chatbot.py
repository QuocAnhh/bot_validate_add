import logging
import json
from typing import AsyncGenerator
import csv
import os
from datetime import datetime

from app.state.manager import ConversationState, ConversationData
from app.services.goong import goong_client
from app.services.gemini import gemini_client

logger = logging.getLogger(__name__)

async def stream_message(text: str) -> AsyncGenerator[str, None]:
    """Helper to stream a message text in SSE format."""
    yield f"data: {json.dumps({'content': text})}\n\n"

def create_gemini_prompt(conv_data: ConversationData, user_message: str) -> str:
    """Creates a tailored prompt for Gemini based on the conversation state."""
    base_prompt = (
        "Bạn là một trợ lý ảo xác thực địa chỉ. "
        "Hãy luôn giữ giọng điệu chuyên nghiệp, lịch sự. "
        "QUAN TRỌNG: Hãy trả lời thật ngắn gọn, súc tích, đi thẳng vào vấn đề."
    )
    
    state = conv_data.state
    
    if state == ConversationState.INITIAL:  
        return f"{base_prompt} Bắt đầu cuộc trò chuyện. Gửi một lời chào ngắn gọn và yêu cầu người dùng cung cấp địa chỉ."

    if state == ConversationState.WAITING_FOR_CONFIRMATION:
        return (
            f"{base_prompt} "
            f"Bạn đã tìm thấy địa chỉ gợi ý: '{conv_data.potential_address}'. "
            f"Hỏi người dùng xác nhận địa chỉ này trong một câu ngắn gọn, yêu cầu họ trả lời 'đúng' hoặc 'sai'."
        )
    
    if state == ConversationState.WAITING_FOR_DISTRICT:
        return (
            f"{base_prompt} "
            f"Người dùng nói địa chỉ trước đó là sai. "
            "Yêu cầu họ cung cấp thêm thông tin quận/huyện một cách ngắn gọn."
        )

    if state == ConversationState.WAITING_FOR_CLARIFICATION:
        address_options = ""
        for i, addr in enumerate(conv_data.potential_addresses, 1):
            address_options += f"{i}. {addr['description']}\\n"
        
        return (
            f"{base_prompt} "
            f"Bạn đã tìm thấy nhiều kết quả khớp với địa chỉ '{conv_data.address_raw}'. "
            "Hãy hiển thị các lựa chọn sau cho người dùng và yêu cầu họ chọn một bằng cách trả lời số thứ tự tương ứng. "
            "Nếu không có lựa chọn nào đúng, hãy yêu cầu họ cung cấp lại địa chỉ đầy đủ hơn.\\n\\n"
            f"Các lựa chọn:\\n{address_options}"
        )

    return f"{base_prompt} Người dùng nói: '{user_message}'. Hãy phản hồi ngắn gọn."

def log_confirmed_address(conversation_id: str, address: str, lat: float, lng: float):
    """Appends a confirmed address to a CSV file."""
    filepath = "confirmed_addresses.csv"
    file_exists = os.path.isfile(filepath)

    try:
        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'conversation_id', 'address', 'latitude', 'longitude']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'conversation_id': conversation_id,
                'address': address,
                'latitude': lat,
                'longitude': lng
            })
        logger.info(f"Logged confirmed address for conv {conversation_id} to {filepath}")
    except IOError as e:
        logger.error(f"Failed to write to {filepath}: {e}")

async def chatbot_logic_generator(conv_data: ConversationData, user_message: str, conversation_id: str) -> AsyncGenerator[str, None]:
    """
    The main state machine powered by Gemini for natural language responses.
    """
    try:
        # STATE: INITIAL
        if conv_data.state == ConversationState.INITIAL:
            prompt = create_gemini_prompt(conv_data, user_message)
            response_text = await gemini_client.generate_response(prompt)
            conv_data.state = ConversationState.WAITING_FOR_ADDRESS
            async for chunk in stream_message(response_text):
                yield chunk
            return

        # STATE: WAITING_FOR_CONFIRMATION (Handling user's yes/no)
        if conv_data.state == ConversationState.WAITING_FOR_CONFIRMATION:
            user_lower = user_message.lower().strip()
            confirm_words = ["đúng", "yes", "ok", "chính xác"]
            deny_words = ["sai", "không", "ko", "chưa", "nhầm"]

            if any(word in user_lower for word in confirm_words):
                log_confirmed_address(
                    conversation_id=conversation_id,
                    address=conv_data.potential_address,
                    lat=conv_data.potential_lat,
                    lng=conv_data.potential_lng
                )
                
                prompt = (
                    "Bạn là trợ lý ảo. Trả lời thật ngắn gọn. "
                    "Hãy cảm ơn và xác nhận địa chỉ đã được ghi nhận "
                    f"Tọa độ là: Lat {conv_data.potential_lat}, Lng {conv_data.potential_lng}."
                )
                response_text = await gemini_client.generate_response(prompt)
                async for chunk in stream_message(response_text):
                    yield chunk
                
                conv_data.state = ConversationState.INITIAL
                return

            elif any(word in user_lower for word in deny_words):
                conv_data.retry_count += 1
                if conv_data.retry_count >= 3:
                    prompt = "Bạn là trợ lý ảo. Trả lời ngắn gọn. Thông báo cho người dùng rằng đã thử quá 3 lần và sẽ bắt đầu lại."
                    response_text = await gemini_client.generate_response(prompt)
                    async for chunk in stream_message(response_text):
                        yield chunk
                    conv_data.state = ConversationState.INITIAL
                    return
                
                conv_data.state = ConversationState.WAITING_FOR_DISTRICT
                prompt = create_gemini_prompt(conv_data, user_message)
                response_text = await gemini_client.generate_response(prompt)
                async for chunk in stream_message(response_text):
                    yield chunk
                return

        # STATE: WAITING_FOR_CLARIFICATION (User needs to choose an address)
        if conv_data.state == ConversationState.WAITING_FOR_CLARIFICATION:
            try:
                choice = int(user_message.strip())
                if 1 <= choice <= len(conv_data.potential_addresses):
                    chosen_prediction = conv_data.potential_addresses[choice - 1]
                    place_id = chosen_prediction.get("place_id")

                    if not place_id:
                        raise ValueError("Missing place_id in autocomplete prediction.")

                    place_details = await goong_client.get_place_details(place_id)
                    
                    if not place_details:
                        prompt = "Bạn là trợ lý ảo. Trả lời ngắn gọn. Thông báo có lỗi xảy ra khi lấy chi tiết địa chỉ và yêu cầu thử lại."
                        response_text = await gemini_client.generate_response(prompt)
                        async for chunk in stream_message(response_text):
                            yield chunk
                        conv_data.state = ConversationState.WAITING_FOR_ADDRESS
                        return

                    conv_data.potential_address = place_details.get("formatted_address")
                    location = place_details.get("geometry", {}).get("location", {})
                    conv_data.potential_lat = location.get("lat")
                    conv_data.potential_lng = location.get("lng")
                    
                    conv_data.state = ConversationState.WAITING_FOR_CONFIRMATION
                    prompt = create_gemini_prompt(conv_data, user_message)
                    response_text = await gemini_client.generate_response(prompt)
                    async for chunk in stream_message(response_text):
                        yield chunk
                    return
                else:
                    raise ValueError("Choice out of range.")
            except (ValueError, IndexError):
                conv_data.state = ConversationState.WAITING_FOR_ADDRESS
                prompt = "Bạn là trợ lý ảo. Trả lời ngắn gọn. Yêu cầu người dùng cung cấp lại địa chỉ một cách chi tiết hơn."
                response_text = await gemini_client.generate_response(prompt)
                async for chunk in stream_message(response_text):
                    yield chunk
                return

        # STATE: WAITING_FOR_ADDRESS or WAITING_FOR_DISTRICT (Main geocoding logic)
        if conv_data.state in [ConversationState.WAITING_FOR_ADDRESS, ConversationState.WAITING_FOR_DISTRICT]:
            if conv_data.state == ConversationState.WAITING_FOR_DISTRICT:
                conv_data.address_raw = f"{conv_data.address_raw}, {user_message}"
            else:
                conv_data.address_raw = user_message

            checking_message = "Dạ, em đang kiểm tra..."
            async for chunk in stream_message(checking_message):
                yield chunk

            predictions = await goong_client.autocomplete(conv_data.address_raw)
            
            if not predictions:
                prompt = "Bạn là trợ lý ảo. Trả lời ngắn gọn. Thông báo không tìm thấy địa chỉ và yêu cầu cung cấp lại thông tin cụ thể hơn."
                response_text = await gemini_client.generate_response(prompt)
                async for chunk in stream_message(response_text):
                    yield chunk
                conv_data.state = ConversationState.WAITING_FOR_ADDRESS
                return

            if len(predictions) > 1:
                conv_data.potential_addresses = predictions[:3]
                conv_data.state = ConversationState.WAITING_FOR_CLARIFICATION
                prompt = create_gemini_prompt(conv_data, "")
                response_text = await gemini_client.generate_response(prompt)
                async for chunk in stream_message(response_text):
                    yield chunk
                return

            first_prediction = predictions[0]
            place_id = first_prediction.get("place_id")
            if not place_id:
                prompt = "Bạn là trợ lý ảo. Trả lời ngắn gọn. Thông báo có lỗi với địa chỉ được tìm thấy và yêu cầu cung cấp lại."
                response_text = await gemini_client.generate_response(prompt)
                async for chunk in stream_message(response_text):
                    yield chunk
                conv_data.state = ConversationState.WAITING_FOR_ADDRESS
                return

            place_details = await goong_client.get_place_details(place_id)
            if not place_details:
                prompt = "Bạn là trợ lý ảo. Trả lời ngắn gọn. Thông báo có lỗi xảy ra khi lấy chi tiết địa chỉ và yêu cầu thử lại."
                response_text = await gemini_client.generate_response(prompt)
                async for chunk in stream_message(response_text):
                    yield chunk
                conv_data.state = ConversationState.WAITING_FOR_ADDRESS
                return

            conv_data.potential_address = place_details.get("formatted_address")
            location = place_details.get("geometry", {}).get("location", {})
            conv_data.potential_lat = location.get("lat")
            conv_data.potential_lng = location.get("lng")
            
            conv_data.state = ConversationState.WAITING_FOR_CONFIRMATION
            prompt = create_gemini_prompt(conv_data, user_message)
            response_text = await gemini_client.generate_response(prompt)
            async for chunk in stream_message(response_text):
                yield chunk
            return

    except Exception as e:
        logger.error(f"Error in chatbot logic: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': 'An internal server error occurred.'})}\n\n" 