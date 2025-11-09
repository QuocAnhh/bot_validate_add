# Xử lý Negative Cases (Failed Cases)

## Vấn đề

Khi retrieve cases từ memory, có thể có cả **positive cases** (reward=1) và **negative cases** (reward=0). 

**Câu hỏi:** Nếu các case tương tự bị fail thì sao?

## Giải pháp

Có 2 cách xử lý:

### 1. **Filter Negative Cases** (Mặc định - Recommended)
- Chỉ retrieve và show **positive cases** (reward=1)
- Bỏ qua negative cases khi retrieve
- **Lợi ích:** LLM chỉ học từ good examples
- **Nhược điểm:** Không học từ mistakes

### 2. **Include Negative Examples** (Optional)
- Retrieve cả positive và negative
- Show negative examples với label "Examples to avoid"
- LLM học tránh patterns này
- **Lợi ích:** Học từ mistakes, tránh lỗi tương tự
- **Nhược điểm:** Có thể confuse nếu quá nhiều negative

## Implementation

### Current Behavior (Default)

```python
# Trong SimpleAgent
retrieved_cases = self.memory.retrieve(query=user_message, top_k=top_k)
# → Retrieve tất cả cases (cả positive và negative)

memory_prompt = build_prompt_from_cases(
    retrieved_cases=retrieved_cases,
    include_negative=False  # ← Chỉ show positive
)
```

**Kết quả:**
- Retrieve cả positive và negative
- Nhưng chỉ show positive examples
- Negative cases bị filter out

### Option 1: Filter at Retrieval (Recommended)

**Update `non_parametric.py`:**
```python
def retrieve(
    self,
    query: str,
    top_k: int = 4,
    filter_negative: bool = True  # ← Filter negative cases
) -> List[Dict[str, Any]]:
    # ... retrieve logic ...
    
    if filter_negative:
        # Filter out negative cases (reward=0)
        filtered_results = [
            r for r in results
            if self._cases[r['line_index']].get('reward', 1) == 1
        ]
        return filtered_results[:top_k]
    
    return results
```

**Lợi ích:**
- Chỉ retrieve positive cases
- Efficient hơn
- LLM chỉ thấy good examples

### Option 2: Show Negative Examples

**Update config:**
```yaml
memory:
  include_negative_examples: true  # Show negative examples
  max_negative_examples: 2
```

**Update SimpleAgent:**
```python
memory_prompt = build_prompt_from_cases(
    retrieved_cases=retrieved_cases,
    include_negative=config.memory.include_negative_examples,
    max_negative=config.memory.max_negative_examples
)
```

**Prompt sẽ có:**
```
Similar previous conversations:
Example 1: User: ... → Assistant: ... (good)
Example 2: User: ... → Assistant: ... (good)

Examples to avoid:
Example 1: User: ... → Assistant: ... (bad)
Example 2: User: ... → Assistant: ... (bad)

Based on the above examples, please respond...
```

## Best Practice

**Recommended approach:**
1. **Filter negative at retrieval** - Chỉ retrieve positive cases
2. **Optional: Include negative** - Nếu muốn LLM học từ mistakes
3. **Configurable** - Cho phép user chọn behavior

## How to Mark Cases as Negative?

### 1. **User Feedback** (Future)
```python
# API endpoint
POST /api/memory/cases/{id}/feedback
{
  "reward": 0  # Mark as negative
}
```

### 2. **Manual Edit**
```json
{"user_message": "...", "assistant_response": "...", "reward": 0}
```

### 3. **Auto-detect** (Future)
- Detect error patterns
- Low confidence responses
- User corrections

## Current Implementation

Hiện tại:
- ✅ Support negative cases trong storage (reward=0)
- ✅ `prompt_builder.py` có logic để separate positive/negative
- ⚠️ `include_negative=False` (chỉ show positive)
- ⚠️ Auto-save luôn set `reward=1`

**Next steps:**
1. Add filter option trong `retrieve()`
2. Add config để control behavior
3. Update SimpleAgent để support negative examples
4. Add API để mark cases as negative

