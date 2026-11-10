USE marketnest;

-- Views for customer, administrator, and seller reporting.
CREATE OR REPLACE VIEW v_product_catalog AS
SELECT p.product_id, p.product_name, p.brand_name, c.category_name,
       s.store_name, pv.variant_no, pv.sku, pv.color, pv.size, pv.price,
       pv.stock_qty,
       COALESCE(AVG(r.rating), 0) AS average_rating,
       COUNT(r.review_id) AS review_count
FROM products p
JOIN categories c ON c.category_id = p.category_id
JOIN sellers s ON s.seller_id = p.seller_id
JOIN product_variants pv ON pv.product_id = p.product_id
LEFT JOIN order_items oi ON oi.product_id = pv.product_id AND oi.variant_no = pv.variant_no
LEFT JOIN reviews r ON r.order_id = oi.order_id AND r.line_no = oi.line_no
WHERE p.status = 'Active'
GROUP BY p.product_id, p.product_name, p.brand_name, c.category_name,
         s.store_name, pv.variant_no, pv.sku, pv.color, pv.size,
         pv.price, pv.stock_qty;

CREATE OR REPLACE VIEW v_order_summary AS
SELECT o.order_id, o.order_date, o.order_status, c.customer_id, c.full_name,
       o.subtotal, o.discount_amount, o.shipping_fee, o.total_amount,
       COALESCE(pay.successful_payment_total, 0) AS successful_payment_total,
       COALESCE(sh.shipment_count, 0) AS shipment_count
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
LEFT JOIN (
  SELECT order_id, SUM(CASE WHEN pay_status = 'Success' THEN amount ELSE 0 END) AS successful_payment_total
  FROM payments GROUP BY order_id
) pay ON pay.order_id = o.order_id
LEFT JOIN (
  SELECT order_id, COUNT(*) AS shipment_count FROM shipments GROUP BY order_id
) sh ON sh.order_id = o.order_id;

CREATE OR REPLACE VIEW v_seller_monthly_sales AS
SELECT s.seller_id, s.store_name,
       CAST(DATE_FORMAT(o.order_date, '%Y-%m-01') AS DATE) AS month_start,
       COUNT(DISTINCT o.order_id) AS order_count,
       SUM(oi.quantity * oi.unit_price_paid) AS gross_sales,
       ROUND(SUM(oi.quantity * oi.unit_price_paid) * s.commission_rate / 100, 2) AS commission_amount,
       ROUND(SUM(oi.quantity * oi.unit_price_paid) * (1 - s.commission_rate / 100), 2) AS net_sales
FROM sellers s
JOIN products p ON p.seller_id = s.seller_id
JOIN product_variants pv ON pv.product_id = p.product_id
JOIN order_items oi ON oi.product_id = pv.product_id AND oi.variant_no = pv.variant_no
JOIN orders o ON o.order_id = oi.order_id
WHERE o.order_status = 'Delivered'
GROUP BY s.seller_id, s.store_name, CAST(DATE_FORMAT(o.order_date, '%Y-%m-01') AS DATE), s.commission_rate;

-- Trigger 1: validate coupon dates, minimum spend, calculated discount, and usage limit.
DROP TRIGGER IF EXISTS bi_orders_validate_coupon;
DELIMITER $$
CREATE TRIGGER bi_orders_validate_coupon
BEFORE INSERT ON orders
FOR EACH ROW
BEGIN
  DECLARE v_type VARCHAR(10) DEFAULT NULL;
  DECLARE v_value DECIMAL(10,2) DEFAULT NULL;
  DECLARE v_minimum DECIMAL(12,2) DEFAULT NULL;
  DECLARE v_valid_from DATE DEFAULT NULL;
  DECLARE v_valid_to DATE DEFAULT NULL;
  DECLARE v_limit INT DEFAULT NULL;
  DECLARE v_used INT DEFAULT 0;
  DECLARE v_expected DECIMAL(12,2) DEFAULT 0;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_type = NULL;
  IF NEW.coupon_id IS NULL THEN
    IF NEW.discount_amount <> 0 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'An order without a coupon cannot have a coupon discount';
    END IF;
  ELSE
    SELECT discount_type, discount_value, min_order_amount, valid_from, valid_to, usage_limit
    INTO v_type, v_value, v_minimum, v_valid_from, v_valid_to, v_limit
    FROM coupons WHERE coupon_id = NEW.coupon_id FOR UPDATE;
    IF v_type IS NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Coupon was not found';
    END IF;
    IF DATE(NEW.order_date) < v_valid_from OR DATE(NEW.order_date) > v_valid_to THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Coupon is outside its validity period';
    END IF;
    IF NEW.subtotal < v_minimum THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Order does not meet the coupon minimum';
    END IF;
    IF v_type = 'Percent' THEN
      SET v_expected = ROUND(NEW.subtotal * v_value / 100, 2);
    ELSE
      SET v_expected = LEAST(v_value, NEW.subtotal);
    END IF;
    IF NEW.discount_amount <> v_expected THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Order discount does not match the coupon rule';
    END IF;
    SELECT COUNT(*) INTO v_used FROM orders WHERE coupon_id = NEW.coupon_id;
    IF v_used >= v_limit THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Coupon usage limit has been reached';
    END IF;
  END IF;
