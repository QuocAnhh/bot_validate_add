# Chatbot Xác thực Địa chỉ

Một chatbot dựa trên FastAPI được thiết kế để xác thực địa chỉ người dùng một cách thông minh thông qua một cuộc hội thoại tự nhiên. Chatbot sử dụng API của Goong để tìm kiếm và lấy thông tin địa chỉ, và Google Gemini để xử lý ngôn ngữ tự nhiên.

## Tính năng

-   **Gợi ý địa chỉ (Autocomplete)**: Tự động gợi ý và hoàn thành địa chỉ khi người dùng đang nhập.
-   **Hội thoại thông minh**: Sử dụng mô hình ngôn ngữ lớn (LLM) của Gemini để hiểu và phản hồi người dùng một cách tự nhiên.
-   **Quản lý hội thoại theo trạng thái**: Theo dõi và duy trì ngữ cảnh của từng cuộc hội thoại riêng biệt.
-   **Lưu trữ kết quả**: Ghi lại tất cả các địa chỉ đã được xác nhận thành công vào file CSV.
-   **Streaming Response**: Phản hồi được trả về ngay lập tức dưới dạng stream (SSE).

## Cài đặt & Chạy ứng dụng

### Yêu cầu

-   Python 3.8+
-   Một tài khoản Goong và Google Gemini để lấy API key.

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
    -   Tạo một file mới có tên là `.env` trong thư mục gốc của dự án (`test_api_map`).
    -   Thêm nội dung sau vào file `.env` và thay thế bằng các API key của bạn:
        ```env
        GOONG_API_KEY="YOUR_GOONG_API_KEY_HERE"
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
        ```

5.  **Chạy ứng dụng:**
    ```bash
    python main.py
    ```
    Server sẽ chạy tại `http://127.0.0.1:8000`.

## API Endpoint

-   **URL**: `/chat/stream`
-   **Method**: `POST`
-   **Payload (JSON)**:
    ```json
    {
        "message": "123 nguyễn huệ",
        "conversation_id": "some-unique-user-id-123"
    }
    ```
-   **Response**: Dữ liệu được trả về dưới dạng `text/event-stream`. 