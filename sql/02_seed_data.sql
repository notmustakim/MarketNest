-- Synthetic deterministic sample data for MarketNest coursework.
USE marketnest;

INSERT INTO customers (customer_id, full_name, email, phone, password_hash, registered_on, status) VALUES
  (1, 'Amina Rahman', 'customer01@example.test', '+8801700000001', 'pbkdf2_sha256$210000$MNsalt0001$XEcloaZDnDtiSUS8x+kxdmfuTp0VaoC1dn5Qz38sxtY=', '2026-01-11 09:00:00', 'Active'),
  (2, 'Rafi Ahmed', 'customer02@example.test', '+8801700000002', 'pbkdf2_sha256$210000$MNsalt0002$r4J9gbB7guOua7rKwbM3s2vEfV4ajyCUh6cfAyDJfuE=', '2026-01-12 09:00:00', 'Active'),
  (3, 'Nadia Islam', 'customer03@example.test', '+8801700000003', 'pbkdf2_sha256$210000$MNsalt0003$8qI+LOagrolOZUAIGEFsaLlwreMBSOa5zMciJ0dajpk=', '2026-01-13 09:00:00', 'Active'),
  (4, 'Samiul Hasan', 'customer04@example.test', '+8801700000004', 'pbkdf2_sha256$210000$MNsalt0004$7ZK9mvh4+vluA0kLQB+4r9/jF6tQd8PfsuSIom1KbuY=', '2026-01-14 09:00:00', 'Active'),
  (5, 'Tasnim Akter', 'customer05@example.test', '+8801700000005', 'pbkdf2_sha256$210000$MNsalt0005$jboKePPlCRjdz79ngGu+5HT9/MlUAGNjAnoVtMgNdq8=', '2026-01-15 09:00:00', 'Active'),
  (6, 'Farhan Kabir', 'customer06@example.test', '+8801700000006', 'pbkdf2_sha256$210000$MNsalt0006$bP00iNxA0QC3eNnr2rJWCtEhmtlYNoFzizNnjdSjrao=', '2026-01-16 09:00:00', 'Active'),
  (7, 'Jannat Chowdhury', 'customer07@example.test', '+8801700000007', 'pbkdf2_sha256$210000$MNsalt0007$FfDT0lWILkhJPlCQuURSa/hGf9dLTI67MCQlEORGrI0=', '2026-01-17 09:00:00', 'Active'),
  (8, 'Adnan Hossain', 'customer08@example.test', '+8801700000008', 'pbkdf2_sha256$210000$MNsalt0008$tipzanjDD0I0rJ4xDj8Le+7BFZLhbG7N6akOfFrE63o=', '2026-01-18 09:00:00', 'Active'),
  (9, 'Maliha Karim', 'customer09@example.test', '+8801700000009', 'pbkdf2_sha256$210000$MNsalt0009$ROqzj87VLAIrXIUJ8ww4/mCl/bBcOTBbBFzwHt03zZY=', '2026-01-19 09:00:00', 'Active'),
  (10, 'Imran Sarker', 'customer10@example.test', '+8801700000010', 'pbkdf2_sha256$210000$MNsalt0010$T7ubSu9MuKyvQVcxLGBTlEyK3G5GVev1TOpErwWirC0=', '2026-01-20 09:00:00', 'Suspended');

