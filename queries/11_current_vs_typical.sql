-- Compare the latest wait for each attraction
-- with its average wait at the same hour

WITH local_waits AS (
    SELECT
        attraction,
        wait_minutes,
        recorded_at,
        datetime(recorded_at, 'localtime') AS local_recorded_at
    FROM wait_times
    WHERE wait_minutes IS NOT NULL
),

latest_time AS (
    SELECT
        MAX(recorded_at) AS latest_recorded_at
    FROM local_waits
),

latest_waits AS (
    SELECT
        l.attraction,
        l.wait_minutes AS current_wait,
        CAST(strftime('%H', l.local_recorded_at) AS INTEGER) AS current_hour
    FROM local_waits l
    JOIN latest_time t
        ON l.recorded_at = t.latest_recorded_at
),

typical_waits AS (
    SELECT
        attraction,
        CAST(strftime('%H', local_recorded_at) AS INTEGER) AS hour_of_day,
        ROUND(AVG(wait_minutes), 1) AS typical_wait,
        COUNT(*) AS observations
    FROM local_waits
    GROUP BY
        attraction,
        hour_of_day
)

SELECT
    l.attraction,
    l.current_hour,
    l.current_wait,
    t.typical_wait,
    ROUND(l.current_wait - t.typical_wait, 1) AS difference,
    t.observations,

    CASE
        WHEN l.current_wait <= t.typical_wait - 10
            THEN 'Below typical'
        WHEN l.current_wait >= t.typical_wait + 10
            THEN 'Above typical'
        ELSE 'Near typical'
    END AS wait_status

FROM latest_waits l

JOIN typical_waits t
    ON l.attraction = t.attraction
    AND l.current_hour = t.hour_of_day

ORDER BY
    difference ASC;
