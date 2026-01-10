# Decision Records (ADRs)

This document captures important architectural decisions made during the Data Canary AI project lifecycle, following the Architecture Decision Record (ADR) format.

## Table of Contents
- [ADR-001: Polars as Primary Data Frame Library](#adr-001-polars-as-primary-data-frame-library)
- [ADR-002: OpenAI API Pattern for LLM Integration](#adr-002-openai-api-pattern-for-llm-integration)
- [ADR-003: Streamlit for UI Framework](#adr-003-streamlit-for-ui-framework)

---

## ADR-001: Polars as Primary Data Frame Library

**Status:** ✅ Accepted
**Date:** 2024-12-01
**Last Updated:** 2026-01-11

### Context

The initial prototype used pandas for data processing due to:
- Team familiarity with pandas API
- Extensive ecosystem integration
- Streamlit's native pandas support

However, we encountered several limitations:
- Performance issues with files larger than 1GB
- Unpredictable memory usage patterns
- No built-in lazy/streaming evaluation
- Slow operations on large datasets

### Decision

Migrate to **Polars** as the primary data frame library for all data processing:

**Implementation Strategy:**
- Use Polars LazyFrame API for all profiling operations
- Maintain pandas compatibility layer for UI components (temporary)
- Plan full migration to Polars-native UI when Streamlit improves support
- Convert all statistical calculations to use Polars expressions

**Migration Phases:**
- ✅ MVP0: Use Polars Eager API (prototype stage - completed)
- 🔄 MVP0: Migration to LazyFrame API (in progress, critical for large file support)
- ⏳ MVP1: Full LazyFrame implementation for delta ingestion
- ⏳ MVP2: Remove pandas dependency entirely

### Consequences

**Positive:**
- ✅ 5-10x performance improvement in data processing
- ✅ Constant memory usage regardless of file size (with Lazy API)
- ✅ Built-in parallel processing capabilities
- ✅ Native support for streaming large files
- ✅ Type safety with Rust backend

**Negative:**
- ⚠️ Learning curve for team members familiar with pandas
- ⚠️ Temporary need for pandas compatibility layer
- ⚠️ Some UI operations still require careful memory management
- ⚠️ Different API patterns to learn (expressions vs. method chaining)

**Mitigations:**
- Document Polars patterns in development-guide.md
- Provide examples of common pandas → Polars conversions
- Add type hints to ease IDE autocomplete
- Use comprehensive test coverage to catch API misuse

### Related Files

- `data_canary/core/basic_profiler.py` - Main profiling logic (to be migrated)
- `data_canary/core/contract_builder.py` - Uses Polars for transformations ✅
- `data_canary/core/export.py` - Polars-native export ✅
- `docs/development-guide.md` - Polars best practices

### References

- [Polars Documentation](https://docs.pola.rs/)
- [Polars vs Pandas Performance Benchmark](https://www.pola.rs/benchmarks.html)
- [LazyFrame API Guide](https://docs.pola.rs/lazy-frame/)

---

## ADR-002: OpenAI API Pattern for LLM Integration

**Status:** ✅ Accepted
**Date:** 2025-01-09
**Last Updated:** 2026-01-11

### Context

We evaluated multiple approaches for LLM integration:

**Option A: Proprietary SDKs**
- **Gemini SDK**: Better JSON schema validation, native Python support
- **OpenAI SDK**: Standard but limited to OpenAI
- **Anthropic SDK**: Different API patterns

**Option B: OpenAI-Compatible API Pattern**
- Single client for multiple providers
- Switch via base_url parameter
- JSON schema via prompt engineering

**Requirements:**
- Flexibility to switch providers based on cost, performance, availability
- Support for local models (Llama for sensitive data)
- Minimize code changes when switching providers
- Strong validation of LLM outputs

### Decision

Use **OpenAI-Compatible API Pattern** with the following implementation:

**Core Design:**
```python
# Single client, multiple providers
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)

# Schema enforcement via system prompt
system_prompt = f"""
You are a data quality analyst. Respond in JSON matching this schema:
{schema_definition}
"""
```

**Provider Configuration:**
```bash
# Moonshot AI (current provider)
OPENAI_API_KEY="sk-..."
OPENAI_BASE_URL="https://api.moonshot.ai/v1"
OPENAI_MODEL_NAME="kimi-k2-thinking"

# OpenAI (alternative)
OPENAI_API_KEY="sk-..."
OPENAI_BASE_URL="https://api.openai.com/v1"
OPENAI_MODEL_NAME="gpt-4-turbo"

# Local Llama (sensitive data)
OPENAI_API_KEY="not-needed"
OPENAI_BASE_URL="http://localhost:11434/v1"
OPENAI_MODEL_NAME="llama2:70b"
```

### Consequences

**Positive:**
- ✅ Works with 10+ providers (Moonshot, OpenAI, Anthropic, local)
- ✅ Easy provider switching via environment variables
- ✅ Minimal code changes when switching models
- ✅ Consistent API across providers
- ✅ Cost optimization possible (choose cheapest per token)

**Negative:**
- ⚠️ Less reliable than native JSON schema validation
- ⚠️ Larger prompts (schema included in every request)
- ⚠️ Potential for schema drift (schema in prompt, not code)
- ⚠️ Different providers have different capabilities

**Mitigations:**
- Implement comprehensive Pydantic validation
- Add retry logic with exponential backoff
- Log all LLM responses for analysis
- Create provider capability matrix
- Use stronger models for critical paths

### Implementation Notes

**Schema Enforcement Strategy:**
1. Embed full JSON schema in system prompt
2. Use Pydantic for runtime validation
3. Add error recovery logic for malformed responses
4. Implement request/response logging for debugging

**Cost Tracking:**
```python
# Track token usage
llm_metrics = {
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
    "total_tokens": response.usage.total_tokens,
    "model": model_name,
    "cost": calculate_cost(response.usage, model_name)
}
```

### Related Files

- `data_canary/llm/base.py` - Generic LLM client
- `data_canary/llm/prompts.py` - Schema definitions
- `data_canary/schemas/data_models.py` - Validation schemas
- `data_canary/config.py` - Environment variable loading

### Related ADRs

- ADR-001: Polars migration (performance requirements)
- ADR-003: Streamlit UI (integration with LLM results)

### References

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Moonshot AI API](https://platform.moonshot.ai/docs/)
- [JSON Schema Specification](https://json-schema.org/)

---

## ADR-003: Streamlit for UI Framework

**Status:** ✅ Accepted (with future evaluation clause)
**Date:** 2024-10-15
**Last Updated:** 2026-01-11

### Context

We evaluated multiple UI framework options:

**Option A: Streamlit**
- Pure Python, rapid prototyping
- Built-in data exploration widgets
- Native file upload support
- No frontend build pipeline
- Limited customization

**Option B: Dash by Plotly**
- More production-ready
- Better state management
- Better for complex workflows
- Requires some JavaScript knowledge

**Option C: React/TypeScript**
- Full customization freedom
- Production-grade performance
- Steep learning curve
- Significant development overhead

**Requirements:**
- Rapid MVP0 development (3-4 week timeline)
- Interactive data exploration capabilities
- Team primarily skilled in Python
- Future migration path if UI needs grow

### Decision

Use **Streamlit** for MVP0 and MVP1 with the following constraints:

**Implementation Strategy:**
```python
# Keep UI layer thin
# Separate UI logic from business logic
def display_results(results: AnalysisResults):
    """UI layer - minimal business logic"""
    st.header("AI Governance Report")
    st.json(results.metadata_contract)

# Business logic in core modules
def analyze_data(df: pl.DataFrame) -> AnalysisResults:
    """Business logic - no UI dependencies"""
    # Profiling, LLM calls, etc.
    return results
```

**Migration Path Planning:**
- Keep Streamlit code isolated from core business logic
- Use pure functions for all data transformations
- Document UI → business logic boundaries
- Create clear API interfaces
- Budget for potential migration in MVP2

**Evaluation Criteria for MVP2:**
- User feedback on UI limitations
- Performance requirements
- Multi-tenant needs
- Customization requirements

### Consequences

**Positive:**
- ✅ Fast development (~3x faster than React for data apps)
- ✅ Built-in data exploration widgets (dataframes, charts)
- ✅ Minimal boilerplate code
- ✅ Native Python integration (no build pipeline)
- ✅ Active community and ecosystem
- ✅ Easy deployment (streamlit run app.py)

**Negative:**
- ⚠️ Limited customization options (can't create custom components easily)
- ⚠️ State management can be complex for multi-page workflows
- ⚠️ Not ideal for multi-user scenarios (shared state)
- ⚠️ Performance degrades with many widgets
- ⚠️ Less professional look than custom React app

**Mitigations:**
- Keep UI layer thin (separate business logic)
- Use session state carefully
- Limit number of widgets per page
- Use caching for expensive operations
- Plan migration path if needed later

### Current Implementation

**UI Architecture:**
```
data_canary/app.py
├── Session State Management
├── File Upload Handling
├── Tab Navigation (Raw Data, Profile, AI Governance)
└── Results Display (calls core modules)

data_canary/core/
├── All business logic
├── No Streamlit dependencies
└── Pure functions with clear inputs/outputs
```

**Key Patterns:**
- Use `@st.cache_data` for expensive operations
- Separate LLM calls into standalone functions
- Validate all inputs at function boundaries
- Use Pydantic models for type safety

### Performance Considerations

**Current:**
- Handles files up to 100MB efficiently
- Response time: < 10 seconds for typical analysis
- Memory usage scales with file size

**MVP1 Targets:**
- Files up to 1GB with streaming
- Response time: < 30 seconds
- Lazy loading for large datasets

### Limitations

**Known Issues:**
- File upload limited by Streamlit (configurable to 1GB)
- State resets on page refresh (unless explicitly saved)
- Cannot easily create complex custom visualizations
- Limited theming/branding options

**Workarounds:**
- Use Polars LazyFrame for memory efficiency
- Implement manual save/load for long sessions
- Export results to file for persistence
- Use custom components library for advanced widgets (future)

### Related Files

- `data_canary/app.py` - Streamlit UI entry point
- `data_canary/core/*.py` - Business logic (UI agnostic)
- `data_canary/schemas/*.py` - Data models (shared)
- `docs/development-guide.md` - UI development patterns

### Related ADRs

- ADR-001: Polars migration (data processing performance)
- ADR-002: LLM API pattern (generating UI content)

### Evaluation Timeline

**MVP0-MVP1:** Use Streamlit, focus on core features
**End of MVP1:** Collect user feedback on UI limitations
**MVP2 Planning:** Decide whether to stick with Streamlit or migrate

### References

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit GitHub](https://github.com/streamlit/streamlit)
- [Streamlit Components](https://docs.streamlit.io/streamlit-community-cloud)
- [Dash by Plotly](https://dash.plotly.com/) (alternative)

---

## Future Decisions (Template)

### ADR-004: [Title]

**Status:** ⏳ Pending / 🔄 In Progress / ✅ Accepted / ❌ Rejected
**Date:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD

### Context

[Describe the problem, requirements, and constraints that led to this decision]

### Decision

[Describe what was decided and how it will be implemented]

### Consequences

**Positive:**
- ✅ Benefit 1
- ✅ Benefit 2

**Negative:**
- ⚠️ Trade-off 1
- ⚠️ Trade-off 2

**Mitigations:**
- Mitigation for trade-off 1
- Mitigation for trade-off 2

### Related Files

- File path 1
- File path 2

### Related ADRs

- ADR-XXX: Related decision

### References

- [Link to specification or documentation]

---

*This document is updated as new architectural decisions are made.*
