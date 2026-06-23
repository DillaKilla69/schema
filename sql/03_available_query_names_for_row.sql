-- List available option names for a given page/row pair.
-- Useful when mapping UI row context to valid query names.
-- Parameters:
--   %(page_name)s  text
--   %(row_name)s   text
SELECT
    p.page_name,
    r.row_name,
    o.option_name,
    o.tag_value
FROM mock_pages p
JOIN mock_rows r
    ON r.page_id = p.page_id
JOIN mock_options o
    ON o.row_id = r.row_id
WHERE p.page_name = %(page_name)s
  AND r.row_name = %(row_name)s
ORDER BY o.option_name;
