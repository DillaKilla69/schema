"""
State management helpers.

State is stored entirely in st.session_state using widget keys.
Each widget key is namespaced by page and row name, so keys never collide.

Key helpers are centralised here so the renderer and export/import
both use the exact same key format.
"""

import json
import streamlit as st
from schema import Page

FILTER_OPTIONS: tuple[str, ...] = ("all", "none", "red", "blue")
_DEFAULT_FILTER = "all"
_DEFAULT_SELECTIONS: list[str] = []


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

def filter_key(page_name: str, row_name: str) -> str:
    return f"filter__{page_name}__{row_name}"


def options_key(page_name: str, row_name: str) -> str:
    return f"options__{page_name}__{row_name}"


# ---------------------------------------------------------------------------
# State initialisation (lazy, called on first page visit)
# ---------------------------------------------------------------------------

def init_page_state(page: Page) -> None:
    """Set default values for any row that has not been visited yet."""
    for row in page.rows:
        fk = filter_key(page.name, row.name)
        ok = options_key(page.name, row.name)
        if fk not in st.session_state:
            st.session_state[fk] = _DEFAULT_FILTER
        if ok not in st.session_state:
            st.session_state[ok] = list(_DEFAULT_SELECTIONS)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_state(pages: tuple[Page, ...]) -> str:
    """Return current session state for all pages as a JSON string."""
    result: dict = {}
    for page in pages:
        result[page.name] = {}
        for row in page.rows:
            result[page.name][row.name] = {
                "filter": st.session_state.get(filter_key(page.name, row.name), _DEFAULT_FILTER),
                "selections": st.session_state.get(options_key(page.name, row.name), list(_DEFAULT_SELECTIONS)),
            }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Import / restore
# ---------------------------------------------------------------------------

def import_state(json_str: str, pages: tuple[Page, ...]) -> None:
    """
    Load state from a JSON string into st.session_state.
    Unknown pages or rows are silently ignored.
    """
    data: dict = json.loads(json_str)
    page_map = {p.name: p for p in pages}

    for page_name, rows in data.items():
        if page_name not in page_map:
            continue
        page = page_map[page_name]
        row_map = {r.name: r for r in page.rows}

        for row_name, row_state in rows.items():
            if row_name not in row_map:
                continue
            row = row_map[row_name]

            incoming_filter = row_state.get("filter", _DEFAULT_FILTER)
            incoming_selections = row_state.get("selections", list(_DEFAULT_SELECTIONS))

            # Validate incoming values against known options
            if incoming_filter not in FILTER_OPTIONS:
                incoming_filter = _DEFAULT_FILTER
            incoming_selections = [s for s in incoming_selections if s in row.options]

            st.session_state[filter_key(page_name, row_name)] = incoming_filter
            st.session_state[options_key(page_name, row_name)] = incoming_selections