INSERT INTO addresses (customer_id, address_no, label, street_line, city, postal_code, country, is_default) VALUES
  (1, 1, 'Home', '12 Lake Road', 'Dhaka', '1001', 'Bangladesh', 1),
  (2, 1, 'Home', '24 Lake Road', 'Rajshahi', '1002', 'Bangladesh', 1),
  (3, 1, 'Home', '36 Lake Road', 'Chattogram', '1003', 'Bangladesh', 1),
  (4, 1, 'Home', '48 Lake Road', 'Sylhet', '1004', 'Bangladesh', 1),
  (5, 1, 'Home', '60 Lake Road', 'Khulna', '1005', 'Bangladesh', 1),
  (6, 1, 'Home', '72 Lake Road', 'Barishal', '1006', 'Bangladesh', 1),
  (7, 1, 'Home', '84 Lake Road', 'Rangpur', '1007', 'Bangladesh', 1),
  (8, 1, 'Home', '96 Lake Road', 'Mymensingh', '1008', 'Bangladesh', 1),
  (9, 1, 'Home', '108 Lake Road', 'Cumilla', '1009', 'Bangladesh', 1),
  (10, 1, 'Home', '120 Lake Road', 'Narayanganj', '1010', 'Bangladesh', 1),
  (1, 2, 'Office', '8 Central Avenue', 'Dhaka', '1201', 'Bangladesh', 0),
  (2, 2, 'Office', '16 Central Avenue', 'Dhaka', '1202', 'Bangladesh', 0),
  (3, 2, 'Office', '24 Central Avenue', 'Dhaka', '1203', 'Bangladesh', 0),
  (4, 2, 'Office', '32 Central Avenue', 'Dhaka', '1204', 'Bangladesh', 0),
  (5, 2, 'Office', '40 Central Avenue', 'Dhaka', '1205', 'Bangladesh', 0);

INSERT INTO sellers (seller_id, store_name, email, phone, tax_id, commission_rate, joined_on, status) VALUES
  (1, 'MarketNest Seller 01', 'seller01@example.test', '+8801800000001', 'TAX-MN-0001', 6, '2026-01-01 10:00:00', 'Active'),
  (2, 'MarketNest Seller 02', 'seller02@example.test', '+8801800000002', 'TAX-MN-0002', 7, '2026-01-02 10:00:00', 'Active'),
  (3, 'MarketNest Seller 03', 'seller03@example.test', '+8801800000003', 'TAX-MN-0003', 8, '2026-01-03 10:00:00', 'Active'),
  (4, 'MarketNest Seller 04', 'seller04@example.test', '+8801800000004', 'TAX-MN-0004', 9, '2026-01-04 10:00:00', 'Active'),
  (5, 'MarketNest Seller 05', 'seller05@example.test', '+8801800000005', 'TAX-MN-0005', 10, '2026-01-05 10:00:00', 'Active'),
  (6, 'MarketNest Seller 06', 'seller06@example.test', '+8801800000006', 'TAX-MN-0006', 11, '2026-01-06 10:00:00', 'Active'),
  (7, 'MarketNest Seller 07', 'seller07@example.test', '+8801800000007', 'TAX-MN-0007', 12, '2026-01-07 10:00:00', 'Active'),
  (8, 'MarketNest Seller 08', 'seller08@example.test', '+8801800000008', 'TAX-MN-0008', 13, '2026-01-08 10:00:00', 'Active'),
  (9, 'MarketNest Seller 09', 'seller09@example.test', '+8801800000009', 'TAX-MN-0009', 14, '2026-01-09 10:00:00', 'Active'),
  (10, 'MarketNest Seller 10', 'seller10@example.test', '+8801800000010', 'TAX-MN-0010', 15, '2026-01-10 10:00:00', 'Pending');

INSERT INTO categories (category_id, category_name, parent_category_id) VALUES
  (1, 'Electronics', NULL),
  (2, 'Home and Living', NULL),
  (3, 'Fashion', NULL),
  (4, 'Phones', 1),
  (5, 'Audio', 1),
  (6, 'Kitchen', 2),
  (7, 'Decor', 2),
  (8, 'Clothing', 3),
  (9, 'Bags', 3),
  (10, 'Computer Accessories', 1),
  (11, 'Storage', 2),
  (12, 'Footwear', 3);

