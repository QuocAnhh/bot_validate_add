# bot_nhaXe - Multi-Agent Template System

Template system để tạo và test nhiều AI agents khác nhau chỉ bằng cách thay đổi prompt/config.

## 🎯 Tính năng

- **Multi-Agent Support**: Tạo và test nhiều agents khác nhau
- **Configuration-Based**: Chỉ cần thay config để tạo agent mới
- **Prompt Templates**: Template system với variable replacement
- **Simple UI**: Web interface để test agents
- **OpenAI Integration**: Sử dụng GPT-4.1-mini (hoặc gpt-4o-mini)
- **Logging**: Logging đầy đủ với rotation
- **Docker Support**: Deploy dễ dàng với Docker

## 🏗️ Kiến trúc

```
bot_nhaXe/
├── app/
│   ├── core/              # Core modules (config, logging, agent factory)
│   ├── prompts/           # Prompt framework và templates
│   ├── use_cases/         # Use cases (booking, customer_support, etc.)
│   ├── services/          # Services (OpenAI client, memory, etc.)
│   ├── api/               # API routes
│   ├── ui/                # Simple UI (HTML/JS/CSS)
│   └── main.py            # FastAPI app
├── configs/               # Agent configs (YAML)
│   ├── booking_agent.yaml
│   └── examples/
├── docker/                # Docker files
├── logs/                  # Log files
└── requirements.txt
```

## 🚀 Quick Start

### 1. Cài đặt

```bash
# Clone repo
git clone <repo-url>
cd bot_nhaXe

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate  # hoặc venv\Scripts\activate trên Windows

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cấu hình

Tạo file `.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
LOG_LEVEL=INFO
PORT=8000
```

### 3. Chạy ứng dụng

**Local:**
```bash
python main.py
```

**Docker:**
```bash
docker compose up -d
```

### 4. Truy cập

- **API Docs**: http://localhost:8000/docs
- **UI**: http://localhost:8000/ui
- **Health**: http://localhost:8000/health

## 📝 Tạo Agent mới

### Bước 1: Tạo config file

Copy template:
```bash
cp configs/examples/customer_support.yaml configs/my_agent.yaml
```

### Bước 2: Sửa config

Sửa `configs/my_agent.yaml`:
```yaml
agent:
  name: "My Agent"
  description: "Mô tả agent của bạn"

# Tools (optional - để trống nếu không cần)
tools: []

# Model settings
model:
  model_name: "gpt-4o-mini"
  temperature: 0.7

# Memory (optional - sẽ enable trong Phase 2)
memory:
  enabled: false
```

### Bước 3: Tạo prompt template (optional)

Nếu muốn custom prompt:
```bash
cp app/prompts/templates/booking_agent.txt app/prompts/templates/my_agent.txt
```

Sửa template và update config:
```yaml
prompt_template: "my_agent"  # Tên file template (không có .txt)
```

### Bước 4: Test

1. Restart server (nếu đang chạy)
2. Truy cập UI: http://localhost:8000/ui
3. Select agent "my_agent" từ dropdown
4. Start chatting!

## 🔧 API Usage

### Chat với agent

```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Xin chào!",
    "conversation_id": "test-123",
    "agent_name": "booking_agent"
  }'
```

### List agents

```bash
curl http://localhost:8000/api/agents
```

### Get agent info

```bash
curl http://localhost:8000/api/agents/booking_agent
```

## 🐳 Docker

### Build và Run

```bash
# Build
docker compose build

# Run
docker compose up -d

# Logs
docker compose logs -f

# Stop
docker compose down
```

## 📊 Logging

Logs được lưu trong `logs/`:
- `app.log` - Main application log
- `api.log` - API requests
- `agent.log` - Agent processing
- `error.log` - Errors only

Log rotation: 10MB per file, 5 backups

## 🎨 UI Features

- Agent selection dropdown
- Chat interface với streaming
- Conversation history
- Reset conversation
- Agent info display

## 📚 Cấu trúc Config

```yaml
agent:
  name: "Agent Name"
  description: "Agent description"

tools: []  # List of tools (optional)

memory:
  enabled: false
  type: "non_parametric"
  top_k: 4

model:
  provider: "openai"
  model_name: "gpt-4o-mini"
  temperature: 0.7
  max_tokens: 2000

conversation:
  max_steps: 4
  enable_memory_injection: false
```

## 🔄 Workflow để test nhiều agents

1. Tạo config mới: `configs/my_agent.yaml`
2. (Optional) Tạo prompt template: `app/prompts/templates/my_agent.txt`
3. Restart server hoặc reload config
4. Test trong UI hoặc qua API
5. Xem logs để debug

## 📋 Requirements

- Python 3.11+
- OpenAI API Key
- Docker (optional, cho deployment)

## 🛠️ Development

### Project Structure

- `app/core/` - Core modules (config, logging, factory)
- `app/prompts/` - Prompt framework và templates
- `app/use_cases/` - Use cases (agents)
- `app/services/` - Services (OpenAI, memory, etc.)
- `app/api/` - API endpoints
- `app/ui/` - Web UI
- `configs/` - Agent configurations

### Adding New Agent

1. Create config: `configs/new_agent.yaml`
2. (Optional) Create prompt template: `app/prompts/templates/new_agent.txt`
3. Test via UI or API

## 📝 Notes

- Tools là optional - có thể để trống `tools: []` cho simple prompt-only agent
- Memory sẽ được enable trong Phase 2 (Memento integration)
- Prompt templates sử dụng variables: `{{AGENT.NAME}}`, `{{TOOLS_DESCRIPTION}}`, etc.

## 🚧 Phase 2: Memento Integration

Sau khi hoàn thành Phase 1 (template system), sẽ tích hợp:
- Non-parametric memory từ Memento
- Case-based reasoning
- Memory retrieval và injection

## 📄 License

MIT
