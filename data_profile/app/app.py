from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.report_generator import create_word_report
from profiler import DataProfiler
from utils.databricks_client import DatabricksMetadataClient, WarehouseOption
from utils.sql_client import create_sql_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Sigmatic Data Profiling",
    page_icon="📈",
    layout="wide",
)

@st.cache_resource(show_spinner=False)
def get_client() -> DatabricksMetadataClient:
    return DatabricksMetadataClient()


@st.cache_data(show_spinner=False)
def load_catalogs(catalog_name: str | None = None) -> list[str]:
    return get_client().list_catalogs()


@st.cache_data(show_spinner=False)
def load_schemas(catalog: str) -> list[str]:
    return get_client().list_schemas(catalog)


@st.cache_data(show_spinner=False)
def load_tables(catalog: str, schema: str) -> list[str]:
    return get_client().list_tables(catalog, schema)


@st.cache_data(show_spinner=False)
def load_warehouses() -> list[WarehouseOption]:
    return get_client().list_warehouses()


def render_dashboard(profile_result: dict[str, Any]) -> None:
    st.subheader("Profiling Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Row Count", f"{profile_result['row_count']:,}")
    col2.metric("Column Count", profile_result["column_count"])
    col3.metric("Duplicate Count", profile_result["duplicate_count"])
    col4.metric("Quality Score", f"{profile_result['quality_score']} / 100")

    st.divider()

    with st.expander("Schema Overview", expanded=True):
        schema_df = pd.DataFrame(profile_result["schema"])
        st.dataframe(schema_df, use_container_width=True, hide_index=True)

    tab_schema, tab_nulls, tab_cardinality, tab_quality, tab_recommendations = st.tabs(
        ["Column Statistics", "Null Percentages", "Cardinality", "Quality Warnings", "Recommendations"]
    )

    with tab_schema:
        stats_df = pd.DataFrame(profile_result["numeric_statistics"])
        if not stats_df.empty:
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        else:
            st.info("No numeric statistics available for the selected table.")

    with tab_nulls:
        null_df = pd.DataFrame(
            [{"column_name": key, "null_percentage": value} for key, value in profile_result["null_percentages"].items()]
        )
        st.dataframe(null_df, use_container_width=True, hide_index=True)

    with tab_cardinality:
        cardinality_df = pd.DataFrame(
            [{"column_name": key, "unique_count": value} for key, value in profile_result["unique_counts"].items()]
        )
        st.dataframe(cardinality_df, use_container_width=True, hide_index=True)
        if profile_result["candidate_primary_keys"]:
            st.success(f"Candidate primary keys: {', '.join(profile_result['candidate_primary_keys'])}")
        else:
            st.warning("No candidate primary keys were identified.")

    with tab_quality:
        if profile_result["data_type_issues"]:
            st.warning("Data type concerns detected")
            st.dataframe(pd.DataFrame(profile_result["data_type_issues"]), use_container_width=True, hide_index=True)
        else:
            st.success("No data type issues detected.")

        if profile_result["quality_warnings"]:
            st.dataframe(pd.DataFrame(profile_result["quality_warnings"]), use_container_width=True, hide_index=True)
        else:
            st.info("No quality warnings detected.")

    with tab_recommendations:
        for recommendation in profile_result["recommendations"]:
            st.info(recommendation)


def main() -> None:

    logo_path = Path(__file__).parent / "Logo Sigmatic-r0d1-01.png"

    col1, col2 = st.columns([1, 5])

    with col1:
        st.image(str(logo_path), width=180)

    with col2:
        st.markdown(
            """
            <h1 style="margin-bottom:0px;">
                Sigmatic Data Profiling & Quality
            </h1>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <span style="font-size:18px;color:#8c8c8c;">
            Enterprise-grade profiling powered by Databricks SQL Warehouse
            </span>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    with st.sidebar:
        st.header("Configuration")
        client = get_client()
        warehouses = load_warehouses()
        warehouse_names = [warehouse.name for warehouse in warehouses]
        default_warehouse_name = next(
            (
                name
                for name in warehouse_names
                if "serverless" in name.lower() or "starter" in name.lower()
            ),
            warehouse_names[0] if warehouse_names else None,
        )

        if not warehouse_names:
            st.warning("No SQL warehouses were discovered. Check your Databricks profile and workspace access.")

        warehouse_options = warehouse_names or ["No warehouse available"]
        catalog_options = load_catalogs() or ["No catalogs available"]

        selected_warehouse = st.selectbox(
            "SQL Warehouse",
            warehouse_options,
            index=(warehouse_options.index(default_warehouse_name) if default_warehouse_name and default_warehouse_name in warehouse_options else 0),
            disabled=not warehouse_names,
        )
        selected_catalog = st.selectbox(
            "Catalog",
            catalog_options,
            index=0,
            disabled=not catalog_options or catalog_options == ["No catalogs available"],
        )

        schema_options = load_schemas(selected_catalog) if selected_catalog != "No catalogs available" else ["No schemas available"]
        selected_schema = st.selectbox(
            "Schema",
            schema_options,
            index=0,
            disabled=not schema_options or schema_options == ["No schemas available"],
        )

        table_options = load_tables(selected_catalog, selected_schema) if selected_catalog != "No catalogs available" and selected_schema != "No schemas available" else ["No tables available"]
        selected_table = st.selectbox(
            "Table",
            table_options,
            index=0,
            disabled=not table_options or table_options == ["No tables available"],
        )

        if st.button("Profile", type="primary"):
            if not warehouse_names or selected_warehouse == "No warehouse available":
                st.error("No SQL Warehouse is available. Configure your Databricks workspace access first.")
            else:
                with st.spinner("Profiling in progress..."):
                    try:
                        connection = create_sql_connection(selected_warehouse, warehouses)
                        profiler = DataProfiler(connection, selected_catalog, selected_schema, selected_table)
                        result = profiler.profile()
                        st.session_state["profile_result"] = result
                        st.success("Profiling completed successfully")
                    except Exception as exc:  # pragma: no cover - runtime guard
                        logger.exception("Profiling failed: %s", exc)
                        st.error(f"Profiling failed: {exc}")

    if "profile_result" in st.session_state:

        st.markdown("---")

        left, right = st.columns([6, 2])

        with left:
            st.subheader("📊 Data Quality Assessment")

        with right:
            st.download_button(
                label="📄 Download Profiling Report",
                data=create_word_report(st.session_state["profile_result"]),
                file_name="Sigmatic_Data_Profiling_Report.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )

        render_dashboard(st.session_state["profile_result"])


if __name__ == "__main__":
    main()
