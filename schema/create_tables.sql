-- Initial tables for Magic Kingdom wait time data

CREATE TABLE parks (
    park_id INT PRIMARY KEY,
    park_name VARCHAR(100) NOT NULL
);

CREATE TABLE attractions (
    attraction_id INT PRIMARY KEY,
    park_id INT NOT NULL,
    attraction_name VARCHAR(150) NOT NULL,
    land_name VARCHAR(100),
    height_requirement_inches INT,
    FOREIGN KEY (park_id) REFERENCES parks(park_id)
);

CREATE TABLE wait_times (
    wait_id BIGINT PRIMARY KEY,
    attraction_id INT NOT NULL,
    recorded_at DATETIME NOT NULL,
    posted_wait_minutes INT,
    status VARCHAR(30),
    FOREIGN KEY (attraction_id) REFERENCES attractions(attraction_id)
);