from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_czml_file(czml_path: str) -> list[dict[str, Any]]:
    """Read CZML JSON file from disk."""
    return json.loads(Path(czml_path).read_text(encoding="utf-8"))


def render_cesium_viewer(czml_path: str | None, height: int = 700) -> str:
    """
    Render Cesium viewer HTML with injected CZML data.
    
    Args:
        czml_path: Path to the .czml.json file. If None, returns an error page.
        height: Height in pixels for the viewer container.
    
    Returns:
        HTML string safe for st.components.v1.html()
    """
    if not czml_path:
        return "<p style='color: red;'>No CZML data available. Run the pipeline first.</p>"

    czml_data = load_czml_file(czml_path)
    template_path = Path(__file__).parent / "templates" / "cesium.html"
    template_html = template_path.read_text(encoding="utf-8")

    czml_json = json.dumps(czml_data)
    injection_script = f"<script>window.CZML_DATA = {czml_json};</script>"

    html_with_data = template_html.replace("</head>", f"{injection_script}\n</head>")

    return html_with_data
