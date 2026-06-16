from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pipeline import PipelineConfig, run_pipeline
from query_plan import SelectionPayload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build CZML from database inputs.")
    parser.add_argument("db_name", help="Postgres/MySQL database name")
    parser.add_argument("repetition_count", type=int, help="Repetition count used by the legacy pipeline")
    parser.add_argument(
        "--selection-payload",
        default="{}",
        help="Selection payload JSON string. Defaults to empty object.",
    )
    parser.add_argument(
        "--selection-file",
        help="Path to a JSON file containing the selection payload.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Directory used for run artifacts, cache, and run history.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compile SQL and estimate rows without generating CZML.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable selection-hash cache.",
    )
    parser.add_argument(
        "--output",
        default="output.czml",
        help="Optional path to copy generated CZML output.",
    )
    return parser.parse_args()


def _load_selection_payload(args: argparse.Namespace) -> SelectionPayload:
    if args.selection_file:
        payload_text = Path(args.selection_file).read_text(encoding="utf-8")
    else:
        payload_text = args.selection_payload

    parsed: Any = json.loads(payload_text)
    if not isinstance(parsed, dict):
        raise ValueError("Selection payload must be a JSON object.")

    return parsed


def _copy_output_if_requested(result_czml_path: str | None, output_path: str) -> None:
    if not result_czml_path:
        return

    source = Path(result_czml_path)
    target = Path(output_path).resolve()
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> None:
    args = parse_args()
    payload = _load_selection_payload(args)

    config = PipelineConfig(
        db_name=args.db_name,
        repetition_count=args.repetition_count,
        artifacts_dir=Path(args.artifacts_dir),
        cache_enabled=not args.no_cache,
    )

    result = run_pipeline(selection_payload=payload, config=config, dry_run=args.dry_run)

    _copy_output_if_requested(result.czml_path, args.output)

    summary = {
        "run_id": result.run_id,
        "created_at": result.created_at,
        "used_cache": result.used_cache,
        "dry_run": result.dry_run,
        "selection_hash": result.selection_hash,
        "estimated_row_count": result.estimated_row_count,
        "artifact_dir": result.artifact_dir,
        "czml_path": result.czml_path,
        "validation_errors": list(result.validation_errors),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()