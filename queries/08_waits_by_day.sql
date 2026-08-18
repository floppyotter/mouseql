-- Average wait times by day of week
-- Convert UTC timestamps to Eastern time

WITH local_waits AS (
    SELECT
        wait_minutes,
        datetime(recorded_at, 'localtime') AS local_recorded_at
    FROM wait_times
    WHERE wait_minutes IS NOT NULL
)

SELECT
    CASE strftime('%w', local_recorded_at)
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END AS day_of_week,

    ROUND(AVG(wait_minutes), 1) AS avg_wait,
    MIN(wait_minutes) AS min_wait,
    MAX(wait_minutes) AS max_wait,
    COUNT(*) AS observations

FROM local_waits

GROUP BY strftime('%w', local_recorded_at)

ORDER BY CAST(strftime('%w', local_recorded_at) AS INTEGER);
