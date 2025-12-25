# Model Setup Guide

## Overview

The ArduPilot AI Assistant uses a fine-tuned model called `ardupilot-stage1`. This model is **not stored in the repository** - it's installed in your local Ollama instance.

## Why the Model Isn't in the Repo

1. **Size**: The model is ~500MB (too large for Git)
2. **Storage**: Ollama manages models in its own directory (`~/.ollama/models/`)
3. **Architecture**: The code calls the model via Ollama's API by name

## For Users: Getting the Model

### Option 1: Use Pre-trained Model (Easiest)

If the model is published to Ollama's library:

```bash
ollama pull deepakpopli/ardupilot-stage1
```

### Option 2: Import from Modelfile

If a Modelfile is provided in this repo:

```bash
cd models/
ollama create ardupilot-stage1 -f ardupilot-stage1.Modelfile
```

### Option 3: Train Your Own (Advanced)

See [TRAINING_GUIDE.md](../docs/TRAINING_GUIDE.md) for instructions on training the model yourself.

## For Developers: Exporting Your Model

If you've trained the model and want to share it:

### Export Modelfile

```bash
# Export the model configuration
ollama show ardupilot-stage1 --modelfile > models/ardupilot-stage1.Modelfile

# Commit to repo
git add models/ardupilot-stage1.Modelfile
git commit -m "Add ardupilot-stage1 Modelfile"
```

### Publish to Ollama Library

```bash
# Tag your model
ollama tag ardupilot-stage1 yourusername/ardupilot-stage1

# Push to Ollama's public library
ollama push yourusername/ardupilot-stage1
```

Then update the README to tell users:
```bash
ollama pull yourusername/ardupilot-stage1
```

## Verifying Model Installation

Check if the model is installed:

```bash
ollama list | grep ardupilot-stage1
```

You should see:
```
ardupilot-stage1    latest    abc123def456    500 MB    2 days ago
```

Test the model:

```bash
ollama run ardupilot-stage1 "arm the drone"
```

Expected output:
```
<start_function_call>call:arm{}<end_function_call>
```

## Model Location on Your System

Ollama stores models in:
- **Linux**: `~/.ollama/models/`
- **macOS**: `~/.ollama/models/`
- **Windows**: `%USERPROFILE%\.ollama\models\`

**Note**: You don't need to access this directory directly. Use `ollama` commands instead.

## Troubleshooting

### Model Not Found

```bash
Error: model 'ardupilot-stage1' not found
```

**Solutions**:
1. Check if model exists: `ollama list`
2. Pull/create the model (see options above)
3. Verify Ollama is running: `ollama serve`

### Model Performance Issues

If the model gives poor results:
1. Verify it's the correct model: `ollama show ardupilot-stage1`
2. Check model size (should be ~500MB for Stage 1)
3. Try retraining with more examples

## Model Versions

- **Stage 1** (current): 8 core functions, 85% accuracy
- **Stage 2** (planned): 15 additional functions, 90%+ accuracy
- **Stage 3** (future): All 29 functions, context awareness

## Training Data

The training data used for Stage 1 is available in:
- `models/training_data_stage1.json` (if included)
- Or see [TRAINING_GUIDE.md](../docs/TRAINING_GUIDE.md) for how to create it

## License

The model is based on Google's FunctionGemma (Apache 2.0 license) and fine-tuned for ArduPilot commands.

---

**Need help?** See [INSTALLATION.md](../docs/INSTALLATION.md) or open an issue.
