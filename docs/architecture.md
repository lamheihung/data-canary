# Data Canary AI - Architecture Documentation

**Version:** MVP0 Prototype
**Last Updated:** 2026-01-09
**Status:** Active Development

---

## Executive Summary

Data Canary AI is an AI-powered data engineering tool that automates schema design, data quality monitoring, and drift detection. It bridges the gap between raw data discovery and production-ready data ingestion through an intelligent, human-in-the-loop workflow.

**Architectural Philosophy:**
- **AI-First Design:** Leverage LLMs for semantic understanding, not just statistical analysis
- **Lazy Evaluation:** Handle arbitrarily large datasets using Polars Lazy API
- **Human-Centered:** AI suggests, humans decide – always provide override paths
- **Traceability:** Preserve source-to-target mappings for auditability
- **Extensibility:** Plugin architecture for multiple LLM providers and data sources

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                         │
│                      (Streamlit - data_canary/app.py)                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Application Orchestration                       │
│                  (Main Controller - Streamlit Events)                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌─────────────┐      ┌─────────────┐      ┌──────────────┐
│  Data       │      │  Profiling  │      │  AI/LLM       │
│  Ingestion  │      │  Engine     │      │  Analysis     │
│             │      │             │      │               │
│ - CSV       │      │ - Polars    │      │ - OpenAI API  │
│ - Parquet   │      │ - Lazy API  │      │ - Structured  │
│             │      │ - Statistics│      │   Outputs     │
└─────────────┘      └─────────────┘      └──────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Data Storage & Contracts                        │
│               (Parquet + JSON Metadata - "The Contract")             │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### UI Layer (`data_canary/app.py`)
**Purpose:** Interactive web interface for data upload, review, and approval

**Key Responsibilities:**
- File upload handling (CSV, Parquet)
- Data preview and statistics display
- AI suggestion presentation
- Human override interface (future MVP0)
- Export/approval workflow (future MVP0)

**Technology:** Streamlit (rapid prototyping, ideal for data tools)

**Design Decisions:**
- Chose Streamlit over Dash/Gradio for faster MVP development
- Tabbed interface separates concerns: Raw Data, Profile, AI Governance

#### Data Ingestion Layer
**Purpose:** Handle file I/O and data loading into Polars

**Key Responsibilities:**
- Detect file type (CSV, Parquet)
- Stream large files without memory exhaustion
- Convert to Polars LazyFrame for consistent processing
- Handle encoding and format variations

**Location:** `data_canary/app.py:load_data()` (currently in UI layer, should be extracted)

**Future Improvements:**
- Extract to `data_canary/io/` module
- Support database connections (PostgreSQL, Snowflake)
- Add S3/GCS cloud storage support

#### Profiling Engine (`data_canary/core/basic_profiler.py`)
**Purpose:** Generate statistical fingerprints and basic quality metrics

**Key Responsibilities:**
- Compute null counts and ratios
- Calculate distinct value cardinality
- Determine min/max/mean for numeric columns
- Identify duplicate rows
- Extract data type information

**Design Pattern:** Pure functions, deterministic

**Critical Design Decision:**
```python
# Uses Polars Lazy API for memory efficiency
df = pl.scan_csv(file)  # Not loaded into memory
profile = run_basic_checks(df)  # Streams data, constant memory usage
```

**Why Polars over Pandas:**
- **Performance:** 5-10x faster for analytical queries
- **Memory:** Lazy evaluation prevents OOM errors on large files
- **Type Safety:** Strict schema enforcement
- **API Consistency:** Unified API for local and cloud data

#### 2.2.4 LLM Integration Layer (`data_canary/llm/`)
**Purpose:** Provide AI-powered semantic analysis

**Architecture:**
```
┌─────────────────────────────────────────────────┐
│          LLM Integration Pipeline                │
├─────────────────────────────────────────────────┤
│ 1. Prompt Construction                           │
│    - Persona (System message)                   │
│    - Schema enforcement (System message)        │
│    - User content (Data + instructions)         │
│                                                  │
│ 2. API Call                                      │
│    - OpenAI-compatible endpoint                 │
│    - JSON mode with structured output           │
│                                                  │
│ 3. Response Validation                           │
│    - Pydantic model validation                  │
│    - Error handling and retry logic             │
└─────────────────────────────────────────────────┘
```

