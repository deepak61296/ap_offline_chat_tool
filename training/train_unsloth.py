#!/usr/bin/env python3
"""
ArduPilot AI: configurable Unsloth fine-tuning entrypoint.

Default workflow:
1. python training/build_dataset.py
2. python training/train_unsloth.py --profile agent-focused
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path

print("=" * 60)
print("ArduPilot AI - Unsloth Local Training Initializing")
print("=" * 60)

try:
    from datasets import load_dataset
    from transformers import DataCollatorForLanguageModeling, Trainer, TrainingArguments
    from unsloth import FastLanguageModel, is_bfloat16_supported
    from unsloth.chat_templates import get_chat_template
except ImportError as e:
    print(f"\n❌ Error: Missing Dependencies. {e}")
    print("Run this command first:")
    print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    print('pip install "unsloth[cu121-ampere-torch220] @ git+https://github.com/unslothai/unsloth.git"')
    print('pip install --no-deps "xformers<0.0.27" "trl<0.9.0" peft accelerate bitsandbytes datasets"')
    sys.exit(1)


ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET_DIR = ROOT / "data" / "processed"
DEFAULT_TRAIN_PATH = DEFAULT_DATASET_DIR / "train.jsonl"
DEFAULT_VAL_PATH = DEFAULT_DATASET_DIR / "validation.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "outputs"
DEFAULT_EXPORT_DIR = ROOT / "exports" / "ardupilot_ai_qwen25_3b"

PROFILE_CONFIGS = {
    "agent-focused": {
        "lr": 2e-4,
        "epochs": 2.0,
        "batch_size": 1,
        "grad_accum": 8,
        "lora_r": 16,
        "lora_alpha": 16,
        "max_seq_length": 1536,
    },
    "balanced": {
        "lr": 1.5e-4,
        "epochs": 2.0,
        "batch_size": 1,
        "grad_accum": 8,
        "lora_r": 16,
        "lora_alpha": 32,
        "max_seq_length": 1536,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune Qwen2.5-3B for ArduPilot AI.")
    parser.add_argument("--profile", choices=sorted(PROFILE_CONFIGS), default="agent-focused")
    parser.add_argument("--model-name", default="unsloth/Qwen2.5-3B-Instruct")
    parser.add_argument("--train-file", default=str(DEFAULT_TRAIN_PATH))
    parser.add_argument("--validation-file", default=str(DEFAULT_VAL_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--export-dir", default=str(DEFAULT_EXPORT_DIR))
    parser.add_argument("--epochs", type=float)
    parser.add_argument("--learning-rate", type=float)
    parser.add_argument("--per-device-batch-size", type=int)
    parser.add_argument("--gradient-accumulation-steps", type=int)
    parser.add_argument("--max-seq-length", type=int)
    parser.add_argument("--lora-r", type=int)
    parser.add_argument("--lora-alpha", type=int)
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument("--save-steps", type=int, default=100)
    parser.add_argument("--eval-steps", type=int, default=100)
    parser.add_argument("--disable-eval", action="store_true", default=True)
    parser.add_argument("--per-device-eval-batch-size", type=int, default=1)
    parser.add_argument("--seed", type=int, default=3407)
    parser.add_argument("--skip-export", action="store_true")
    return parser.parse_args()


def ensure_file(path_str: str, label: str) -> Path:
    path = Path(path_str).resolve()
    if not path.exists():
        print(f"❌ Error: {label} not found at {path}")
        sys.exit(1)
    return path


def build_training_args(args: argparse.Namespace, profile: dict) -> TrainingArguments:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    signature = inspect.signature(TrainingArguments.__init__)
    supported = set(signature.parameters)

    kwargs = {
        "per_device_train_batch_size": args.per_device_batch_size or profile["batch_size"],
        "per_device_eval_batch_size": args.per_device_eval_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps or profile["grad_accum"],
        "num_train_epochs": args.epochs or profile["epochs"],
        "learning_rate": args.learning_rate or profile["lr"],
        "fp16": not is_bfloat16_supported(),
        "bf16": is_bfloat16_supported(),
        "logging_steps": args.logging_steps,
        "optim": "adamw_8bit",
        "weight_decay": 0.01,
        "lr_scheduler_type": "linear",
        "seed": args.seed,
        "output_dir": str(output_dir),
        "save_strategy": "steps",
        "save_steps": args.save_steps,
        "load_best_model_at_end": False,
    }

    if args.disable_eval:
        if "evaluation_strategy" in supported:
            kwargs["evaluation_strategy"] = "no"
        elif "eval_strategy" in supported:
            kwargs["eval_strategy"] = "no"
    else:
        kwargs["eval_steps"] = args.eval_steps
        if "evaluation_strategy" in supported:
            kwargs["evaluation_strategy"] = "steps"
        elif "eval_strategy" in supported:
            kwargs["eval_strategy"] = "steps"

    if "report_to" in supported:
        kwargs["report_to"] = "none"

    return TrainingArguments(**kwargs)


def format_dataset(dataset, tokenizer):
    def formatting_prompts_func(examples):
        texts = [
            tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False)
            for convo in examples["messages"]
        ]
        return {"text": texts}

    return dataset.map(formatting_prompts_func, batched=True)


def tokenize_dataset(dataset, tokenizer, max_seq_length):
    def tokenize_batch(examples):
        tokenized = tokenizer(
            examples["text"],
            truncation=True,
            max_length=max_seq_length,
            padding="max_length",
        )
        tokenized["labels"] = [ids[:] for ids in tokenized["input_ids"]]
        return tokenized

    return dataset.map(
        tokenize_batch,
        batched=True,
        remove_columns=dataset.column_names,
    )


def main() -> None:
    args = parse_args()
    profile = PROFILE_CONFIGS[args.profile]
    train_file = ensure_file(args.train_file, "train dataset")
    validation_file = ensure_file(args.validation_file, "validation dataset")
    max_seq_length = args.max_seq_length or profile["max_seq_length"]

    print(f"Profile: {args.profile}")
    print(f"Train file: {train_file}")
    print(f"Validation file: {validation_file}")
    print(f"Loading {args.model_name} in 4-bit mode...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model_name,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    tokenizer = get_chat_template(tokenizer, chat_template="qwen-2.5")

    print("Attaching LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r or profile["lora_r"],
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha=args.lora_alpha or profile["lora_alpha"],
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=args.seed,
    )

    dataset_dict = load_dataset(
        "json",
        data_files={
            "train": str(train_file),
            "validation": str(validation_file),
        },
    )
    train_dataset = tokenize_dataset(format_dataset(dataset_dict["train"], tokenizer), tokenizer, max_seq_length)
    validation_dataset = tokenize_dataset(format_dataset(dataset_dict["validation"], tokenizer), tokenizer, max_seq_length)

    print("\nStarting training...")
    trainer = Trainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=None if args.disable_eval else validation_dataset,
        args=build_training_args(args, profile),
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )

    trainer_stats = trainer.train()
    print(f"Training finished. Steps: {trainer_stats.global_step}")

    if args.skip_export:
        print("Skipping GGUF export by request.")
        return

    export_dir = Path(args.export_dir).resolve()
    export_dir.mkdir(parents=True, exist_ok=True)
    print(f"Exporting GGUF to {export_dir} ...")
    model.save_pretrained_gguf(str(export_dir), tokenizer, quantization_method="q4_k_m")
    print(f"✅ Exported GGUF to {export_dir}")


if __name__ == "__main__":
    main()
