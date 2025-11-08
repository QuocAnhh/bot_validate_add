import logging
import json
from typing import AsyncGenerator, Dict, Any, Optional, Tuple
from dataclasses import asdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re
import dateparser
import asyncio



from app.state.manager import ConversationData
from app.services.goong import goong_client
from app.services.gemini import gemini_client
from app.logic.tools import booking_tools 
from app.services.trip_service import find_trips as db_find_trips
from app.services.logging_service import log_trip_request
from google.generativeai.protos import Content, Part, FunctionCall

logger = logging.getLogger(__name__)


async def stream_message(content: str) -> AsyncGenerator[dict, None]:
    """gửi message đến người dùng"""
    yield {"data": json.dumps({"content": content})}


def _is_filler_message(text: str) -> bool:
    if not text:
        return False
    s = text.strip().lower()
    patterns = [
        r"vui lòng (đợi|chờ)",
        r"đợi một chút",
        r"chờ một chút",
        r"đợi tí",
        r"để em tìm",
        r"em (sẽ )?tìm",
        r"đang tìm",
        r"em kiểm tra",
        r"ok[,.!? ]|được[,.!? ]",
    ]
    return any(re.search(p, s) for p in patterns)


async def _handle_search_address(
    conv_data: ConversationData, args: Dict[str, Any]
) -> Part:
    """xử lý lệnh gọi tool 'search_address_in_vietnam'"""
    query = args.get("query", "")
    tool_results = await goong_client.autocomplete(query)
    return Part(
        function_response={
            "name": "search_address_in_vietnam",
            "response": tool_results,
        }
    )

def _parse_departure_time_vi(text_time: str) -> Optional[datetime]:
    """
    Parses Vietnamese-style date/time expressions into timezone-aware datetime objects.

    This function handles:
    1. Common relative terms like 'hôm nay', 'ngày mai', 'ngày kia'.
    2. Time periods like 'sáng', 'trưa', 'chiều', 'tối'.
    3. Standard time formats as a fallback using the `dateparser` library.

    Args:
        text_time: The Vietnamese time string to parse.

    Returns:
        A timezone-aware datetime object for "Asia/Ho_Chi_Minh" or None if parsing fails.
    """
    if not text_time:
        return None

    try:
        now_in_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        text_lower = text_time.strip().lower()

        # Manual parsing for specific Vietnamese patterns first
        # This approach is more reliable for common, sometimes ambiguous phrases
        parsed_datetime = _parse_vietnamese_time_manually(text_lower, now_in_vn)
        if parsed_datetime:
            logger.debug("Successfully parsed '%s' manually -> %s", text_time, parsed_datetime)
            return parsed_datetime

        # Fallback to the general-purpose dateparser library
        # This handles a wider range of formats but can sometimes be less accurate
        # for colloquialisms.
        dateparser_settings = {
            "TIMEZONE": "Asia/Ho_Chi_Minh",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": now_in_vn,
            "DATE_ORDER": "DMY",
        }
        fallback_dt = dateparser.parse(text_time, languages=["vi", "en"], settings=dateparser_settings)
        if fallback_dt:
            logger.debug("Dateparser fallback for '%s' -> %s", text_time, fallback_dt)
            return fallback_dt

        logger.warning("Could not parse departure time: '%s'", text_time)
        return None
    except Exception as e:
        logger.error("Error parsing time string '%s': %s", text_time, e, exc_info=True)
        return None


def _parse_vietnamese_date(text: str, base_date: datetime) -> Optional[datetime.date]:
    """Parses relative Vietnamese date terms."""
    if "ngày kia" in text or "kia" in text:
        return (base_date + timedelta(days=2)).date()
    if "ngày mai" in text or "mai" in text:
        return (base_date + timedelta(days=1)).date()
    if "hôm nay" in text:
        return base_date.date()
    return None


def _parse_vietnamese_time_of_day(text: str, hour: int, minute: int) -> Optional[Tuple[int, int]]:
    """Adjusts hour based on Vietnamese time-of-day qualifiers."""
    # Default to the provided hour if no qualifier is found
    target_hour = hour

    if "sáng" in text:
        if 1 <= hour <= 11: target_hour = hour
        elif hour == 12: target_hour = 0  # 12 AM is midnight
    elif "trưa" in text:
        if hour == 12 or hour == 1: target_hour = 12
    elif "chiều" in text:
        if 1 <= hour <= 6: target_hour = hour + 12
        elif 13 <= hour <= 18: target_hour = hour
    elif "tối" in text:
        if 6 <= hour <= 11: target_hour = hour + 12
        elif 18 <= hour <= 23: target_hour = hour
    
    return target_hour, minute


