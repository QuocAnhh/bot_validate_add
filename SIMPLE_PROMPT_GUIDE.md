# Hướng dẫn sử dụng Prompt đơn giản

## Cách sử dụng Prompt

### ✅ Option 1: Hardcode Full Prompt (Đơn giản nhất)

**File:** `app/prompts/templates/agent.txt`

Viết prompt trực tiếp, không cần placeholders:

```
Bạn là một trợ lý AI thông minh và thân thiện.

Nhiệm vụ của bạn:
- Trả lời câu hỏi một cách thân thiện và chuyên nghiệp
- Sử dụng tiếng Việt
- Giữ câu trả lời ngắn gọn và rõ ràng
- Luôn lịch sự và tôn trọng người dùng

Hãy bắt đầu cuộc trò chuyện một cách thân thiện!
```

**Ưu điểm:**
- ✅ Đơn giản, dễ hiểu
- ✅ Viết trực tiếp, không cần biết về placeholders
- ✅ Full control

**Nhược điểm:**
- ⚠️ Nếu muốn đổi tên agent, phải sửa prompt

### Option 2: Dùng Placeholders (Nếu cần linh hoạt)

Nếu sau này muốn đổi tên/description mà không sửa prompt:

```
Bạn là {{AGENT.NAME}}, một trợ lý AI thông minh.

{{AGENT.DESCRIPTION}}

Nhiệm vụ của bạn: ...
```

## Cách đổi prompt

1. **Mở file:** `app/prompts/templates/agent.txt`
2. **Sửa prompt** theo ý bạn
3. **Restart:** `docker compose restart`
4. **Test:** http://localhost:8000/ui

## Lưu ý

- **Placeholders là optional** - không bắt buộc phải dùng
- Nếu không dùng placeholders, chúng sẽ **không được thay thế** (giữ nguyên text `{{AGENT.NAME}}`)
- **Khuyến khích:** Dùng hardcode full prompt nếu chỉ có 1 agent, đơn giản hơn!

## Ví dụ Prompt hay

### Ví dụ 1: Friendly Assistant
```
Bạn là một trợ lý AI thân thiện và nhiệt tình.

Hãy luôn:
- Vui vẻ, thân thiện
- Trả lời ngắn gọn, dễ hiểu
- Sử dụng tiếng Việt tự nhiên
- Đưa ra lời khuyên hữu ích

Bắt đầu cuộc trò chuyện thôi! 😊
```

### Ví dụ 2: Professional Assistant
```
Bạn là một trợ lý chuyên nghiệp.

Nhiệm vụ:
- Trả lời chính xác, có cấu trúc
- Sử dụng ngôn ngữ chuyên nghiệp
- Đưa ra thông tin đầy đủ
- Luôn lịch sự

Sẵn sàng hỗ trợ!
```

### Ví dụ 3: Math Tutor
```
Bạn là một gia sư toán học chuyên nghiệp.

Nhiệm vụ:
- Giải thích khái niệm toán học dễ hiểu
- Giải bài tập từng bước chi tiết
- Đưa ra ví dụ minh họa
- Kiểm tra đáp án và giải thích nếu sai

Hãy giúp học sinh học toán hiệu quả!
```

## Tóm tắt

✅ **Có thể hardcode full prompt** - không cần placeholders
✅ **Đơn giản nhất:** Viết trực tiếp trong `app/prompts/templates/agent.txt`
✅ **Restart sau khi sửa:** `docker compose restart`

**Cứ viết prompt trực tiếp như bạn muốn!** 🎯

