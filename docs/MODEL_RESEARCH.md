# Model Research & Comparison

## Current Model: FunctionGemma (270M parameters)

**Pros:**
- Specifically designed for function calling
- Small size (270M parameters)
- Fast inference
- Good for edge deployment

**Cons:**
- Limited accuracy (85%)
- Rigid command patterns
- Requires preprocessing layer
- Small parameter count limits understanding

## Alternative Models Research

### 1. Gemma 2 (2B parameters)

**Specifications:**
- Parameters: 2B
- Size: ~1.5 GB
- Context: 8K tokens
- Developer: Google

**Pros:**
- 7x more parameters than FunctionGemma
- Better natural language understanding
- More flexible with command variations
- Still relatively small for edge deployment

**Cons:**
- Not specifically trained for function calling
- Requires custom prompting strategy
- Larger model size

**Ollama Model:** `gemma2:2b`

### 2. Qwen 2.5 (3B parameters)

**Specifications:**
- Parameters: 3B
- Size: ~2 GB
- Context: 32K tokens
- Developer: Alibaba

**Pros:**
- Excellent instruction following
- Large context window (32K)
- Strong reasoning capabilities
- Good multilingual support

**Cons:**
- Larger model size
- Not function-calling specific
- May need more prompt engineering

**Ollama Model:** `qwen2.5:3b`

### 3. Phi-3 Mini (3.8B parameters)

**Specifications:**
- Parameters: 3.8B
- Size: ~2.3 GB
- Context: 128K tokens
- Developer: Microsoft

**Pros:**
- Excellent performance for size
- Huge context window
- Strong reasoning
- Good instruction following

**Cons:**
- Largest of the options
- Not function-calling specific

**Ollama Model:** `phi3:mini`

### 4. Llama 3.2 (3B parameters)

**Specifications:**
- Parameters: 3B
- Size: ~2 GB
- Context: 128K tokens
- Developer: Meta

**Pros:**
- Latest Llama architecture
- Excellent general capabilities
- Good instruction following
- Large context window

**Cons:**
- Not function-calling specific
- Requires prompt engineering

**Ollama Model:** `llama3.2:3b`

## Recommended Approach

### Option 1: Gemma 2 (2B) - RECOMMENDED

**Why:**
- Same family as FunctionGemma (easier transition)
- Good balance of size and capability
- Strong instruction following
- 7x more parameters = better understanding

**Implementation:**
- Use structured prompting with function definitions
- JSON output format
- Few-shot examples in system prompt

### Option 2: Qwen 2.5 (3B)

**Why:**
- Best instruction following
- Huge context window (good for complex scenarios)
- Strong reasoning

**Implementation:**
- Similar to Gemma 2
- May handle more complex multi-step commands

### Option 3: Hybrid Approach

**Why:**
- Use FunctionGemma for simple commands (fast)
- Fall back to larger model for complex/ambiguous commands

## Testing Plan

### Phase 1: Model Comparison
1. Test each model with same command set
2. Measure accuracy
3. Measure inference speed
4. Compare resource usage

### Phase 2: Prompt Engineering
1. Design optimal system prompts
2. Test function definition formats
3. Optimize few-shot examples

### Phase 3: Integration
1. Create model adapter interface
2. Support multiple models
3. Allow runtime model selection

## Expected Improvements

### Accuracy
- **Current**: 85% (FunctionGemma)
- **Target**: 95%+ (with larger models)

### Command Flexibility
- **Current**: Requires specific phrasings
- **Target**: Natural variations understood

### Multi-step Commands
- **Current**: Single command only
- **Target**: "arm and takeoff to 15 meters" works

### Context Awareness
- **Current**: No memory
- **Target**: Remember previous commands

## Implementation Strategy

### 1. Create Experimental Branch
```bash
git checkout -b experiment/alternative-models
```

### 2. Create Model Adapter
```python
class ModelAdapter:
    def __init__(self, model_name):
        self.model = model_name
        
    def get_function_call(self, user_input):
        # Model-specific implementation
        pass
```

### 3. Test Suite
- Run existing tests with new models
- Add new tests for complex commands
- Benchmark performance

### 4. Documentation
- Model comparison results
- Setup instructions
- Performance benchmarks

## Resource Requirements

| Model | Size | RAM | Inference Time |
|-------|------|-----|----------------|
| FunctionGemma | 552 MB | ~1 GB | ~100ms |
| Gemma 2 (2B) | ~1.5 GB | ~2 GB | ~200ms |
| Qwen 2.5 (3B) | ~2 GB | ~3 GB | ~300ms |
| Phi-3 Mini | ~2.3 GB | ~3.5 GB | ~350ms |
| Llama 3.2 (3B) | ~2 GB | ~3 GB | ~300ms |

## Next Steps

1. **Create experimental branch**
2. **Implement model adapter interface**
3. **Test Gemma 2 (2B)** - Most promising
4. **Test Qwen 2.5 (3B)** - Best instruction following
5. **Compare results**
6. **Document findings**

## Conclusion

**Recommended**: Start with **Gemma 2 (2B)**
- Same family as current model
- Good size/performance balance
- Should achieve 95%+ accuracy
- Easier migration path

**Alternative**: **Qwen 2.5 (3B)**
- If we need maximum accuracy
- Better for complex commands
- Larger context window

Both are significant upgrades from FunctionGemma (270M).
