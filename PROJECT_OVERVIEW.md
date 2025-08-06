# Tổng quan dự án Chatbot Xác thực Địa chỉ

Đây là tài liệu giải thích chi tiết về cấu trúc thư mục và luồng hoạt động của dự án chatbot.

## I. Cấu trúc thư mục

Dự án được cấu trúc theo module để đảm bảo code sạch sẽ, dễ bảo trì và mở rộng.

```
test_api_map/
├── app/
│   ├── __init__.py             # Đánh dấu thư mục app là một package Python
│   ├── main.py                 # Khởi tạo ứng dụng FastAPI, cấu hình middleware (CORS, logging)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # Định nghĩa tất cả các API endpoint (VD: /chat/stream, /health)
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Tải các biến cấu hình và khóa API từ file .env
│   ├── logic/
│   │   ├── __init__.py
│   │   └── chatbot.py          # Chứa logic cốt lõi của chatbot, bao gồm cả máy trạng thái (state machine)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── chat.py             # Định nghĩa các Pydantic model để xác thực dữ liệu request (payload)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini.py           # Client để tương tác với Google Gemini API
│   │   └── goong.py            # Client để tương tác với Goong Maps API
│   └── state/
│       ├── __init__.py
│       └── manager.py          # Quản lý trạng thái của các cuộc hội thoại (lưu trữ trong bộ nhớ)
├── main.py                     # Entrypoint - Điểm bắt đầu để chạy ứng dụng bằng uvicorn
├── confirmed_addresses.csv     # File CSV để lưu lại các địa chỉ đã được xác nhận thành công
├── requirements.txt            # Danh sách các thư viện Python cần thiết cho dự án
└── .env                        # (File người dùng tự tạo) Chứa các khóa API bí mật
```

## II. Luồng hoạt động (Workflow)

Luồng xử lý chính bắt đầu khi có một request được gửi đến endpoint `/chat/stream`.

1.  **Tiếp nhận Request:**
    *   Live-demo gửi một HTTP POST request đến `/chat/stream`.
    *   `app/api/routes.py` tiếp nhận request này. Dữ liệu (payload) được validate dựa trên Pydantic model `StreamChatRequest` trong `app/schemas/chat.py`.

2.  **Quản lý Trạng thái:**
    *   Hàm `stream_chat_handler` trong `routes.py` gọi hàm `get_or_create_conversation` từ `app/state/manager.py`.
    *   Hàm này sẽ tìm kiếm cuộc hội thoại dựa trên `conversation_id`. Nếu chưa có, nó sẽ tạo một đối tượng `ConversationData` mới và lưu vào một dictionary trong bộ nhớ. Nếu đã có, nó sẽ lấy ra dữ liệu state hiện tại.

3.  **Xử lý Logic Chatbot:**
    *   Endpoint sau đó gọi hàm `chatbot_logic_generator` trong `app/logic/chatbot.py`, truyền vào dữ liệu state (`conv_data`) và tin nhắn của người dùng.
    *   Đây là nơi diễn ra "bộ não" của chatbot, hoạt động như một máy trạng thái (state machine):
        *   **`INITIAL`**: Nếu là tin nhắn đầu tiên, bot gửi lời chào và yêu cầu địa chỉ.
        *   **`WAITING_FOR_ADDRESS`**: Khi nhận được địa chỉ, bot gọi `goong_client.autocomplete()` (từ `app/services/goong.py`).
        *   **Xử lý kết quả từ Goong:**
            *   **Nhiều kết quả**: Nếu API trả về nhiều hơn một gợi ý, bot lưu lại 3 gợi ý hàng đầu, chuyển state sang `WAITING_FOR_CLARIFICATION` và dùng Gemini để tạo câu hỏi yêu cầu người dùng chọn.
            *   **Một kết quả**: Nếu chỉ có một gợi ý, bot sẽ lấy `place_id` và gọi `goong_client.get_place_details()` ngay lập tức.
            *   **Không có kết quả**: Bot thông báo không tìm thấy và yêu cầu nhập lại.
        *   **`WAITING_FOR_CLARIFICATION`**: Bot chờ người dùng nhập số thứ tự (1, 2, 3) tương ứng với địa chỉ họ muốn. Sau khi người dùng chọn, bot lấy `place_id` và gọi `get_place_details`.
        *   **Lấy chi tiết và chờ xác nhận**: Sau khi `get_place_details` trả về thông tin chi tiết (địa chỉ đầy đủ, lat, lng), bot lưu các thông tin này, chuyển state sang `WAITING_FOR_CONFIRMATION` và yêu cầu người dùng xác nhận lần cuối.
        *   **`WAITING_FOR_CONFIRMATION`**:
            *   Nếu người dùng trả lời "đúng", bot gọi hàm `log_confirmed_address` để ghi vào file `confirmed_addresses.csv`, sau đó gửi lời cảm ơn và kết thúc.
            *   Nếu người dùng trả lời "sai", bot tăng biến đếm `retry_count` và yêu cầu cung cấp lại thông tin.

4.  **Tạo phản hồi bằng AI:**
    *   Trong suốt quá trình, mỗi khi cần tạo một câu trả lời tự nhiên, `chatbot.py` sẽ gọi hàm `gemini_client.generate_response()` (từ `app/services/gemini.py`) với một prompt đã được xây dựng tùy theo ngữ cảnh.

5.  **Streaming Phản hồi:**
    *   Toàn bộ quá trình trả lời được thực hiện dưới dạng streaming (Server-Sent Events), giúp phản hồi được gửi đến client ngay lập tức mà không cần chờ toàn bộ logic xử lý xong. 