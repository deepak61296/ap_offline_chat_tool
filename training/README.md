# Training Pipeline

This directory now contains a training-only workflow for improving `qwen2.5:3b` on the current ArduPilot backend without editing runtime code outside `training/`.

## What It Covers

- `build_dataset.py`: builds ChatML JSONL datasets aligned to the backend's current tool-calling behavior.
- `fetch_ardupilot_docs.py`: optionally downloads a small curated slice of official ArduPilot docs into `training/data/raw_docs/`.
- `train_unsloth.py`: configurable LoRA SFT trainer for `unsloth/Qwen2.5-3B-Instruct`.
- `evaluate_model.py`: runs the existing golden backend tests and stores copies of the reports in `training/reports/`.

## Recommended Workflow

```bash
conda activate ardupilot_ai
python training/build_dataset.py
python training/train_unsloth.py --profile agent-focused
python training/evaluate_model.py --label baseline-or-ft-run
```

## With Official Docs

The docs fetcher is optional. It requires network access.

```bash
python training/fetch_ardupilot_docs.py
python training/build_dataset.py --include-docs
```

## Notes

- The builder uses `backend/apm.pdef.json` as the main source of grounded parameter names and descriptions.
- The golden datasets under `tests/` are left untouched and are reused only for evaluation.
- The dataset intentionally emphasizes weak areas seen in current results, especially radio/RC calibration and vague parameter queries.
