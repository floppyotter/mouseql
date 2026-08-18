-- Find attractions with the biggest changes in wait time

WITH wait_changes AS (
    SELECT
        attraction,
        recorded_at,
        wait_minutes,
        LAG(wait_minutes) OVER (
            PARTITION BY attraction
            ORDER BY recorded_at
        ) AS previous_wait
    FROM wait_times
    WHERE wait_minutes IS NOT NULL
),

changes AS (
    SELECT
        attraction,
        ABS(wait_minutes - previous_wait) AS wait_change
    FROM wait_changes
    WHERE previous_wait IS NOT NULL
)

SELECT
    attraction,
    ROUND(AVG(wait_change), 1) AS avg_change,
    MAX(wait_change) AS biggest_change,
    COUNT(*) AS observations
FROM changes
GROUP BY attraction
HAVING COUNT(*) >= 5
ORDER BY avg_change DESC;