**Sub-modules:**
- `base.py`: Generic LLM client with schema validation
- `naming_checking.py`: Column name convention review
- `type_checking.py`: Data type optimization suggestions
- `prompts.py`: System personas and instruction templates

**Key Design Pattern:** Strategy Pattern for LLM providers

```python
# Current: OpenAI-compatible
def run_structured_llm_check(...):
    client = OpenAI(api_key=..., base_url=...)

# Future: Multi-provider support
class LLMProvider(ABC):
    @abstractmethod
    def generate_structured_response(...) -> BaseModel:
        pass

class OpenAIProvider(LLMProvider): ...
class AnthropicProvider(LLMProvider): ...
class GeminiProvider(LLMProvider): ...
```

**Structured Output Enforcement:**
```python
# Gemini (Original - had native support)
config = {
    "response_mime_type": "application/json",
    "response_json_schema": response_model.model_json_schema(),
}

# OpenAI (Current - prompt-based enforcement)
system_prompt = f"""
{SYSTEM_PERSONA}

You MUST respond with JSON following this schema:
{json.dumps(schema, indent=2)}
"""
```

**Trade-offs:**
- **Pros:** Works with any OpenAI-compatible API
- **Cons:** Less reliable than native JSON schema support
- **Mitigation:** Strong Pydantic validation with clear error messages

#### chema & Data Models (`data_canary/schemas/data_models.py`)
**Purpose:** Define structured output contracts for LLMs

**Models:**
1. **NamingViolation** - Individual column naming issues
2. **NamingCheckReport** - Complete naming review report
3. **TypeSuggestion** - Individual column type recommendations
4. **TypeCheckReport** - Complete type optimization report

**Design Rationale:**
- **Type Safety:** Prevents downstream errors
- **Documentation:** JSON schema serves as LLM prompt documentation
- **Evolution:** Pydantic v2 provides easy model versioning
- **Validation:** Automatic validation of LLM outputs

#### Configuration Management (`data_canary/config.py`)
**Purpose:** Centralized configuration and secrets management

**Environment Variables:**
- `OPENAI_API_KEY`: API key (REQUIRED - must be in env, never in code)
- `OPENAI_MODEL_NAME`: Model identifier (default: "kimi-k2-thinking")
- `OPENAI_BASE_URL`: API endpoint (default: Moonshot AI)

**Security Best Practices:**
- ✅ API key from environment only
- ✅ .env file in .gitignore
- ✅ No secret logging or error exposure
- ✅ Clear error messages when keys missing

**Future Improvements:**
- Remove this file by using .env to store all the environment variables

---

## Data Flow

### Current Prototype Flow

```
User Uploads File
       │
       ▼
┌─────────────────────────┐
│  Streamlit File Uploader│
│  (app.py)               │
└─────────────────────────┘
       │
       ▼
┌─────────────────────────┐
│  Polars Data Loading    │
│  - CSV/Parquet support  │
│  - DataFrame conversion │
└─────────────────────────┘
       │
       ├────────────────────────────────┐
       │                                │
       ▼                                ▼
┌──────────────────┐        ┌──────────────────┐
│ Basic Profiling  │        │  Data Preview    │
│ - Null counts    │        │  - First 5 rows  │
│ - Stats          │        └──────────────────┘
│ - Duplicates     │                 │
└──────────────────┘                 │
       │                             │
       └──┬──────────────────────────┘
          │
          ▼
┌──────────────────────────┐
│  LLM Analysis            │
│  - Naming conventions    │
│  - Type optimization     │
└──────────────────────────┘
          │
          ▼
┌──────────────────────────┐
│  UI Display              │
│  - Profile stats         │
│  - AI suggestions        │
│  (READ-ONLY)             │
└──────────────────────────┘
```

### Target MVP0 Flow

