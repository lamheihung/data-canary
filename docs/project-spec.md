# Data Canary - The AI-Powered Schema Designer & Drift Detection Companion
---
## 1. Executive Summary
Data Canary AI is a tool designed for data engineers to bridge the gap between raw data discovery and production-ready ingestion. It automates the tedious work of table design, naming convention enforcement, and data quality monitoring using an "AI-First" approach. By leveraging Python Polars and Active Metadata, it acts as a senior architect sitting next to the engineer, suggesting optimized schemas and alerting them to data drift.

## 2. Problem Statement
Manual Discovery: Engineers waste time running df.describe() and manually mapping CSV headers to database types.

Silent Data Drift: Ingestion pipelines often fail or store low-quality data because schema changes or statistical shifts (like null spikes) go unnoticed.

Inconsistent Naming: Lack of enforcement leads to a "data swamp" with messy, unstandardized column names.

## 3. Core Tech Stack
Engine: Python Polars (utilizing Lazy API & Streaming for memory-efficient profiling).

Storage: Apache Parquet (for the data) and JSON (for the Metadata "Contract").

UI: Streamlit (for MVP0/1 review cycles).

AI Integration: LLM-assisted profiling for semantic role identification and naming suggestions.

## 4. Product Roadmap
### MVP0: The Foundation (Single Source Initialization)
Focus: From Raw CSV to Approved Parquet

Ingestion: Point to a local CSV file.

AI Profiling:

- Detect Column Roles (e.g., PK, Metric, Event Marker, Category).

- Suggest Optimal Datatypes (e.g., Int32 vs Int64 based on Min/Max calculations).

- Proposed Schema View: A Streamlit UI showing the AI's suggestions.

- Human-in-the-loop: User approves or overrides names/types.

- Contract Creation: Save a metadata.json containing the "Historical Fingerprint" (Physical schema + Statistical baseline).

### MVP1: Monitoring & Delta Ingestion
Focus: Guardrails for Recurring Data with Dual-Mode Support

MVP1 extends MVP0 by adding **automatic mode detection**. The system checks if metadata.json exists and automatically switches between:

**Initialization Mode** (No existing metadata):
- All MVP0 features for new data sources
- Human-in-the-loop approval workflow
- Contract creation and Parquet materialization

**Delta Ingestion Mode** (Existing metadata):

- Batch Processing: Support for multiple CSVs or daily delta files.

- Automated Audit: Compare incoming data against the metadata.json baseline.

- Drift Detection:

  - Schema Drift: Identify new or dropped columns.

  - Type Drift: Warn if data types change (e.g., String appearing in an Int column).

  - Null/Value Drift: Alert if null percentages or value ranges shift significantly.

- Alerting: Provide a "Health Report" (Warnings/Errors) before finalizing ingestion.

### MVP2: Governance & Modernization
Focus: Scaling Standards

Semantic Renaming: Suggest modern naming conventions (snake_case, etc.) while maintaining the original source name as an alias in the metadata.

Pattern Learning: AI scans the centralized metadata directory to suggest names based on previously approved tables.

## 5. Metadata Schema Structure (The "Contract")
The metadata.json is split into three logical blocks:

### Identity: 
- Table Name
- Version
- Source/Storage Paths
- Last Updated.

### Physical Schema: 
- source_name: Original CSV header.
- target_name: Approved standardized name.
- data_type: Polars-specific type.
- is_nullable: Boolean constraint.

### Statistical Profile (The Fingerprint):
- null_count_pct: Baseline for null drift.

- cardinality: For identifying categorical changes. Top 5 / 10 values.

- quantiles: (25th, 50th, 75th) to detect distribution shifts.

- min/max/mean: For numeric range validation.

## 6. Workflow Design
Initialization Mode:

Scan CSV (Lazy/Streaming) → Generate Proposal → User Review → Write Parquet + JSON.

Ingestion Mode:

Scan Delta → Compare vs. JSON → Generate Drift Report → User Accept/Reject → Append Parquet.

## 7. Development Principles (AI Coding)
Lazy First: All data profiling must use Polars Lazy API to handle large-scale data.

Trust but Verify: The AI suggests; the user decides. The system must always provide an "Override" path.

Traceability: Never lose the mapping back to the original source column name.