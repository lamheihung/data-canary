# Changelog

All notable changes to the Data Canary AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - TBD

### Changed
- **Polars API**: Migration from Eager API to Lazy API (planned for MVP1)

### Planned
- Delta ingestion mode with automatic drift detection
- Health Report generation with warnings/errors
- Batch processing for multiple/daily files
- Version control for metadata contracts

## [0.0.4] - 2026-01-11

### Added
- **MVP0 Features Implemented: Human-in-the-Loop UI with LLM Integration**
  - ⚠️ **Note:** MVP0 not yet complete - Polars Lazy API migration remains as critical blocker
  - **Streamlit 4-Tab Interface**:
    - Tab 1: Raw Data Sample (first 5 rows)
    - Tab 2: Basic Profile & Issues (statistics, quality issues)
    - Tab 3: AI Governance Report (naming + type suggestions)
    - Tab 4: Review & Approve (human-in-the-loop)
  - **Full LLM Integration**:
    - Moonshot AI (Kim-2-thinking) for type optimization
    - Column naming convention analysis
    - Retry logic with exponential backoff (3 attempts)
    - Mock fallback for development (no API key needed)
  - **Approval Workflow**:
    - Editable column names with AI suggestions as defaults
    - Editable data types with intelligent dropdowns
    - Override tracking (User > AI > Original precedence)
    - Parquet generation on approval
    - Metadata contract JSON generation on approval
    - Success screen with file locations
  - **Professional Reliability**:
    - Comprehensive error handling
    - Graceful degradation to mock mode
    - LLM usage and cost tracking (minimal implementation)

### Changed
- **Documentation Standards**
  - All 59 functions/classes now use Google-style docstrings
  - Updated Args, Returns, Raises sections
  - Consistent formatting across codebase
- **Removed Premature Optimization**
  - Removed LLMUsage tracking class (unused in workflow)
  - Simpler codebase, less maintenance overhead
- **Comment Policy**
  - Removed unnecessary section headers and comments
  - Code is now self-documenting with better naming
  - Only kept comments that explain "why" not "what"

### Fixed
- **Test Suite**: Additional tests bringing total to 59 (100% passing)
  - Integration tests for complete workflow
  - Edge case handling in contract validation
  - Export module path handling

### Deprecated
- **LLM Usage Tracking**: Removed from MVP0 (premature optimization)
  - Can be reintroduced in MVP1 if needed
  - Currently provides no value but adds complexity

## [0.0.3] - 2026-01-11

### Added
- **MVP0 Phase 2: Contract Builder & Export Module**
  - `data_canary/core/contract_builder.py`: Schema transformation and contract creation
    - `build_physical_schema()`: Build schema with AI suggestions and user override support
    - `apply_schema_transform()`: Apply schema changes to Polars DataFrames
    - `create_metadata_contract()`: Assemble complete metadata contracts
    - `validate_contract()`: Comprehensive contract validation
  - `data_canary/core/export.py`: Output generation
    - `generate_parquet()`: Convert DataFrames to Parquet format
    - `save_metadata_contract()`: Serialize contracts to JSON
    - `generate_outputs()`: Generate both files in single operation
  - **Comprehensive test coverage**: 44 tests (24 + 20)
    - `tests/test_contract_builder.py`: Full workflow testing
    - `tests/test_export.py`: Output generation testing
  - **Override precedence logic**: User > AI > Original
  - **Column order preservation**: Via column_index field
  - **Column role support**: For vendor-provided metadata (PK, Metric, etc.)

### Fixed
- **Phase 2 Bug Fix**: Removed ~130 lines of duplicate code in contract_builder.py
  - Fixed undefined `dtype_str` variable
  - Removed duplicate `apply_schema_transform()` function
  - Applied ruff formatting
  - All CI checks now passing

### Documentation
- **New Development Guide**: `docs/development-guide.md`
  - Pre-commit checklist with step-by-step verification
  - Git workflow with branch lifecycle
  - Code quality standards and Python guidelines
  - Common issues and solutions
  - Agent selection logic
- **New Agent Usage Guide**: `docs/agent-usage-guide.md`
  - When to use direct tools vs specialized agents
  - Project-specific agent recommendations by phase
  - Decision framework and agent categories
- **New Project Status**: `docs/project-status.md`
  - Current phase and implementation status
  - Critical blockers and technical debt
  - Next steps and priority order
  - Git history summary and quick commands

### Changed
- **Total Test Coverage**: 64 tests (20 + 44), 100% passing
- **Module Line Count**: data_canary/core/contract_builder.py reduced from 532 to 402 lines
- **CI Pipeline**: All 4 checks consistently passing (Lint, Security, Type Check, Build)

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
