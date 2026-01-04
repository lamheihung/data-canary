import streamlit as st
import polars as pl
import pandas as pd
import io
from typing import Optional, Any, Dict, List

from data_canary.core.basic_profiler import run_basic_checks 
from data_canary.llm.naming_checking import run_llm_naming_check 
from data_canary.llm.type_checking import run_llm_type_check
from data_canary.schemas.data_models import NamingCheckReport, TypeCheckReport


def load_data(uploaded_file) -> Optional[pl.DataFrame]:
    """Handles file type detection and loading into a Polars DataFrame."""
    try:
        file_bytes = io.BytesIO(uploaded_file.read())

        if uploaded_file.name.endswith(".csv"):
            df = pl.read_csv(file_bytes)
        elif uploaded_file.name.endswith(".parquet"):
            df = pl.read_parquet(file_bytes)
        else:
            st.error("Unsupported file type. Please upload a CSV or Parquet file.")
            return None
        
        return df
    except Exception as e:
        st.error(f"Error loading or processing file: {e}")

        return None

def display_basic_issues(issues: List[Dict[str, Any]]):
    """Formats and displays the list of basic data quality issues using expanders."""
    if not issues:
        st.success("No critical basic issues found!")

        return None

    st.warning(f"Found {len(issues)} Basic Data Issue(s). Expand for details.")
    
    with st.expander("Details of Basic Issues"):
        for issue in issues:
            message = issue["message"]
            severity = issue["severity"].upper()
            issue_type = issue["type"]
            
            if "column" in issue:
                col_name = issue["column"]
                st.markdown(f"**[{severity}]** ({issue_type}): Column `{col_name}`: {message}")
            else:
                st.markdown(f"**[{severity}]** ({issue_type}): {message}")

    return None

def display_naming_check_report(report: Optional[NamingCheckReport]):
    """Displays the results of the Naming Convention Check."""
    st.subheader("1. 🗣️ Naming Convention Review")
    
    if report is None:
        st.error("Naming Check failed. Check console for details.")

        return None
        
    st.info(f"AI Summary: {report.summary}")
    
    if report.violations:
        st.error(f"Found {len(report.violations)} Potential Naming Violation(s)")
        violation_data = [v.model_dump() for v in report.violations]
        violation_df = pd.DataFrame(violation_data)
        
        display_cols = ["column_name", "violation_reason", "suggested_name"]
        st.dataframe(
            violation_df[display_cols].set_index("column_name"), 
            use_container_width=True
        )
    else:
        st.success("The AI found no naming convention issues!")

    return None
        
def display_type_check_report(report: Optional[TypeCheckReport]):
    """Displays the results of the Schema/Type Suggestion Check."""
    st.subheader("2. 🧩 Schema & Type Optimization")
    
    if report is None:
        st.error("Type Check failed. Check console for details.")

        return None
        
    st.info(f"AI Summary: {report.summary}")
    
    if report.suggestions:
        st.warning(f"Found {len(report.suggestions)} Type Suggestion(s)")
        suggestion_data = [s.model_dump() for s in report.suggestions]
        suggestion_df = pd.DataFrame(suggestion_data)
        
        display_cols = ["column_name", "current_dtype", "suggested_logical_type", "suggested_polars_type", "reasoning"]
        st.dataframe(
            suggestion_df[display_cols].set_index("column_name"), 
            use_container_width=True
        )
    else:
        st.success("The AI found no immediate type optimization suggestions!")

    return None


# --- Main Application Function ---
def main():
    """The main application function controlling the flow."""
    
    st.set_page_config(
        page_title="Data Canary: AI Data Quality",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("🐤 Data Canary: AI-Powered Data Quality Framework")
    st.markdown("---")

    # --- Sidebar: File Upload ---
    uploaded_file = st.sidebar.file_uploader(
        "Upload a CSV or Parquet file",
        type=["csv", "parquet"],
        accept_multiple_files=False,
    )

    if uploaded_file is None:
        st.info("Upload a file in the sidebar to begin the data quality analysis.")
        return

    # --- Data Loading ---
    df = load_data(uploaded_file)

    if df is None:
        return  None
        
    st.subheader(f"Analyzing: `{uploaded_file.name}`")
    st.markdown(f"Shape: **{df.shape[0]} rows**, **{df.shape[1]} columns**")
    
    # --- Main Analysis Trigger (Consolidated) ---
    st.markdown("---")
    if st.button("🚀 Start Comprehensive Data Analysis & Run All AI Checks"):
        
        # 1. Run Basic Profile
        with st.spinner("Running basic profiling checks..."):
            profile = run_basic_checks(df)

        # 2. Run All AI Checks (Simultaneously or sequentially for simplicity)
        with st.spinner("Running all AI checks with Gemini... This may take a moment."):
            naming_report = run_llm_naming_check(profile["schema"].keys())
            type_report = run_llm_type_check(profile["schema"], profile["columns"])
        
        # --- Display Results ---
        
        # Setup Tabs
        tab_data, tab_profile, tab_ai = st.tabs(["Raw Data Sample", "Basic Profile & Issues", "AI Checks & Governance"])

        with tab_data:
            st.markdown("### First 5 Rows of Data")
            st.dataframe(df.head().to_pandas(), use_container_width=True)

        with tab_profile:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("### Basic Profile Summary")
                display_basic_issues(profile["issues"])
                st.metric(label="Total Rows", value=f"{profile['row_count']:,}")
                st.metric(label="Duplicate Rows", value=f"{profile['duplicate_rows']:,}")
                st.markdown("---")

            with col2:
                st.markdown("### Full Column Statistics")
                stats_df = pd.DataFrame(profile["columns"])
                stats_df = stats_df.set_index("name")
                stats_df["null_ratio"] = stats_df["null_ratio"].apply(lambda x: f"{x:.2%}")
                st.dataframe(stats_df, use_container_width=True)


        with tab_ai:
            st.markdown("## AI-Powered Data Governance Report")
            display_naming_check_report(naming_report)
            st.markdown("---")
            display_type_check_report(type_report)


if __name__ == "__main__":
    main()