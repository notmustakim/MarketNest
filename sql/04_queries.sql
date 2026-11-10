USE marketnest;

-- 25+ meaningful SQL queries grouped by the course brief's required categories.

-- BASIC QUERIES (Q01-Q04)
-- Q01 Active product listings with available stock.
SELECT product_id, product_name, store_name, sku, price, stock_qty
FROM v_product_catalog WHERE stock_qty > 0 ORDER BY product_name, sku;

-- Q02 Orders placed during a selected date range.
SELECT order_id, order_date, order_status, total_amount
FROM orders WHERE order_date >= '2026-01-01' AND order_date < '2027-01-01'
ORDER BY order_date DESC;

-- Q03 Products priced within a customer-selected range.
SELECT product_name, sku, price FROM v_product_catalog
WHERE price BETWEEN 500 AND 3000 ORDER BY price;

-- Q04 Low-stock variants that need replenishment.
SELECT product_id, variant_no, sku, stock_qty FROM product_variants
WHERE stock_qty <= 10 ORDER BY stock_qty, sku;

-- JOIN QUERIES (Q05-Q11)
-- Q05 Customer order history with delivery address.
SELECT o.order_id, c.full_name, a.city, a.street_line, o.order_date, o.order_status, o.total_amount
FROM orders o JOIN customers c ON c.customer_id = o.customer_id
JOIN addresses a ON a.customer_id = o.customer_id AND a.address_no = o.address_no
ORDER BY o.order_date DESC;

-- Q06 Product, seller, category, and inventory details.
SELECT p.product_name, s.store_name, c.category_name, pv.sku, pv.price, pv.stock_qty
FROM products p JOIN sellers s ON s.seller_id = p.seller_id
JOIN categories c ON c.category_id = p.category_id
JOIN product_variants pv ON pv.product_id = p.product_id
ORDER BY s.store_name, p.product_name;

-- Q07 Order line detail with seller and purchase-time price.
SELECT oi.order_id, oi.line_no, p.product_name, pv.sku, s.store_name,
       oi.quantity, oi.unit_price_paid, oi.quantity * oi.unit_price_paid AS line_total
FROM order_items oi JOIN products p ON p.product_id = oi.product_id
JOIN product_variants pv ON pv.product_id = oi.product_id AND pv.variant_no = oi.variant_no
JOIN sellers s ON s.seller_id = p.seller_id
ORDER BY oi.order_id, oi.line_no;

-- Q08 Shipment tracking list with courier contact.
SELECT o.order_id, sh.tracking_no, sh.ship_status, co.courier_name, co.phone
FROM shipments sh JOIN orders o ON o.order_id = sh.order_id
JOIN couriers co ON co.courier_id = sh.courier_id
ORDER BY o.order_id;

-- Q09 Payment attempts and order balances.
SELECT o.order_id, o.total_amount, p.method, p.amount, p.pay_status, p.transaction_ref
FROM orders o LEFT JOIN payments p ON p.order_id = o.order_id
ORDER BY o.order_id, p.payment_id;

-- Q10 Return requests with the purchased item and customer.
SELECT rr.return_id, c.full_name, o.order_id, p.product_name, rr.quantity,
       rr.return_status, rr.refund_amount
FROM return_requests rr JOIN order_items oi ON oi.order_id = rr.order_id AND oi.line_no = rr.line_no
JOIN orders o ON o.order_id = rr.order_id JOIN customers c ON c.customer_id = o.customer_id
JOIN products p ON p.product_id = oi.product_id
ORDER BY rr.requested_at DESC;

-- Q11 Products that have never received a review (LEFT JOIN).
SELECT p.product_id, p.product_name FROM products p
LEFT JOIN product_variants pv ON pv.product_id = p.product_id
LEFT JOIN order_items oi ON oi.product_id = pv.product_id AND oi.variant_no = pv.variant_no
LEFT JOIN reviews r ON r.order_id = oi.order_id AND r.line_no = oi.line_no
GROUP BY p.product_id, p.product_name HAVING COUNT(r.review_id) = 0;

