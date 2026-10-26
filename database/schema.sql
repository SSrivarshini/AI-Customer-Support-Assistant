CREATE DATABASE IF NOT EXISTS support_db;
USE support_db;

CREATE TABLE IF NOT EXISTS orders (
    order_id          VARCHAR(20) PRIMARY KEY,
    customer_name     VARCHAR(100) NOT NULL,
    product_name      VARCHAR(150) NOT NULL,
    status            ENUM('processing','shipped','out_for_delivery','delivered','cancelled') NOT NULL,
    order_date        DATE NOT NULL,
    expected_delivery DATE NOT NULL,
    carrier           VARCHAR(50),
    tracking_number   VARCHAR(50),
    last_location     VARCHAR(100),
    last_update       DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_requests (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    order_id      VARCHAR(20) NOT NULL,
    issue_type    ENUM('damaged','delayed','wrong_item','other') NOT NULL,
    description   TEXT,
    assigned_team VARCHAR(50) NOT NULL,
    priority      ENUM('low','medium','high') NOT NULL,
    status        ENUM('open','in_progress','resolved') DEFAULT 'open',
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
