# Memento Framework Analysis

## Cấu trúc Non-Parametric Memory

### 1. Core Components

#### `np_memory.py` - Core Memory Functions

**Functions:**
- `load_jsonl(path)` - Load cases từ JSONL file
- `extract_pairs(items, key_field, value_field)` - Extract (key, value, index) tuples
- `embed_texts(texts, tokenizer, model, device)` - Embed texts thành vectors
- `retrieve(task, pairs, tokenizer, model, top_k)` - Semantic search để tìm similar cases

**Key Points:**
- Sử dụng `transformers` với model `princeton-nlp/sup-simcse-bert-base-uncased`
- Embedding: normalize vectors (L2 norm)
- Similarity: cosine similarity (dot product của normalized vectors)
- Return: top-k cases với scores

#### `no_parametric_cbr.py` - Case-Based Reasoning

**Key Components:**
- `HierarchicalClient` class
- `_memory_prompt_for(task_text)` - Retrieve và build prompt từ cases
- `build_prompt_from_cases()` - Format cases thành prompt với positive/negative examples

**Memory Integration:**
```python
# Load memory
self._memory_items = mem_load_jsonl(MEMORY_JSONL_PATH)
self._memory_pairs = mem_extract_pairs(
    self._memory_items, 
    MEMORY_KEY_FIELD,  # "question"
    MEMORY_VALUE_FIELD  # "plan"
)

# Retrieve
results = mem_retrieve(
    task=task_text,
    pairs=self._memory_pairs,
    tokenizer=memo_tokenizer,
    model=memo_model,
    top_k=MEMORY_TOP_K,  # 8
)

# Build prompt
mem_prompt = build_prompt_from_cases(task_text, results, self._memory_items)
```

### 2. Memory Format (JSONL)

**Structure:**
```json
{"question": "What is the capital of France?", "plan": "Paris", "reward": 1}
{"question": "What is 2+2?", "plan": "4", "reward": 1}
{"question": "Bad question", "plan": "Bad answer", "reward": 0}
```

**Fields:**
- `question`: Query text (key field for retrieval)
- `plan`: Response/answer (value field)
- `reward`: 1 (positive) or 0 (negative)

### 3. Prompt Building

**`build_prompt_from_cases()`:**
- Separate positive (reward=1) và negative (reward=0) cases
- Format thành examples:
  ```
  Positive Examples (reward=1):
  Example 1:
  Question: ...
  Plan: ...
  
  Negative Examples (reward=0):
  Example 1:
  Question: ...
  Plan: ...
  
  Based on the above examples, please provide a plan for the current task.
  ```

### 4. Workflow

1. **Load memory** từ JSONL file
2. **Extract pairs** (question, plan)
3. **User query** → Retrieve top-k similar cases
4. **Build prompt** với examples
5. **Inject vào messages** (user message)
6. **Call LLM** với enhanced prompt
7. **Save successful cases** back to memory

### 5. Key Implementation Details

**Embedding Model:**
- Model: `princeton-nlp/sup-simcse-bert-base-uncased`
- Device: CUDA if available, else CPU
- Max length: 256 tokens
- Normalization: L2 norm

**Retrieval:**
- Cosine similarity (dot product)
- Top-k results với scores
- Return format: `[{"rank": 1, "score": 0.95, "question": "...", "plan": "...", "line_index": 0}]`

**Memory Storage:**
- Format: JSONL (one JSON per line)
- Append mode: Add new cases to file
- Reload after adding: Update in-memory cache

## Adaptation cho Single Agent

### Simplified Version

**Cho single agent (không có planner-executor):**
- Key field: `user_message` hoặc `query`
- Value field: `assistant_response` hoặc `response`
- Reward: Optional (có thể bỏ nếu không cần negative examples)

**Simplified format:**
```json
{"user_message": "Xin chào", "assistant_response": "Chào bạn! Tôi có thể giúp gì?", "timestamp": "2024-01-01"}
{"user_message": "Thời tiết hôm nay thế nào?", "assistant_response": "Tôi không có thông tin về thời tiết...", "timestamp": "2024-01-01"}
```

**Simplified prompt:**
```
Similar previous conversations:

Example 1:
User: ...
Assistant: ...

Example 2:
User: ...
Assistant: ...

Based on these examples, respond to the current user message.
```

## Next Steps

1. **Create simplified memory module** based on Memento
2. **Adapt for single agent** (không cần planner-executor)
3. **Integrate với SimpleAgent**
4. **Test và optimize**

