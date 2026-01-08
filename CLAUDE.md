# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data Canary is an AI-powered data quality and profiling tool that:
- Performs high-performance data analysis using Polars
- Uses LLM to review naming conventions and suggest schema optimizations
- Provides structured Pydantic-validated reports
- Offers a Streamlit web interface for interactive analysis

## Development Commands

### Installation
```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .[dev]
```

### Running the Application
```bash
# Launch Streamlit UI
streamlit run data_canary/app.py
```

### Development Tools
```bash
# Format code
uv run ruff format .

# Lint code (currently disabled in CI)
uv run ruff check .

# Security scan (currently disabled in CI)
uv run bandit -r data_canary

# Run tests
uv run pytest
```

## Architecture Overview

### Module Structure
```
data_canary/
├── app.py                    # Streamlit UI entry point
├── config.py                 # Environment configuration (OPENAI_API_KEY, OPENAI_BASE_URL, etc.)
├── core/
│   └── basic_profiler.py     # Polars-based data profiling
├── llm/
│   ├── base.py               # Generic OpenAI API wrapper with Pydantic validation
│   ├── prompts.py            # LLM persona and instruction templates
│   ├── naming_checking.py    # Column naming convention analysis
│   └── type_checking.py      # Schema optimization recommendations
└── schemas/
    └── data_models.py        # Pydantic models for structured LLM outputs
```

### Key Design Patterns

1. **LLM-Powered Analysis Pipeline**
   - `run_structured_llm_check()` in `llm/base.py` provides generic API integration
   - Prompts are constructed with persona + specific instructions from `llm/prompts.py`
   - All LLM outputs are validated against Pydantic schemas in `schemas/data_models.py`
   - Structured JSON output ensures reliable downstream processing

2. **Multi-Stage Data Analysis**
   - **Stage 1**: `run_basic_checks()` performs fast Polars analysis (nulls, duplicates, statistics)
   - **Stage 2**: `run_llm_naming_check()` reviews column names for conventions
   - **Stage 3**: `run_llm_type_check()` suggests logical types and storage optimizations

3. **Configuration Management**
   - API keys and model settings read from environment variables
   - Model configurable via `OPENAI_MODEL_NAME` (defaults to "kimi-k2-thinking")
   - Use `.env` file or shell exports for local development

### Data Flow

1. User uploads CSV/Parquet → `app.py:load_data()`
2. Polars profiling → `core/basic_profiler.py:run_basic_checks()`
3. LLM naming review → `llm/naming_checking.py:run_llm_naming_check()`
4. LLM type optimization → `llm/type_checking.py:run_llm_type_check()`
5. Results displayed in Streamlit UI tabs

### Critical Dependencies

- **Polars**: Core data processing - use for all statistical calculations
- **OpenAI API**: LLM integration (OpenAI-compatible, e.g., Moonshot AI) - ensure `OPENAI_API_KEY` is set
- **Pydantic v2**: Response validation - models must inherit from `BaseModel`
- **Streamlit**: Web UI - tabs for data view, profile, and AI reports

## Environment Variables

```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_MODEL_NAME="kimi-k2-thinking"  # Optional, defaults to kimi-k2-thinking
export OPENAI_BASE_URL="https://api.moonshot.ai/v1"  # For OpenAI-compatible providers like Moonshot AI
```

## Testing Approach

Currently minimal test coverage. When adding tests:
- Test Polars profiler with sample DataFrames
- Mock API calls for LLM modules
- Verify Pydantic model validation

## CI/CD

GitHub Actions workflow runs on:
- Push to `main` or `feat/**` branches
- Pull requests to `main`

Current checks: Python 3.11, dependency installation, basic import verification
Linting and security scans are commented out (future work)
