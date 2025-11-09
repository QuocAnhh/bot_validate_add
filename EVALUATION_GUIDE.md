# Hướng dẫn đánh giá hiệu quả Memory (Phase 2)

## Vấn đề

Làm sao biết được memory có hiệu quả hơn không? Cần có cách để so sánh và đo lường!

## Giải pháp

Đã tạo hệ thống evaluation để:
- ✅ So sánh responses với/không có memory
- ✅ Track metrics (response time, length, quality)
- ✅ Log tất cả comparisons
- ✅ API endpoints để test
- ✅ Script để test tự động

## Cách sử dụng

### 1. API Endpoint: So sánh trực tiếp

**Endpoint:** `POST /api/evaluation/compare`

**Request:**
```json
{
  "message": "Giải thích về AI là gì?",
  "conversation_id": "test-1"
}
```

**Response:**
```json
{
  "success": true,
  "results": {
    "query": "Giải thích về AI là gì?",
    "with_memory": {
      "response": "...",
      "response_time": 1.234,
      "memory_cases_used": 3
    },
    "without_memory": {
      "response": "...",
      "response_time": 0.987
    },
    "comparison": {
      "response_length_diff": 50,
      "response_time_diff": 0.247,
      "responses_are_different": true
    }
  }
}
```

**Cách test:**
```bash
curl -X POST http://localhost:8000/api/evaluation/compare \
  -H "Content-Type: application/json" \
  -d '{"message": "Xin chào"}'
```

### 2. Xem Statistics

**Endpoint:** `GET /api/evaluation/statistics`

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_comparisons": 10,
    "total_with_memory": 50,
    "total_without_memory": 50,
    "comparison_stats": {
      "avg_response_time_with_memory": 1.234,
      "avg_response_time_without_memory": 0.987,
      "avg_response_length_with_memory": 150.5,
      "avg_response_length_without_memory": 120.3,
      "time_difference": 0.247,
      "length_difference": 30.2
    }
  }
}
```

### 3. Test Script

**Chạy script tự động:**
```bash
# Trong Docker
docker compose exec bot_nhaXe python scripts/compare_memory.py

# Hoặc local
python scripts/compare_memory.py
```

Script sẽ:
- Tạo 2 agents (với/không memory)
- Test với nhiều queries
- So sánh responses
- Show statistics

### 4. Auto-logging

Mỗi khi agent trả lời, metrics được tự động log vào `evaluation/metrics.jsonl`:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "query": "...",
  "response": "...",
  "has_memory": true,
  "memory_cases_used": 3,
  "response_time": 1.234,
  "response_length": 150
}
```

## Metrics được track

### 1. Response Time
- Thời gian trả lời với/không memory
- So sánh performance

### 2. Response Length
- Độ dài response
- Memory có làm response dài hơn không?

### 3. Memory Cases Used
- Số cases được retrieve
- Memory có hoạt động không?

### 4. Response Quality (Manual)
- Cần đánh giá thủ công
- So sánh nội dung responses

## Cách đánh giá hiệu quả

### 1. Quantitative Metrics

**Response Time:**
- Memory có làm chậm không? (thường có, do embedding)
- Nhưng có đáng không? (nếu quality tốt hơn)

**Response Length:**
- Memory có làm response dài hơn không?
- Có phù hợp với context không?

**Memory Usage:**
- Có retrieve được cases không?
- Cases có relevant không?

### 2. Qualitative Metrics (Manual)

**Consistency:**
- Responses có nhất quán hơn không?
- Có follow style của examples không?

**Relevance:**
- Responses có relevant hơn không?
- Có hiểu context tốt hơn không?

**Accuracy:**
- Responses có chính xác hơn không?
- Có ít lỗi hơn không?

## Test Plan

### Phase 1: Baseline (Without Memory)
1. Test với 10-20 queries
2. Log responses
3. Đánh giá quality

### Phase 2: With Memory
1. Enable memory
2. Test với cùng queries
3. So sánh responses

### Phase 3: Analysis
1. Xem statistics
2. So sánh quantitative metrics
3. Đánh giá qualitative (manual)

## Example Workflow

```bash
# 1. Start server
docker compose up

# 2. Test với memory disabled (tạm thời)
# Edit configs/agent.yaml: memory.enabled = false
# Test qua UI hoặc API

# 3. Enable memory
# Edit configs/agent.yaml: memory.enabled = true
# Test lại với cùng queries

# 4. So sánh
curl http://localhost:8000/api/evaluation/statistics

# 5. Hoặc dùng script
python scripts/compare_memory.py
```

## Files

- `app/evaluation/metrics.py` - Track metrics
- `app/evaluation/comparator.py` - Compare responses
- `app/api/evaluation.py` - API endpoints
- `scripts/compare_memory.py` - Test script
- `evaluation/metrics.jsonl` - Logged metrics

## Tips

1. **Test với cùng queries** - Để so sánh công bằng
2. **Test nhiều lần** - Để có statistics đáng tin
3. **Check memory cases** - Xem có retrieve được không
4. **Manual review** - Quantitative không đủ, cần qualitative
5. **Track over time** - Memory cải thiện qua thời gian

## Next Steps

1. ✅ Basic comparison - Done
2. ✅ Metrics logging - Done
3. ⏳ Quality scoring (future)
4. ⏳ User feedback integration (future)
5. ⏳ Automated quality metrics (future)

---

**Giờ bạn có thể đánh giá được hiệu quả của memory rồi!** 🎉