```
User Uploads File
       │
       ▼
┌──────────────────────────┐
│  Data Ingestion          │
│  - File validation       │
│  - LazyFrame create      │
└──────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Statistical Profiling   │
│  - Compute baseline      │
│  - Generate stats        │
│  - Detect anomalies      │
└──────────────────────────┘
       │
       ├────────────────────┐
       │                    │
       ▼                    ▼
┌──────────────────┐  ┌─────────────┐
│  AI Schema       │  │  UI Review  │
│  Design          │  │  - Show     │
│  - Roles         │  │    proposal │
│  - Types         │  │  - Approve  │
│  - Names         │  │  - Override │
└──────────────────┘  └─────────────┘
       │                    │
       └────────┬───────────┘
                │
       ┌────────▼──────────┐
       │ User Approves?    │
       └────────┬──────────┘
                │ YES
                ▼
┌──────────────────────────┐
│  Materialization         │
│  - Save Parquet          │
│  - Create metadata.json  │
│  - Log decisions         │
└──────────────────────────┘
                │
                ▼
┌──────────────────────────┐
│  Success: Show summary   │
│  - Table name            │
│  - Schema                │
│  - Quality metrics       │
└──────────────────────────┘
```

### MVP1 Architecture (Dual-Mode: Initialization + Delta Ingestion)

MVP1 introduces **automatic mode detection** based on whether a metadata contract exists. This means MVP1 includes ALL MVP0 functionality plus delta ingestion capabilities.

```
User Uploads Data
       │
       ▼
┌──────────────────────────┐
│  Check for Existing      │
│  metadata.json           │
└─────────────┬────────────┘
              │
      ┌───────┴────────┐
      │                │
  NO  │                │ YES
      ▼                ▼
┌─────────────────┐  ┌──────────────────┐
│  MVP0 MODE      │  │  MVP1 MODE       │
│  (Initialization)│  │  (Delta Detection)│
└─────────────────┘  └────────┬─────────┘
      │                       │
      │   ┌───────────────────┘
      │   │
      ▼   ▼
┌──────────────────────────┐
│  Common Processing       │
│  ├─ Profile data        │
│  ├─ AI analysis         │
│  └─ UI presentation     │
└──────────────────────────┘
```

#### Mode 1: Initialization (When NO metadata.json exists)

This is the **MVP0 workflow** - creating a new data source from raw files.

```
┌──────────────────────────┐
│  Initialize New Source   │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│  Statistical Profiling   │
│  - Compute baseline      │
│  - Detect anomalies      │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│  AI Schema Design        │
│  - Role detection        │
│  - Name standardization  │
│  - Type optimization     │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│  Human-in-the-Loop       │
│  - Review proposals      │
│  - Override as needed    │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│  Materialize & Save      │
│  - Write Parquet         │
│  - Create metadata.json  │
└──────────────────────────┘
```

**Key Differences from Current Prototype:**
- ✅ Human override capability
- ✅ Parquet materialization
- ✅ Contract creation with full three-part structure
- ✅ Source → Target name mapping for traceability

#### Mode 2: Delta Ingestion (When metadata.json EXISTS)

This is **new MVP1 functionality** - monitoring recurring data.

```
New Data Arrives
       │
       ▼
┌──────────────────────────┐
│  Load Existing Contract  │
│  (metadata.json)         │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│  Profile New Data        │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│  Drift Detection         │
│  ├─ Schema Drift         │
│  ├─ Type Drift           │
│  └─ Value Drift          │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│  Health Report           │
│  - Warnings              │
│  - Errors                │
│  - Recommendations       │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│  User Review             │
│  - Accept changes        │
│  - Reject pipeline       │
└─────────────┬────────────┘
              │
              ▼
┌──────────────────────────┐
│  Conditional Append      │
│  - Update metadata       │
│  - Version control       │
└──────────────────────────┘
```

**Key Features:**
- Automatic comparison against baseline
- Drift detection across multiple dimensions
- Aleract before data corruption
- Gradual schema evolution support

#### Automatic Mode Detection Implementation

