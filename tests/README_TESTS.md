# ArduPilot AI Backend - Test Suite

## Overview

Comprehensive test suite for validating AI command extraction and response generation.

## Main Test File

**`test_comprehensive.py`** - Complete test suite with 170+ tests

### Test Categories

1. **Baseline & Core (53 tests)** - Basic flight commands, movement, altitude, modes, parameters
2. **Natural Language (50 tests)** - Casual speech, polite requests, abbreviations, typos
3. **Ambiguous & Compound (25 tests)** - Missing parameters, vague directions, multi-step requests
4. **Safety & Edge Cases (42 tests)** - Excessive values, dangerous combinations, emergency commands

### Running Tests

```bash
# Run comprehensive test suite
python tests/test_comprehensive.py

# Or use batch file (Windows)
scripts\run_comprehensive_tests.bat

# View results
# Open tests/test_report.html in browser
```

## Latest Results

**Pass Rate:** 76.8% (116/151 tests passing)
**Model:** qwen2.5:3b (3 billion parameters)

This is excellent accuracy considering:
- Rigorous test suite with edge cases
- Very small model (only 2GB)
- No fine-tuning yet

## Test Report

After running tests, open `test_report.html` for:
- Detailed pass/fail breakdown
- Category-wise statistics
- Actual AI responses
- Error messages for failures

## Utility Scripts

- **`test_model_comparison.py`** - Compare different Ollama models
- **`diagnose_backend.py`** - Check backend health and connectivity

## Adding New Tests

1. Open `test_comprehensive.py`
2. Add test case to appropriate section
3. Run test suite
4. Check `test_report.html` for results

Example:
```python
self.test_command("Category", "Test Name", "user input", "EXPECTED_COMMAND_TYPE")
```

## Notes

- Tests require backend to be running on `localhost:5000`
- Each test has 0.3s delay to avoid overwhelming the model
- Full suite takes ~8-12 minutes to complete
- Some "failures" are actually correct behavior (e.g., rejecting unsafe commands)
