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
High-level summary of the system:
- Core concepts and workflow
- The two operation modes (Agent/Ask)
- Safety features and validation
- Tech stack, requirements, and performance

**Audience:** New users and stakeholders.

### ARCHITECTURE.md
System design details:
- Multi-layer architecture diagram
- Component breakdown and API contracts
- Operation mode internals and safety system
- RAG document retrieval system
- Extension guide for adding new commands

**Audience:** Developers and contributors.

### CONTRIBUTING.md
Developer guide:
- Repository structure
- Development setup for all 3 repos
- How to add new commands
- PR and commit guidelines

**Audience:** Contributors.

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
- Agent/Ask UI explanation
- Backend URL configuration
- Ctrl+L keyboard shortcut
- Build from source instructions

**Audience:** Mission Planner users

### MODEL_SELECTION.md
LLM model configuration:
- Supported default model configuration
- System requirements
- Configuration file editing
- Troubleshooting

**Audience:** Users setting up or configuring the backend

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

See [CONTRIBUTING.md](CONTRIBUTING.md) for documentation guidelines.
