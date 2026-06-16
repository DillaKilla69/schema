from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict

_ALLOWED_FILTERS: tuple[str, ...] = ("all", "none", "red", "blue")


class SelectionRow(TypedDict):
    filter: str
    selections: list[str]


SelectionPayload = dict[str, dict[str, SelectionRow]]


@dataclass(frozen=True)
class WhereClause:
    sql: str
    param_name: str | None = None
    value: Any | None = None


@dataclass(frozen=True)
class QueryPlan:
    where_clauses: tuple[WhereClause, ...]
    selected_tags: tuple[str, ...]
    repetition_count: int


def validate_selection_payload(payload: SelectionPayload) -> list[str]:
    errors: list[str] = []

    for page_name, rows in payload.items():
        if not isinstance(rows, dict):
            errors.append(f"Page '{page_name}' must map to a dictionary of rows.")
            continue

        for row_name, row_state in rows.items():
            if not isinstance(row_state, dict):
                errors.append(f"Row '{page_name}/{row_name}' must be an object.")
                continue

            row_filter = row_state.get("filter")
            selections = row_state.get("selections")

            if row_filter not in _ALLOWED_FILTERS:
                errors.append(
                    f"Row '{page_name}/{row_name}' has invalid filter '{row_filter}'. "
                    f"Allowed values: {_ALLOWED_FILTERS}."
                )

            if not isinstance(selections, list) or any(not isinstance(item, str) for item in selections):
                errors.append(f"Row '{page_name}/{row_name}' selections must be a list of strings.")

    return errors


def build_query_plan(payload: SelectionPayload, repetition_count: int) -> QueryPlan:
    where_clauses: list[WhereClause] = []
    selected_tags: list[str] = []
    color_param_index = 0

    for page_name, rows in payload.items():
        for row_name, row_state in rows.items():
            row_filter = row_state["filter"]
            selections = row_state["selections"]

            if row_filter == "none":
                # 'none' means this row should contribute no entities.
                where_clauses.append(WhereClause(sql="1 = 0"))
            elif row_filter in ("red", "blue"):
                param_name = f"status_color_{color_param_index}"
                color_param_index += 1
                where_clauses.append(
                    WhereClause(
                        sql=f"e.status_color = :{param_name}",
                        param_name=param_name,
                        value=row_filter,
                    )
                )

            for item in selections:
                selected_tags.append(f"{page_name}:{row_name}:{item}")

    # Keep plan deterministic for caching.
    selected_tags = sorted(set(selected_tags))

    return QueryPlan(
        where_clauses=tuple(where_clauses),
        selected_tags=tuple(selected_tags),
        repetition_count=max(1, repetition_count),
    )
