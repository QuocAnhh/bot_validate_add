# Docker Setup

## Build và Run

### Build và Run (Simple)
```bash
# Build
docker compose build

# Run
docker compose up -d

# Stop
docker compose down

# Logs
docker compose logs -f
```

### Run without docker-compose
```bash
# Build
docker build -f docker/Dockerfile -t bot_nhaXe:latest .

# Run
docker run -d \
  --name bot_nhaXe \
  -p 8000:8000 \
  -v $(pwd)/configs:/app/configs:ro \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  bot_nhaXe:latest
```

## Environment Variables

Tạo file `.env` với các biến sau:
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/dbname
LOG_LEVEL=INFO
PORT=8000
```

## Volumes

- `configs/` - Agent configs (read-only)
- `logs/` - Log files (read-write)
- `app/prompts/` - Prompt templates (read-only)

## Health Check

Container có health check tự động:
- Endpoint: `http://localhost:8000/health`
- Interval: 30s
- Timeout: 10s

## Logs

Xem logs:
```bash
docker-compose -f docker/docker-compose.yml logs -f
```

Hoặc:
```bash
docker logs -f bot_nhaXe
```

