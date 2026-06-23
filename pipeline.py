from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pandas.core.frame import DataFrame
from pathlib import Path
import streamlit as st
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from query_plan import SelectionPayload, build_query_plan, validate_selection_payload
from sql_compiler import compile_query_plan
from sql_conn import query_db


RowExecutor = Callable[[str, dict[str, Any]], Sequence[Mapping[str, Any]]]


@dataclass(frozen=True)
class PipelineConfig:
    db_name: str
    repetition_count: int
    artifacts_dir: Path = Path("artifacts")
    cache_enabled: bool = True


@dataclass(frozen=True)
class PipelineResult:
    # run_id: str
    # created_at: str
    # db_name: str
    # repetition_count: int
    # selection_hash: str
    # dry_run: bool
    # validation_errors: tuple[str, ...]
    sql_text: str
    sql_params: dict[str, Any]
    # estimated_row_count: int
    # artifact_dir: str
    # used_cache: bool


# def _utc_now_iso() -> str:
#     return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


# def _canonical_json(value: Any) -> str:
#     return json.dumps(value, sort_keys=True, separators=(",", ":"))


# def _selection_hash(payload: SelectionPayload, config: PipelineConfig) -> str:
#     payload_blob = _canonical_json(payload)
#     key = f"{config.db_name}|{config.repetition_count}|{payload_blob}"
#     return sha256(key.encode("utf-8")).hexdigest()


# def _ensure_dirs(base: Path, selection_hash: str) -> tuple[Path, Path]:
#     run_id = uuid4().hex
#     run_dir = base / "runs" / run_id
#     cache_dir = base / "cache"
#     run_dir.mkdir(parents=True, exist_ok=True)
#     cache_dir.mkdir(parents=True, exist_ok=True)
#     return run_dir, cache_dir / f"{selection_hash}.json"


# def _init_history_db(base: Path) -> Path:
#     db_path = base / "run_history.sqlite"
#     conn = sqlite3.connect(db_path)
#     try:
#         conn.execute(
#             """
#             CREATE TABLE IF NOT EXISTS run_history (
#                 run_id TEXT PRIMARY KEY,
#                 created_at TEXT NOT NULL,
#                 db_name TEXT NOT NULL,
#                 repetition_count INTEGER NOT NULL,
#                 selection_hash TEXT NOT NULL,
#                 dry_run INTEGER NOT NULL,
#                 used_cache INTEGER NOT NULL,
#                 estimated_row_count INTEGER NOT NULL,
#                 artifact_dir TEXT NOT NULL
#             )
#             """
#         )
#         conn.commit()
#     finally:
#         conn.close()
#     return db_path


# def _insert_history_row(db_path: Path, result: PipelineResult) -> None:
#     conn = sqlite3.connect(db_path)
#     try:
#         conn.execute(
#             """
#             INSERT INTO run_history (
#                 run_id, created_at, db_name, repetition_count, selection_hash,
#                 dry_run, used_cache, estimated_row_count, artifact_dir
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#             """,
#             (
#                 result.run_id,
#                 result.created_at,
#                 result.db_name,
#                 result.repetition_count,
#                 result.selection_hash,
#                 int(result.dry_run),
#                 int(result.used_cache),
#                 result.estimated_row_count,
#                 result.artifact_dir,
#             ),
#         )
#         conn.commit()
#     finally:
#         conn.close()


# # def _write_json(path: Path, payload: Any) -> None:
# #     path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# def _estimate_row_count(repetition_count: int, tag_count: int) -> int:
#     return max(100, repetition_count * max(1, tag_count) * 20)


def _default_mock_executor(_: str, __: dict[str, Any]) -> Sequence[Mapping[str, Any]]:
    now = datetime.now(tz=timezone.utc)
    rows: list[dict[str, Any]] = []
    for entity_id in range(1, 6):
        for step in range(0, 12):
            rows.append(
                {
                    "entity_id": entity_id,
                    "entity_name": f"Entity {entity_id}",
                    "ts": now,
                    "lat": 30.0 + entity_id + (step * 0.01),
                    "lon": -110.0 - entity_id - (step * 0.01),
                    "height_m": 500.0 + (step * 5.0),
                    "velocity": 120.0,
                    "heading_deg": float((step * 12) % 360),
                    "category": "mock",
                    "status": "active",
                }
            )
    return rows


