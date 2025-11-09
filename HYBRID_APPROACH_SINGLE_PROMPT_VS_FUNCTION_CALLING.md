# Kết Hợp Single Prompt và Function Calling

## 🎯 Câu Trả Lời Ngắn Gọn

**CÓ!** Bạn hoàn toàn có thể kết hợp cả hai:
- **Function Calling** cho các tác vụ cần gọi tool (tìm địa chỉ, tìm chuyến xe, đặt vé)
- **Single Prompt** cho các tác vụ đơn giản (trả lời câu hỏi, chào hỏi, xử lý logic)

## 📊 So Sánh Khi Nào Dùng Gì

### **Function Calling** - Dùng khi:

✅ **Cần gọi tool/API bên ngoài:**
- Tìm kiếm địa chỉ (Goong Maps)
- Tìm chuyến xe (Database)
- Đặt vé (Booking system)
- Bất kỳ tác vụ nào cần dữ liệu thực tế

✅ **Cần cấu trúc rõ ràng:**
- Dễ debug
- Dễ maintain
- Dễ test

✅ **Cần xử lý kết quả:**
- Parse response từ API
- Validate data
- Transform data

### **Single Prompt** - Dùng khi:

✅ **Trả lời câu hỏi đơn giản:**
- FAQ
- Thông tin chung
- Hướng dẫn
- Không cần dữ liệu thực tế

✅ **Xử lý logic phức tạp trong prompt:**
- Routing giữa các agents
- Quyết định flow phức tạp
- Xử lý nhiều điều kiện

✅ **Cần format output đặc biệt:**
- Format `Message|Action` như BIVA
- Custom output format
- Structured text response

## 🏗️ Kiến Trúc Hybrid

### **Pattern từ Repo BIVA:**

```
┌─────────────────────────────────────┐
│         Master Agent                 │
│  (Single Prompt - Routing)          │
│  - Quyết định chuyển agent nào      │
│  - Xử lý câu hỏi đơn giản           │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│ Sub-Agent 1 │  │ Sub-Agent 2 │
│ (Single     │  │ (Single     │
│  Prompt)    │  │  Prompt)    │
│             │  │             │
│ - Knowledge │  │ - Knowledge │
│   riêng     │  │   riêng     │
└─────────────┘  └─────────────┘
```

### **Pattern cho dự án của bạn:**

```
┌─────────────────────────────────────┐
│      Main Chatbot Logic             │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Single Prompt Handler       │   │
│  │  - FAQ                        │   │
│  │  - Chào hỏi                  │   │
│  │  - Thông tin chung           │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Function Calling Handler    │   │
│  │  - search_address_in_vietnam│   │
│  │  - find_trips                │   │
│  │  - book_trip                 │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## 💡 Cách Áp Dụng Vào Dự Án Của Bạn

### **1. Thêm Single Prompt Handler**

Tạo một handler mới để xử lý các câu hỏi đơn giản không cần tool:

```python
# app/logic/simple_chat.py

async def handle_simple_chat(
    user_message: str,
    conversation_data: ConversationData
) -> str:
    """
    Xử lý các câu hỏi đơn giản không cần tool.
    Sử dụng single prompt approach.
    """
    simple_prompt = """
    Bạn là trợ lý ảo BIVA, chuyên hỗ trợ đặt xe tại Việt Nam.
    
    ## Nhiệm vụ:
    - Trả lời các câu hỏi thường gặp
    - Cung cấp thông tin chung về dịch vụ
    - Hướng dẫn sử dụng
    
    ## Lưu ý:
    - Nếu người dùng hỏi về địa chỉ hoặc đặt vé, trả lời ngắn gọn và hướng dẫn họ cung cấp thông tin
    - Luôn thân thiện và chuyên nghiệp
    
    Câu hỏi của người dùng: {user_message}
    """
    
    response = await gemini_client.generate_response(
        prompt=[{"role": "user", "content": simple_prompt.format(user_message=user_message)}],
        tools=None  # Không dùng tool
    )
    
    return response.text
```

### **2. Cải Thiện Logic Routing**

Cải thiện logic trong `chatbot.py` để quyết định khi nào dùng single prompt vs function calling:

```python
# app/logic/chatbot.py

async def chatbot_logic_generator(conv_data: ConversationData, user_message: str, conversation_id: str) -> AsyncGenerator[dict, None]:
    
    # 1. Kiểm tra xem có phải câu hỏi đơn giản không
    is_simple_question = _is_simple_question(user_message)
    
    if is_simple_question:
        # Dùng single prompt cho câu hỏi đơn giản
        response_text = await handle_simple_chat(user_message, conv_data)
        async for chunk in stream_message(response_text):
            yield chunk
        return
    
    # 2. Nếu không phải câu hỏi đơn giản, dùng function calling
    # ... logic hiện tại của bạn ...
