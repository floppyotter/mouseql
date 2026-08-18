-- Quick look at wait times by attraction

SELECT
    attraction,
    COUNT(*) AS observations,
    ROUND(AVG(wait_minutes), 1) AS avg_wait,
    MIN(wait_minutes) AS min_wait,
    MAX(wait_minutes) AS max_wait
FROM wait_times
WHERE wait_minutes IS NOT NULL
GROUP BY attraction
ORDER BY avg_wait DESC;
