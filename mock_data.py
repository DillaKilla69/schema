#!/usr/bin/env python3
import argparse
import os
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.extras import execute_values

from page_definitions import PAGES


DDL = """
CREATE TABLE IF NOT EXISTS mock_pages (
    page_id BIGSERIAL PRIMARY KEY,
    page_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS mock_rows (
    row_id BIGSERIAL PRIMARY KEY,
    page_id BIGINT NOT NULL REFERENCES mock_pages(page_id) ON DELETE CASCADE,
    row_name TEXT NOT NULL,
    UNIQUE (page_id, row_name)
);

CREATE TABLE IF NOT EXISTS mock_options (
    option_id BIGSERIAL PRIMARY KEY,
    row_id BIGINT NOT NULL REFERENCES mock_rows(row_id) ON DELETE CASCADE,
    option_name TEXT NOT NULL,
    tag_value TEXT NOT NULL UNIQUE,
    UNIQUE (row_id, option_name)
);

CREATE TABLE IF NOT EXISTS mock_entities (
    entity_id BIGSERIAL PRIMARY KEY,
    entity_name TEXT NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    status_color TEXT NOT NULL CHECK (status_color IN ('red', 'blue'))
);

CREATE TABLE IF NOT EXISTS mock_entity_points (
    point_id BIGSERIAL PRIMARY KEY,
    entity_id BIGINT NOT NULL REFERENCES mock_entities(entity_id) ON DELETE CASCADE,
    ts TIMESTAMPTZ NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    height_m DOUBLE PRECISION NOT NULL,
    velocity DOUBLE PRECISION NOT NULL,
    heading_deg DOUBLE PRECISION NOT NULL,
    UNIQUE (entity_id, ts)
);

CREATE TABLE IF NOT EXISTS mock_entity_tags (
    entity_id BIGINT NOT NULL REFERENCES mock_entities(entity_id) ON DELETE CASCADE,
    option_id BIGINT NOT NULL REFERENCES mock_options(option_id) ON DELETE CASCADE,
    PRIMARY KEY (entity_id, option_id)
);

CREATE INDEX IF NOT EXISTS ix_mock_entities_status_color
    ON mock_entities (status_color);

CREATE INDEX IF NOT EXISTS ix_mock_entity_points_entity_ts
    ON mock_entity_points (entity_id, ts);

CREATE INDEX IF NOT EXISTS ix_mock_entity_tags_option_id
    ON mock_entity_tags (option_id);

DROP VIEW IF EXISTS mock_entity_selected_tags;

CREATE VIEW mock_entity_selected_tags AS
SELECT
    et.entity_id,
    p.page_name,
    r.row_name,
    o.option_name,
    o.tag_value
FROM mock_entity_tags et
JOIN mock_options o ON o.option_id = et.option_id
JOIN mock_rows r ON r.row_id = o.row_id
JOIN mock_pages p ON p.page_id = r.page_id;
"""


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print(database_url)
        return psycopg2.connect(database_url)

    missing = [
        name for name in ("PGDATABASE", "PGUSER", "PGPASSWORD")
        if not os.getenv(name)
    ]
    if missing:
        raise RuntimeError(
            "Set DATABASE_URL or PGDATABASE, PGUSER, PGPASSWORD "
            "(optionally PGHOST and PGPORT). Missing: " + ", ".join(missing)
        )

    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
    )


def upsert_page(cur, page_name):
    cur.execute(
        """
        INSERT INTO mock_pages (page_name)
        VALUES (%s)
        ON CONFLICT (page_name)
        DO UPDATE SET page_name = EXCLUDED.page_name
        RETURNING page_id
        """,
        (page_name,),
    )
    return cur.fetchone()[0]


def upsert_row(cur, page_id, row_name):
    cur.execute(
        """
        INSERT INTO mock_rows (page_id, row_name)
        VALUES (%s, %s)
        ON CONFLICT (page_id, row_name)
        DO UPDATE SET row_name = EXCLUDED.row_name
        RETURNING row_id
        """,
        (page_id, row_name),
    )
    return cur.fetchone()[0]


def upsert_option(cur, row_id, option_name, tag_value):
    cur.execute(
        """
        INSERT INTO mock_options (row_id, option_name, tag_value)
        VALUES (%s, %s, %s)
        ON CONFLICT (row_id, option_name)
        DO UPDATE SET tag_value = EXCLUDED.tag_value
        RETURNING option_id
        """,
        (row_id, option_name, tag_value),
    )
    return cur.fetchone()[0]


