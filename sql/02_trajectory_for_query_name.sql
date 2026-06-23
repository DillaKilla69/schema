-- Return trajectory points for one selected query/option name.
-- Parameters:
--   %(tag_value)s      text
--   %(status_color)s   text
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
ORDER BY e.entity_id, p.ts;
