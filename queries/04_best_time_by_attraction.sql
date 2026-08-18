-- Find the lowest average wait hour for each attraction

WITH hourly_waits AS (
    SELECT
        attraction,
        CAST(strftime('%H', recorded_at, 'localtime') AS INTEGER) AS hour_of_day,
        ROUND(AVG(wait_minutes), 1) AS avg_wait,
        COUNT(*) AS observations
    FROM wait_times
    WHERE wait_minutes IS NOT NULL
    GROUP BY attraction, hour_of_day
),

ranked AS (
    SELECT
        attraction,
        hour_of_day,
        avg_wait,
        observations,
        ROW_NUMBER() OVER (
            PARTITION BY attraction
            ORDER BY avg_wait
        ) AS wait_rank
    FROM hourly_waits
)

SELECT
    attraction,
    hour_of_day AS best_hour,
    avg_wait,
    observations
FROM ranked
WHERE wait_rank = 1
ORDER BY attraction;
