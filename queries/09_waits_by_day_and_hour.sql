-- Average wait times by day of week and hour

SELECT
    CASE strftime('%w', recorded_at)
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END AS day_of_week,

    CAST(strftime('%H', recorded_at) AS INTEGER) AS hour_of_day,

    ROUND(AVG(wait_minutes), 1) AS avg_wait,

    MIN(wait_minutes) AS min_wait,

    MAX(wait_minutes) AS max_wait,

    COUNT(*) AS observations

FROM wait_times

WHERE wait_minutes IS NOT NULL

GROUP BY
    strftime('%w', recorded_at),
    strftime('%H', recorded_at)

ORDER BY
    CAST(strftime('%w', recorded_at) AS INTEGER),
    hour_of_day;
