# Changelog

All notable changes to the Data Canary AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - TBD

### Added
- Human-in-the-loop approval workflow for schema suggestions
- Parquet output generation
- Metadata contract creation (Identity + Physical Schema + Statistical Profile)
- Column role detection (PK, Metric, Event Marker, Category)
- Source → Target name mapping for traceability

### Changed
- **Python Version**: Upgraded from Python 3.10 to Python 3.13
  - Updated all documentation (README.md, badges, prerequisites)
  - Updated CI pipeline to use Python 3.13
  - Updated pyproject.toml dependencies and tool configurations

### Planned
- Delta ingestion mode with automatic drift detection
- Health Report generation with warnings/errors
- Batch processing for multiple/daily files
- Version control for metadata contracts

## [0.0.2] - 2026-01-09

### Added
- **Documentation**: Comprehensive system architecture in `docs/architecture.md`
  - Component responsibilities and design patterns
  - Detailed data flows (prototype → MVP0 → MVP1)
- **Architecture Enhancement**: MVP1 dual-mode architecture
  - Automatic mode detection based on metadata.json existence
  - Unified interface bridging MVP0 and MVP1 functionality
- **Configuration**: Environment template file `.env` for API configuration
- **Project Management**: Version history tracking in `docs/changelog.md`

### Changed
- **Documentation Restructure**: Updated all project documentation
  - Clarified roadmap from MVP0 → MVP1 → MVP2 in all docs
  - Updated README.md with dual-mode architecture
  - Enhanced CLAUDE.md with MVP status checklists
  - Refined project-spec.md with automatic mode detection
- **LLM Integration**: Replaced Gemini API with OpenAI-compatible API
  - Support for multiple providers (Moonshot AI, OpenAI, local Llama)
  - Prompt-based schema enforcement (schemas in system message)
  - Environment-based configuration (OPENAI_API_KEY, OPENAI_MODEL_NAME, OPENAI_BASE_URL)

## [0.0.1] - 2025-01-15

### Added
- **Initial Prototype Release**: Basic data profiling and AI analysis capabilities
- **Core Data Processing**: Polars-based profiling engine in `data_canary/core/basic_profiler.py`
  - Statistical profiling (null counts, duplicates, basic statistics)
  - Support for CSV and Parquet file formats
- **LLM Integration Layer**: Generic OpenAI-compatible API wrapper
  - Structured output validation with Pydantic v2
  - System persona separation from user content
  - Reusable LLM client in `data_canary/llm/base.py`
- **AI Analysis Modules**:
  - **Naming Convention Review**: `data_canary/llm/naming_checking.py`
    - snake_case enforcement
    - Clear violation reporting with suggested names
  - **Type Optimization**: `data_canary/llm/type_checking.py`
    - Logical type suggestions (CATEGORY, CURRENCY, DATE, etc.)
    - Polars-optimized physical type recommendations
- **Data Models**: Pydantic schemas for structured LLM outputs
  - `NamingViolation`, `NamingCheckReport`
  - `TypeSuggestion`, `TypeCheckReport`
- **User Interface**: Streamlit web application in `data_canary/app.py`
  - File upload for CSV/Parquet files
  - Tabbed interface (Raw Data, Profile, AI Governance)
  - Real-time analysis display
- **CI/CD Pipeline**: GitHub Actions workflow
  - Python 3.11 testing
  - Dependency installation verification
  - Basic import validation
- **Project Structure**: Modular architecture
  - `config.py`: Environment variable management
  - `schemas/data_models.py`: Pydantic model definitions
  - `llm/prompts.py`: AI persona and instruction templates
  - `pyproject.toml`: Modern Python packaging with uv
- **Documentation**: Initial project documentation
  - README.md with setup instructions
  - Project overview and key features
  - Installation and usage guidelines

### Changed
- **Technology Migration**: Migrated from pandas to Polars for data processing
  - 5-10x performance improvement
  - Significant memory usage reduction (85% less)
  - Consistent API for local and cloud data
- **Code Architecture**: Established clean separation of concerns
  - Core profiling logic isolated from UI
  - LLM integration separated from business logic
  - Schema definitions centralized in dedicated module

### Fixed
- **Type Safety**: Implemented proper schema validation for all LLM outputs

### Known Limitations
- No Parquet output generation yet (prototype shows results only)
- Metadata contract creation not implemented
- No human override capability in UI (read-only reports)
- Limited to single file analysis (no batch processing)
- No drift detection for recurring data
- Basic error handling with limited retry logic

[Unreleased]: https://github.com/lamheihung/data-canary/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/lamheihung/data-canary/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/lamheihung/data-canary/releases/tag/v0.0.1