-- AGGREGATES, GROUP BY, AND HAVING (Q12-Q16)
-- Q12 Gross delivered sales by seller (HAVING filters sellers with sales).
SELECT s.seller_id, s.store_name, SUM(oi.quantity * oi.unit_price_paid) AS gross_sales
FROM sellers s JOIN products p ON p.seller_id = s.seller_id
JOIN order_items oi ON oi.product_id = p.product_id
JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_status = 'Delivered'
GROUP BY s.seller_id, s.store_name
HAVING SUM(oi.quantity * oi.unit_price_paid) > 0
ORDER BY gross_sales DESC;

-- Q13 Categories with more than one listed product.
SELECT c.category_name, COUNT(p.product_id) AS product_count
FROM categories c LEFT JOIN products p ON p.category_id = c.category_id
GROUP BY c.category_id, c.category_name HAVING COUNT(p.product_id) > 1;

-- Q14 Monthly order totals and average basket size.
SELECT DATE_FORMAT(order_date, '%Y-%m') AS order_month, COUNT(*) AS orders,
       SUM(total_amount) AS booked_value, AVG(total_amount) AS average_order
FROM orders GROUP BY DATE_FORMAT(order_date, '%Y-%m') ORDER BY order_month;

-- Q15 Ratings by product, retaining only products averaging at least 4.
SELECT p.product_id, p.product_name, AVG(r.rating) AS average_rating, COUNT(*) AS review_count
FROM products p JOIN order_items oi ON oi.product_id = p.product_id
JOIN reviews r ON r.order_id = oi.order_id AND r.line_no = oi.line_no
GROUP BY p.product_id, p.product_name HAVING AVG(r.rating) >= 4;

-- Q16 Return volume by processing status.
SELECT return_status, COUNT(*) AS request_count, SUM(quantity) AS units_requested
FROM return_requests GROUP BY return_status ORDER BY request_count DESC;

-- SUBQUERIES (Q17-Q20)
-- Q17 Products priced above the marketplace average.
SELECT p.product_id, p.product_name, pv.sku, pv.price
FROM products p JOIN product_variants pv ON pv.product_id = p.product_id
WHERE pv.price > (SELECT AVG(price) FROM product_variants) ORDER BY pv.price DESC;

-- Q18 Customers whose lifetime delivered spend is above the customer average.
SELECT c.customer_id, c.full_name, SUM(o.total_amount) AS lifetime_spend
FROM customers c JOIN orders o ON o.customer_id = c.customer_id
WHERE o.order_status = 'Delivered'
GROUP BY c.customer_id, c.full_name
HAVING SUM(o.total_amount) > (
  SELECT AVG(customer_spend) FROM (
    SELECT customer_id, SUM(total_amount) AS customer_spend
    FROM orders WHERE order_status = 'Delivered' GROUP BY customer_id
  ) AS spend_by_customer
);

-- Q19 Sellers who have at least one product with a low-stock variant (EXISTS).
SELECT s.seller_id, s.store_name FROM sellers s
WHERE EXISTS (
  SELECT 1 FROM products p JOIN product_variants pv ON pv.product_id = p.product_id
  WHERE p.seller_id = s.seller_id AND pv.stock_qty < 10
);

-- Q20 Products that appear in delivered orders (correlated EXISTS).
SELECT p.product_id, p.product_name FROM products p
WHERE EXISTS (
  SELECT 1 FROM order_items oi JOIN orders o ON o.order_id = oi.order_id
  WHERE oi.product_id = p.product_id AND o.order_status = 'Delivered'
);

-- ARITHMETIC AND LOGICAL OPERATIONS (Q21-Q23)
-- Q21 Calculate line revenue and seller commission for each delivered line.
SELECT oi.order_id, p.product_name, oi.quantity * oi.unit_price_paid AS line_revenue,
       ROUND(oi.quantity * oi.unit_price_paid * s.commission_rate / 100, 2) AS commission
