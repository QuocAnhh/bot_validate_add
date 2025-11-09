# Phase 2: Memento Integration Plan

## Tổng quan

Sau khi hoàn thành Phase 1 (Template System), bước tiếp theo là tích hợp **Memento Framework** với **non-parametric memory** để agent có thể:
- Lưu trữ và retrieve các cases (conversation examples)
- Học từ các cuộc hội thoại trước
- Cải thiện responses dựa trên memory

## Mục tiêu Phase 2

1. ✅ **Non-parametric Memory**
   - Sử dụng semantic search để tìm similar cases
   - Không cần training model
   - Simple và hiệu quả

2. ✅ **Case Storage**
   - Lưu successful conversations
   - Store cases với metadata (intent, response quality, etc.)

3. ✅ **Memory Retrieval**
   - Retrieve top-k similar cases khi có query mới
   - Inject vào prompt để guide LLM

4. ✅ **Memory Injection**
   - Tự động inject relevant cases vào prompt
   - Giúp LLM học từ examples

## Cấu trúc Phase 2

### Step 1: Setup Memento Memory Module
- [ ] Tạo `app/memory/` module
- [ ] Implement non-parametric memory (semantic search)
- [ ] Setup embedding model (sentence-transformers)
- [ ] Create case storage (JSONL hoặc database)

### Step 2: Integrate với SimpleAgent
- [ ] Update `SimpleAgent` để support memory
- [ ] Add memory retrieval trước khi call LLM
- [ ] Inject memory vào prompt

### Step 3: Case Management
- [ ] API để add cases
- [ ] API để view/search cases
- [ ] Auto-save successful conversations

### Step 4: Testing & Optimization
- [ ] Test memory retrieval
- [ ] Test với different queries
- [ ] Optimize embedding model
- [ ] Tune top-k parameter

## Files cần tạo

```
app/
├── memory/
│   ├── __init__.py
│   ├── non_parametric.py      # Non-parametric memory implementation
│   ├── case_storage.py         # Case storage (JSONL/database)
│   ├── embedding.py            # Embedding utilities
│   └── retriever.py            # Memory retriever
```

## Dependencies cần thêm

```txt
sentence-transformers>=2.2.0
numpy>=1.24.0
scikit-learn>=1.3.0
```

## Config updates

```yaml
# configs/agent.yaml
memory:
  enabled: true  # Enable memory
  type: "non_parametric"
  top_k: 4  # Retrieve top 4 similar cases
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  storage_type: "jsonl"  # or "database"
```

## Workflow

1. **User sends message**
2. **Retrieve similar cases** từ memory
3. **Inject cases vào prompt** (few-shot examples)
4. **Call LLM** với enhanced prompt
5. **Save successful conversation** as new case

## Next Steps

1. **Review Memento code** trong `Memento/` folder
2. **Extract non-parametric memory** logic
3. **Integrate vào SimpleAgent**
4. **Test và optimize**

## Timeline Estimate

- **Day 1-2**: Setup memory module, embedding
- **Day 3-4**: Integrate với SimpleAgent
- **Day 5-6**: Case management API
- **Day 7**: Testing & optimization

## Notes

- Bắt đầu với **non-parametric** (đơn giản hơn)
- **Parametric memory** (MLP training) sẽ làm sau nếu cần
- Focus vào **case retrieval** và **prompt injection**

