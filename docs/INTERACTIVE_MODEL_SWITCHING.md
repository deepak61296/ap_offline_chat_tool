# Interactive Model Switching - Quick Guide

## ✨ New Feature: Switch Models On-The-Fly!

You can now change AI models **during runtime** without restarting the application!

### Usage

**View Current Model:**
```
/model
```

Output:
```
Current Model: qwen2.5:3b

Available Models:
  • qwen2.5:3b (default) - 96% accuracy, 2.5s response
  • gemma3:4b - 96% accuracy, 4.5s response
  • ardupilot-stage1 (legacy) - 85% accuracy, 0.4s response

Usage: /model <model-name>
Example: /model gemma3:4b
```

**Switch Model:**
```
/model gemma3:4b
```

Output:
```
Switching model...
From: qwen2.5:3b
To: gemma3:4b
✓ Model switched to gemma3:4b
Conversation history preserved
```

### Examples

**Switch to Gemma 3:**
```
You: /model gemma3:4b
✓ Model switched to gemma3:4b

You: arm and takeoff to 15m
[Using Gemma 3 now]
```

**Switch to Legacy Model:**
```
You: /model ardupilot-stage1
✓ Model switched to ardupilot-stage1

You: check battery
[Using legacy model now]
```

**Switch Back to Default:**
```
You: /model qwen2.5:3b
✓ Model switched to qwen2.5:3b
```

### All Special Commands

- `/help` or `/h` - Show available functions
- `/status` or `/s` - Get drone status
- **`/model [name]`** - Switch AI model ⭐ NEW!
- `/reset` or `/r` - Clear conversation history
- `/quit` or `/q` - Exit application

### Benefits

1. **No Restart Needed** - Switch models instantly
2. **Compare Performance** - Test different models on same commands
3. **Optimize for Task** - Use fast model for simple tasks, accurate for complex
4. **Conversation Preserved** - History maintained across switches
5. **Easy Discovery** - Just type `/model` to see options

### Use Cases

**Performance Testing:**
```
/model qwen2.5:3b
arm and takeoff to 20m
[Note response time]

/model gemma3:4b
arm and takeoff to 20m
[Compare response time]
```

**Resource Optimization:**
```
# Use fast model for simple commands
/model ardupilot-stage1
check battery
get position

# Switch to accurate model for complex operations
/model qwen2.5:3b
create mission and add waypoints
```

**Model Comparison:**
```
/model qwen2.5:3b
hover for 5 seconds
[Test accuracy]

/model gemma3:4b
hover for 5 seconds
[Compare accuracy]
```

### Error Handling

**Model Not Found:**
```
You: /model invalid-model
✗ Failed to switch model: Model not found
Make sure the model is installed: ollama pull <model-name>
```

**Solution:**
```bash
# Install missing model
ollama pull gemma3:4b

# Then try again
/model gemma3:4b
```

### Tips

1. **Start with default** - Qwen 2.5 is optimized for best accuracy
2. **Test before switching** - Use `/model` to see current model
3. **Install first** - Make sure model is installed before switching
4. **Compare performance** - Try different models for your use case

---

**Quick Reference:**
- `/model` - Show current model and options
- `/model qwen2.5:3b` - Switch to Qwen (default, 96% accuracy)
- `/model gemma3:4b` - Switch to Gemma (96% accuracy, slower)
- `/model ardupilot-stage1` - Switch to legacy (85% accuracy, fast)
