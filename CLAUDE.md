# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data Canary AI is an AI-powered tool designed for data engineers to bridge the gap between raw data discovery and production-ready ingestion. It automates table design, naming convention enforcement, and data quality monitoring using an "AI-First" approach.

**Core Problems Solved:**
- Manual Discovery: Engineers waste time running df.describe() and manually mapping CSV headers to database types
- Silent Data Drift: Ingestion pipelines fail or store low-quality data due to undetected schema changes or statistical shifts
- Inconsistent Naming: Lack of enforcement leads to "data swamps" with messy, unstandardized column names

## Repository Structure

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

docs/
├── project-spec.md           # Full requirements and workflow definition
├── architecture.md           # System design, patterns, and technical decisions
├── decision-records.md       # Architectural decision records (ADRs)
├── development-guide.md      # Development workflows, troubleshooting, contributing
├── agent-usage-guide.md      # Agent selection and tool usage logic
├── project-status.md         # Current phase, blockers, next steps
└── changelog.md              # Version history and release notes
```

## Architecture Overview

### Module Structure
```
data_canary/
├── app.py                    # Streamlit UI entry point
├── config.py                 # Environment configuration (OPENAI_API_KEY, OPENAI_BASE_URL, etc.)
├── core/
│   └── basic_profiler.py     # Polars-based data profiling (Eager API currently, Lazy API target for MVP0)
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
   - `run_structured_llm_check()` in `llm/base.py` provides generic OpenAI-compatible API integration
   - System message includes both persona and JSON schema enforcement
   - User prompts contain task instructions + data
   - All LLM outputs validated against Pydantic schemas from `schemas/data_models.py`

2. **Multi-Stage Data Analysis**
   - **Stage 1**: `run_basic_checks()` performs Polars analysis (nulls, duplicates, statistics)
   - **Stage 2**: `run_llm_naming_check()` reviews column names for conventions
   - **Stage 3**: `run_llm_type_check()` suggests logical types and storage optimizations

3. **Configuration Management**
   - API keys and model settings read from environment variables
   - Model configurable via `OPENAI_MODEL_NAME` (defaults to "kimi-k2-thinking")
   - Base URL configurable via `OPENAI_BASE_URL` for OpenAI-compatible providers
   - Use `.env` file or shell exports for local development

### Data Flow

1. User uploads CSV/Parquet → `app.py:load_data()`
2. Polars profiling → `core/basic_profiler.py:run_basic_checks()`
3. LLM naming review → `llm/naming_checking.py:run_llm_naming_check()`
4. LLM type optimization → `llm/type_checking.py:run_llm_type_check()`
5. Results displayed in Streamlit UI tabs (Data Sample, Profile, AI Governance Report)

### Critical Dependencies

- **Polars**: Core data processing - use for all statistical calculations (Eager API in prototype, Lazy API target for MVP0)
- **OpenAI API**: LLM integration (OpenAI-compatible) - ensure `OPENAI_API_KEY` is set
- **Pydantic v2**: Response validation - models must inherit from `BaseModel`
- **Streamlit**: Web UI - tabs for data view, profile, and AI reports

## Environment Variables

```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_MODEL_NAME="kimi-k2-thinking"  # Optional, defaults to kimi-k2-thinking
export OPENAI_BASE_URL="https://api.moonshot.ai/v1"  # Optional, for OpenAI-compatible providers
```

## Development Principles

- **Lazy First (MVP0):** All data profiling must use Polars Lazy API to handle large-scale data efficiently
- **Trust but Verify:** The AI suggests; the user decides. Always provide an "Override" path
- **Traceability:** Never lose mapping back to original source column names

## Testing Approach

Currently minimal test coverage. When adding tests:
- Test Polars profiler with sample DataFrames
- Mock API calls for LLM modules
- Verify Pydantic model validation

## Current Status: Basic Prototype

The current implementation is a basic prototype that provides:
- File ingestion (CSV/Parquet) with Polars Eager API
- Basic Polars profiling with statistical analysis
- LLM-powered naming convention review
- LLM-powered type optimization suggestions
- Streamlit UI for viewing reports

**NOT YET IMPLEMENTED** (needed for MVP0 completion):
- Human-in-the-loop approval workflow (override capability)
- Parquet output generation
- `metadata.json` contract creation with Identity/Physical Schema/Statistical Profile structure
- Column role detection (PK, Metric, Event Marker, Category)
- Source → Target name mapping for traceability
- Polars Lazy API migration (for large file handling)

For detailed metrics, see: [docs/project-status.md](./docs/project-status.md)

## Product Roadmap: MVP0 → Production

### MVP0: Single Source Initialization (Target)
Focus: From raw CSV/Parquet to approved data with metadata contract

**Current State:** Basic prototype with profiling and AI suggestions
**Required for MVP0:**
- [ ] Human-in-the-loop override workflow
- [ ] Parquet output generation
- [ ] metadata.json contract creation with three-part structure:
  - Identity: Table name, version, source paths, last updated
  - Physical Schema: source_name, target_name, data_type, is_nullable
  - Statistical Profile: null_count_pct, cardinality, quantiles, min/max/mean
- [ ] Column role detection in prompts
- [ ] Source → Target name mapping preservation
- [ ] Migrate from Polars Eager API to Lazy API for memory efficiency

### MVP1: Monitoring & Delta Ingestion
Focus: Guardrails for recurring data with automatic mode detection

MVP1 includes BOTH initialization (MVP0) and delta ingestion functionality. The system automatically detects which mode to use based on whether metadata exists.

**Initialization Mode** (NO metadata.json):
- [ ] Batch/delta file processing
- [ ] Human-in-the-loop override workflow
- [ ] Parquet output generation
- [ ] metadata.json contract creation
- [ ] Column role detection
- [ ] Source → Target name mapping

**Delta Ingestion Mode** (metadata.json EXISTS):
- [ ] Automated audit against metadata baseline
- [ ] Drift detection (schema, type, null/value drift)
- [ ] Health Report generation with warnings/errors
- [ ] User approval workflow for changes
- [ ] Conditional append with version control

### MVP2: Governance & Modernization
Focus: Scaling standards across organization

- [ ] Semantic renaming suggestions
- [ ] Pattern learning from metadata directory
- [ ] Centralized governance features

## Documentation
- [Project Spec](docs/project-spec.md) - Full requirements and workflow definition
- [Architecture](docs/architecture.md) - System design, patterns, and technical decisions
- [Decision Records](docs/decision-records.md) - Architectural decisions (ADRs)
- [Development Guide](docs/development-guide.md) - Workflows, troubleshooting, contributing guidelines
- [Agent Usage Guide](docs/agent-usage-guide.md) - Agent selection and tool usage logic
- [Project Status](docs/project-status.md) - Current phase, blockers, next steps
- [Changelog](docs/changelog.md) - Version history and release notes

**Important:** See `docs/development-guide.md` for detailed development workflows, Git practices, security policies, and troubleshooting.

## References
- [Polars Documentation](https://docs.pola.rs/)
- [Pydantic v2 Docs](https://docs.pydantic.dev/2.0/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [OpenAI API Docs](https://platform.openai.com/docs/)
