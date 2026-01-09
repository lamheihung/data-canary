# 🐤 Data Canary AI: The Schema Designer & Drift Detection Companion

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Framework: Polars](https://img.shields.io/badge/Polars-v0.20%2B-purple)](https://www.pola.rs/)
[![CI Status](https://github.com/lamheihung/data-canary/actions/workflows/ci.yml/badge.svg)](https://github.com/lamheihung/data-canary/actions/workflows/ci.yml)

**Data Canary AI** is an AI-powered tool designed for data engineers to bridge the gap between raw data discovery and production-ready ingestion. It automates table design, naming convention enforcement, and data quality monitoring using an "AI-First" approach.

By leveraging Python Polars for high-performance profiling and LLMs for semantic analysis, Data Canary acts as a senior architect sitting next to the engineer, suggesting optimized schemas and alerting them to data drift.

---

## 🚀 Key Features

* **High-Performance Profiling:** Built on **Polars** Lazy API & Streaming for memory-efficient analysis of large datasets (CSV, Parquet).
* **AI-Powered Schema Design:** Automatically detects column roles (e.g., PK, Metric, Event Marker, Category) and suggests optimal Polars data types.
* **Human-in-the-Loop:** AI suggests; you decide. Interactive Streamlit UI for reviewing and overriding AI recommendations.
* **Metadata Contracts:** Saves a `metadata.json` "Historical Fingerprint" containing physical schema and statistical baselines.
* **Naming Convention Enforcement:** Reviews column names and suggests standardized naming (e.g., `snake_case`) to prevent "data swamps".

---

## ⚙️ Getting Started

### Prerequisites

1.  **Python 3.10+**
2.  **API Key:** Get an API key from any OpenAI-compatible provider and set it as an environment variable:
    ```bash
    export OPENAI_API_KEY="YOUR_API_KEY"
    export OPENAI_BASE_URL="https://api.provider.com/v1"  # Optional, defaults to OpenAI
    ```

### Setup and Installation

We recommend using `uv` for a fast and reliable dependency setup.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/lamheihung/data-canary.git](https://github.com/lamheihung/data-canary.git)
    cd data-canary
    ```

2.  **Create and activate virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    uv pip install -e .[dev]
    ```

### Running the Application

Launch the Streamlit interface from the root directory:

```bash
streamlit run data_canary/app.py
```

---

## 📋 Product Roadmap

### MVP0: The Foundation (Current) - Single Source Initialization
**Focus:** From Raw CSV to Approved Parquet

- **Ingestion:** Point to a local CSV or Parquet file
- **AI Profiling:** Detect column roles and suggest optimal datatypes based on statistical analysis
- **Proposed Schema View:** Streamlit UI showing AI suggestions with real-time column statistics
- **Human-in-the-Loop:** Approve or override column names and types before finalizing
- **Contract Creation:** Save `metadata.json` containing the "Historical Fingerprint" (physical schema + statistical baseline)

### MVP1: Monitoring & Delta Ingestion (Upcoming)
**Focus:** Guardrails for recurring data with automatic mode detection

MVP1 builds on MVP0 foundation and adds **delta ingestion** capabilities. The system automatically detects which mode to use:

**Initialization Mode** (new data sources):
- All MVP0 features for creating new tables
- Human-in-the-loop approval workflow
- Contract creation and Parquet materialization

**Delta Ingestion Mode** (existing data sources):
- **Batch Processing:** Support for multiple CSVs or daily delta files
- **Automated Audit:** Compare incoming data against the `metadata.json` baseline
- **Drift Detection:**
  - **Schema Drift:** Identify new or dropped columns
  - **Type Drift:** Warn if data types change (e.g., String in Int column)
  - **Null/Value Drift:** Alert if null percentages or value ranges shift significantly
- **Alerting:** Provide a "Health Report" (Warnings/Errors) before finalizing ingestion
- **Approval Workflow:** User accepts/rejects detected changes

### MVP2: Governance & Modernization (Future)
**Focus:** Scaling Standards

- **Semantic Renaming:** AI suggests modern naming conventions while maintaining original source names as aliases
- **Pattern Learning:** Scan centralized metadata directory to suggest names based on previously approved tables

---

## 🏗️ Development Principles

- **Lazy First:** All data profiling uses Polars Lazy API to handle large-scale data efficiently
- **Trust but Verify:** The AI suggests; the user decides. Always provide an "Override" path
- **Traceability:** Never lose mapping back to original source column names

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
