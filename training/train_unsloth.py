#!/usr/bin/env python3
"""
ArduPilot AI: Unsloth Fine-Tuning Pipeline (RTX 4050 6GB Optimized)

Headless training script. Run with:
python train_unsloth.py
"""

import sys
import os

print("="*60)
print("ArduPilot AI - Unsloth Local Training Initializing")
print("="*60)

try:
    from unsloth import FastLanguageModel
    from datasets import load_dataset
    from unsloth.chat_templates import get_chat_template
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from unsloth import is_bfloat16_supported
except ImportError as e:
    print(f"\n❌ Error: Missing Dependencies. {e}")
    print("Run this command first:")
    print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    print('pip install "unsloth[cu121-ampere-torch220] @ git+https://github.com/unslothai/unsloth.git"')
    print('pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes datasets')
    sys.exit(1)

# 1. Configuration
max_seq_length = 2048 # Safe context window for 6GB VRAM
model_name = "unsloth/Qwen2.5-3B-Instruct"
dataset_path = "../scripts/qwen_finetune_dataset.jsonl"
export_path = "ardupilot_ai_finetuned"

if not os.path.exists(dataset_path):
    print(f"❌ Error: Dataset {dataset_path} not found.")
    sys.exit(1)

print(f"Loading {model_name} in 4-bit mode (VRAM optimized)...")

# 2. Load Model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    dtype = None,
    load_in_4bit = True, # CRITICAL for RTX 4050
)

# 3. LoRA setup
print("Attaching LoRA training adapters...")
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth", # Saves 30% VRAM
    random_state = 3407,
)

# 4. Load Dataset
print(f"Formatting dataset {dataset_path} for Qwen 2.5...")
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "qwen-2.5",
)

def formatting_prompts_func(examples):
    convos = examples["messages"]
    texts = [tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False) for convo in convos]
    return { "text" : texts }

dataset = load_dataset("json", data_files=dataset_path, split="train")
dataset = dataset.map(formatting_prompts_func, batched=True)

# 5. Trainer Configuration
print("\nStarting Training Pipeline...")
print("This may take 1-2 hours on a mobile 4050 GPU.\n")

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        num_train_epochs = 1, # Run over dataset 1 time
        learning_rate = 2e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 10,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
    ),
)

# Run Training
trainer_stats = trainer.train()

# 6. Export
print("\nTraining Complete! Exporting to Ollama GGUF format...")
model.save_pretrained_gguf(export_path, tokenizer, quantization_method = "q4_k_m")
print(f"✅ SUCCESSFULLY EXPORTED TO /{export_path}")
print("You can now import this into Ollama!")
