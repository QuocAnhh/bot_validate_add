# Phase 2 Implementation Plan - Based on Memento

## Phân tích Memento Framework

### Core Components từ Memento

1. **`np_memory.py`**:
   - `load_jsonl()` - Load cases
   - `extract_pairs()` - Extract key-value pairs
   - `embed_texts()` - Embedding với transformers
   - `retrieve()` - Semantic search

2. **Memory Format** (JSONL):
   ```json
   {"question": "query", "plan": "response", "reward": 1}
   ```

3. **Integration**:
   - Load memory on init
   - Retrieve before LLM call
   - Build prompt với examples
   - Inject vào messages

## Implementation Plan

### Step 1: Create Memory Module

**File:** `app/memory/non_parametric.py`

Adapt từ `Memento/memory/np_memory.py`:
- Simplified cho single agent
- Key: `user_message`
- Value: `assistant_response`
- Optional: `reward` (nếu cần negative examples)

### Step 2: Create Case Storage

**File:** `app/memory/case_storage.py`

- Load/save JSONL
- Add new cases
- Reload cache

### Step 3: Create Embedding Module

**File:** `app/memory/embedding.py`

- Load embedding model
- Embed texts
- Similarity search

### Step 4: Integrate với SimpleAgent

**Update:** `app/use_cases/base/simple_agent.py`

- Add memory retrieval
- Build prompt với cases
- Inject vào system/user message

### Step 5: Update Config

**Update:** `configs/agent.yaml`

```yaml
memory:
  enabled: true
  type: "non_parametric"
  top_k: 4
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"  # Lighter than Memento's
  storage_path: "memory/cases.jsonl"
```

## Key Differences từ Memento

1. **Simpler format**: `user_message` + `assistant_response` (không cần `plan`, `reward`)
2. **Lighter model**: `sentence-transformers/all-MiniLM-L6-v2` (thay vì BERT-base)
3. **No planner-executor**: Direct response (không cần hierarchical planning)
4. **Optional reward**: Có thể bỏ nếu không cần negative examples

## Files cần tạo

```
app/memory/
├── __init__.py
├── non_parametric.py      # Core retrieval (adapt từ np_memory.py)
├── case_storage.py         # JSONL storage
├── embedding.py            # Embedding utilities
└── retriever.py            # High-level retriever
```

## Next: Bắt đầu implement?

