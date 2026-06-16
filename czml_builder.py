from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any, Mapping, Sequence


def _to_iso8601(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return str(value)


def _build_position_cartographic(points: list[Mapping[str, Any]]) -> list[float]:
    if not points:
        return []

    first_ts = _to_iso8601(points[0]["ts"])
    start_dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
    cartographic: list[float] = []

    for row in points:
        row_ts = _to_iso8601(row["ts"])
        row_dt = datetime.fromisoformat(row_ts.replace("Z", "+00:00"))
        offset_seconds = (row_dt - start_dt).total_seconds()
        cartographic.extend([offset_seconds, float(row["lon"]), float(row["lat"]), float(row["height_m"])])

    return cartographic


def build_czml(rows: Sequence[Mapping[str, Any]], document_name: str = "Pipeline Output") -> list[dict[str, Any]]:
    grouped: dict[int, list[Mapping[str, Any]]] = defaultdict(list)

    for row in rows:
        grouped[int(row["entity_id"])].append(row)

    packets: list[dict[str, Any]] = [
        {
            "id": "document",
            "name": document_name,
            "version": "1.0",
        }
    ]

    for entity_id, points in grouped.items():
        points = sorted(points, key=lambda item: _to_iso8601(item["ts"]))
        if not points:
            continue

        start = _to_iso8601(points[0]["ts"])
        end = _to_iso8601(points[-1]["ts"])
        entity_name = str(points[0].get("entity_name", f"Entity {entity_id}"))

        packets.append(
            {
                "id": str(entity_id),
                "name": entity_name,
                "availability": f"{start}/{end}",
                "label": {
                    "text": entity_name,
                    "font": "12pt sans-serif",
                    "horizontalOrigin": "LEFT",
                    "pixelOffset": {"cartesian2": [10, 0]},
                },
                "position": {
                    "epoch": start,
                    "cartographicDegrees": _build_position_cartographic(points),
                },
                "path": {
                    "show": True,
                    "width": 2,
                    "material": {
                        "solidColor": {
                            "color": {"rgba": [0, 255, 255, 255]}
                        }
                    },
                },
            }
        )

    return packets