INSERT INTO products (product_id, seller_id, category_id, product_name, description, brand_name, status, created_at) VALUES
  (1, 1, 1, 'Wireless Speaker 01', 'Synthetic demo listing 01 for database testing.', 'Brand 01', 'Active', '2026-02-02 09:00:00'),
  (2, 2, 2, 'Desk Lamp 02', 'Synthetic demo listing 02 for database testing.', 'Brand 02', 'Active', '2026-02-03 09:00:00'),
  (3, 3, 3, 'Travel Backpack 03', 'Synthetic demo listing 03 for database testing.', 'Brand 03', 'Active', '2026-02-04 09:00:00'),
  (4, 4, 4, 'Cotton Shirt 04', 'Synthetic demo listing 04 for database testing.', 'Brand 04', 'Active', '2026-02-05 09:00:00'),
  (5, 5, 5, 'Coffee Grinder 05', 'Synthetic demo listing 05 for database testing.', 'Brand 05', 'Active', '2026-02-06 09:00:00'),
  (6, 6, 6, 'Bluetooth Earbuds 06', 'Synthetic demo listing 06 for database testing.', 'Brand 06', 'Active', '2026-02-07 09:00:00'),
  (7, 7, 7, 'Storage Box 07', 'Synthetic demo listing 07 for database testing.', 'Brand 07', 'Active', '2026-02-08 09:00:00'),
  (8, 8, 8, 'Running Shoes 08', 'Synthetic demo listing 08 for database testing.', 'Brand 08', 'Active', '2026-02-09 09:00:00'),
  (9, 9, 9, 'Phone Stand 09', 'Synthetic demo listing 09 for database testing.', 'Brand 09', 'Active', '2026-02-10 09:00:00'),
  (10, 10, 10, 'Ceramic Mug 10', 'Synthetic demo listing 10 for database testing.', 'Brand 10', 'Draft', '2026-02-11 09:00:00'),
  (11, 1, 11, 'Wireless Speaker 11', 'Synthetic demo listing 11 for database testing.', 'Brand 01', 'Active', '2026-02-12 09:00:00'),
  (12, 2, 12, 'Desk Lamp 12', 'Synthetic demo listing 12 for database testing.', 'Brand 02', 'Active', '2026-02-13 09:00:00'),
  (13, 3, 1, 'Travel Backpack 13', 'Synthetic demo listing 13 for database testing.', 'Brand 03', 'Active', '2026-02-14 09:00:00'),
  (14, 4, 2, 'Cotton Shirt 14', 'Synthetic demo listing 14 for database testing.', 'Brand 04', 'Active', '2026-02-15 09:00:00'),
  (15, 5, 3, 'Coffee Grinder 15', 'Synthetic demo listing 15 for database testing.', 'Brand 05', 'Active', '2026-02-16 09:00:00'),
  (16, 6, 4, 'Bluetooth Earbuds 16', 'Synthetic demo listing 16 for database testing.', 'Brand 06', 'Active', '2026-02-17 09:00:00'),
  (17, 7, 5, 'Storage Box 17', 'Synthetic demo listing 17 for database testing.', 'Brand 07', 'Active', '2026-02-18 09:00:00'),
  (18, 8, 6, 'Running Shoes 18', 'Synthetic demo listing 18 for database testing.', 'Brand 08', 'Active', '2026-02-19 09:00:00'),
  (19, 9, 7, 'Phone Stand 19', 'Synthetic demo listing 19 for database testing.', 'Brand 09', 'Active', '2026-02-20 09:00:00'),
  (20, 10, 8, 'Ceramic Mug 20', 'Synthetic demo listing 20 for database testing.', 'Brand 10', 'Draft', '2026-02-21 09:00:00');

