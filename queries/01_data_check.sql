-- Check how much data has been collected

SELECT COUNT(*) AS total_records
FROM wait_times;


-- See which attractions are in the dataset

SELECT DISTINCT attraction
FROM wait_times
ORDER BY attraction;