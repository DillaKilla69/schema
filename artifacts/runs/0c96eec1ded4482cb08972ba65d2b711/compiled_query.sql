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
        JOIN mock_entity_points p ON p.entity_id = e.entity_id
        WHERE 1 = 1 AND 1 = 0 AND e.status_color = :status_color_0 AND e.status_color = :status_color_1 AND (cardinality(:selected_tags::text[]) >= 0)
        ORDER BY e.entity_id, p.ts
        LIMIT 1000
