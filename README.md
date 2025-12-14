# 🐦 Data Canary: AI-Powered Data Quality & Profiling

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Framework: Polars](https://img.shields.io/badge/Polars-v0.20%2B-purple)](https://www.pola.rs/)

**Data Canary** is a high-performance data quality tool that utilizes the Gemini API for advanced, contextual data governance checks. It bridges the gap between basic statistical profiling and human-in-the-loop data architecture review by leveraging Large Language Models (LLMs) to automatically assess naming conventions, recommend schema optimizations, and provide clear, actionable reasoning.

---

## 🚀 Key Features

* **High-Performance Profiling:** Built on **Polars** for lightning-fast data ingestion (CSV, Parquet) and statistical aggregation, ensuring low-latency analysis on large datasets.
* **LLM-Powered Naming Review:** Automatically reviews column names against established conventions (e.g., `snake_case`) and suggests changes, providing detailed reports in a structured (Pydantic) format.
* **LLM-Powered Type Optimization:** Recommends optimal logical types (e.g., `CURRENCY`, `UUID`, `CATEGORY`) and corresponding physical types (e.g., `Int16`, `Decimal`) beyond simple data type inference.
* **Structured Output:** Uses **Pydantic** models to strictly enforce the output schema of the LLM, ensuring the results are reliable, parseable, and ready for downstream automation.
* **Streamlit UI:** Provides a simple, interactive web interface for uploading files and reviewing reports.

## 🏗️ Architecture and Design Philosophy

The project is structured following the **Separation of Concerns (SoC)** principle to ensure modularity, maintainability, and testability.

| Directory/File | Responsibility | Technologies |
| :--- | :--- | :--- |
| `data_canary/core/` | **Data Domain Logic:** Handles deterministic tasks like file loading, statistical calculation, and high-performance profiling. **(Polars Integration)** | `polars` |
| `data_canary/llm/` | **External Interface:** Encapsulates all calls to the Gemini API, prompt generation, structured response parsing, and error handling. **(DRY Principle)** | `google-genai` |
| `data_canary/schemas/` | **Data Contract:** Holds all Pydantic models, defining the exact data structure for inputs, outputs, and the LLM response reports. | `pydantic` |
| `data_canary/config.py` | **Configuration:** Manages settings, model names, and environment variables (following 12-Factor App methodology). | `os.getenv` |



This structure allows us to swap the LLM provider (e.g., to Azure OpenAI) by only touching the `llm/` directory, or switch the core engine (e.g., from Polars to Spark) by only changing the `core/` directory, without impacting the application logic or LLM prompts.

## ⚙️ Getting Started

### Prerequisites

1.  **Python 3.9+**
2.  **API Key:** Get a Gemini API key and set it as an environment variable:
    ```bash
    export GEMINI_API_KEY="YOUR_API_KEY"
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