INSERT INTO product_variants (product_id, variant_no, sku, color, size, price, stock_qty) VALUES
  (1, 1, 'MN-001-01', 'Green', 'M', 682.00, 22),
  (1, 2, 'MN-001-02', 'White', 'L', 717.00, 25),
  (2, 1, 'MN-002-01', 'White', 'L', 779.00, 29),
  (2, 2, 'MN-002-02', 'Black', 'S', 814.00, 32),
  (3, 1, 'MN-003-01', 'Black', 'One size', 876.00, 36),
  (3, 2, 'MN-003-02', 'Blue', 'L', 911.00, 39),
  (4, 1, 'MN-004-01', 'Blue', 'S', 973.00, 43),
  (4, 2, 'MN-004-02', 'Green', 'S', 1008.00, 46),
  (5, 1, 'MN-005-01', 'Green', 'M', 1070.00, 50),
  (5, 2, 'MN-005-02', 'White', 'L', 1105.00, 13),
  (6, 1, 'MN-006-01', 'White', 'L', 1167.00, 17),
  (6, 2, 'MN-006-02', 'Black', 'S', 1202.00, 20),
  (7, 1, 'MN-007-01', 'Black', 'One size', 1264.00, 24),
  (7, 2, 'MN-007-02', 'Blue', 'L', 1299.00, 27),
  (8, 1, 'MN-008-01', 'Blue', 'S', 1361.00, 31),
  (8, 2, 'MN-008-02', 'Green', 'S', 1396.00, 34),
  (9, 1, 'MN-009-01', 'Green', 'M', 1458.00, 38),
  (9, 2, 'MN-009-02', 'White', 'L', 1493.00, 41),
  (10, 1, 'MN-010-01', 'White', 'L', 1555.00, 45),
  (10, 2, 'MN-010-02', 'Black', 'S', 1590.00, 48),
  (11, 1, 'MN-011-01', 'Black', 'One size', 1652.00, 12),
  (12, 1, 'MN-012-01', 'Blue', 'S', 1749.00, 19),
  (13, 1, 'MN-013-01', 'Green', 'M', 1846.00, 26),
  (14, 1, 'MN-014-01', 'White', 'L', 1943.00, 33),
  (15, 1, 'MN-015-01', 'Black', 'One size', 2040.00, 40),
  (16, 1, 'MN-016-01', 'Blue', 'S', 2137.00, 47),
  (17, 1, 'MN-017-01', 'Green', 'M', 2234.00, 14),
  (18, 1, 'MN-018-01', 'White', 'L', 2331.00, 21),
  (19, 1, 'MN-019-01', 'Black', 'One size', 2428.00, 28),
  (20, 1, 'MN-020-01', 'Blue', 'S', 2525.00, 35);

INSERT INTO carts (cart_id, customer_id, updated_at) VALUES
  (1, 1, '2026-10-02 12:00:00'),
  (2, 2, '2026-10-03 12:00:00'),
  (3, 3, '2026-10-04 12:00:00'),
  (4, 4, '2026-10-05 12:00:00'),
  (5, 5, '2026-10-06 12:00:00'),
  (6, 6, '2026-10-07 12:00:00'),
  (7, 7, '2026-10-08 12:00:00'),
  (8, 8, '2026-10-09 12:00:00'),
  (9, 9, '2026-10-10 12:00:00'),
  (10, 10, '2026-10-11 12:00:00');

INSERT INTO cart_items (cart_id, product_id, variant_no, quantity, added_at) VALUES
  (1, 1, 1, 2, '2026-10-06 09:00:00'),
  (1, 11, 1, 1, '2026-10-07 09:00:00'),
  (2, 2, 1, 3, '2026-10-07 09:00:00'),
  (2, 12, 1, 1, '2026-10-08 09:00:00'),
  (3, 3, 1, 1, '2026-10-08 09:00:00'),
  (3, 13, 1, 1, '2026-10-09 09:00:00'),
  (4, 4, 1, 2, '2026-10-09 09:00:00'),
  (4, 14, 1, 1, '2026-10-10 09:00:00'),
  (5, 5, 1, 3, '2026-10-10 09:00:00'),
  (5, 15, 1, 1, '2026-10-11 09:00:00'),
  (6, 6, 1, 1, '2026-10-11 09:00:00'),
  (6, 16, 1, 1, '2026-10-12 09:00:00'),
  (7, 7, 1, 2, '2026-10-12 09:00:00'),
  (7, 17, 1, 1, '2026-10-13 09:00:00'),
  (8, 8, 1, 3, '2026-10-13 09:00:00'),
  (8, 18, 1, 1, '2026-10-14 09:00:00'),
  (9, 9, 1, 1, '2026-10-14 09:00:00'),
  (9, 19, 1, 1, '2026-10-15 09:00:00'),
  (10, 10, 1, 2, '2026-10-15 09:00:00'),
  (10, 20, 1, 1, '2026-10-16 09:00:00');

