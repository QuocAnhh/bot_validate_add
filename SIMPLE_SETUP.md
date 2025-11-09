# Simple Setup - Single Agent

## Cấu trúc đơn giản

Project đã được đơn giản hóa thành **single agent** với **prompt-only**:

### Files chính:

1. **Config**: `configs/agent.yaml` - Cấu hình agent
2. **Prompt**: `app/prompts/templates/agent.txt` - Prompt template

### Để sửa prompt:

1. **Sửa prompt template**: `app/prompts/templates/agent.txt`
2. **Restart server**: `docker compose restart`

### Để sửa config:

1. **Sửa config**: `configs/agent.yaml`
   - `agent.name` - Tên agent
   - `agent.description` - Mô tả
   - `model.temperature` - Độ sáng tạo (0.0-1.0)
   - `model.model_name` - Model name
   - `prompt_template` - Tên template (mặc định: "agent")

2. **Restart server**

## Không cần:

- ❌ Multi-agent selection
- ❌ Tools
- ❌ Memory (Phase 2)
- ❌ Complex configuration

## Chỉ cần:

- ✅ 1 config file: `configs/agent.yaml`
- ✅ 1 prompt template: `app/prompts/templates/agent.txt`
- ✅ SimpleAgent (no tools)

## Quick Start

1. Sửa prompt: `app/prompts/templates/agent.txt`
2. Restart: `docker compose restart`
3. Test: http://localhost:8000/ui

Done! 🎉

