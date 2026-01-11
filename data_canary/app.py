import streamlit as st
import polars as pl
import pandas as pd
import io
from typing import Optional, Any, Dict, List, Callable

from data_canary.core.basic_profiler import run_basic_checks
from data_canary.llm.naming_checking import run_llm_naming_check
from data_canary.llm.type_checking import run_llm_type_check
from data_canary.schemas.data_models import (
    NamingCheckReport,
    TypeCheckReport,
    MetadataContract,
    PhysicalColumn,
)
from data_canary.core.contract_builder import (
    build_physical_schema_with_overrides,
    apply_schema_transform,
    create_metadata_contract,
    validate_contract,
)
from data_canary.core.export import generate_parquet, save_metadata_contract


def load_data(uploaded_file) -> Optional[pl.DataFrame]:
    """Handles file type detection and loading into a Polars DataFrame.

    Detects file type from the uploaded file extension (CSV or Parquet) and
    loads it into a Polars DataFrame.

    Args:
        uploaded_file: The uploaded file object from Streamlit.

    Returns:
        A Polars DataFrame containing the uploaded data, or None if loading fails
        or the file type is unsupported.
    """
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
    """Formats and displays the list of basic data quality issues using expanders.

    Displays basic data quality issues in an expandable format with severity,
    type, and column information when available.

    Args:
        issues: List of issue dictionaries containing message, severity, type,
                and optional column information.

    Returns:
        None
    """
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
    """Displays the results of the Naming Convention Check.

    Renders the naming convention check results in the Streamlit UI,
    showing violations in a table format or a success message if none found.

    Args:
        report: NamingCheckReport with violation details, or None if check failed.

    Returns:
        None
    """
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
        st.dataframe(violation_df[display_cols].set_index("column_name"), use_container_width=True)
    else:
        st.success("The AI found no naming convention issues!")

    return None


def display_type_check_report(report: Optional[TypeCheckReport]):
    """Displays the results of the Schema/Type Suggestion Check.

    Renders the type optimization check results in the Streamlit UI,
    showing suggestions in a table format or a success message if none found.

    Args:
        report: TypeCheckReport with optimization suggestions, or None if check failed.

    Returns:
        None
    """
    st.subheader("2. 🧩 Schema & Type Optimization")

    if report is None:
        st.error("Type Check failed. Check console for details.")

        return None

    st.info(f"AI Summary: {report.summary}")

    if report.suggestions:
        st.warning(f"Found {len(report.suggestions)} Type Suggestion(s)")
        suggestion_data = [s.model_dump() for s in report.suggestions]
        suggestion_df = pd.DataFrame(suggestion_data)

        display_cols = [
            "column_name",
            "current_dtype",
            "suggested_logical_type",
            "suggested_polars_type",
            "reasoning",
        ]
        st.dataframe(suggestion_df[display_cols].set_index("column_name"), use_container_width=True)
    else:
        st.success("The AI found no immediate type optimization suggestions!")

    return None