END$$
DELIMITER ;

-- Trigger 2: lock the variant row and reject an order line that oversells stock.
DROP TRIGGER IF EXISTS bi_order_item_check_stock;
DELIMITER $$
CREATE TRIGGER bi_order_item_check_stock
BEFORE INSERT ON order_items
FOR EACH ROW
BEGIN
  DECLARE v_stock INT DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_stock = NULL;
  SELECT stock_qty INTO v_stock
  FROM product_variants
  WHERE product_id = NEW.product_id AND variant_no = NEW.variant_no
  FOR UPDATE;
  IF v_stock IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Product variant does not exist';
  END IF;
  IF v_stock < NEW.quantity THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock for this order line';
  END IF;
END$$
DELIMITER ;

-- Trigger 3: allow only the defined order lifecycle and block cancellation after dispatch.
DROP TRIGGER IF EXISTS bu_orders_validate_transition;
DELIMITER $$
CREATE TRIGGER bu_orders_validate_transition
BEFORE UPDATE ON orders
FOR EACH ROW
BEGIN
  IF OLD.order_status <> NEW.order_status AND NOT (
       (OLD.order_status = 'Pending' AND NEW.order_status IN ('Confirmed','Cancelled'))
    OR (OLD.order_status = 'Confirmed' AND NEW.order_status IN ('Shipped','Cancelled'))
    OR (OLD.order_status = 'Shipped' AND NEW.order_status = 'Delivered')
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid order status transition';
  END IF;
  IF NEW.order_status = 'Cancelled' AND EXISTS (
    SELECT 1 FROM shipments
    WHERE order_id = OLD.order_id AND ship_status IN ('Shipped','Out for Delivery','Delivered')
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'An order cannot be cancelled after shipment';
  END IF;
END$$
DELIMITER ;

-- Trigger 4: return reserved stock when an unshipped order is cancelled.
DROP TRIGGER IF EXISTS au_orders_restore_cancelled_stock;
DELIMITER $$
CREATE TRIGGER au_orders_restore_cancelled_stock
AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
  IF OLD.order_status IN ('Pending','Confirmed') AND NEW.order_status = 'Cancelled' THEN
    UPDATE product_variants pv
    JOIN order_items oi ON oi.product_id = pv.product_id AND oi.variant_no = pv.variant_no
    SET pv.stock_qty = pv.stock_qty + oi.quantity
    WHERE oi.order_id = OLD.order_id;
  END IF;
END$$
DELIMITER ;

-- Trigger 5: permit reviews only for delivered order items.
DROP TRIGGER IF EXISTS bi_reviews_require_delivery;
DELIMITER $$
CREATE TRIGGER bi_reviews_require_delivery
BEFORE INSERT ON reviews
FOR EACH ROW
BEGIN
  DECLARE v_status VARCHAR(20) DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_status = NULL;
  SELECT o.order_status INTO v_status
  FROM orders o
  JOIN order_items oi ON oi.order_id = o.order_id
  WHERE oi.order_id = NEW.order_id AND oi.line_no = NEW.line_no;
  IF v_status IS NULL OR v_status <> 'Delivered' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A review requires a delivered order item';
  END IF;
END$$
DELIMITER ;

-- Trigger 6: enforce the seven-day return window and aggregate return quantity limit.
DROP TRIGGER IF EXISTS bi_returns_validate_request;
DELIMITER $$
CREATE TRIGGER bi_returns_validate_request
BEFORE INSERT ON return_requests
FOR EACH ROW
BEGIN
  DECLARE v_status VARCHAR(20) DEFAULT NULL;
  DECLARE v_delivered DATETIME DEFAULT NULL;
  DECLARE v_purchased INT DEFAULT NULL;
  DECLARE v_already_requested INT DEFAULT 0;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_status = NULL;
  SELECT o.order_status, MAX(sh.delivered_at), oi.quantity
  INTO v_status, v_delivered, v_purchased
  FROM orders o
  JOIN order_items oi ON oi.order_id = o.order_id
  LEFT JOIN shipments sh ON sh.order_id = o.order_id AND sh.ship_status = 'Delivered'
  WHERE oi.order_id = NEW.order_id AND oi.line_no = NEW.line_no
  GROUP BY o.order_status, oi.quantity;
  IF v_status IS NULL OR v_status <> 'Delivered' OR v_delivered IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A return requires a delivered order item';
  END IF;
  IF NEW.requested_at > DATE_ADD(v_delivered, INTERVAL 7 DAY) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Return requests must be made within seven days of delivery';
  END IF;
  SELECT COALESCE(SUM(quantity), 0) INTO v_already_requested
  FROM return_requests
  WHERE order_id = NEW.order_id AND line_no = NEW.line_no AND return_status <> 'Rejected';
  IF v_already_requested + NEW.quantity > v_purchased THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Return quantity exceeds the purchased quantity';
  END IF;
END$$
DELIMITER ;

-- Trigger 7: preserve the cumulative return-quantity limit when an administrator updates a request.
DROP TRIGGER IF EXISTS bu_returns_validate_quantity;
DELIMITER $$
CREATE TRIGGER bu_returns_validate_quantity
BEFORE UPDATE ON return_requests
FOR EACH ROW
BEGIN
  DECLARE v_purchased INT DEFAULT NULL;
  DECLARE v_other_requests INT DEFAULT 0;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_purchased = NULL;
  SELECT quantity INTO v_purchased FROM order_items
  WHERE order_id = NEW.order_id AND line_no = NEW.line_no;
  IF v_purchased IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Return order item was not found';
  END IF;
  IF NEW.return_status <> 'Rejected' THEN
    SELECT COALESCE(SUM(quantity),0) INTO v_other_requests
    FROM return_requests
    WHERE order_id = NEW.order_id AND line_no = NEW.line_no
      AND return_status <> 'Rejected' AND return_id <> OLD.return_id;
    IF v_other_requests + NEW.quantity > v_purchased THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Return quantity exceeds the purchased quantity';
    END IF;
  END IF;
END$$
DELIMITER ;

-- Trigger 8: constrain return-request status changes to the supported workflow.
DROP TRIGGER IF EXISTS bu_returns_validate_transition;
DELIMITER $$
CREATE TRIGGER bu_returns_validate_transition
BEFORE UPDATE ON return_requests
FOR EACH ROW
BEGIN
  IF OLD.return_status <> NEW.return_status AND NOT (
       (OLD.return_status = 'Requested' AND NEW.return_status IN ('Approved','Rejected'))
    OR (OLD.return_status = 'Approved' AND NEW.return_status = 'Refunded')
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid return status transition';
  END IF;
END$$
DELIMITER ;

-- Trigger 9: restock returned items only when an approved return is refunded.
DROP TRIGGER IF EXISTS au_returns_restock_refunded;
DELIMITER $$
CREATE TRIGGER au_returns_restock_refunded
AFTER UPDATE ON return_requests
FOR EACH ROW
BEGIN
  IF OLD.return_status <> 'Refunded' AND NEW.return_status = 'Refunded' THEN
    UPDATE product_variants pv
    JOIN order_items oi ON oi.product_id = pv.product_id AND oi.variant_no = pv.variant_no
    SET pv.stock_qty = pv.stock_qty + NEW.quantity
    WHERE oi.order_id = NEW.order_id AND oi.line_no = NEW.line_no;
  END IF;
END$$
DELIMITER ;

-- Trigger 10: payout periods for a seller cannot overlap on insert.
DROP TRIGGER IF EXISTS bi_payouts_no_overlap;
DELIMITER $$
CREATE TRIGGER bi_payouts_no_overlap
BEFORE INSERT ON seller_payouts
FOR EACH ROW
BEGIN
  IF EXISTS (
    SELECT 1 FROM seller_payouts
    WHERE seller_id = NEW.seller_id
      AND period_start <= NEW.period_end
      AND period_end >= NEW.period_start
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Seller payout periods must not overlap';
  END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS bu_payouts_no_overlap;
DELIMITER $$
-- Trigger 11: keep payout periods non-overlapping when an existing record is changed.
CREATE TRIGGER bu_payouts_no_overlap
BEFORE UPDATE ON seller_payouts
FOR EACH ROW
BEGIN
  IF EXISTS (
    SELECT 1 FROM seller_payouts
    WHERE seller_id = NEW.seller_id
      AND payout_id <> OLD.payout_id
      AND period_start <= NEW.period_end
      AND period_end >= NEW.period_start
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Seller payout periods must not overlap';
  END IF;
END$$
DELIMITER ;

-- Trigger 12: reject a category that names itself as its parent after its AUTO_INCREMENT ID is assigned.
DROP TRIGGER IF EXISTS ai_categories_no_self_parent;
DELIMITER $$
CREATE TRIGGER ai_categories_no_self_parent
AFTER INSERT ON categories
FOR EACH ROW
BEGIN
  IF NEW.parent_category_id = NEW.category_id THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A category cannot be its own parent';
  END IF;
END$$
DELIMITER ;

-- Trigger 13: prevent an existing category from being changed into its own parent.
DROP TRIGGER IF EXISTS bu_categories_no_self_parent;
DELIMITER $$
CREATE TRIGGER bu_categories_no_self_parent
BEFORE UPDATE ON categories
FOR EACH ROW
BEGIN
  IF NEW.parent_category_id = NEW.category_id THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A category cannot be its own parent';
  END IF;
END$$
DELIMITER ;

-- Procedure 1: atomically reserve stock and insert one order line.
-- Call inside a caller-managed transaction; the dashboard commits the complete checkout.
DROP PROCEDURE IF EXISTS sp_reserve_order_line;
DELIMITER $$
CREATE PROCEDURE sp_reserve_order_line(
  IN p_order_id BIGINT UNSIGNED,
  IN p_line_no SMALLINT UNSIGNED,
  IN p_product_id BIGINT UNSIGNED,
  IN p_variant_no SMALLINT UNSIGNED,
  IN p_quantity INT,
  IN p_unit_price_paid DECIMAL(12,2)
)
BEGIN
  DECLARE v_stock INT DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_stock = NULL;
  SELECT stock_qty INTO v_stock
  FROM product_variants
  WHERE product_id = p_product_id AND variant_no = p_variant_no
  FOR UPDATE;
  IF v_stock IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Product variant does not exist';
  END IF;
  IF p_quantity <= 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Order quantity must be positive';
  END IF;
  IF v_stock < p_quantity THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock for this order line';
  END IF;
  INSERT INTO order_items(order_id,line_no,product_id,variant_no,quantity,unit_price_paid)
  VALUES(p_order_id,p_line_no,p_product_id,p_variant_no,p_quantity,p_unit_price_paid);
  UPDATE product_variants
  SET stock_qty = stock_qty - p_quantity
  WHERE product_id = p_product_id AND variant_no = p_variant_no;
END$$
DELIMITER ;

-- Procedure 2: cancel an unshipped order atomically and invoke the stock-restoration trigger.
DROP PROCEDURE IF EXISTS sp_cancel_order;
DELIMITER $$
CREATE PROCEDURE sp_cancel_order(IN p_order_id BIGINT UNSIGNED)
BEGIN
  DECLARE v_status VARCHAR(20) DEFAULT NULL;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_status = NULL;
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;
  START TRANSACTION;
  SELECT order_status INTO v_status FROM orders WHERE order_id = p_order_id FOR UPDATE;
  IF v_status IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Order was not found';
  END IF;
  IF v_status NOT IN ('Pending','Confirmed') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only pending or confirmed orders can be cancelled';
  END IF;
  UPDATE orders SET order_status = 'Cancelled' WHERE order_id = p_order_id;
  UPDATE payments
  SET pay_status = CASE WHEN pay_status = 'Success' THEN 'Refunded' ELSE 'Failed' END
  WHERE order_id = p_order_id;
  COMMIT;
END$$
DELIMITER ;

-- Procedure 3: create a seller payout from delivered order lines in a closed date range.
DROP PROCEDURE IF EXISTS sp_generate_seller_payout;
DELIMITER $$
CREATE PROCEDURE sp_generate_seller_payout(
  IN p_seller_id BIGINT UNSIGNED,
  IN p_period_start DATE,
  IN p_period_end DATE,
  OUT p_payout_id BIGINT UNSIGNED
)
BEGIN
  DECLARE v_rate DECIMAL(5,2) DEFAULT NULL;
  DECLARE v_gross DECIMAL(14,2) DEFAULT 0;
  DECLARE v_commission DECIMAL(14,2) DEFAULT 0;
  IF p_period_end < p_period_start THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payout period end precedes period start';
  END IF;
  SELECT commission_rate INTO v_rate FROM sellers WHERE seller_id = p_seller_id;
  IF v_rate IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Seller was not found';
  END IF;
  SELECT COALESCE(SUM(oi.quantity * oi.unit_price_paid), 0)
  INTO v_gross
  FROM order_items oi
  JOIN orders o ON o.order_id = oi.order_id
  JOIN products p ON p.product_id = oi.product_id
  WHERE p.seller_id = p_seller_id
    AND o.order_status = 'Delivered'
    AND o.order_date >= p_period_start
    AND o.order_date < DATE_ADD(p_period_end, INTERVAL 1 DAY);
  SET v_commission = ROUND(v_gross * v_rate / 100, 2);
  INSERT INTO seller_payouts(
    seller_id, period_start, period_end, gross_sales,
    commission_amount, net_amount, payout_status
  ) VALUES (
    p_seller_id, p_period_start, p_period_end, v_gross,
    v_commission, v_gross - v_commission, 'Pending'
  );
  SET p_payout_id = LAST_INSERT_ID();
END$$
DELIMITER ;
