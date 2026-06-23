-- Aggregate entity counts by option/query name for one page and one color filter.
-- Parameters:
--   %(page_name)s      text
--   %(status_color)s   text
SELECT
    s.page_name,
    s.row_name,
    s.option_name,
    COUNT(DISTINCT e.entity_id) AS entity_count
FROM mock_entities e
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