def seed_metadata(cur):
    option_lookup = {}
    page_count = 0
    row_count = 0
    option_count = 0

    for page in PAGES:
        page_id = upsert_page(cur, page.name)
        page_count += 1

        for row in page.rows:
            row_id = upsert_row(cur, page_id, row.name)
            row_count += 1

            for option_name in row.options:
                tag_value = f"{page.name}:{row.name}:{option_name}"
                option_id = upsert_option(cur, row_id, option_name, tag_value)
                option_lookup[(page.name, row.name, option_name)] = option_id
                option_count += 1

    return option_lookup, page_count, row_count, option_count


def seed_entities(cur, option_lookup, entity_count, points_per_entity):
    categories = ["air", "ground", "maritime", "cyber"]
    statuses = ["active", "idle", "maintenance"]
    now = datetime.now(timezone.utc).replace(microsecond=0)

    total_points = 0
    total_tags = 0

    all_rows = []
    for page in PAGES:
        for row in page.rows:
            all_rows.append((page.name, row.name, row.options))

    for entity_index in range(entity_count):
        entity_name = f"Mock Entity {entity_index + 1:03d}"
        category = categories[entity_index % len(categories)]
        status = statuses[entity_index % len(statuses)]
        status_color = "red" if entity_index % 2 == 0 else "blue"

        cur.execute(
            """
            INSERT INTO mock_entities (entity_name, category, status, status_color)
            VALUES (%s, %s, %s, %s)
            RETURNING entity_id
            """,
            (entity_name, category, status, status_color),
        )
        entity_id = cur.fetchone()[0]

        tag_rows = []
        for row_index, (page_name, row_name, options) in enumerate(all_rows):
            option_name = options[(entity_index + row_index) % len(options)]
            option_id = option_lookup[(page_name, row_name, option_name)]
            tag_rows.append((entity_id, option_id))

        execute_values(
            cur,
            """
            INSERT INTO mock_entity_tags (entity_id, option_id)
            VALUES %s
            ON CONFLICT DO NOTHING
            """,
            tag_rows,
        )
        total_tags += len(tag_rows)

        base_lat = 29.0 + (entity_index % 8) * 1.35
        base_lon = -108.0 - (entity_index % 8) * 1.15
        velocity = 110.0 + (entity_index % 5) * 8.0

        point_rows = []
        start_time = now - timedelta(minutes=points_per_entity * 5)

        for step in range(points_per_entity):
            ts = start_time + timedelta(minutes=step * 5, seconds=entity_index)
            lat = base_lat + step * 0.015 + entity_index * 0.001
            lon = base_lon - step * 0.015 - entity_index * 0.001
            height_m = 400.0 + entity_index * 12.0 + step * 4.0
            heading_deg = float((entity_index * 17 + step * 22) % 360)

            point_rows.append(
                (entity_id, ts, lat, lon, height_m, velocity, heading_deg)
            )

        execute_values(
            cur,
            """
            INSERT INTO mock_entity_points (
                entity_id, ts, lat, lon, height_m, velocity, heading_deg
            )
            VALUES %s
            ON CONFLICT (entity_id, ts) DO NOTHING
            """,
            point_rows,
        )
        total_points += len(point_rows)

    return total_tags, total_points


def maybe_reset(cur, reset):
    if not reset:
        return

    cur.execute(
        """
        TRUNCATE TABLE
            mock_entity_tags,
            mock_entity_points,
            mock_entities,
            mock_options,
            mock_rows,
            mock_pages
        RESTART IDENTITY CASCADE
        """
    )


def main():
    parser = argparse.ArgumentParser(description="Seed mock config and entity data.")
    parser.add_argument("--reset", action="store_true", help="Truncate mock tables first.")
    parser.add_argument("--entity-count", type=int, default=24, help="Number of mock entities.")
    parser.add_argument("--points-per-entity", type=int, default=16, help="Trajectory points per entity.")
    args = parser.parse_args()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(DDL)
            maybe_reset(cur, args.reset)
            option_lookup, page_count, row_count, option_count = seed_metadata(cur)
            tag_count, point_count = seed_entities(
                cur,
                option_lookup=option_lookup,
                entity_count=args.entity_count,
                points_per_entity=args.points_per_entity,
            )

        conn.commit()

    print("Seed complete")
    print(f"pages: {page_count}")
    print(f"rows: {row_count}")
    print(f"options: {option_count}")
    print(f"entities: {args.entity_count}")
    print(f"entity_tags: {tag_count}")
    print(f"entity_points: {point_count}")


if __name__ == "__main__":
    main()