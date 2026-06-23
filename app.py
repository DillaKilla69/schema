import streamlit as st
import json
from pathlib import Path

from page_definitions import PAGES
from pipeline import PipelineConfig, run_pipeline
from schema import Page
from sql_conn import query_db
from state import (
    FILTER_OPTIONS,
    filter_key,
    options_key,
    init_page_state,
    export_state,
    import_state,
)


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def render_page(page: Page) -> None:
    """Render the 3-column table for a single page."""
    init_page_state(page)

    # Header
    h_name, h_filter, h_options = st.columns([2, 2, 4])
    h_name.markdown("**Name**")
    h_filter.markdown("**Filter**")
    h_options.markdown("**Options**")
    st.divider()

    for row in page.rows:
        col_name, col_filter, col_options = st.columns([2, 2, 4])

        col_name.write(row.name)

        col_filter.selectbox(
            label="Filter",
            options=FILTER_OPTIONS,
            key=filter_key(page.name, row.name),
            label_visibility="collapsed",
        )

        col_options.multiselect(
            label="Options",
            options=row.options,
            key=options_key(page.name, row.name),
            label_visibility="collapsed",
        )


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> Page:
    """Render navigation and state controls; return the selected Page."""
    st.sidebar.title("Navigation")

    page_names = [p.name for p in PAGES]
    selected_name = st.sidebar.radio(
        "Page",
        page_names,
        label_visibility="collapsed",
    )
    current_page = next(p for p in PAGES if p.name == selected_name)

    st.sidebar.divider()
    st.sidebar.subheader("State")

    st.sidebar.subheader("Pipeline")
    db_name = st.sidebar.text_input("Database name", value="mock_db")
    repetition_count = st.sidebar.number_input("Repetition count", min_value=1, max_value=500, value=4)
    dry_run = st.sidebar.checkbox("Dry run (no query execution)", value=False)
    enable_cache = st.sidebar.checkbox("Use cache", value=True)

    if st.sidebar.button("Run pipeline", use_container_width=True):
        payload = json.loads(export_state(PAGES))
        config = PipelineConfig(
            db_name=db_name,
            repetition_count=int(repetition_count),
            artifacts_dir=Path("artifacts"),
            cache_enabled=enable_cache,
        )
        result = run_pipeline(selection_payload=payload, config=config, dry_run=dry_run)
        st.session_state["_pipeline_result"] = {
            "run_id": result.run_id,
            "created_at": result.created_at,
            "db_name": result.db_name,
            "repetition_count": result.repetition_count,
            "used_cache": result.used_cache,
            "dry_run": result.dry_run,
            "selection_hash": result.selection_hash,
            "estimated_row_count": result.estimated_row_count,
            "artifact_dir": result.artifact_dir,
            "validation_errors": list(result.validation_errors),
            "sql_text": result.sql_text,
            "sql_params": result.sql_params,
        }
        st.dataframe(data=result)

    if st.sidebar.button("Export JSON", use_container_width=True):
        st.session_state["_export_payload"] = export_state(PAGES)

    # with st.sidebar.expander("Import JSON"):
    #     json_input = st.text_area("Paste exported JSON", height=200, label_visibility="collapsed")
    #     if st.button("Load state", use_container_width=True):
    #         try:
    #             import_state(json_input, PAGES)
    #             st.success("State loaded successfully.")
    #             st.rerun()
    #         except (ValueError, KeyError) as e:
    #             st.error(f"Invalid JSON: {e}")

    return current_page


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Config App", layout="wide")

    current_page = render_sidebar()

    st.title(current_page.name)
    render_page(current_page)

    # Show export payload if it was just generated
    if "_export_payload" in st.session_state:
        st.divider()
        st.subheader("Exported JSON")
        st.code(st.session_state.pop("_export_payload"), language="json")

    if "_pipeline_result" in st.session_state:
        pipeline_result = st.session_state["_pipeline_result"]
        st.divider()
        # st.subheader("Pipeline Result")
        # st.json(pipeline_result)
        st.caption("Compiled SQL")
        st.code(pipeline_result["sql_text"], language="sql")


if __name__ == "__main__":
    main()