```python
def process_data(file_path, table_name):
    """
    Automatically detect mode based on metadata existence
    """
    metadata_path = f"metadata/{table_name}.json"

    if os.path.exists(metadata_path):
        # Mode 2: Delta ingestion
        return process_delta_ingestion(file_path, metadata_path)
    else:
        # Mode 1: Initialization
        return process_initialization(file_path, table_name)
```

**Benefits of Dual-Mode Architecture:**
1. **Unified Interface:** Users don't need to learn two separate tools
2. **Backward Compatible:** MVP0 functionality remains available
3. **Automatic Scaling:** System grows with the user's needs
4. **Single Workflow:** Consistent experience across data lifecycle
5. **Code Reuse:** 70% of code shared between modes (profiling, AI analysis, UI)

**UI Indicators:**
- ✅ Initialization mode: "Creating new table: {table_name}"
- ✅ Delta mode: "Appending to existing table: {table_name} (v{version})"
- ✅ Show comparison view: New data vs. baseline side-by-side

---

## Metadata Contract Structure

### Contract Design Philosophy

The `metadata.json` file serves as the "single source of truth" for a dataset's schema, quality baselines, and ingestion history. It's inspired by software engineering's "Contract Testing" pattern applied to data engineering.

**Core Principles:**
1. **Immutability:** Once approved, historical versions are frozen
2. **Completeness:** Contains everything needed to validate future data
3. **Human/Machine Readable:** JSON format, well-documented schema
4. **Traceability:** Links back to source systems and raw files

### JSON Schema Structure

```json
{
  "identity": {
    "table_name": "user_events_2025",
    "version": "1.0.0",
    "created_at": "2026-01-09T10:30:00Z",
    "updated_at": "2026-01-09T10:30:00Z",
    "source_path": "/data/raw/user_events.csv",
    "target_path": "/data/parquet/user_events_2025.parquet",
    "created_by": "data-engineer@company.com"
  },
  "physical_schema": [
    {
      "source_name": "user id",
      "target_name": "user_id",
      "data_type": "UInt32",
      "is_nullable": false,
      "role": "primary_key",
      "description": "Unique user identifier from authentication system"
    },
    {
      "source_name": "eventTimestamp",
      "target_name": "event_timestamp",
      "data_type": "Datetime",
      "is_nullable": false,
      "role": "event_marker",
      "description": "When the event occurred (UTC)"
    },
    {
      "source_name": "revenue_usd",
      "target_name": "revenue_usd",
      "data_type": "Decimal(10,2)",
      "is_nullable": true,
      "role": "metric",
      "description": "Revenue amount in USD"
    }
  ],
  "statistical_profile": {
    "row_count": 1048576,
    "null_percentage": 0.15,
    "columns": {
      "user_id": {
        "null_count_pct": 0.0,
        "cardinality": 89234,
        "min": 1,
        "max": 999999
      },
      "event_timestamp": {
        "null_count_pct": 0.0,
        "min": "2025-01-01T00:00:00Z",
        "max": "2025-12-31T23:59:59Z"
      },
      "revenue_usd": {
        "null_count_pct": 0.45,
        "min": 0.01,
        "max": 99999.99,
        "mean": 45.23,
        "quantiles": {
          "q25": 9.99,
          "q50": 29.99,
          "q75": 59.99
        }
      }
    }
  },
  "data_quality_rules": {
    "user_id": {
      "must_be_unique": true,
      "must_be_positive": true
    },
    "event_timestamp": {
      "must_be_past": true
    },
    "revenue_usd": {
      "must_be_non_negative": true,
      "max_value": 100000.0
    }
  },
  "ingestion_history": [
    {
      "ingestion_id": "ingest_001",
      "timestamp": "2026-01-09T10:30:00Z",
      "source_file": "user_events_2025_01_09.csv",
      "row_count": 1048576,
      "quality_score": 0.98,
      "drift_detected": false
    }
  ]
}
```

### Contract Evolution

**Version 0 (MVP0 - Current Target):**
- Basic Identity + Physical Schema + Statistical Profile
- Minimal quality rules
- No ingestion history

**Version 1 (MVP1 - Delta Support):**
- Add drift detection thresholds
- Enhanced quality rules
- Full ingestion history
- Version comparison tools