```

### **3. Hàm Helper Để Phân Loại**

```python
def _is_simple_question(text: str) -> bool:
    """
    Kiểm tra xem câu hỏi có phải là câu hỏi đơn giản không cần tool không.
    """
    simple_keywords = [
        "xin chào", "chào", "hello", "hi",
        "làm thế nào", "hướng dẫn", "cách",
        "giờ làm việc", "liên hệ", "hotline",
        "cảm ơn", "tạm biệt",
        "bạn là ai", "bạn làm gì",
    ]
    
    text_lower = text.lower()
    
    # Nếu có từ khóa đơn giản và không có từ khóa cần tool
    has_simple_keyword = any(keyword in text_lower for keyword in simple_keywords)
    has_tool_keyword = any(keyword in text_lower for keyword in ["tìm", "đặt", "địa chỉ", "chuyến", "vé"])
    
    return has_simple_keyword and not has_tool_keyword
```

## 🔄 Flow Hoàn Chỉnh

```
User Message
    │
    ▼
┌───────────────────────┐
│  Phân Loại Câu Hỏi    │
└───────────┬───────────┘
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌─────────┐    ┌──────────────┐
│ Simple  │    │ Need Tool    │
│ Question│    │              │
└────┬────┘    └──────┬───────┘
     │                │
     ▼                ▼
┌─────────┐    ┌──────────────┐
│ Single  │    │ Function     │
│ Prompt  │    │ Calling      │
│         │    │              │
│ - FAQ   │    │ - search_    │
│ - Info  │    │   address    │
│ - Guide │    │ - find_trips  │
│         │    │ - book_trip   │
└─────────┘    └──────────────┘
```

## 📝 Ví Dụ Cụ Thể

### **Ví dụ 1: Câu hỏi đơn giản → Single Prompt**

**User:** "Xin chào, bạn là ai?"

**Handler:** Single Prompt
```python
# Không cần tool, trả lời trực tiếp
response = await handle_simple_chat(user_message, conv_data)
# Output: "Xin chào! Em là BIVA, trợ lý ảo hỗ trợ đặt xe..."
```

### **Ví dụ 2: Cần tìm địa chỉ → Function Calling**

**User:** "Tìm cho tôi địa chỉ công viên hòa bình ở hà nội"

**Handler:** Function Calling
```python
# Cần gọi tool search_address_in_vietnam
response = await gemini_client.generate_response(
    prompt=conv_data.history,
    tools=[booking_tools]  # Có tool
)
# LLM sẽ gọi function search_address_in_vietnam
```

### **Ví dụ 3: Câu hỏi FAQ → Single Prompt**

**User:** "Giờ làm việc của nhà xe là gì?"

**Handler:** Single Prompt
```python
# Câu hỏi FAQ, không cần tool
faq_prompt = """
Bạn là trợ lý BIVA. Trả lời câu hỏi sau:
Q: Giờ làm việc của nhà xe là gì?
A: Nhà xe hoạt động từ 6h sáng đến 10h tối hàng ngày...
"""
response = await handle_simple_chat(faq_prompt, conv_data)
```

## 🎯 Lợi Ích Của Hybrid Approach

### **1. Tối Ưu Cost**
- Single prompt cho câu hỏi đơn giản → Rẻ hơn
- Function calling chỉ khi cần → Hiệu quả hơn

### **2. Tối Ưu Performance**
- Single prompt → Nhanh hơn (không cần đợi tool)
- Function calling → Chính xác hơn (có dữ liệu thực tế)

### **3. Linh Hoạt**
- Có thể chuyển đổi giữa hai approach
- Dễ customize cho từng use case

### **4. Dễ Maintain**
- Tách biệt logic rõ ràng
- Dễ test từng phần

## ⚠️ Lưu Ý

### **1. Không Over-Engineer**
- Chỉ dùng single prompt khi thực sự cần
- Đừng tạo quá nhiều handlers

### **2. Consistency**
- Giữ format response nhất quán
- User không nên thấy sự khác biệt

### **3. Fallback**
- Luôn có fallback nếu single prompt fail
- Có thể fallback về function calling

## 🚀 Bước Tiếp Theo

1. **Thêm Simple Chat Handler** (optional)
   - Tạo `app/logic/simple_chat.py`
   - Implement `handle_simple_chat()`

2. **Cải Thiện Routing Logic**
   - Thêm `_is_simple_question()` vào `chatbot.py`
   - Quyết định khi nào dùng single prompt

3. **Test & Iterate**
   - Test với các câu hỏi khác nhau
   - Điều chỉnh logic phân loại

## 📌 Kết Luận

**Có thể kết hợp cả hai!** Nhưng:
- ✅ **Giữ Function Calling** cho các tác vụ cần tool (tìm địa chỉ, đặt vé)
- ✅ **Thêm Single Prompt** cho các câu hỏi đơn giản (FAQ, chào hỏi)
- ✅ **Routing thông minh** để quyết định khi nào dùng gì

Điều quan trọng là **không cần thiết phải chuyển toàn bộ sang single prompt**. Function calling approach của bạn đã tốt rồi, chỉ cần bổ sung single prompt cho các trường hợp đơn giản.

