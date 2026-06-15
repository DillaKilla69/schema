import streamlit as st

from page_definitions import PAGES
from schema import Page
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

    if st.sidebar.button("Export JSON", use_container_width=True):
        st.session_state["_export_payload"] = export_state(PAGES)

    with st.sidebar.expander("Import JSON"):
        json_input = st.text_area("Paste exported JSON", height=200, label_visibility="collapsed")
        if st.button("Load state", use_container_width=True):
            try:
                import_state(json_input, PAGES)
                st.success("State loaded successfully.")
                st.rerun()
            except (ValueError, KeyError) as e:
                st.error(f"Invalid JSON: {e}")

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


if __name__ == "__main__":
    main()
