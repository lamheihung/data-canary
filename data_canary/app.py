import streamlit as st
import pandas as pd
from data_canary.check.basic import run_basic_checks
from data_canary.check.llm_naming import run_llm_naming_check
from data_canary.check.llm_types import run_llm_type_check
import io
from typing import Optional, Any, Dict, List


def load_data(uploaded_file) -> Optional[pd.DataFrame]:
    """Handles file type detection and loading into a Pandas DataFrame."""
    try:
        # Read the file based on its type
        # Use io.BytesIO(uploaded_file.read()) for robust reading of uploaded files
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(uploaded_file.read()))
        elif uploaded_file.name.endswith(".parquet"):
            df = pd.read_parquet(io.BytesIO(uploaded_file.read()))
        else:
            st.error("Unsupported file type. Please upload a CSV or Parquet file.")
            return None
        return df
    except Exception as e:
        st.error(f"Error loading or processing file: {e}")
        return None

def display_issues(issues: List[Dict[str, Any]]):
    """Formats and displays the list of data quality issues."""
    if not issues:
        st.success("No critical basic issues found!")
        return

    st.warning(f"Found {len(issues)} Potential Issue(s)")
    for issue in issues:
        # Use a consistent template for displaying issues
        message = issue["message"]
        severity = issue["severity"].upper()
        issue_type = issue["type"]
        
        if "column" in issue:
            # Issue related to a specific column
            col_name = issue["column"]
            st.markdown(f"**[{severity}]** ({issue_type}): Column `{col_name}`: {message}")
        else:
            # Global dataset issue (e.g., duplicate rows)
            st.markdown(f"**[{severity}]** ({issue_type}): {message}")


def main():
    """The main application function controlling the flow."""
    
    # --- Streamlit Page Configuration ---
    st.set_page_config(
        page_title="Data Canary: AI Data Quality",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("🐤 Data Canary")
    st.markdown("---")

    # --- File Upload Section (Sidebar) ---
    uploaded_file = st.sidebar.file_uploader(
        "Upload a CSV or Parquet file to analyze",
        type=["csv", "parquet"],
        accept_multiple_files=False,
    )

    if uploaded_file is None:
        st.info("Upload a file in the sidebar to begin the data quality analysis.")
        return

    # --- Data Loading ---
    st.subheader("Data Loaded")
    df = load_data(uploaded_file)

    if df is None:
        return # Stop execution if loading failed
        
    # Display basic information
    st.write(f"Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns")
    st.dataframe(df.head(), use_container_width=True)
    
    # --- Basic Check Execution ---
    st.markdown("---")
    st.subheader("Basic Data Profile")
    
    # Run the basic checks logic
    with st.spinner("Running basic profiling checks..."):
        profile = run_basic_checks(df)
    
    # --- Display Issues/Warnings ---
    display_issues(profile["issues"])

    # --- Display Full Schema/Stats (for reference) ---
    st.markdown("---")
    st.subheader("Full Column Statistics")
    
    # Convert list of dicts to a clean DataFrame for display
    stats_df = pd.DataFrame(profile["columns"])
    
    # Clean up the output for better Streamlit display
    stats_df = stats_df.set_index("name")
    stats_df["null_ratio"] = stats_df["null_ratio"].apply(lambda x: f"{x:.2%}")
    
    st.dataframe(stats_df, use_container_width=True)

    # --- AI Naming Convention Check ---
    st.markdown("---")
    st.subheader("🤖 AI Naming Convention Review")

    if st.button("Run AI Check for Naming Conventions"):
        with st.spinner("Analyzing column names with Gemini..."):
            columns = df.columns.tolist()
            report = run_llm_naming_check(columns)
        
        if report:
            # Display the AI's summary
            st.markdown(f"**AI Summary:** {report.summary}")
            
            # Display detailed violations
            if report.violations:
                st.error(f"Found {len(report.violations)} Potential Naming Violation(s)")
                
                # Convert violations list to a clean DataFrame for display
                violation_data = [v.model_dump() for v in report.violations]
                violation_df = pd.DataFrame(violation_data)
                
                # Reorder and format columns for readability
                display_cols = ["column_name", "severity", "violation_reason", "suggested_name"]
                
                st.dataframe(
                    violation_df[display_cols].set_index("column_name"), 
                    use_container_width=True,
                    column_config={
                        "severity": st.column_config.Column("Severity"),
                        "violation_reason": st.column_config.TextColumn("Reason for Violation"),
                        "suggested_name": st.column_config.Column("Suggested Name"),
                    }
                )
            else:
                st.success("The AI found no naming convention issues!")
        else:
            st.error("The AI check could not be completed. Check console for API key or connection errors.")

    # --- AI Schema Suggestion Check ---
    st.markdown("---")
    st.subheader("🤖 AI Schema & Type Suggestion")

    if st.button("Run AI Check for Schema Optimization"):
        # Get the schema from the basic check profile
        # We run the basic check again just to ensure we have the profile data, or you can pass it from the previous run
        with st.spinner("Profiling data to extract schema..."):
            profile = run_basic_checks(df)

        # The schema is a dict of {column_name: dtype_string}
        current_schema = profile.get("schema", {})

        with st.spinner("Analyzing current schema with Gemini for optimization..."):
            report = run_llm_type_check(current_schema)

        if report:
            st.markdown(f"**AI Summary:** {report.summary}")

            if report.suggestions:
                st.info(f"Found {len(report.suggestions)} Type Suggestions")

                # Convert suggestions list to a clean DataFrame for display
                suggestion_data = [s.model_dump() for s in report.suggestions]
                suggestion_df = pd.DataFrame(suggestion_data)

                # Display the suggestion table
                display_cols = ["column_name", "current_dtype", "suggested_logical_type", "suggested_pandas_type", "reasoning"]
                st.dataframe(
                    suggestion_df[display_cols].set_index("column_name"), 
                    use_container_width=True,
                    column_config={
                        "current_dtype": st.column_config.Column("Current Pandas Type"),
                        "suggested_logical_type": st.column_config.Column("Suggested Logical Type"),
                        "suggested_pandas_type": st.column_config.Column("Target Pandas Type"),
                        "reasoning": st.column_config.TextColumn("Reasoning"),
                    }
                )
            else:
                st.success("The AI found no immediate type optimization suggestions!")
        else:
            st.error("The AI Schema check could not be completed. Check console for API key or connection errors.")

if __name__ == "__main__":
    main()