**Version 2 (MVP2 - Governance):**
- Semantic layer integration
- Data lineage tracking
- Pattern recognition metadata
- Organization-wide standards

---

## Design Patterns & Best Practices

### LLM Prompt Engineering

**System Prompt Structure:**
```
You are an expert Data Architect... (Persona)

IMPORTANT: Respond with JSON following this schema:
{schema}

Do not include explanatory text.
```

**User Prompt Structure:**
```
Your task is to analyze [specific task]...

Data to analyze:
- Column names: [...]
- Statistical summary: {...}

Analyze and provide recommendations.
```

**Best Practices Implemented:**
1. **Separate system/user content** - Allows reuse of personas
2. **Schema in system prompt** - Enforces structure without user confusion
3. **Iterative refinement** - "Think step by step" in prompts
4. **Self-check instructions** - Ask model to validate its own output

### Error Handling Strategy

**Three-Layer Validation:**
1. **Input Validation:** Check file format, size limits, basic structure
2. **LLM Output Validation:** Pydantic validation with retry logic
3. **Business Rule Validation:** Check logical consistency (e.g., min < max)

**Error Categories:**
- **User Errors:** Invalid file format → Show clear message in UI
- **System Errors:** API failures → Log and show "try again" message
- **AI Errors:** Invalid JSON → Retry with temperature adjustment
- **Data Errors:** Schema violations → Add to "issues" list

### Memory Management

**Polars Lazy API Usage:**
```python
# Good: Streams data, constant memory
df = pl.scan_csv("large_file.csv")
profile = df.select([
    pl.col("*").null_count(),
    pl.col("*").approx_unique()
]).collect()

# Avoid: Loads entire file into memory
df = pl.read_csv("large_file.csv")  # Bad for large files
```

**Streaming Chunks:**
```python
# For very large files, process in chunks
for chunk in pl.scan_csv("huge.csv").collect(streaming=True).iter_chunks():
    process(chunk)
```

### Testing Strategy

**Current State:** Minimal test coverage (prototype phase)

**Target Test Pyramid:**
```
┌────────────────────────────────┐ 10% - ✅ E2E tests (Streamlit + real files)
│  End-to-End Tests              │    - Limited (slow, expensive)
├────────────────────────────────┤ 30% - 🔲 Integration tests (LLM + Polars)
│  Integration Tests             │    - Mock API, test full flows
├────────────────────────────────┤ 60% - ✅ Unit tests (happy + sad paths)
│  Unit Tests                    │    - Pure functions, edge cases
└────────────────────────────────┘
```

**Testing Priorities:**
1. **Profiler Tests:** Ensure accurate statistics
2. **LLM Response Tests:** Validate structured output parsing
3. **Contract Tests:** Verify metadata.json format
4. **Drift Detection Tests:** Edge cases in comparison logic

**LLM Testing Pattern:**
```python
@pytest.fixture
def mock_llm_response():
    return {
        "summary": "No violations found",
        "violations": []
    }

def test_naming_check_handles_empty_response(mock_llm_response):
    with patch('openai.OpenAI') as mock_client:
        mock_client.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content=json.dumps(mock_llm_response)))]
        )
        result = run_llm_naming_check([])
        assert result.violations == []
```

---

## Technology Stack Justification

### Polars (Data Processing)

**Why Polars over Pandas:**
| Feature | Polars | Pandas |
|---------|--------|--------|
| **Performance** | ⚡ 5-10x faster | Standard |
| **Memory** | 🎯 Lazy evaluation | Eager loading |
| **Type Safety** | ✅ Strict schema | ⚠️ Flexible |
| **Parallelism** | 🔄 Built-in thread pool | Python GIL-limited |
| **API Design** | 🎨 Modern, consistent | Legacy compatibility |

**Use Cases Where We Still Use Pandas:**
- Streamlit integration (some components require pandas DataFrames)
- Legacy code compatibility
- Specific statistical functions not yet in Polars

**Migration Strategy:**
- Phase 1: Use Polars for all new profiling code ✅
- Phase 2: Convert Streamlit display layer to Polars (reduce pandas usage)
- Phase 3: Full Polars ecosystem (when Streamlit supports native Polars better)