def display_review_interface(
    physical_schema: List[PhysicalColumn],
    current_overrides: Dict[str, Dict[str, str]],
    on_approve: Callable[[str, Dict[str, Dict[str, str]], str], None],
    default_output_dir: str,
) -> None:
    """Display the human-in-the-loop review interface for column overrides.

    This is a pure UI function that displays the review interface and collects
    user overrides. The schema is displayed with current_overrides applied, and
    any new overrides entered by the user are collected and passed to on_approve.

    Args:
        physical_schema: Physical schema displayed to user (with current_overrides applied)
        current_overrides: Current user override values (for initializing form inputs)
        on_approve: Callback when user approves changes (receives table_name, overrides, and output_dir)
        default_output_dir: Default directory for output files
    """

    st.markdown("## 🔍 Review & Approve AI Suggestions")
    st.info(
        "Review AI suggestions below. You can override any column name or type before approval."
    )

    # Create review table
    review_data = []
    for col in physical_schema:
        review_data.append(
            {
                "Column Index": col.column_index,
                "Source Name": col.source_name,
                "AI Suggested Name": col.ai_suggested_name or "(no change)",
                "Source Type": col.source_type,  # Show original type
                "AI Suggested Type": col.ai_suggested_type or "(no change)",
            }
        )

    review_df = pd.DataFrame(review_data)

    # Display review table
    st.markdown("### 📋 Schema Review")
    st.dataframe(
        review_df[["Column Index", "Source Name", "AI Suggested Name", "Source Type", "AI Suggested Type"]],
        use_container_width=True,
    )

    # Approval buttons and form
    st.markdown("---")
    st.markdown("### ✅ Approve or Reject Changes")

    # Table name input
    table_name = st.text_input("Table Name", value="my_table")

    # Output directory selection
    output_dir = st.text_input(
        "Output Directory", value=default_output_dir, placeholder="e.g., ./output or /path/to/output"
    )

    # Expanders for detailed editing (only collect inputs, don't apply yet)
    with st.expander("✏️ Edit Column Names"):
        st.markdown("Override column names by entering new names below:")

        name_overrides = {}
        cols = st.columns(3)
        for idx, physical_col in enumerate(physical_schema):
            col_idx = idx % 3
            with cols[col_idx]:
                current_override = current_overrides.get(physical_col.source_name, {}).get("name", "")
                new_name = st.text_input(
                    f"Column: {physical_col.source_name}",
                    value=current_override,
                    key=f"name_override_{physical_col.source_name}",
                    placeholder="Leave empty to use AI suggestion",
                )
                if new_name and new_name != physical_col.target_name:
                    name_overrides[physical_col.source_name] = {"name": new_name}

    with st.expander("⚙️ Edit Data Types"):
        st.markdown("Override data types by selecting new types below:")

        type_overrides: Dict[str, Dict[str, str]] = {}
        common_types = [
            "String",
            "Int8",
            "Int16",
            "Int32",
            "Int64",
            "UInt8",
            "UInt16",
            "UInt32",
            "UInt64",
            "Float32",
            "Float64",
            "Boolean",
            "Date",
            "Datetime",
            "Categorical",
        ]

        cols = st.columns(3)
        for idx, physical_col in enumerate(physical_schema):
            col_idx = idx % 3
            with cols[col_idx]:
                current_override = current_overrides.get(physical_col.source_name, {}).get("type", "")
                # Default to target_type if no user override (preserves AI suggestion)
                current_index = (
                    common_types.index(current_override) if current_override in common_types
                    else common_types.index(physical_col.target_type) if physical_col.target_type in common_types
                    else 0
                )

                new_type = st.selectbox(
                    f"{physical_col.source_name}",
                    options=common_types,
                    index=current_index,
                    key=f"type_override_{physical_col.source_name}",
                )
                if new_type and new_type != physical_col.target_type:
                    if physical_col.source_name not in type_overrides:
                        type_overrides[physical_col.source_name] = {}
                    type_overrides[physical_col.source_name]["type"] = new_type

    # Combine all overrides
    all_overrides: Dict[str, Dict[str, str]] = {}
    for col_name in name_overrides:
        if col_name not in all_overrides:
            all_overrides[col_name] = {}
        all_overrides[col_name].update(name_overrides[col_name])

    for col_name in type_overrides:
        if col_name not in all_overrides:
            all_overrides[col_name] = {}
        all_overrides[col_name].update(type_overrides[col_name])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👍 Approve & Generate Outputs", type="primary", use_container_width=True):
            on_approve(table_name, all_overrides, output_dir)

    with col2:
        if st.button("👎 Reject & Start Over", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.rerun()


def display_success_screen(
    contract: MetadataContract,
    parquet_path: str,
    metadata_path: str,
    transformation_log: List[Dict[str, Any]],
):
    """Display success screen with generated file information.

    Shows a summary of the completed data transformation including table name,
    column count, row count, file locations, transformation log, and metadata
    contract preview.

    Args:
        contract: The metadata contract that was generated.
        parquet_path: Path to the generated Parquet file.
        metadata_path: Path to the generated metadata contract JSON file.
        transformation_log: Log of all transformations applied to the data.

    Returns:
        None
    """

    st.markdown("## 🎉 Success! Outputs Generated")

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Table Name", contract.identity["table_name"])
    with col2:
        st.metric("Columns", len(contract.physical_schema))
    with col3:
        st.metric("Rows", f"{contract.statistical_profile['row_count']:,}")

    st.markdown("---")

    # File locations
    st.markdown("### 📁 Generated Files")
    st.success(f"**Parquet File:** {parquet_path}")
    st.success(f"**Metadata Contract:** {metadata_path}")

    with st.expander("📊 Transformation Log"):
        for log_entry in transformation_log:
            st.markdown(f"**Column:** {log_entry['column']}")
            for action in log_entry["actions"]:
                st.text(f"  • {action}")
            st.markdown("---")

    with st.expander("📋 Metadata Contract Preview"):
        st.json(contract.model_dump())

    st.markdown("---")
    if st.button("🔄 Start New Analysis"):
        st.session_state.clear()
        st.rerun()


def handle_approval(
    table_name: str,
    user_overrides: Dict[str, Dict[str, str]],
    df: pl.DataFrame,
    profile: Dict[str, Any],
    naming_report: NamingCheckReport,
    type_report: TypeCheckReport,
    output_dir: str,
) -> None:
    """Callback for when user approves changes and wants to generate outputs.

    Args:
        table_name: The table name from user input
        user_overrides: Dictionary of NEW user overrides from the form
        df: The DataFrame to transform
        profile: Statistical profile of the data
        naming_report: AI naming suggestions
        type_report: AI type suggestions
        output_dir: Directory path where outputs should be saved
    """
    try:
        # Rebuild schema with the NEW overrides from the form
        # The physical_schema passed for display was built with OLD overrides
        final_physical_schema = build_physical_schema_with_overrides(
            columns=profile["columns"],
            naming_report=naming_report,
            type_report=type_report,
            user_overrides=user_overrides,
        )

        # Create metadata contract with the FINAL schema (using NEW overrides)
        contract = create_metadata_contract(
            table_name=table_name,
            version="1.0.0",
            source_path="uploaded_file",
            target_path=f"{output_dir}/{table_name}.parquet",
            physical_schema=final_physical_schema,
            statistical_profile={
                "row_count": profile["row_count"],
                "columns": profile["columns"],
            },
            created_by="user@example.com",
        )

        # Validate contract
        is_valid, issues = validate_contract(contract)
        if not is_valid:
            st.error(f"Contract validation failed: {issues}")
            return

        # Apply schema transform with the FINAL schema
        transformed_df, transformation_log = apply_schema_transform(
            df=df, physical_schema=final_physical_schema
        )

        # Generate outputs
        with st.spinner("Generating Parquet file..."):
            parquet_path = generate_parquet(
                transformed_df, f"{output_dir}/{table_name}.parquet"
            )

        with st.spinner("Generating metadata contract..."):
            metadata_path = save_metadata_contract(
                contract, f"{output_dir}/_metadata/{table_name}.json"
            )

        # Store results in session state
        st.session_state["contract"] = contract
        st.session_state["parquet_path"] = parquet_path
        st.session_state["metadata_path"] = metadata_path
        st.session_state["transformation_log"] = transformation_log
        st.session_state["user_overrides"] = user_overrides  # Save for next iteration

        st.success("✅ Outputs generated successfully!")
        # Force rerun to show success screen
        st.rerun()

    except Exception as e:
        st.error(f"Error generating outputs: {str(e)}")


def handle_start_analysis(df: pl.DataFrame) -> None:
    """Run profiling and LLM analysis, store results in session state.

    Performs basic data profiling checks, then runs AI-powered naming convention
    and type optimization checks, storing all results in Streamlit session state.

    Args:
        df: The DataFrame to analyze.

    Returns:
        None
    """
    with st.spinner("Running basic profiling checks..."):
        profile = run_basic_checks(df)
        st.session_state["profile"] = profile
        st.session_state["df"] = df

    with st.spinner("Running AI checks... This may take a moment."):
        naming_report = run_llm_naming_check(list(profile["schema"].keys()))
        type_report = run_llm_type_check(profile["schema"], profile["columns"])

        if naming_report is None or type_report is None:
            st.error("AI analysis failed. Please check your API key and try again.")
            return

        st.session_state["naming_report"] = naming_report
        st.session_state["type_report"] = type_report
        st.rerun()


def render_upload_sidebar() -> Optional[Any]:
    """Render file upload sidebar and return uploaded file.

    Creates a Streamlit sidebar file uploader that accepts CSV and Parquet files.

    Returns:
        The uploaded file object, or None if no file uploaded.
    """
    return st.sidebar.file_uploader(
        "Upload a CSV or Parquet file",
        type=["csv", "parquet"],
        accept_multiple_files=False,
    )


def render_data_tab(df: pl.DataFrame) -> None:
    """Render the Raw Data Sample tab.

    Displays the first 5 rows of the DataFrame in the Streamlit UI.

    Args:
        df: The DataFrame to display.

    Returns:
        None
    """
    st.markdown("### First 5 Rows of Data")
    st.dataframe(df.head().to_pandas(), use_container_width=True)


def render_profile_tab(profile: Dict[str, Any]) -> None:
    """Render the Basic Profile & Issues tab.

    Displays basic data profiling information including issue counts, row count,
    duplicate rows, and full column statistics.

    Args:
        profile: Dictionary containing data profiling results.

    Returns:
        None
    """
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


def render_ai_tab(naming_report: NamingCheckReport, type_report: TypeCheckReport) -> None:
    """Render the AI Checks & Governance tab.

    Displays AI-powered data governance reports including naming convention
    and type optimization recommendations.

    Args:
        naming_report: AI naming convention check results.
        type_report: AI type optimization check results.

    Returns:
        None
    """
    st.markdown("## AI-Powered Data Governance Report")
    display_naming_check_report(naming_report)
    st.markdown("---")
    display_type_check_report(type_report)


def render_review_tab(
    df: pl.DataFrame,
    profile: Dict[str, Any],
    naming_report: NamingCheckReport,
    type_report: TypeCheckReport,
) -> None:
    """Render the Review & Approve tab with human-in-the-loop interface.

    Displays the schema review interface where users can:
    - View AI suggestions for column names and types
    - Override column names and types
    - Set table name
    - Specify output directory
    - Approve or reject changes

    Args:
        df: The DataFrame being analyzed
        profile: Statistical profile from basic checks
        naming_report: AI naming suggestions
        type_report: AI type suggestions
    """
    user_overrides = st.session_state.get("user_overrides", {})
    physical_schema = build_physical_schema_with_overrides(
        columns=profile["columns"],
        naming_report=naming_report,
        type_report=type_report,
        user_overrides=user_overrides,
    )

    display_review_interface(
        physical_schema=physical_schema,
        current_overrides=user_overrides,
        on_approve=lambda table_name, overrides, output_dir: handle_approval(
            table_name, overrides, df, profile, naming_report, type_report, output_dir
        ),
        default_output_dir="./output",
    )


# --- Main Application Function ---
def main():
    """Main application entry point with clear orchestration flow.

    Orchestrates the entire Data Canary application flow:
    1. Sets up Streamlit page configuration
    2. Handles file upload and validation
    3. Runs analysis when triggered
    4. Displays results in tabs (data sample, profile, AI checks, review)

    Returns:
        None
    """

    st.set_page_config(
        page_title="Data Canary: AI Data Quality",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("🐤 Data Canary: AI-Powered Data Quality Framework")
    st.markdown("---")

    # Check for success screen first (after approval)
    if "contract" in st.session_state:
        display_success_screen(
            st.session_state["contract"],
            str(st.session_state["parquet_path"]),
            str(st.session_state["metadata_path"]),
            st.session_state["transformation_log"],
        )
        return

    # File upload
    uploaded_file = render_upload_sidebar()
    if not uploaded_file:
        return

    # Load and validate data
    df = load_data(uploaded_file)
    if df is None:
        return

    st.subheader(f"Analyzing: `{uploaded_file.name}`")
    st.markdown(f"Shape: **{df.shape[0]} rows**, **{df.shape[1]} columns**")

    # Analysis button
    st.markdown("---")
    if st.button("🚀 Start Comprehensive Data Analysis & Run All AI Checks"):
        handle_start_analysis(df)

    # Results display (if analysis complete)
    if "profile" in st.session_state and "naming_report" in st.session_state:
        profile = st.session_state["profile"]
        naming_report = st.session_state["naming_report"]
        type_report = st.session_state["type_report"]
        df = st.session_state["df"]

        tab_data, tab_profile, tab_ai, tab_review = st.tabs(
            [
                "Raw Data Sample",
                "Basic Profile & Issues",
                "AI Checks & Governance",
                "Review & Approve",
            ]
        )

        with tab_data:
            render_data_tab(df)

        with tab_profile:
            render_profile_tab(profile)

        with tab_ai:
            render_ai_tab(naming_report, type_report)

        with tab_review:
            render_review_tab(df, profile, naming_report, type_report)


if __name__ == "__main__":
    main()