INSERT INTO wishlist_items (customer_id, product_id, added_at) VALUES
  (1, 1, '2026-09-02 08:00:00'),
  (1, 11, '2026-09-03 08:00:00'),
  (2, 2, '2026-09-03 08:00:00'),
  (2, 12, '2026-09-04 08:00:00'),
  (3, 3, '2026-09-04 08:00:00'),
  (3, 13, '2026-09-05 08:00:00'),
  (4, 4, '2026-09-05 08:00:00'),
  (4, 14, '2026-09-06 08:00:00'),
  (5, 5, '2026-09-06 08:00:00'),
  (5, 15, '2026-09-07 08:00:00'),
  (6, 6, '2026-09-07 08:00:00'),
  (6, 16, '2026-09-08 08:00:00'),
  (7, 7, '2026-09-08 08:00:00'),
  (7, 17, '2026-09-09 08:00:00'),
  (8, 8, '2026-09-09 08:00:00'),
  (8, 18, '2026-09-10 08:00:00'),
  (9, 9, '2026-09-10 08:00:00'),
  (9, 19, '2026-09-11 08:00:00'),
  (10, 10, '2026-09-11 08:00:00'),
  (10, 20, '2026-09-12 08:00:00');

INSERT INTO coupons (coupon_id, code, discount_type, discount_value, min_order_amount, valid_from, valid_to, usage_limit) VALUES
  (1, 'SAVE01', 'Percent', 6, 500, '2026-01-01', '2027-12-31', 110),
  (2, 'SAVE02', 'Fixed', 70, 500, '2026-01-01', '2027-12-31', 120),
  (3, 'SAVE03', 'Percent', 8, 500, '2026-01-01', '2027-12-31', 130),
  (4, 'SAVE04', 'Fixed', 90, 500, '2026-01-01', '2027-12-31', 140),
  (5, 'SAVE05', 'Percent', 10, 500, '2026-01-01', '2027-12-31', 150),
  (6, 'SAVE06', 'Fixed', 110, 500, '2026-01-01', '2027-12-31', 160),
  (7, 'SAVE07', 'Percent', 12, 500, '2026-01-01', '2027-12-31', 170),
  (8, 'SAVE08', 'Fixed', 130, 500, '2026-01-01', '2027-12-31', 180),
  (9, 'SAVE09', 'Percent', 14, 500, '2026-01-01', '2027-12-31', 190),
  (10, 'SAVE10', 'Fixed', 150, 500, '2026-01-01', '2027-12-31', 200);

INSERT INTO couriers (courier_id, courier_name, phone, tracking_url) VALUES
  (1, 'Courier 01', '+8801900000001', 'https://tracking.example.test/courier1'),
  (2, 'Courier 02', '+8801900000002', 'https://tracking.example.test/courier2'),
  (3, 'Courier 03', '+8801900000003', 'https://tracking.example.test/courier3'),
  (4, 'Courier 04', '+8801900000004', 'https://tracking.example.test/courier4'),
  (5, 'Courier 05', '+8801900000005', 'https://tracking.example.test/courier5'),
  (6, 'Courier 06', '+8801900000006', 'https://tracking.example.test/courier6'),
  (7, 'Courier 07', '+8801900000007', 'https://tracking.example.test/courier7'),
  (8, 'Courier 08', '+8801900000008', 'https://tracking.example.test/courier8'),
  (9, 'Courier 09', '+8801900000009', 'https://tracking.example.test/courier9'),
  (10, 'Courier 10', '+8801900000010', 'https://tracking.example.test/courier10');

