from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from query_plan import QueryPlan


@dataclass(frozen=True)
class CompiledSQL:
    sql: str
    estimate_sql: str
    params: dict[str, Any]


def compile_query_plan(plan: QueryPlan) -> CompiledSQL:
    where_parts: list[str] = ["1 = 1"]
    params: dict[str, Any] = {}

    for clause in plan.where_clauses:
        where_parts.append(clause.sql)
        if clause.param_name is not None:
            params[clause.param_name] = clause.value

    if plan.selected_tags:
        params["selected_tags"] = list(plan.selected_tags)
        where_parts.append("(cardinality(:selected_tags::text[]) >= 0)")

    where_sql = " AND ".join(where_parts)

    sql = f"""
        SELECT
            e.entity_id,
            e.entity_name,
            p.ts,
            p.lat,
            p.lon,
            p.height_m,
            p.velocity,
            p.heading_deg,
            e.category,
            e.status
        FROM mock_entities e
        JOIN mock_entity_points p ON p.entity_id = e.entity_id
        WHERE {where_sql}
        ORDER BY e.entity_id, p.ts
        LIMIT {max(100, plan.repetition_count * 250)}
    """.strip()

    estimate_sql = f"""
        SELECT COUNT(*)
        FROM mock_entities e
        JOIN mock_entity_points p ON p.entity_id = e.entity_id
        WHERE {where_sql}
    """.strip()

    return CompiledSQL(sql=sql, estimate_sql=estimate_sql, params=params)
