-- Get the latest known position for each entity matching one selected query/option.
-- Parameters:
--   %(tag_value)s      text
--   %(status_color)s   text
WITH ranked_points AS (
    SELECT
        e.entity_id,
        e.entity_name,
        e.category,
        e.status,
        p.ts,
        p.lat,
        p.lon,
        p.height_m,
        p.velocity,
        p.heading_deg,
        ROW_NUMBER() OVER (
            PARTITION BY e.entity_id
            ORDER BY p.ts DESC
        ) AS point_rank
    FROM mock_entities e
    JOIN mock_entity_points p
        ON p.entity_id = e.entity_id
    JOIN mock_entity_selected_tags s
        ON s.entity_id = e.entity_id
    WHERE s.tag_value = %(tag_value)s
      AND e.status_color = %(status_color)s
)
SELECT
    entity_id,
    entity_name,
    category,
    status,
    ts,
    lat,
    lon,
    height_m,
    velocity,
    heading_deg
FROM ranked_points
WHERE point_rank = 1
ORDER BY entity_name;