INSERT INTO orders (order_id, customer_id, address_no, coupon_id, order_date, order_status, subtotal, discount_amount, shipping_fee, total_amount) VALUES
  (1, 1, 1, NULL, '2026-01-06 10:30:00', 'Delivered', 5646.00, 0.00, 80.00, 5726.00),
  (2, 2, 1, NULL, '2026-02-07 10:30:00', 'Delivered', 5635.00, 0.00, 80.00, 5715.00),
  (3, 3, 1, 4, '2026-03-08 10:30:00', 'Delivered', 10685.00, 90, 80.00, 10675.00),
  (4, 4, 2, NULL, '2026-04-09 10:30:00', 'Delivered', 7128.00, 0.00, 80.00, 7208.00),
  (5, 5, 1, NULL, '2026-05-10 10:30:00', 'Delivered', 4374.00, 0.00, 80.00, 4454.00),
  (6, 6, 1, 7, '2026-06-11 10:30:00', 'Delivered', 1558.00, 186.96, 80.00, 1451.04),
  (7, 7, 1, NULL, '2026-07-12 10:30:00', 'Delivered', 3315.00, 0.00, 80.00, 3395.00),
  (8, 8, 1, NULL, '2026-08-13 10:30:00', 'Delivered', 1361.00, 0.00, 80.00, 1441.00),
  (9, 9, 1, 10, '2026-09-14 10:30:00', 'Delivered', 3304.00, 150, 80.00, 3234.00),
  (10, 10, 1, NULL, '2026-10-15 10:30:00', 'Delivered', 5829.00, 0.00, 80.00, 5909.00),
  (11, 1, 1, NULL, '2026-01-16 10:30:00', 'Delivered', 2234.00, 0.00, 80.00, 2314.00),
  (12, 2, 2, 3, '2026-11-06 10:30:00', 'Delivered', 5050.00, 404.00, 80.00, 4726.00),
  (13, 3, 1, NULL, '2026-03-18 10:30:00', 'Cancelled', 2733.00, 0.00, 80.00, 2813.00),
  (14, 4, 1, NULL, '2026-04-19 10:30:00', 'Shipped', 1167.00, 0.00, 80.00, 1247.00),
  (15, 5, 1, 6, '2026-05-20 10:30:00', 'Confirmed', 2986.00, 110, 80.00, 2956.00);

INSERT INTO order_items (order_id, line_no, product_id, variant_no, quantity, unit_price_paid) VALUES
  (1, 1, 7, 2, 3, 1299.00),
  (1, 2, 12, 1, 1, 1749.00),
  (2, 1, 10, 1, 1, 1555.00),
  (2, 2, 15, 1, 2, 2040.00),
  (3, 1, 13, 1, 2, 1846.00),
  (3, 2, 18, 1, 3, 2331.00),
  (4, 1, 16, 1, 3, 2137.00),
  (4, 2, 1, 2, 1, 717.00),
  (5, 1, 19, 1, 1, 2428.00),
  (5, 2, 4, 1, 2, 973.00),
  (6, 1, 2, 1, 2, 779.00),
  (7, 1, 5, 2, 3, 1105.00),
  (8, 1, 8, 1, 1, 1361.00),
  (9, 1, 11, 1, 2, 1652.00),
  (10, 1, 14, 1, 3, 1943.00),
  (11, 1, 17, 1, 1, 2234.00),
  (12, 1, 20, 1, 2, 2525.00),
  (13, 1, 3, 2, 3, 911.00),
  (14, 1, 6, 1, 1, 1167.00),
  (15, 1, 9, 2, 2, 1493.00);

-- Reflect inventory already reserved by open seed orders.
UPDATE product_variants pv
JOIN (SELECT oi.product_id, oi.variant_no, SUM(oi.quantity) AS reserved_qty
      FROM order_items oi JOIN orders o ON o.order_id=oi.order_id
      WHERE o.order_status IN ('Pending','Confirmed','Shipped')
      GROUP BY oi.product_id, oi.variant_no) r
  ON r.product_id=pv.product_id AND r.variant_no=pv.variant_no
SET pv.stock_qty=pv.stock_qty-r.reserved_qty;

