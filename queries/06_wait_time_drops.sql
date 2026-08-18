-- Find significant drops in posted wait times

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
)

SELECT
    attraction,
    recorded_at,
    previous_wait,
    wait_minutes,
    previous_wait - wait_minutes AS wait_drop
FROM wait_changes
WHERE previous_wait - wait_minutes >= 15
ORDER BY wait_drop DESC;
