-- Tables for Magic Kingdom wait time analysis

CREATE TABLE attractions (
    attraction_id INT AUTO_INCREMENT PRIMARY KEY,
    attraction_name VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE wait_times (
    wait_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    attraction_id INT NOT NULL,
    recorded_at DATETIME NOT NULL,
    wait_minutes INT,
    status VARCHAR(30),
    lightning_lane_cents INT,
    FOREIGN KEY (attraction_id)
        REFERENCES attractions(attraction_id)
);