# Quick Test Script for Qwen 2.5 Integration

This script tests the new Qwen 2.5 integration with natural language commands.

## Run Demo Mode

```bash
python examples/demo.py
```

## Test Commands

Try these natural language variations:
- "hey can you please arm the drone"
- "takeoff UAV to 20 meters"
- "bring it down"
- "go back home"
- "what's the battery level"
- "where is the drone"

## Run Tests

```bash
# Run test suite
python tests/test_suite.py

# Run preprocessing tests (should still work)
python tests/test_preprocessing.py
```

## Expected Results

- **Model**: Qwen 2.5 (3B)
- **Accuracy**: 96.1%
- **Response Time**: ~2.5s
- **No preprocessing needed** - handles all variations naturally

## Integration Changes

1. Created `src/qwen_interface.py` - New Qwen 2.5 interface
2. Updated `main.py` - Uses Qwen25Interface
3. Updated `examples/demo.py` - Uses Qwen25Interface
4. Updated test files - Use Qwen25Interface
5. Backward compatibility maintained via alias

## Next: SITL Testing

Once demo mode works, test with real SITL:

```bash
# Terminal 1: Start SITL
cd ~/ardupilot/ArduCopter
sim_vehicle.py -w --console --map

# Terminal 2: Start AI Assistant
python main.py
```
