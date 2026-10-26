USE support_db;

INSERT INTO orders (order_id, customer_name, product_name, status, order_date, expected_delivery, carrier, tracking_number, last_location) VALUES
('ORD1001','Anita','Wireless Mouse','shipped','2026-10-18','2026-10-27','BlueDart','BD556677','Coimbatore Hub'),
('ORD1002','Ravi','Bluetooth Speaker','out_for_delivery','2026-10-20','2026-10-26','Delhivery','DL998811','Local Delivery Station'),
('ORD1003','Meena','Office Chair','delivered','2026-10-10','2026-10-16','DTDC','DT123456','Delivered'),
('ORD1004','Karthik','Laptop Stand','shipped','2026-10-08','2026-10-15','BlueDart','BD776655','Chennai Hub'),
('ORD1005','Divya','Running Shoes','processing','2026-10-25','2026-11-01',NULL,NULL,'Warehouse');
