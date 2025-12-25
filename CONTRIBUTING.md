# Contributing to ArduPilot AI Assistant

Thank you for your interest in contributing to the ArduPilot AI Assistant project! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style Guidelines](#code-style-guidelines)
- [Adding New Functions](#adding-new-functions)
- [Improving Training Data](#improving-training-data)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/AP_Offline_chat_tools.git
   cd AP_Offline_chat_tools
   ```
3. **Set up the development environment**:
   ```bash
   bash setup.sh
   ```
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Setup

### Prerequisites

- Python 3.8 or higher
- Conda (recommended)
- Ollama
- ArduPilot SITL (for testing)

### Environment Setup

```bash
# Create conda environment
conda create -n ap_chat_tools python=3.8
conda activate ap_chat_tools

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pylint black isort
```

### Verify Setup

```bash
# Run tests
python -m pytest tests/ -v

# Run demo mode
python demo.py
```

## 💡 How to Contribute

### Types of Contributions

1. **Bug Fixes** - Fix issues in existing code
2. **New Features** - Add new drone functions or capabilities
3. **Documentation** - Improve docs, add examples
4. **Training Data** - Improve model accuracy with better data
5. **Testing** - Add or improve test coverage
6. **Performance** - Optimize code for speed or memory

### Finding Issues to Work On

- Check the [Issues](../../issues) page for open issues
- Look for issues labeled `good first issue` or `help wanted`
- Ask in [Discussions](../../discussions) if you're unsure where to start

## 📝 Code Style Guidelines

### Python Style

We follow **PEP 8** with some project-specific conventions:

#### General Rules

- **Line length**: Maximum 100 characters
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Use double quotes for strings
- **Imports**: Group and sort imports (use `isort`)

#### Naming Conventions

```python
# Classes: PascalCase
class DroneController:
    pass

# Functions and methods: snake_case
def get_battery_status():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_ALTITUDE = 100

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

#### Docstrings

Use **Google-style docstrings** for all public functions and classes:

```python
def takeoff(altitude: float) -> Dict[str, Any]:
    """
    Take off to specified altitude.
    
    This function commands the drone to takeoff to the specified altitude
    in meters. The drone must be armed before calling this function.
    
    Args:
        altitude: Target altitude in meters (relative to home position).
                 Must be between 0 and MAX_ALTITUDE.
    
    Returns:
        Dictionary containing:
            - status (str): "success" or "error"
            - message (str): Human-readable result message
            - altitude (float): Target altitude (on success)
    
    Raises:
        ValueError: If altitude is negative or exceeds MAX_ALTITUDE
        ConnectionError: If drone is not connected
    
    Example:
        >>> result = drone.takeoff(15.0)
        >>> print(result)
        {'status': 'success', 'message': 'Taking off to 15.0m', 'altitude': 15.0}
    """
    # Implementation here
```

#### Type Hints

Always use type hints for function parameters and return values:

```python
from typing import Dict, Any, Optional, List

def get_position(self) -> Dict[str, Any]:
    """Get current drone position."""
    pass

def goto_location(self, lat: float, lon: float, alt: float) -> Dict[str, Any]:
    """Navigate to GPS location."""
    pass

def parse_command(self, text: str) -> Optional[Dict[str, Any]]:
    """Parse natural language command."""
    pass
```

#### Code Formatting

Use **Black** for automatic formatting:

```bash
# Format all Python files
black .

# Check formatting without changes
black --check .
```

Use **isort** for import sorting:

```bash
# Sort imports
isort .

# Check import sorting
isort --check .
```

## 🔧 Adding New Functions

### Step 1: Add Function to `drone_functions.py`

```python
def new_function(self, param1: float, param2: str = "default") -> Dict[str, Any]:
    """
    Brief description of what this function does.
    
    Detailed explanation of the function's behavior, safety considerations,
    and any important notes.
    
    Args:
        param1: Description of param1 with units and valid range
        param2: Description of param2 with default value
    
    Returns:
        Dictionary with status, message, and any relevant data
    
    Example:
        >>> result = drone.new_function(10.5, "test")
        >>> print(result['status'])
        'success'
    """
    try:
        # Validate inputs
        if param1 < 0:
            return {
                "status": "error",
                "message": "param1 must be non-negative"
            }
        
        # Implement function logic
        # ... your MAVLink code here ...
        
        return {
            "status": "success",
            "message": f"Function executed with {param1}, {param2}",
            "param1": param1,
            "param2": param2
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Function failed: {str(e)}"
        }
```

### Step 2: Add to `DRONE_FUNCTIONS` Dictionary

```python
DRONE_FUNCTIONS = {
    # ... existing functions ...
    
    "new_function": {
        "description": "Brief description for help text",
        "parameters": {
            "param1": {
                "type": "number",
                "description": "Description of param1",
                "required": True
            },
            "param2": {
                "type": "string",
                "description": "Description of param2",
                "required": False,
                "default": "default"
            }
        }
    }
}
```

### Step 3: Add Mock Implementation to `demo.py`

```python
class MockDroneController:
    # ... existing methods ...
    
    def new_function(self, param1, param2="default"):
        """Mock implementation for demo mode"""
        return {
            "status": "success",
            "message": f"✅ New function executed: {param1}, {param2} (simulated)"
        }
```

### Step 4: Add Tests

```python
# tests/test_new_function.py
import pytest
from drone_functions import DroneController

def test_new_function_success():
    """Test new_function with valid inputs"""
    # Test implementation
    pass

def test_new_function_invalid_input():
    """Test new_function with invalid inputs"""
    # Test implementation
    pass
```

## 📊 Improving Training Data

### Training Data Format

Training data is in JSON format with input-output pairs:

```json
{
  "examples": [
    {
      "input": "arm the drone",
      "output": "<start_function_call>call:arm{}<end_function_call>"
    },
    {
      "input": "takeoff to 15 meters",
      "output": "<start_function_call>call:takeoff{altitude:15}<end_function_call>"
    }
  ]
}
```

### Adding Training Examples

1. **Diverse Phrasing**: Add multiple ways to express the same command
   ```json
   "arm the drone"
   "arm motors"
   "prepare for flight"
   "ready to fly"
   ```

2. **Edge Cases**: Include unusual but valid commands
   ```json
   "takeoff to 0.5 meters"  // Very low altitude
   "fly to exactly 28.535500, 77.391000"  // Precise coordinates
   ```

3. **Error Cases**: Include invalid commands (for future error handling)
   ```json
   "takeoff to -10 meters"  // Invalid negative altitude
   ```

### Guidelines

- **Quality over quantity**: 10 good examples > 100 poor examples
- **Natural language**: Use how people actually speak
- **Consistency**: Follow the established output format exactly
- **Test coverage**: Ensure all parameters are covered

## ✅ Testing Requirements

### Test Coverage

All new functions must have:

1. **Unit tests** - Test function in isolation
2. **Integration tests** - Test with demo mode
3. **Edge case tests** - Test boundary conditions
4. **Error handling tests** - Test failure modes

### Writing Tests

```python
import pytest
from drone_functions import DroneController

class TestNewFunction:
    """Test suite for new_function"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.drone = DroneController()
    
    def test_valid_input(self):
        """Test with valid input"""
        result = self.drone.new_function(10.5, "test")
        assert result["status"] == "success"
        assert result["param1"] == 10.5
    
    def test_invalid_input(self):
        """Test with invalid input"""
        result = self.drone.new_function(-1, "test")
        assert result["status"] == "error"
        assert "must be non-negative" in result["message"]
    
    def test_default_parameter(self):
        """Test with default parameter"""
        result = self.drone.new_function(10.5)
        assert result["param2"] == "default"
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_new_function.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## 🔄 Pull Request Process

### Before Submitting

1. **Update documentation** - README, docstrings, etc.
2. **Add tests** - Ensure good test coverage
3. **Run tests** - All tests must pass
4. **Format code** - Run `black` and `isort`
5. **Update CHANGELOG** - Add your changes to `CHANGELOG.md`

### PR Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts

### Commit Message Format

Use clear, descriptive commit messages:

```
feat: Add new_function for advanced navigation
fix: Correct battery display formatting
docs: Update README with new examples
test: Add tests for takeoff function
refactor: Simplify function parsing logic
```

Prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `style:` - Formatting changes
- `chore:` - Maintenance tasks

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
Describe how you tested your changes

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated
```

## 🎯 Areas Needing Help

### High Priority

1. **Stage 2 Training Data** - Add examples for 15 additional functions
2. **Test Coverage** - Increase test coverage to 80%+
3. **Documentation** - Add more examples and tutorials

### Medium Priority

1. **Performance Optimization** - Reduce response time
2. **Error Messages** - Make errors more helpful
3. **UI Improvements** - Better terminal interface

### Low Priority

1. **Multi-language Support** - Add support for other languages
2. **Voice Input** - Add voice command support
3. **Web Interface** - Create web-based UI

## 📞 Getting Help

- **Questions**: Open a [Discussion](../../discussions)
- **Bugs**: Open an [Issue](../../issues)
- **Chat**: Join our community chat (if available)

## 🙏 Recognition

Contributors will be:
- Listed in README.md
- Mentioned in release notes
- Credited in commit history

Thank you for contributing to ArduPilot AI Assistant! 🚁
