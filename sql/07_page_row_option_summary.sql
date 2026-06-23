-- Summarize the selected-tag space for a page, optionally restricted by color.
-- Parameters:
--   %(page_name)s      text
--   %(status_color)s   text
SELECT
    s.page_name,
    s.row_name,
    s.option_name,
    MIN(p.ts) AS first_point_ts,
    MAX(p.ts) AS last_point_ts,
    COUNT(DISTINCT e.entity_id) AS entity_count,
    COUNT(p.point_id) AS point_count,
    AVG(p.velocity) AS avg_velocity
FROM mock_entities e
JOIN mock_entity_points p
    ON p.entity_id = e.entity_id
JOIN mock_entity_selected_tags s
    ON s.entity_id = e.entity_id
WHERE s.page_name = %(page_name)s
  AND e.status_color = %(status_color)s
GROUP BY
    s.page_name,
    s.row_name,
    s.option_name
ORDER BY
    s.row_name,
    s.option_name;
