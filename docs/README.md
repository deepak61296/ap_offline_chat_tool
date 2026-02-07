# Documentation Index

Complete documentation for the ArduPilot AI Backend project.

## Quick Navigation

### Getting Started
- **[Project Overview](PROJECT_OVERVIEW.md)** - High-level introduction, features, and use cases
- **[Installation (Windows)](INSTALL_WINDOWS.md)** - Step-by-step Windows setup
- **[Architecture](ARCHITECTURE.md)** - System design, components, and data flow

### Development
- **[Contributing Guide](CONTRIBUTING.md)** - Developer workflow and coding standards
- **[Compatibility Matrix](COMPATIBILITY.md)** - Version requirements for all components

### Configuration
- **[Model Selection](MODEL_SELECTION.md)** - Choosing and configuring LLM models

### Integration
- **[Mission Planner Setup](README_MISSION_PLANNER.md)** - Mission Planner integration guide

## Document Descriptions

### PROJECT_OVERVIEW.md
Comprehensive introduction to the project covering:
- What the system does and why
- Core concepts and workflow
- Three operation modes (Agent/Ask/Script)
- Safety features and validation
- Technology stack and requirements
- Command reference table
- Integration options for both MAVProxy and Mission Planner
- Use cases and examples
- Performance metrics

**Audience:** New users, stakeholders, anyone evaluating the project

### ARCHITECTURE.md
Technical deep-dive into system design:
- Multi-layer architecture diagram (User/Backend/Execution)
- Component breakdown with file references
- API contract with JSON examples
- Operation mode internals
- Safety system implementation
- RAG document retrieval system
- Lua template engine design
- Complete data flow from input to execution
- Extension guide for adding new commands
- Performance bottlenecks and optimization

**Audience:** Developers, contributors, architects

### CONTRIBUTING.md
Developer onboarding and workflow:
- Repository structure table
- Development setup for all 3 repos (main + 2 forks)
- How to add new commands (6-step process)
- API contract and testing requirements
- Syncing integration copies from forks
- Commit message guidelines
- Pull request workflow

**Audience:** Contributors, developers extending the system

### COMPATIBILITY.md
Version management reference:
- Compatibility matrix (backend vs MAVProxy vs Mission Planner)
- Installation commands for each version
- Fork URLs and branch names
- Known breaking changes log
- Upgrade paths

**Audience:** Users managing versions, CI/CD pipelines

### INSTALL_WINDOWS.md
Windows-specific installation guide:
- Conda environment setup
- Ollama installation and model pulling
- Backend server configuration
- MAVProxy module installation
- Mission Planner integration
- Troubleshooting common Windows issues

**Audience:** Windows users setting up for first time

### README_MISSION_PLANNER.md
Mission Planner integration reference:
- Plugin architecture
- Three-mode UI explanation
- Backend URL configuration
- Ctrl+L keyboard shortcut
- Script mode MAVFTP deployment
- Build from source instructions

**Audience:** Mission Planner users

### MODEL_SELECTION.md
LLM model configuration:
- Supported models (qwen, llama families)
- Model size vs performance tradeoffs
- GPU/CPU requirements
- Configuration file editing
- Troubleshooting

**Audience:** Users optimizing performance or working with limited hardware

## Documentation Standards

All documentation follows these guidelines:

**Structure:**
- Clear hierarchical headings
- Table of contents for long documents
- Code examples with syntax highlighting
- Visual diagrams where applicable

**Style:**
- Technical but accessible language
- Step-by-step instructions for procedures
- Real-world examples
- Links to related documents

**Maintenance:**
- Updated with each feature release
- Version compatibility clearly stated
- Deprecated information marked or removed
- Links checked for validity

## External Resources

**Official ArduPilot Documentation:**
- https://ardupilot.org/copter/
- https://ardupilot.org/dev/

**MAVLink Protocol:**
- https://mavlink.io/en/

**Ollama Documentation:**
- https://ollama.ai/

**Related Projects:**
- MAVProxy: https://github.com/ArduPilot/MAVProxy
- Mission Planner: https://github.com/ArduPilot/MissionPlanner
- QGroundControl: https://github.com/mavlink/qgroundcontrol

## Contributing to Documentation

See [CONTRIBUTING.md](CONTRIBUTING.md) section on documentation for:
- Writing style guide
- Adding new documents
- Updating existing documentation
- Screenshot guidelines
- Diagram creation tools

## Documentation TODO

Planned documentation improvements:

- [ ] Linux/macOS installation guides
- [ ] QGroundControl integration guide (when available)
- [ ] API reference with all endpoints
- [ ] Command reference with parameter details
- [ ] Lua scripting guide for Script mode
- [ ] Safety configuration customization
- [ ] Multi-vehicle setup guide
- [ ] Performance tuning guide
- [ ] Troubleshooting FAQ
- [ ] Video tutorial transcripts
