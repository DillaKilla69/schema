-- Return trajectory points for one query/option inside a time window.
-- Parameters:
--   %(tag_value)s      text
--   %(status_color)s   text
--   %(start_ts)s       timestamptz
--   %(end_ts)s         timestamptz
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
JOIN mock_entity_points p
    ON p.entity_id = e.entity_id
JOIN mock_entity_selected_tags s
    ON s.entity_id = e.entity_id
WHERE s.tag_value = %(tag_value)s
  AND e.status_color = %(status_color)s
  AND p.ts >= %(start_ts)s
  AND p.ts < %(end_ts)s
ORDER BY e.entity_id, p.ts;