INSERT INTO payments (payment_id, order_id, method, amount, pay_status, transaction_ref, paid_at) VALUES
  (1, 1, 'Card', 5726.00, 'Success', 'PAY-MN-0001', '2026-01-06 11:30:00'),
  (2, 2, 'Wallet', 5715.00, 'Success', 'PAY-MN-0002', '2026-02-07 11:30:00'),
  (3, 3, 'Bank Transfer', 10675.00, 'Success', 'PAY-MN-0003', '2026-03-08 11:30:00'),
  (4, 4, 'Cash on Delivery', 7208.00, 'Success', 'PAY-MN-0004', '2026-04-09 11:30:00'),
  (5, 5, 'Card', 4454.00, 'Success', 'PAY-MN-0005', '2026-05-10 11:30:00'),
  (6, 6, 'Wallet', 1451.04, 'Success', 'PAY-MN-0006', '2026-06-11 11:30:00'),
  (7, 7, 'Bank Transfer', 3395.00, 'Success', 'PAY-MN-0007', '2026-07-12 11:30:00'),
  (8, 8, 'Cash on Delivery', 1441.00, 'Success', 'PAY-MN-0008', '2026-08-13 11:30:00'),
  (9, 9, 'Card', 3234.00, 'Success', 'PAY-MN-0009', '2026-09-14 11:30:00'),
  (10, 10, 'Wallet', 5909.00, 'Success', 'PAY-MN-0010', '2026-10-15 11:30:00'),
  (11, 11, 'Bank Transfer', 2314.00, 'Success', 'PAY-MN-0011', '2026-01-16 11:30:00'),
  (12, 12, 'Cash on Delivery', 4726.00, 'Success', 'PAY-MN-0012', '2026-11-06 11:30:00'),
  (13, 13, 'Card', 2813.00, 'Failed', 'PAY-MN-0013', NULL),
  (14, 14, 'Wallet', 1247.00, 'Pending', 'PAY-MN-0014', NULL),
  (15, 15, 'Bank Transfer', 2956.00, 'Pending', 'PAY-MN-0015', NULL);

INSERT INTO shipments (shipment_id, order_id, courier_id, tracking_no, ship_status, shipped_at, delivered_at) VALUES
  (1, 1, 1, 'TRK-0001', 'Delivered', '2026-01-07 10:30:00', '2026-01-09 10:30:00'),
  (2, 2, 2, 'TRK-0002', 'Delivered', '2026-02-08 10:30:00', '2026-02-10 10:30:00'),
  (3, 3, 3, 'TRK-0003', 'Delivered', '2026-03-09 10:30:00', '2026-03-11 10:30:00'),
  (4, 4, 4, 'TRK-0004', 'Delivered', '2026-04-10 10:30:00', '2026-04-12 10:30:00'),
  (5, 5, 5, 'TRK-0005', 'Delivered', '2026-05-11 10:30:00', '2026-05-13 10:30:00'),
  (6, 6, 6, 'TRK-0006', 'Delivered', '2026-06-12 10:30:00', '2026-06-14 10:30:00'),
  (7, 7, 7, 'TRK-0007', 'Delivered', '2026-07-13 10:30:00', '2026-07-15 10:30:00'),
  (8, 8, 8, 'TRK-0008', 'Delivered', '2026-08-14 10:30:00', '2026-08-16 10:30:00'),
  (9, 9, 9, 'TRK-0009', 'Delivered', '2026-09-15 10:30:00', '2026-09-17 10:30:00'),
  (10, 10, 10, 'TRK-0010', 'Delivered', '2026-10-16 10:30:00', '2026-10-18 10:30:00'),
  (11, 11, 1, 'TRK-0011', 'Delivered', '2026-01-17 10:30:00', '2026-01-19 10:30:00'),
  (12, 12, 2, 'TRK-0012', 'Delivered', '2026-11-07 10:30:00', '2026-11-09 10:30:00'),
  (13, 14, 4, 'TRK-0014', 'Shipped', '2026-04-20 10:30:00', NULL);