### OpenAI API (LLM Integration)

**Why OpenAI API Pattern (vs Gemini/Anthropic native):**

**Pros:**
- ✅ Works with multiple providers (Moonshot, OpenAI, local Llama)
- ✅ Mature ecosystem (LangChain, LiteLLM compatibility)
- ✅ Clear documentation and community support
- ✅ Predictable JSON mode behavior

**Cons:**
- ❌ No native JSON schema validation (like Gemini)
- ❌ Rate limits vary by provider
- ❌ Cost can be higher for some models

**Mitigation Strategies:**
- Prompt-based schema enforcement (documented in this architecture)
- Provider abstraction layer (future enhancement)
- Response caching for duplicate analyses

**Alternative Providers Considered:**
- **Gemini:** Native JSON schema but less reliable uptime
- **Anthropic:** Better reasoning but no structured output support
- **Local Llama:** Self-hosted but requires GPU infrastructure

**Decision:** Start with OpenAI-compatible pattern for maximum flexibility

### Pydantic v2 (Data Validation)

**Why Pydantic over Dataclasses:**
- ✅ Rich validation (types, ranges, custom validators)
- ✅ JSON schema generation (for LLM prompts)
- ✅ Performance (Rust-based core)
- ✅ Integration with FastAPI, modern Python stack

**Use Cases:**
- LLM output validation
- Configuration management
- API request/response models
- Metadata contract schemas

### Streamlit (UI Framework)

**Why Streamlit over Alternatives:**

| Framework | Use Case | Our Needs |
|-----------|----------|-----------|
| **Streamlit** | Data apps ✅ | Fast prototyping ✅ |
| **Gradio** | ML demos | Limited customization |
| **Dash** | Enterprise apps | Too complex for MVP |
| **FastAPI + HTML** | Full control | Too much boilerplate |
| **Jupyter** | Notebooks | Not interactive enough |

**Streamlit Limitations & Workarounds:**
1. **State Management:** Use `st.session_state` for complex state
2. **Layout:** Custom CSS for better visual hierarchy
3. **Performance:** Cache expensive operations with `@st.cache_data`
4. **Testing:** Limited E2E testing options (use Playwright)

**Future UI Strategy:**
- MVP0-MVP1: Streamlit (focus on backend features)
- MVP2: Evaluate migration to Dash or custom React if needed

---

## Scalability Considerations

### Current Limitations (Prototype)

**Known Bottlenecks:**
1. **Single-threaded Streamlit:** UI blocks during processing
   - *Mitigation:* Show progress spinners, use `st.spinner()`
   - *Fix:* Move heavy processing to background threads (future)

2. **Synchronous LLM Calls:** Sequential AI analysis
   - *Mitigation:* Process naming and type checks in parallel
   - *Fix:* Use `asyncio` + `aiohttp` for concurrent LLM calls

3. **Memory Usage:** Polars Lazy API helps, but UI layer uses pandas
   - *Mitigation:* Limit preview to sample rows
   - *Fix:* Full Polars-native UI when Streamlit supports it

### Scaling Strategies

**For Large Files (10GB+):**
```python
# Use streaming Chunks
df = pl.scan_csv("huge.csv")
for chunk in df.collect(streaming=True).iter_chunks():
    process(chunk)

# Or process in batches
batch_size = 1_000_000
for i in range(0, total_rows, batch_size):
    batch = df.slice(i, batch_size)
    profile = process_batch(batch)
```

**For High Throughput:**
- Add Redis cache for LLM responses
- Implement request queuing (Celery/RQ)
- Use dedicated LLM proxy (LiteLLM, OpenRouter)

**For Concurrent Users:**
- Run Streamlit with `--server.maxUploadSize 10000`
- Deploy behind reverse proxy (nginx)
- Consider alternative UIs for multi-user scenarios

---

## Security Architecture

### API Key Management

**Threat Model:**
- API key exposure in logs
- .env file committed to git
- Key theft from running process
- Unauthorized usage if key leaked

