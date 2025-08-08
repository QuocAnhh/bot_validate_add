# Chatbot verify address with Gemini & Function Calling

## Kiến trúc cốt lõi: Tool Calling

### Luồng hoạt động
1.  **Gửi yêu cầu & Công cụ cho LLM:** Toàn bộ lịch sử trò chuyện và danh sách các "công cụ" có sẵn được gửi đến Gemini.
2.  **LLM ra quyết định:** Gemini phân tích ngữ cảnh và quyết định:
    *   **Trả lời trực tiếp:** Nếu câu hỏi không liên quan đến địa chỉ.
    *   **Gọi công cụ:** Nếu người dùng yêu cầu tìm kiếm địa chỉ, Gemini sẽ tạo ra một **lệnh gọi hàm** (function call) với các tham số cần thiết (ví dụ: `search_address_in_vietnam(query='công viên hòa bình, hà nội')`).
3.  **Backend thực thi:**
    *   Ứng dụng FastAPI nhận lệnh gọi hàm, thực thi hàm Python tương ứng (ví dụ: gọi Goong Maps API).
    *   Kết quả từ hàm được gửi ngược lại cho Gemini.
4.  **LLM tổng hợp câu trả lời:** Dựa trên kết quả thực tế từ "công cụ", Gemini tạo ra một câu trả lời cuối cùng, tự nhiên và thông minh cho người dùng.

### Ưu điểm
*   **Linh hoạt:** LLM tự quyết định khi nào cần tìm kiếm, giúp cuộc hội thoại tự nhiên hơn.
*   **Dễ mở rộng:** Chỉ cần định nghĩa thêm "công cụ" mới để có chức năng mới, không cần sửa đổi luồng logic chính.
*   **Đáng tin cậy:** Dựa trên cấu trúc `function_call` chuẩn, giảm thiểu lỗi so với các phương pháp cũ.

## Cấu trúc thư mục

```
test_api_map/
├── app/
│   ├── main.py                 # khởi tạo FastAPI
│   ├── api/
│   │   └── routes.py           # define API endpoint
│   ├── core/
│   │   └── config.py           # tải các biến config
│   ├── logic/
│   │   ├── chatbot.py          # chứa luồng xử lý chính của chatbot
│   │   └── tools.py            # define tool cho LLM
│   ├── schemas/
│   │   └── chat.py             # Pydantic model để xác thực dữ liệu
│   ├── services/
│   │   ├── gemini.py           # Client tương tác với Google Gemini API
│   │   └── goong.py            # Client tương tác với Goong Maps API
│   └── state/
│       └── manager.py          # Quản lý trạng thái các cuộc hội thoại
├── main.py                     # Entrypoint để chạy ứng dụng
└── requirements.txt            # các thư viện
```

## Cài đặt & Chạy ứng dụng

### Yêu cầu

-   Python 3.8+
-   Tài khoản [Goong](https://goong.io/) và [Google AI Studio](https://aistudio.google.com/) để lấy API key.

### Các bước cài đặt

1.  **Clone a repository:**
    ```bash
    git clone https://github.com/QuocAnhh/bot_validate_add
    cd bot_validate_add
    ```

2.  **Tạo và kích hoạt môi trường ảo:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
    *Trên Windows, dùng:* `venv\Scripts\activate`

3.  **Cài đặt các thư viện cần thiết:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Cấu hình API Keys:**
    -   Tạo một file mới có tên là `.env` trong thư mục gốc của dự án.
    -   Thêm nội dung sau vào file `.env` và thay thế bằng các API key của bạn:
        ```env
        GOONG_API_KEY="YOUR_GOONG_API_KEY_HERE"
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
        ```
    -   *Lưu ý: File `app/core/config.py` đã được cấu hình để tự động đọc các biến này.*

5.  **Chạy ứng dụng:**
    ```bash
    python main.py
    ```
    Server sẽ chạy tại `http://127.0.0.1:8000`. Bạn có thể truy cập `http://127.0.0.1:8000/docs` để xem tài liệu API.

## API Endpoint

-   **URL**: `/chat/stream`
-   **Method**: `POST`
-   **Payload (JSON)**:
    ```json
    {
        "message": "tìm cho tôi địa chỉ công viên hòa bình ở hà nội",
        "conversation_id": "user-session-12345"
    }
    ```
-   **Response**: Dữ liệu được trả về dưới dạng `text/event-stream` (Server-Sent Events). 