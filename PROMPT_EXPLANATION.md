# Giải thích về Prompt Template và Placeholders

## Đúng rồi! Đổi prompt ở đâu?

**Đúng!** Bạn đổi prompt ở: `app/prompts/templates/agent.txt`

## Placeholders là gì?

Các placeholder như `{{AGENT.NAME}}`, `{{AGENT.DESCRIPTION}}` là **variables** sẽ được **tự động thay thế** bằng giá trị từ file config `configs/agent.yaml`.

### Ví dụ:

**File config** (`configs/agent.yaml`):
```yaml
agent:
  name: "BIVA"
  description: "Trợ lý ảo chuyên hỗ trợ đặt xe tại Việt Nam"
```

**File prompt template** (`app/prompts/templates/agent.txt`):
```
Bạn là {{AGENT.NAME}}, một trợ lý AI thông minh.

{{AGENT.DESCRIPTION}}
```

**Kết quả sau khi thay thế** (gửi cho LLM):
```
Bạn là BIVA, một trợ lý AI thông minh.

Trợ lý ảo chuyên hỗ trợ đặt xe tại Việt Nam
```

## Tại sao dùng placeholders?

### Lợi ích:
1. **Không cần sửa prompt mỗi khi đổi tên/description**
   - Chỉ sửa config → prompt tự động update
   
2. **Dễ quản lý**
   - Config = data (tên, mô tả, settings)
   - Template = structure (cách trình bày)
   
3. **Linh hoạt**
   - Có thể tạo nhiều agents với cùng template, chỉ khác config

## Các placeholders có sẵn:

### 1. `{{AGENT.NAME}}`
- Lấy từ: `configs/agent.yaml` → `agent.name`
- Ví dụ: "BIVA", "Assistant", "Math Tutor"

### 2. `{{AGENT.DESCRIPTION}}`
- Lấy từ: `configs/agent.yaml` → `agent.description`
- Ví dụ: "Trợ lý ảo chuyên hỗ trợ đặt xe"

### 3. `{{TOOLS_DESCRIPTION}}`
- Tự động generate từ `tools` trong config
- Hiện tại: Empty (vì `tools: []`)

### 4. `{{MEMORY_INSTRUCTIONS}}`
- Tự động generate từ `memory` config
- Hiện tại: Empty (vì `memory.enabled: false`)

## Cách sử dụng:

### Option 1: Dùng placeholders (Recommended)
```
Bạn là {{AGENT.NAME}}.

{{AGENT.DESCRIPTION}}

Nhiệm vụ của bạn:
- Trả lời câu hỏi
- Sử dụng tiếng Việt
```

**Khi đổi tên agent:** Chỉ sửa `configs/agent.yaml` → prompt tự động update!

### Option 2: Hardcode (Không khuyến khích)
```
Bạn là BIVA.

Trợ lý ảo chuyên hỗ trợ đặt xe tại Việt Nam

Nhiệm vụ của bạn:
- Trả lời câu hỏi
- Sử dụng tiếng Việt
```

**Khi đổi tên agent:** Phải sửa cả prompt template → không linh hoạt!

## Ví dụ thực tế:

### Bước 1: Sửa config
`configs/agent.yaml`:
```yaml
agent:
  name: "Math Tutor"
  description: "Gia sư toán học, giúp giải bài tập"
```

### Bước 2: Prompt tự động thay thế
`app/prompts/templates/agent.txt`:
```
Bạn là {{AGENT.NAME}}.

{{AGENT.DESCRIPTION}}

Hãy giúp học sinh giải bài tập toán!
```

### Bước 3: Kết quả gửi cho LLM
```
Bạn là Math Tutor.

Gia sư toán học, giúp giải bài tập

Hãy giúp học sinh giải bài tập toán!
```

## Tóm tắt:

✅ **Đổi prompt:** `app/prompts/templates/agent.txt`

✅ **Placeholders có ý nghĩa:**
- Tự động thay thế từ config
- Không cần sửa prompt khi đổi config
- Linh hoạt và dễ maintain

✅ **Cách dùng:**
- Dùng `{{AGENT.NAME}}`, `{{AGENT.DESCRIPTION}}` trong prompt
- Sửa config → prompt tự động update

**Không cần lo về placeholders - chúng sẽ tự động được thay thế!** 🎯

