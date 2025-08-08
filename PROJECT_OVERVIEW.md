# Tổng quan dự án Chatbot Xác thực Địa chỉ

Đây là tài liệu giải thích chi tiết về cấu trúc thư mục và luồng hoạt động của dự án, được xây dựng trên kiến trúc **Tool Calling** (Function Calling) tiên tiến của Google Gemini.

## I. Cấu trúc thư mục

Cấu trúc thư mục được tổ chức theo module để đảm bảo code sạch sẽ và dễ mở rộng.

```
test_api_map/
├── app/
│   ├── main.py                 # khởi tạo FastAPI
│   ├── api/
│   │   └── routes.py           # define API endpoint
│   ├── core/
│   │   └── config.py           # tải các biến config
│   ├── logic/
│   │   ├── chatbot.py          # luồng xử lý chính của chatbot
│   │   └── tools.py            # define tool cho LLM
│   ├── schemas/
│   │   └── chat.py             # Pydantic model để verify data
│   ├── services/
│   │   ├── gemini.py           # Client interact với Google Gemini API
│   │   └── goong.py            # Client interact với Goong Maps API
│   └── state/
│       └── manager.py          # Manage trạng thái các cuộc hội thoại
├── main.py                     # Entrypoint để chạy ứng dụng
└── requirements.txt            # thư viện python
```

## II. Luồng hoạt động - Kiến trúc Tool Calling

Kiến trúc cũ đã được thay thế hoàn toàn bằng một luồng xử lý mạnh mẽ và linh hoạt, trong đó LLM được trao quyền để "hành động" thay vì chỉ "trả lời".

### **Khái niệm cốt lõi: "Công cụ" (Tool)**

Thay vì bắt LLM trả về một định dạng JSON tự chế, chúng ta định nghĩa các hàm Python của mình (ví dụ: `search_address`) như những "công cụ" mà LLM có thể gọi.

-   **Định nghĩa (Schema):** Trong `app/logic/tools.py`, chúng ta mô tả cho LLM biết có một công cụ tên là `search_address_in_vietnam`, nó dùng để làm gì và cần tham số `query` là một chuỗi địa chỉ.
-   **Trao quyền:** Khi gọi API Gemini, chúng ta nói với nó: "Đây là cuộc hội thoại, và đây là bộ công cụ của anh. Hãy tự quyết định khi nào cần dùng."

### **Vòng lặp xử lý (The Loop)**

Toàn bộ logic giờ đây xoay quanh một vòng lặp thông minh trong `app/logic/chatbot.py`:

1.  **Gửi yêu cầu & Công cụ cho LLM:**
    *   Toàn bộ lịch sử cuộc trò chuyện và danh sách các công cụ có sẵn (`address_validation_tool`) được gửi đến Gemini.

2.  **LLM ra quyết định:**
    *   LLM phân tích cuộc trò chuyện. Nó sẽ tự quyết định một trong hai hướng:
        *   **A) Trả lời trực tiếp:** Nếu người dùng chỉ chào hỏi hoặc câu nói không liên quan đến địa chỉ, LLM sẽ tạo ra một câu trả lời văn bản bình thường.
        *   **B) Gọi công cụ:** Nếu người dùng cung cấp một địa chỉ, LLM sẽ nhận ra rằng nó cần phải "hành động". Nó sẽ không trả lời, mà thay vào đó tạo ra một **lệnh gọi hàm (function call)**. Ví dụ: `function_call: search_address_in_vietnam(query='công viên hòa bình, hà nội')`.

3.  **Backend thực thi & Phản hồi:**
    *   **Trường hợp A (Trả lời trực tiếp):** Backend nhận câu trả lời văn bản và gửi thẳng cho người dùng. Vòng lặp kết thúc.
    *   **Trường hợp B (Gọi công cụ):**
        *   **3a. Thực thi:** Backend nhận lệnh gọi hàm, trích xuất tên hàm (`search_address_in_vietnam`) và các tham số (`query=...`). Sau đó, nó thực sự gọi hàm Python tương ứng (`goong_client.autocomplete(query)`).
        *   **3b. Gửi lại kết quả:** Sau khi có kết quả từ Goong API, backend sẽ gọi Gemini **lần thứ hai**. Lần này, nó gửi lại toàn bộ lịch sử chat, cộng thêm một tin nhắn đặc biệt có nội dung: "Thưa sếp, tôi đã thực thi xong lệnh gọi hàm `search_address_in_vietnam` của sếp, và đây là kết quả... `(dữ liệu từ Goong)`".
        *   **3c. LLM tổng hợp câu trả lời cuối cùng:** Nhận được dữ liệu thực tế từ công cụ, LLM giờ đã có đủ mọi thông tin cần thiết. Nó sẽ phân tích dữ liệu này và tạo ra một câu trả lời cuối cùng, hoàn chỉnh và thông minh để gửi cho người dùng.
