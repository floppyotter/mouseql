# MOUSEQL

A SQL project using Walt Disney World attraction wait-time data.

I built this project to collect Magic Kingdom wait times over time and use SQL to look for patterns in the data. The database is updated automatically throughout the day, so the analysis gets more useful as more data is collected.

## What it does

MOUSEQL collects current attraction wait times and stores them in a SQLite database.

The SQL queries look at things like:

- average wait times
- highest and lowest wait attractions
- wait times by hour
- wait times by day of the week
- best observed time for each attraction
- best observed time for an attraction on a specific day
- large drops in posted wait times
- attractions with the most wait-time changes

There is also an automatically generated Magic Kingdom report that summarizes the current dataset.

## How it works

The project uses:

- Python for collecting and processing wait-time data
- SQLite for storing the data
- SQL for the analysis
- GitHub Actions for automatic data collection and running the analysis

Wait-time data is collected on a schedule and added to the database. The analysis queries can then be run against everything collected so far.

## SQL analysis

The `queries` folder contains the SQL used for the project.

Current queries include:

1. Data checks
2. Wait-time summary
3. Wait times by hour
4. Best time by attraction
5. Attraction comparison
6. Wait-time drops
7. Wait-time volatility
8. Wait times by day of week
9. Wait times by day and hour
10. Best attraction time by day

Some of the analysis uses CTEs and window functions to rank wait times and compare observations.

## Reports

The latest generated Magic Kingdom report is available here:

[View the Magic Kingdom Wait Time Report](reports/magic_kingdom_report.md)

The report is regenerated from the latest data and includes current wait-time analysis and dataset statistics.

## Data

This is an ongoing dataset.

Early results are based on a small number of observations and shouldn't be treated as established park trends yet. As the collector continues running, the historical comparisons should become more useful.

## Why I built it

I work with SQL regularly and wanted a project where I could use it on something I was actually interested in.

Disney wait times gave me a dataset that changes constantly and plenty of questions to answer with SQL, so I started collecting the data instead of working from a static sample dataset.
