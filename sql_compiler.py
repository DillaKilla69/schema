from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from query_plan import QueryPlan


@dataclass(frozen=True)
class CompiledSQL:
    sql: str
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

    sql_dir = Path("sql")
    sql_files = {
        sql_file.stem: sql_file.read_text(encoding="utf-8")
        for sql_file in sql_dir.glob("*.sql")
    }

    return CompiledSQL(sql=sql_files["01_entities_for_row_filter"], params=params)
