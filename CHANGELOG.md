# Changelog

All notable changes to the ArduPilot AI Assistant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-26

### Added

#### Core Functionality
- Fine-tuned `ardupilot-stage1` model with 85% accuracy (17/20 test cases)
- 8 core drone control functions (arm, disarm, takeoff, land, rtl, change_mode, get_battery, get_position)
- Natural language command processing via FunctionGemma (270M parameters)
- PyMAVLink integration for drone control
- Demo mode for testing without SITL
- SITL mode for full ArduPilot simulation

#### User Interface
- Rich terminal UI with colored output
- Interactive command-line interface
- Welcome banners for both demo and SITL modes
- Command shortcuts (`/q`, `/h`, `/s`, `/r`)
- Help system with function reference table
- Status command showing battery and position

#### Safety Features
- Pre-arm condition checks
- GPS lock verification
- Battery voltage monitoring
- Mode change validation
- Altitude safety limits
- Comprehensive error handling

#### Documentation
- Professional README.md with badges and examples
- Quick start guide (zero to running in 15 minutes)
- Architecture diagram
- Troubleshooting section
- Usage examples for all 8 functions
- Installation instructions

#### Configuration
- Command-line arguments (`--connection`, `--model`, `--verbose`)
- Flexible connection strings (UDP, TCP, Serial)
- Model selection support
- Verbose mode for debugging

### Fixed

- **Critical**: Battery display now shows actual values (voltage, current, percentage) instead of generic "Command executed successfully"
- **Critical**: Position display now shows coordinates (lat, lon, altitude, heading) instead of generic message
- Improved error messages with actionable guidance
- Better handling of edge cases in function parsing
- Consistent formatting across demo and SITL modes

### Changed

- Enhanced welcome banners with ASCII art and model information
- Improved command parsing with better error messages
- Updated function result formatting for data-returning functions
- Better separation of concerns in code structure
- More descriptive variable names and function signatures

### Technical Details

#### Model Training
- Base model: google/functiongemma-270m-it
- Training data: 206 examples
- Training time: 4 min 24 sec (Colab T4 GPU)
- Final loss: 0.0207
- Accuracy: 85% (17/20 test cases)

#### Response Format
```
Input: "arm the drone"
Output: <start_function_call>call:arm{}<end_function_call>

Input: "takeoff to 15 meters"
Output: <start_function_call>call:takeoff{altitude:15}<end_function_call>
```

#### Supported Functions (Stage 1)
1. `arm()` - Arm drone motors
2. `disarm()` - Disarm drone motors
3. `takeoff(altitude)` - Takeoff to specified altitude
4. `land()` - Land at current location
5. `rtl()` - Return to launch position
6. `change_mode(mode)` - Change flight mode
7. `get_battery()` - Get battery status
8. `get_position()` - Get current GPS position

### Dependencies

- Python 3.8+
- pymavlink >= 2.4.0
- ollama >= 0.1.0
- rich >= 13.0.0

### Known Issues

- Stage 1 limited to 8 functions (21 more available in code, pending Stage 2 training)
- Best performance with single commands (multi-command sequences coming in Stage 2)
- English language only
- Coordinate precision limited to ~6 decimal places

### Performance Metrics

- Response time: < 1 second per command
- Model size: 270M parameters
- Memory usage: ~2GB RAM
- Disk space: ~500MB (model + dependencies)

---

## [Unreleased]

### Planned for Stage 2

- [ ] 15 additional functions (waypoints, missions, advanced navigation)
- [ ] Multi-step command sequences
- [ ] Improved accuracy (target: 90%+)
- [ ] Better context awareness
- [ ] Command history and autocomplete

### Planned for Stage 3

- [ ] All 29 functions
- [ ] Full context awareness
- [ ] Error recovery and suggestions
- [ ] Multi-language support
- [ ] Voice input support

---

## Version History

- **1.0.0** (2025-12-26) - Stage 1 Complete - Initial release with 8 core functions

---

[1.0.0]: https://github.com/yourusername/AP_Offline_chat_tools/releases/tag/v1.0.0
