-- Compare wait times across attractions

SELECT
    attraction,
    ROUND(AVG(wait_minutes), 1) AS avg_wait,
    MIN(wait_minutes) AS shortest_wait,
    MAX(wait_minutes) AS longest_wait,
    COUNT(*) AS observations
FROM wait_times
WHERE wait_minutes IS NOT NULL
GROUP BY attraction
HAVING COUNT(*) >= 5
ORDER BY avg_wait DESC;
