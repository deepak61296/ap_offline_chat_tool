# Model Selection Guide

## Available Models

The ArduPilot AI Assistant supports multiple AI models via Ollama. You can select which model to use via command-line arguments.

### Recommended Models

#### 1. **Qwen 2.5 (3B)** - Default ⭐
```bash
python main.py --model qwen2.5:3b
# or simply
python main.py
```

**Specifications:**
- Accuracy: **96.1%**
- Response Time: ~2.5s
- Model Size: 1.9 GB
- Best For: Production use, high accuracy

**Pros:**
- Highest accuracy
- Excellent natural language understanding
- Handles all command variations
- No preprocessing needed

**Cons:**
- Slower than legacy model
- Larger model size

---

#### 2. **Gemma 3 (4B)** - Alternative
```bash
python main.py --model gemma3:4b
```

**Specifications:**
- Accuracy: **96.1%**
- Response Time: ~4.5s
- Model Size: 2.5 GB
- Best For: Alternative to Qwen

**Pros:**
- Same accuracy as Qwen
- Good natural language understanding

**Cons:**
- Slower than Qwen
- Larger model size

---

#### 3. **ArduPilot Stage 1** - Legacy
```bash
python main.py --model ardupilot-stage1
```

**Specifications:**
- Accuracy: **85%**
- Response Time: ~0.4s
- Model Size: 552 MB
- Best For: Resource-constrained environments

**Pros:**
- Very fast
- Small model size
- Low resource usage

**Cons:**
- Lower accuracy
- Requires preprocessing layer
- Limited natural language understanding

---

## Usage Examples

### Basic Usage (Default Model)
```bash
# Uses qwen2.5:3b by default
python main.py
```

### Select Specific Model
```bash
# Use Gemma 3
python main.py --model gemma3:4b

# Use legacy model
python main.py --model ardupilot-stage1
```

### List Available Models
```bash
# See all installed Ollama models
python main.py --list-models
```

### Combine with Other Options
```bash
# Custom connection + model
python main.py --connection tcp:192.168.1.100:5760 --model qwen2.5:3b

# Verbose mode with specific model
python main.py --model gemma3:4b --verbose
```

---

## Installing Models

### Install Qwen 2.5 (Default)
```bash
ollama pull qwen2.5:3b
```

### Install Gemma 3
```bash
ollama pull gemma3:4b
```

### Install Legacy Model
```bash
ollama pull deepakpopli/ardupilot-stage1
```

---

## Model Comparison

| Model | Accuracy | Speed | Size | RAM | Best For |
|-------|----------|-------|------|-----|----------|
| **Qwen 2.5** | 96.1% | 2.5s | 1.9GB | ~3GB | Production |
| **Gemma 3** | 96.1% | 4.5s | 2.5GB | ~4GB | Alternative |
| **Stage 1** | 85% | 0.4s | 552MB | ~1GB | Edge devices |

---

## Switching Models

You can switch models at any time by:

1. **Command Line:**
   ```bash
   python main.py --model <model-name>
   ```

2. **Environment Variable (Future):**
   ```bash
   export ARDUPILOT_MODEL=qwen2.5:3b
   python main.py
   ```

3. **Configuration File (Future):**
   ```yaml
   # config.yaml
   model: qwen2.5:3b
   ```

---

## Troubleshooting

### Model Not Found
```bash
# List installed models
ollama list

# Pull missing model
ollama pull qwen2.5:3b
```

### Model Too Slow
- Try legacy model: `--model ardupilot-stage1`
- Ensure Ollama is using GPU acceleration
- Check system resources

### Low Accuracy
- Use Qwen 2.5 or Gemma 3 for best accuracy
- Legacy model has 85% accuracy (expected)

---

## Performance Tips

1. **For Best Accuracy:** Use `qwen2.5:3b` (default)
2. **For Speed:** Use `ardupilot-stage1` (legacy)
3. **For Balance:** Use `qwen2.5:3b` with GPU acceleration

---

## Future Models

We're continuously evaluating new models. Check the documentation for updates on:
- Qwen 2.5 (7B) - Higher accuracy
- Llama 3 variants
- Custom fine-tuned models

---

**Default Recommendation:** Stick with `qwen2.5:3b` for the best experience!
