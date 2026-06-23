-- Return distinct entities that match one page/row selection and a chosen color filter.
-- Parameters:
--   :page_name    text
--   :row_name      text
--   :status_color  text
SELECT DISTINCT
    e.entity_id,
    e.entity_name,
    e.category,
    e.status,
    e.status_color,
    s.page_name,
    s.row_name,
    s.option_name,
    s.tag_value
FROM mock_entities e
JOIN mock_entity_selected_tags s
    ON s.entity_id = e.entity_id
WHERE s.page_name = :page_name
  AND s.row_name = :row_name
  AND e.status_color = :status_color
ORDER BY e.entity_name;