def _parse_vietnamese_time_manually(text: str, base_now: datetime) -> Optional[datetime]:
    """
    Attempts to parse a Vietnamese time string using explicit rules.
    This is more reliable for common colloquialisms than a generic parser.
    """
    target_date = _parse_vietnamese_date(text, base_now)
    
    # Regex to find hours and optional minutes (e.g., "9h30", "15:00", "7 giờ")
    hour_match = re.search(r"(\d{1,2})(?:\s*[h:]\s*(\d{1,2}))?", text)
    if not hour_match:
        return None

    hour = int(hour_match.group(1))
    minute = int(hour_match.group(2)) if hour_match.group(2) else 0

    time_of_day = _parse_vietnamese_time_of_day(text, hour, minute)
    if not time_of_day:
        return None
        
    target_hour, target_minute = time_of_day

    # If no date was specified, assume today or tomorrow depending on the time
    if not target_date:
        if target_hour < base_now.hour:
            # If the requested hour is in the past, assume it's for the next day
            target_date = (base_now + timedelta(days=1)).date()
        else:
            target_date = base_now.date()
    
    try:
        # Combine the date and time components
        final_dt = datetime.combine(
            target_date, 
            datetime.min.time().replace(hour=target_hour, minute=target_minute)
        )
        # Return as a timezone-aware object
        return final_dt.replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
    except ValueError:
        logger.warning("Could not combine date/time for: %s, %s:%s", target_date, target_hour, target_minute)
        return None


async def _handle_find_trips(
    conv_data: ConversationData, args: Dict[str, Any]
) -> Part:
    """Handler for the 'find_trips' tool call with DB-backed results and safe fallback."""
    # cập nhật state với thông tin từ tool call
    conv_data.booking_state.origin = args.get("origin")
    conv_data.booking_state.destination = args.get("destination")
    conv_data.booking_state.departure_time = args.get("departure_time")

    parsed_dt = _parse_departure_time_vi(conv_data.booking_state.departure_time)
    
    trips = db_find_trips(
        origin=(conv_data.booking_state.origin or "").strip(),
        destination=(conv_data.booking_state.destination or "").strip(),
        departure_dt=parsed_dt,
    )

    if trips and trips[0].get("status") == "ROUTE_EXISTS":
        origin_coords_task = goong_client.get_coords_from_address(conv_data.booking_state.origin)
        dest_coords_task = goong_client.get_coords_from_address(conv_data.booking_state.destination)
        
        origin_coords, dest_coords = await asyncio.gather(origin_coords_task, dest_coords_task)
        
        log_trip_request(
            origin_address=conv_data.booking_state.origin or "",
            origin_coords=origin_coords,
            destination_address=conv_data.booking_state.destination or "",
            destination_coords=dest_coords,
            departure_time_text=conv_data.booking_state.departure_time or ""
        )
    
    # không có fallback giả: nếu DB không được cấu hình hoặc không có kết quả, trả về danh sách trống và cho phép LLM thông báo cho người dùng
    if not trips:
        trips = []

    conv_data.booking_state.available_trips = trips

    return Part(
        function_response={
            "name": "find_trips",
            "response": {"trips": trips},
        }
    )


async def _handle_book_trip(
    conv_data: ConversationData, args: Dict[str, Any]
) -> Part:
    
    trip_id = args.get("trip_id")
    trip_to_book = next((trip for trip in conv_data.booking_state.available_trips if trip["trip_id"] == trip_id), None)

    if not trip_to_book:
        return Part(function_response={"name": "book_trip", "response": {"success": False, "error": "Không tìm thấy chuyến đi với ID này."}})

    conv_data.booking_state.selected_trip_id = trip_id
    conv_data.booking_state.status = "confirmed"

    booking_confirmation = {
        "success": True,
        "booking_id": f"BK-{trip_id}-{hash(args.get('passenger_name'))}",
        "passenger_name": args.get("passenger_name"),
        "details": f"Đã đặt thành công chuyến đi {trip_id} của nhà xe {trip_to_book.get('provider')}.",
    }

    return Part(function_response={"name": "book_trip", "response": booking_confirmation})