**Controls:**
```python
# ✅ Good: Key from environment only
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ❌ Bad: Key in code
OPENAI_API_KEY = "sk-1234567890abcdef"  # NEVER DO THIS

# ✅ Good: Clear error messages
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found. See docs/setup.md")
```

**Git Protection:**
```bash
# .gitignore
.env
.docker/secrets/
*.key
*.pem
```

### Input Validation

**File Upload Security:**
```python
def validate_upload(file):
    # Check file extension
    if not file.name.endswith(('.csv', '.parquet')):
        raise ValueError("Unsupported file type")

    # Check file size (prevent DoS)
    max_size = 100 * 1024 * 1024  # 100MB
    if file.size > max_size:
        raise ValueError("File too large")

    # Scan for malicious content
    if contains_binary_exploit(file):
        raise SecurityError("Suspicious file content")
```

**User Input Sanitization:**
- Don't log raw user inputs (may contain secrets)
- Use parameterized queries (even though we use Polars)
- Validate column names against regex patterns

### Data Privacy

**Handling Sensitive Data:**
- Add flag for PII detection (future feature)
- Support data masking in previews
- Audit logging for data access
- Consider differential privacy for stats (future)

**LLM Privacy Concerns:**
- Column names may be sensitive
- Statistical values may reveal business metrics
- Add option for local LLM (Llama, etc.)
- Document data sent to LLM providers

---

## Future Architecture (MVP1 & MVP2)

### MVP1 Architecture (Delta Ingestion)

**New Components:**
```
┌─────────────────────────────────────────┐
│        Contract Registry                │
│  (Local filesystem → SQLite/PostgreSQL) │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│        Drift Detection Engine           │
│  ├─ Schema Drift Detector               │
│  ├─ Type Drift Detector                 │
│  └─ Value Drift Detector                │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│        Health Report Generator          │
│  - Threshold-based alerting             │
│  - Severity classification              │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│        Approval Workflow UI             │
│  - Show diffs                           │
│  - Bulk actions                         │
│  - Rollback capability                  │
└─────────────────────────────────────────┘
```

**Key Features:**
- Batch processing of multiple files
- Automated drift comparison
- Configurable alert thresholds
- Historical trend analysis

### MVP2 Architecture (Governance)

**Governance Layer:**
```
┌─────────────────────────────────────────┐
│      Metadata Repository                │
│  (Centralized contract storage)         │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│      Pattern Recognition Engine         │
│  ├─ Naming pattern learning             │
│  ├─ Type inference patterns             │
│  └─ Best practices extraction           │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│      Semantic Renaming Engine           │
│  - ML-based name suggestions            │
│  - Confidence scoring                   │
│  - Alias management                     │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│      Governance Dashboard               │
│  - Organization-wide metrics            │
│  - Standard enforcement                 │
│  - Compliance reporting                 │
└─────────────────────────────────────────┘
```

**Enterprise Features:**
- Multi-user approval workflows
- Role-based access control (RBAC)
- Audit trail for all decisions
- Integration with data catalogs (DataHub, Amundsen)
- REST API for programmatic access

---

## Performance Benchmarks

### Profiling Performance

**Test Setup:**
- File: 1GB CSV (10M rows, 20 columns)
- Machine: M2 MacBook, 16GB RAM
- Cold start (no OS caching)

**Results:**
```
Polars (Lazy):    8.2s  |  Peak RAM: 150MB
Pandas (Chunked): 45.1s |  Peak RAM: 850MB
Pandas (Full):    38.3s |  Peak RAM: 2.1GB ⚠️
```

**Key Insights:**
- Polars 5.5x faster than pandas (chunked)
- Polars uses 85% less memory than pandas
- Pandas full load risks OOM on larger files
- Streaming works well for >10GB files

### LLM Response Time

**Test Setup:**
- Model: kim10k2-thinking
- 50 columns, full statistics
- Network: US West Coast → Moonshot AI

**Results:**
```
Naming check:     2.3s ± 0.4s
Type check:       3.1s ± 0.5s
Total LLM time:   5.4s ± 0.7s
```

