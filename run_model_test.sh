#!/bin/bash
# Run model comparison test with conda environment

# Activate conda environment
source ~/.bashrc
conda activate ap_chat_tools

# Run the test
python tests/test_model_comparison.py
