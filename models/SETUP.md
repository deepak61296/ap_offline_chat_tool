# Quick Model Setup Instructions

## For New Users

If you're setting up this project for the first time, you need to get the `ardupilot-stage1` model.

### Option 1: Use the Modelfile (Recommended)

```bash
# From the project root
cd models/
ollama create ardupilot-stage1 -f ardupilot-stage1.Modelfile

# Verify it worked
ollama list | grep ardupilot-stage1
```

### Option 2: Pull from Ollama Library (If Published)

```bash
ollama pull deepakpopli/ardupilot-stage1
```

### Option 3: Train Your Own

See the training guide (coming soon) to train the model yourself using the training data.

## Verifying Installation

Test the model:

```bash
ollama run ardupilot-stage1 "arm the drone"
```

Expected output:
```
<start_function_call>call:arm{}<end_function_call>
```

## Model Details

- **Name**: ardupilot-stage1
- **Base**: google/functiongemma-270m-it
- **Size**: ~500MB
- **Functions**: 8 (arm, disarm, takeoff, land, rtl, change_mode, get_battery, get_position)
- **Accuracy**: 85% (17/20 test cases)

## Troubleshooting

**Model not found?**
```bash
# Check if Ollama is running
ollama serve

# List all models
ollama list

# Recreate from Modelfile
cd models/
ollama create ardupilot-stage1 -f ardupilot-stage1.Modelfile
```

**Model gives wrong results?**
- Make sure you're using `ardupilot-stage1`, not the base `functiongemma` model
- Check model size is ~500MB (not 270MB which would be the base model)
- Verify with: `ollama show ardupilot-stage1`

---

**Ready to use?** Go back to the main [README.md](../README.md) and run the demo!
