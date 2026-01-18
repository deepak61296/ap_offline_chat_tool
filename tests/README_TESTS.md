# Automated Test Suite - Quick Reference

## What This Tests

This comprehensive test suite verifies **ALL** claimed functions actually exist and work correctly. It will catch any hallucinations or missing features.

## Test Coverage

### 1. Basic Flight Commands (5 tests)
- ARM
- DISARM  
- TAKEOFF
- LAND
- RTL (Return to Launch)

### 2. Directional Movement (8 tests)
- Move North/South/East/West
- Multiple command variations
- Distance validation

### 3. Altitude Changes (8 tests)
- Increase/Decrease altitude
- Go up/down
- Ascend/Descend
- Climb/Drop

### 4. Mode Changes (6 tests)
- GUIDED, AUTO, LOITER
- STABILIZE, ALT_HOLD, LAND
- Mode validation

### 5. Navigation (5 tests)
- GOTO coordinates
- GOTO with altitude
- GOTO home
- Coordinate validation

### 6. Parameters (6 tests)
- GET parameter
- SET parameter
- Multiple parameter types

### 7. System Commands (3 tests)
- REBOOT
- RESTART
- System control

### 8. Conversational Queries (10 tests)
- Greetings
- Status queries
- Location queries (Ask mode)
- No accidental command execution

### 9. Edge Cases & Safety (8 tests)
- Excessive values
- Invalid modes
- Uncertain commands
- Ask mode restrictions

**Total: 60+ test cases**

## How to Run

### Prerequisites
1. Backend must be running:
   ```bash
   scripts\start_backend.bat
   ```

2. Ollama must be running:
   ```bash
   ollama serve
   ```

### Run Tests

**Option 1: Using batch file (Recommended)**
```bash
scripts\run_tests.bat
```

**Option 2: Manual**
```bash
conda activate ap_chat_tools
python tests\test_all_functions.py
```

## Test Duration

- Expected: **10-15 minutes**
- Includes 30-second timeout per test
- Tests run sequentially for accuracy

## Report Output

### Console Output
- Real-time test results with ✓/✗ indicators
- Color-coded pass/fail
- Summary statistics

### HTML Report (`test_report.html`)
- Detailed test results table
- Success rate visualization
- Input/Output for each test
- Error messages for failures
- Automatically opens in browser

## Interpreting Results

### Success Rates
- **90-100%**: ✅ Excellent - All systems operational
- **70-89%**: ⚠️ Good - Some issues need attention  
- **<70%**: ❌ Critical - Major issues detected

### Common Failures
1. **Backend not running** - Start backend first
2. **Model not downloaded** - Run `ollama pull qwen2.5:3b`
3. **Timeout errors** - Backend may be slow, increase TIMEOUT in script
4. **Command extraction fails** - Check prompts.py and commands.py

## What Gets Verified

✅ Backend health and connectivity
✅ Command extraction accuracy
✅ AI response correctness
✅ Parameter validation
✅ Safety checks (no accidental execution)
✅ Edge case handling
✅ Ask mode vs Agent mode behavior
✅ Telemetry integration
✅ Error handling

## Troubleshooting

**Tests fail to start:**
- Check backend is running: `curl http://localhost:5000/health`
- Verify conda environment: `conda activate ap_chat_tools`
- Check Python dependencies: `pip install requests`

**Many tests fail:**
- Check Ollama is running: `ollama list`
- Verify model is downloaded: `ollama pull qwen2.5:3b`
- Review backend logs for errors

**Timeout errors:**
- Increase TIMEOUT in test_all_functions.py (line 14)
- Check system resources (CPU/RAM)
- Try CPU-only mode: `scripts\start_backend_cpu.bat`

## Extending Tests

To add more test cases, edit `tests/test_all_functions.py`:

```python
# Add to appropriate section
self.test_command(
    category="YourCategory",
    test_name="Test Name",
    input_text="user command",
    expected_command_type="COMMAND_TYPE",
    expected_phrase="expected response phrase"
)
```

## Files Generated

- `test_report.html` - Detailed HTML report (auto-opens)
- Console output - Real-time results

## Next Steps After Testing

1. Review HTML report for failures
2. Fix any failing tests
3. Re-run tests to verify fixes
4. Keep report for documentation

---

**Note:** This test suite is designed to be comprehensive and will take 10-15 minutes. It's worth the wait to ensure everything works correctly!
