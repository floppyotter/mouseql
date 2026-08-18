-- Average wait by hour of day
-- Uses Eastern time for Walt Disney World

SELECT
    CAST(strftime('%H', recorded_at, 'localtime') AS INTEGER) AS hour_of_day,
    ROUND(AVG(wait_minutes), 1) AS avg_wait,
    MIN(wait_minutes) AS min_wait,
    MAX(wait_minutes) AS max_wait,
    COUNT(*) AS observations
FROM wait_times
WHERE wait_minutes IS NOT NULL
GROUP BY hour_of_day
ORDER BY hour_of_day;