INSERT INTO reviews (review_id, order_id, line_no, rating, title, comment, created_at) VALUES
  (1, 1, 1, 4, 'Review 01', 'Synthetic feedback for coursework demonstration.', '2026-01-10 10:30:00'),
  (2, 2, 1, 5, 'Review 02', 'Synthetic feedback for coursework demonstration.', '2026-02-11 10:30:00'),
  (3, 3, 1, 3, 'Review 03', 'Synthetic feedback for coursework demonstration.', '2026-03-12 10:30:00'),
  (4, 4, 1, 4, 'Review 04', 'Synthetic feedback for coursework demonstration.', '2026-04-13 10:30:00'),
  (5, 5, 1, 5, 'Review 05', 'Synthetic feedback for coursework demonstration.', '2026-05-14 10:30:00'),
  (6, 6, 1, 3, 'Review 06', 'Synthetic feedback for coursework demonstration.', '2026-06-15 10:30:00'),
  (7, 7, 1, 4, 'Review 07', 'Synthetic feedback for coursework demonstration.', '2026-07-16 10:30:00'),
  (8, 8, 1, 5, 'Review 08', 'Synthetic feedback for coursework demonstration.', '2026-08-17 10:30:00'),
  (9, 9, 1, 3, 'Review 09', 'Synthetic feedback for coursework demonstration.', '2026-09-18 10:30:00'),
  (10, 10, 1, 4, 'Review 10', 'Synthetic feedback for coursework demonstration.', '2026-10-19 10:30:00');

INSERT INTO return_requests (return_id, order_id, line_no, quantity, reason, return_status, refund_amount, requested_at) VALUES
  (1, 1, 1, 1, 'Demo reason 01', 'Requested', 0.00, '2026-01-10 10:30:00'),
  (2, 2, 1, 1, 'Demo reason 02', 'Requested', 0.00, '2026-02-11 10:30:00'),
  (3, 3, 1, 1, 'Demo reason 03', 'Requested', 0.00, '2026-03-12 10:30:00'),
  (4, 4, 1, 1, 'Demo reason 04', 'Approved', 0.00, '2026-04-13 10:30:00'),
  (5, 5, 1, 1, 'Demo reason 05', 'Approved', 0.00, '2026-05-14 10:30:00'),
  (6, 6, 1, 1, 'Demo reason 06', 'Approved', 0.00, '2026-06-15 10:30:00'),
  (7, 7, 1, 1, 'Demo reason 07', 'Rejected', 0.00, '2026-07-16 10:30:00'),
  (8, 8, 1, 1, 'Demo reason 08', 'Rejected', 0.00, '2026-08-17 10:30:00'),
  (9, 9, 1, 1, 'Demo reason 09', 'Refunded', 1652.00, '2026-09-18 10:30:00'),
  (10, 10, 1, 1, 'Demo reason 10', 'Refunded', 1943.00, '2026-10-19 10:30:00');

INSERT INTO seller_payouts (payout_id, seller_id, period_start, period_end, gross_sales, commission_amount, net_amount, payout_status, paid_at) VALUES
  (1, 1, '2026-01-01', '2026-12-31', 4021.00, 241.26, 3779.74, 'Paid', '2026-11-01 12:00:00'),
  (2, 2, '2026-01-01', '2026-12-31', 3307.00, 231.49, 3075.51, 'Paid', '2026-11-01 12:00:00'),
  (3, 3, '2026-01-01', '2026-12-31', 3692.00, 295.36, 3396.64, 'Paid', '2026-11-01 12:00:00'),
  (4, 4, '2026-01-01', '2026-12-31', 7775.00, 699.75, 7075.25, 'Paid', '2026-11-01 12:00:00'),
  (5, 5, '2026-01-01', '2026-12-31', 7395.00, 739.50, 6655.50, 'Paid', '2026-11-01 12:00:00'),
  (6, 6, '2026-01-01', '2026-12-31', 6411.00, 705.21, 5705.79, 'Paid', '2026-11-01 12:00:00'),
  (7, 7, '2026-01-01', '2026-12-31', 6131.00, 735.72, 5395.28, 'Paid', '2026-11-01 12:00:00'),
  (8, 8, '2026-01-01', '2026-12-31', 8354.00, 1086.02, 7267.98, 'Paid', '2026-11-01 12:00:00'),
  (9, 9, '2026-01-01', '2026-12-31', 2428.00, 339.92, 2088.08, 'Paid', '2026-11-01 12:00:00'),
  (10, 10, '2026-01-01', '2026-12-31', 6605.00, 990.75, 5614.25, 'Paid', '2026-11-01 12:00:00');