FROM order_items oi JOIN orders o ON o.order_id = oi.order_id
JOIN products p ON p.product_id = oi.product_id JOIN sellers s ON s.seller_id = p.seller_id
WHERE o.order_status = 'Delivered';

-- Q22 Find orders with failed or pending payments and a positive total.
SELECT DISTINCT o.order_id, o.total_amount, o.order_status
FROM orders o JOIN payments p ON p.order_id = o.order_id
WHERE p.pay_status IN ('Pending','Failed') AND o.total_amount > 0;

-- Q23 Apply a simple low-stock and active-listing rule.
SELECT p.product_name, pv.sku, pv.stock_qty
FROM products p JOIN product_variants pv ON pv.product_id = p.product_id
WHERE p.status = 'Active' AND pv.stock_qty <= 10 AND pv.price > 0;

-- COMPLEX ANALYTICAL QUERIES (Q24-Q28)
-- Q24 Top five products by delivered quantity.
SELECT p.product_id, p.product_name, SUM(oi.quantity) AS units_sold,
       SUM(oi.quantity * oi.unit_price_paid) AS revenue
FROM products p JOIN order_items oi ON oi.product_id = p.product_id
JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_status = 'Delivered'
GROUP BY p.product_id, p.product_name
ORDER BY units_sold DESC, revenue DESC LIMIT 5;

-- Q25 Rank sellers by monthly delivered revenue.
SELECT seller_id, store_name, month_start, gross_sales,
       DENSE_RANK() OVER (PARTITION BY month_start ORDER BY gross_sales DESC) AS monthly_rank
FROM v_seller_monthly_sales;

-- Q26 Monthly revenue compared with the previous month.
WITH monthly AS (
  SELECT DATE_FORMAT(o.order_date, '%Y-%m-01') AS month_start,
         SUM(oi.quantity * oi.unit_price_paid) AS revenue
  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id
  WHERE o.order_status = 'Delivered'
  GROUP BY DATE_FORMAT(o.order_date, '%Y-%m-01')
)
SELECT month_start, revenue,
       LAG(revenue) OVER (ORDER BY month_start) AS previous_month_revenue,
       revenue - LAG(revenue) OVER (ORDER BY month_start) AS change_from_previous
FROM monthly ORDER BY month_start;

-- Q27 Coupon effectiveness: order count, discount, and average order value.
SELECT cp.code, COUNT(o.order_id) AS order_count,
       SUM(o.discount_amount) AS total_discount,
       AVG(o.total_amount) AS average_order_value
FROM coupons cp LEFT JOIN orders o ON o.coupon_id = cp.coupon_id
GROUP BY cp.coupon_id, cp.code ORDER BY order_count DESC, total_discount DESC;

-- Q28 Calculate the 90th percentile-like ordered spend using window ranking.
WITH ranked AS (
  SELECT order_id, total_amount,
         CUME_DIST() OVER (ORDER BY total_amount) AS spend_percentile
  FROM orders WHERE order_status = 'Delivered'
)
SELECT order_id, total_amount FROM ranked WHERE spend_percentile >= 0.90
ORDER BY total_amount DESC;

-- Q29 Return rate by product (returned units / sold units).
SELECT p.product_id, p.product_name,
       SUM(COALESCE(rr.returned_units, 0)) AS returned_units,
       SUM(oi.quantity) AS sold_units,
       ROUND(SUM(COALESCE(rr.returned_units, 0)) / NULLIF(SUM(oi.quantity), 0) * 100, 2) AS return_rate_pct
FROM products p JOIN order_items oi ON oi.product_id = p.product_id
JOIN orders o ON o.order_id = oi.order_id AND o.order_status = 'Delivered'
LEFT JOIN (
  SELECT order_id, line_no, SUM(quantity) AS returned_units
  FROM return_requests WHERE return_status <> 'Rejected'
  GROUP BY order_id, line_no
) rr ON rr.order_id = oi.order_id AND rr.line_no = oi.line_no
GROUP BY p.product_id, p.product_name ORDER BY return_rate_pct DESC;