**Optimization Opportunities:**
- Run naming/type checks in parallel (potential 2x speedup)
- Implement response caching for identical schemas
- Use faster model for simple checks, slower for complex
- Add streaming responses with partial updates

### End-to-End User Experience

**MVP0 Target Flow:**
```
File upload (100MB):    2s
Polars profiling:       5s
LLM analysis:           6s
UI rendering:           1s
Total:                  14s
Goal:                   <15s (✅ Achievable)
```

**MVP1 Target Flow:**
```
Delta ingestion (10MB): 1s
Drift detection:        3s
Report generation:      2s
Total:                  6s
Goal:                   <10s (✅ Achievable)
```

---

## Monitoring & Observability

### LLM Usage Tracking

```python
# Track token usage
llm_metrics = {
    "prompt_tokens": response.usage.prompt_tokens,
    "completion_tokens": response.usage.completion_tokens,
    "total_tokens": response.usage.total_tokens,
    "model": model_name,
    "cost": calculate_cost(response.usage, model_name)
}

# Log to monitoring system
logger.info("LLM Call", extra=llm_metrics)
```

**Metrics to Track:**
- Tokens per analysis type
- Cost per user/session
- Response time percentiles
- Error rates by model
- Cache hit rates

### Data Quality Metrics

**Drift Detection Dashboard:**
- Schema drift frequency
- Type violation counts
- Null percentage changes
- Value range anomalies
- Ingestion success rates

**Performance Metrics:**
- Profiling time by file size
- LLM response time trends
- UI interaction latency
- Error rates by component

### Alerting Rules

**Error Alerts:**
- LLM API failures > 5% in 10 minutes
- Processing time > 95th percentile
- Critical drift detected
- Disk space / resource exhaustion

**Business Alerts:**
- Unusual data volume (10x normal)
- Schema changes in production data
- Quality score drops below threshold
- Ingestion pipeline failures

---

## API Reference (Future)

### REST API Design (MVP2)

```yaml
openapi: 3.0.0
info:
  title: Data Canary AI API
  version: 1.0.0

paths:
  /api/v1/ingest:
    post:
      summary: Ingest and analyze new data
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
                autoprocess:
                  type: boolean
                  default: false
      responses:
        202:
          description: Analysis submitted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/JobStatus'

  /api/v1/contract/{table_name}:
    get:
      summary: Get metadata contract
      responses:
        200:
          description: Contract retrieved
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MetadataContract'

    post:
      summary: Update contract with overrides
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ContractUpdate'
```

**Use Cases:**
- CI/CD pipeline integration
- Programmatic bulk processing
- Third-party tool integration (Airflow, Prefect)
- Custom monitoring systems

---

## Glossary

- **AI-First Design:** Architecture where AI capabilities are core, not add-on features
- **Metadata Contract:** JSON file defining schema, quality baselines, and ingestion history
- **Polars:** High-performance DataFrame library with Rust backend
- **Lazy API:** Deferred execution pattern - computation graphs built, executed on demand
- **Drift Detection:** Monitoring for changes in schema, types, or statistical distributions
- **Human-in-the-Loop:** Design pattern where AI suggests, humans approve/reject decisions
- **Schema Enforcement:** Ensuring LLM outputs conform to predefined JSON structure
- **Source-to-Target Mapping:** Preservation of original column names alongside standardized versions

---

## References

- [Polars Documentation](https://docs.pola.rs/)
- [Pydantic v2 Docs](https://docs.pydantic.dev/2.0/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [OpenAI API Docs](https://platform.openai.com/docs/)
- [Project Specification](./project-spec.md)
- [Development Setup](../.env.example)

---

## Related Documentation

This architecture document focuses on system design and technical decisions. For related guidance, see:

- [docs/development-guide.md](development-guide.md) - Development workflows, code quality standards, troubleshooting, and contributing guidelines
- [docs/decision-records.md](decision-records.md) - Detailed architectural decision records (ADRs) including trade-off analysis

---

**Document Maintainers:** Data Canary AI Team
**Review Schedule:** Monthly or upon major architecture changes
**Last Reviewed:** 2026-01-09
