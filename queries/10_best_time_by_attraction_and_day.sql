-- Best hour for each attraction by day of week
-- Times are converted from UTC to Eastern time

WITH local_waits AS (
    SELECT
        attraction,
        wait_minutes,
        datetime(recorded_at, 'localtime') AS local_recorded_at
    FROM wait_times
    WHERE wait_minutes IS NOT NULL
),

hourly_waits AS (
    SELECT
        attraction,
        strftime('%w', local_recorded_at) AS day_number,
        CAST(strftime('%H', local_recorded_at) AS INTEGER) AS hour_of_day,
        ROUND(AVG(wait_minutes), 1) AS avg_wait,
        COUNT(*) AS observations
    FROM local_waits
    GROUP BY
        attraction,
        day_number,
        hour_of_day
),

ranked AS (
    SELECT
        attraction,
        day_number,
        hour_of_day,
        avg_wait,
        observations,
        ROW_NUMBER() OVER (
            PARTITION BY attraction, day_number
            ORDER BY avg_wait, hour_of_day
        ) AS wait_rank
    FROM hourly_waits
)

SELECT
    attraction,

    CASE day_number
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END AS day_of_week,

    hour_of_day AS best_hour,
    avg_wait,
    observations

FROM ranked

WHERE wait_rank = 1

ORDER BY
    attraction,
    CAST(day_number AS INTEGER);