# def _load_cached_result(cache_file: Path) -> PipelineResult | None:
#     if not cache_file.exists():
#         return None

#     data = json.loads(cache_file.read_text(encoding="utf-8"))
#     return PipelineResult(
#         run_id=data["run_id"],
#         created_at=data["created_at"],
#         db_name=data["db_name"],
#         repetition_count=data["repetition_count"],
#         selection_hash=data["selection_hash"],
#         dry_run=data["dry_run"],
#         validation_errors=tuple(data.get("validation_errors", [])),
#         sql_text=data["sql_text"],
#         sql_params=data["sql_params"],
#         estimated_row_count=data["estimated_row_count"],
#         artifact_dir=data["artifact_dir"],
#         used_cache=True,
#     )


def run_pipeline(
    selection_payload: SelectionPayload,
    config: PipelineConfig,
    dry_run: bool = False,
    row_executor: RowExecutor | None = None,
) -> PipelineResult | DataFrame:
    """
    Validate selections, generate SQL artifacts, and optionally execute queries.

    The function is deterministic for a given payload/config pair and supports
    simple content-addressed caching via selection hash.
    """
    config = PipelineConfig(
        db_name=config.db_name,
        repetition_count=max(1, config.repetition_count),
        artifacts_dir=Path(config.artifacts_dir),
        cache_enabled=config.cache_enabled,
    )

    # config.artifacts_dir.mkdir(parents=True, exist_ok=True)
    # history_db = _init_history_db(config.artifacts_dir)
    # selection_hash = _selection_hash(selection_payload, config)
    # run_dir, cache_file = _ensure_dirs(config.artifacts_dir, selection_hash)

    # if config.cache_enabled and not dry_run:
    #     cached = _load_cached_result(cache_file)
    #     if cached is not None:
    #         cache_event = PipelineResult(
    #             run_id=uuid4().hex,
    #             created_at=_utc_now_iso(),
    #             db_name=cached.db_name,
    #             repetition_count=cached.repetition_count,
    #             selection_hash=cached.selection_hash,
    #             dry_run=cached.dry_run,
    #             validation_errors=cached.validation_errors,
    #             sql_text=cached.sql_text,
    #             sql_params=cached.sql_params,
    #             estimated_row_count=cached.estimated_row_count,
    #             artifact_dir=cached.artifact_dir,
    #             used_cache=True,
    #         )
    #         _insert_history_row(history_db, cache_event)
    #         return cache_event

    validation_errors = validate_selection_payload(selection_payload)
    plan = build_query_plan(selection_payload, repetition_count=config.repetition_count)
    compiled = compile_query_plan(plan)
    # estimated_rows = _estimate_row_count(config.repetition_count, len(plan.selected_tags))

    # created_at = _utc_now_iso()
    # run_id = run_dir.name

    rows: list[Mapping[str, Any]] = []
    if not dry_run:
        executor = row_executor or _default_mock_executor
        rows = list(executor(compiled.sql, compiled.params))
        # _write_json(run_dir / "query_rows.json", rows)

    # _write_json(run_dir / "selection_payload.json", selection_payload)
    # (run_dir / "compiled_query.sql").write_text(compiled.sql + "\n", encoding="utf-8")
    # _write_json(run_dir / "query_params.json", compiled.params)
    # _write_json(run_dir / "run_meta.json", {
    #     "run_id": run_id,
    #     "created_at": created_at,
    #     "db_name": config.db_name,
    #     "repetition_count": config.repetition_count,
    #     "selection_hash": selection_hash,
    #     "dry_run": dry_run,
    #     "estimated_row_count": estimated_rows,
    #     "validation_errors": validation_errors,
    # })

    result = PipelineResult(
        # run_id=run_id,
        # created_at=created_at,
        # db_name=config.db_name,
        # repetition_count=config.repetition_count,
        # selection_hash=selection_hash,
        # dry_run=dry_run,
        # validation_errors=tuple(validation_errors),
        sql_text=compiled.sql,
        sql_params=compiled.params,
        # estimated_row_count=estimated_rows,
        # artifact_dir=str(run_dir.resolve()),
        # used_cache=False,
    )

    query = query_db(sql=compiled.sql, params=compiled.params)

    # if config.cache_enabled and not dry_run:
    #     _write_json(cache_file, asdict(result))

    # _insert_history_row(history_db, result)
    # return result
    return query