async def _execute_function_call(
    conv_data: ConversationData, function_call: FunctionCall
) -> Part:
    """phân tích và thực thi công cụ phù hợp"""
    tool_name = function_call.name
    tool_args = function_call.args

    if tool_name == "search_address_in_vietnam":
        return await _handle_search_address(conv_data, tool_args)
    if tool_name == "find_trips":
        return await _handle_find_trips(conv_data, tool_args)
    if tool_name == "book_trip":
        return await _handle_book_trip(conv_data, tool_args)
    
    return Part(function_response={"name": tool_name, "response": {"error": f"Tool '{tool_name}' không được hỗ trợ."}})


async def chatbot_logic_generator(conv_data: ConversationData, user_message: str, conversation_id: str) -> AsyncGenerator[dict, None]:
    
    try:
        # 1. thêm tin nhắn của người dùng và trạng thái vào context, kèm thời gian hiện tại 
        now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        now_context = (
            f"Thời gian hiện tại (giờ Việt Nam): {now_vn.strftime('%Y-%m-%d %H:%M')}\n"
            f"Nếu người dùng nói các cụm như 'hôm nay', 'ngày mai', 'tối mai', hãy hiểu theo thời gian hiện tại này.\n"
            f"Nếu đã có 'departure_time' trong trạng thái, đừng hỏi lại thời gian, chỉ xác nhận ngắn gọn nếu cần."
        )

        context_message = (
            f"{now_context}\n"
            f"Người dùng nói: '{user_message}'.\n"
            f"Trạng thái đặt vé hiện tại là: {json.dumps(asdict(conv_data.booking_state), ensure_ascii=False)}.\n"
            "Dựa trên lịch sử hội thoại và trạng thái này, hãy quyết định bước đi tiếp theo một cách hợp lý."
        )
        conv_data.add_message("user", context_message)

        max_steps = 4
        steps = 0
        while True:
            steps += 1
            # gọi gemini API với toàn bộ lịch sử hiện tại
            response = await gemini_client.generate_response(
                prompt=conv_data.history,
                tools=[booking_tools]
            )
            
            if not response.candidates:
                logger.warning(f"Gemini API returned no candidates for conv {conversation_id}. Feedback: {response.prompt_feedback}")
                error_payload = {"error": "Xin lỗi, BIVA không thể xử lý yêu cầu này. Vui lòng thử lại với một câu hỏi khác."}
                yield {"data": json.dumps(error_payload)}
                break

            response_content = response.candidates[0].content

            # thêm lượt trả lời của model vào history (dù là tool call hay text)
            conv_data.history.append(response_content)

            # kiểm tra xem CÓ BẤT KỲ tool call nào trong các part của response không
            has_tool_call = any(part.function_call for part in response_content.parts)

            if not has_tool_call:
                # không có tool call: stream văn bản
                final_text = response.text
                if final_text:
                    async for chunk in stream_message(final_text):
                        yield chunk
                # nếu là filler message thì TIẾP TỤC vòng lặp để buộc model gọi tool
                if _is_filler_message(final_text) and steps < max_steps:
                    logger.warning(
                        f"Filler message detected for conv {conversation_id}. "
                        f"Content: '{final_text}'. Forcing a tool call retry ({steps}/{max_steps})."
                    )
                    continue
                # kết thúc nếu không phải filler hoặc đã quá số bước an toàn
                break

            # 4. có tool call: model muốn sử dụng một công cụ
            # thực thi các tool call được yêu cầu
            tool_response_parts = []
            for part in response_content.parts:
                if fc := part.function_call:
                    tool_result = await _execute_function_call(conv_data, fc)
                    tool_response_parts.append(tool_result)

            # thêm kết quả của tool vào history để chuẩn bị cho lần lặp tiếp theo
            tool_response_content = Content(parts=tool_response_parts, role="tool")
            conv_data.history.append(tool_response_content)
            
            # vòng lặp sẽ tiếp tục, gửi kết quả của tool về lại cho model

    except Exception as e:
        logger.error(f"Error in chatbot logic for conv {conversation_id}: {e}", exc_info=True)
        error_payload = {"error": "An internal server error occurred."}
        yield {"data": json.dumps(error_payload)}