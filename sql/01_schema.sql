-- MarketNest multi-vendor marketplace database
-- Target: MySQL 8.0.16+ (enforced CHECK constraints) with InnoDB.
-- Run this file first in MySQL Workbench or with the mysql command-line client.
CREATE DATABASE IF NOT EXISTS marketnest
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE marketnest;

CREATE TABLE IF NOT EXISTS customers (
  customer_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(254) NOT NULL,
  phone VARCHAR(25),
  password_hash VARCHAR(255) NOT NULL,
  registered_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status ENUM('Active','Suspended') NOT NULL DEFAULT 'Active',
  PRIMARY KEY (customer_id),
  CONSTRAINT uq_customers_email UNIQUE (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS addresses (
  customer_id BIGINT UNSIGNED NOT NULL,
  address_no SMALLINT UNSIGNED NOT NULL,
  label VARCHAR(40) NOT NULL,
  street_line VARCHAR(180) NOT NULL,
  city VARCHAR(80) NOT NULL,
  postal_code VARCHAR(20),
  country VARCHAR(80) NOT NULL DEFAULT 'Bangladesh',
  is_default TINYINT(1) NOT NULL DEFAULT 0,
  default_customer_id BIGINT UNSIGNED AS (CASE WHEN is_default = 1 THEN customer_id ELSE NULL END) STORED,
  PRIMARY KEY (customer_id, address_no),
  CONSTRAINT fk_addresses_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT uq_one_default_address UNIQUE (default_customer_id),
  CONSTRAINT ck_address_default CHECK (is_default IN (0,1))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sellers (
  seller_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  store_name VARCHAR(120) NOT NULL,
  email VARCHAR(254) NOT NULL,
  phone VARCHAR(25),
  tax_id VARCHAR(40) NOT NULL,
  commission_rate DECIMAL(5,2) NOT NULL DEFAULT 10.00,
  joined_on DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status ENUM('Pending','Active','Suspended') NOT NULL DEFAULT 'Pending',
  PRIMARY KEY (seller_id),
  CONSTRAINT uq_sellers_email UNIQUE (email),
  CONSTRAINT uq_sellers_tax_id UNIQUE (tax_id),
  CONSTRAINT ck_seller_commission CHECK (commission_rate BETWEEN 0 AND 100)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categories (
  category_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_name VARCHAR(100) NOT NULL,
  parent_category_id BIGINT UNSIGNED,
  PRIMARY KEY (category_id),
  CONSTRAINT uq_categories_name UNIQUE (category_name),
  CONSTRAINT fk_categories_parent FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
  product_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  seller_id BIGINT UNSIGNED NOT NULL,
  category_id BIGINT UNSIGNED NOT NULL,
  product_name VARCHAR(160) NOT NULL,
  description TEXT,
  brand_name VARCHAR(100),
  status ENUM('Draft','Active','Hidden') NOT NULL DEFAULT 'Draft',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (product_id),
  CONSTRAINT fk_products_seller FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
  CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(category_id),
  INDEX idx_products_name (product_name),
  INDEX idx_products_category (category_id),
  INDEX idx_products_seller (seller_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS product_variants (
  product_id BIGINT UNSIGNED NOT NULL,
  variant_no SMALLINT UNSIGNED NOT NULL,
  sku VARCHAR(64) NOT NULL,
  color VARCHAR(50),
  size VARCHAR(50),
  price DECIMAL(12,2) NOT NULL,
  stock_qty INT NOT NULL DEFAULT 0,
  PRIMARY KEY (product_id, variant_no),
  CONSTRAINT uq_variants_sku UNIQUE (sku),
  CONSTRAINT fk_variants_product FOREIGN KEY (product_id) REFERENCES products(product_id),
  CONSTRAINT ck_variant_price CHECK (price >= 0),
  CONSTRAINT ck_variant_stock CHECK (stock_qty >= 0),
  INDEX idx_variants_stock (stock_qty)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS carts (
  cart_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  customer_id BIGINT UNSIGNED NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (cart_id),
  CONSTRAINT uq_carts_customer UNIQUE (customer_id),
  CONSTRAINT fk_carts_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS cart_items (
  cart_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  variant_no SMALLINT UNSIGNED NOT NULL,
  quantity INT NOT NULL,
  added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (cart_id, product_id, variant_no),
  CONSTRAINT fk_cart_items_cart FOREIGN KEY (cart_id) REFERENCES carts(cart_id),
  CONSTRAINT fk_cart_items_variant FOREIGN KEY (product_id, variant_no) REFERENCES product_variants(product_id, variant_no),
  CONSTRAINT ck_cart_item_quantity CHECK (quantity > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS wishlist_items (
  customer_id BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (customer_id, product_id),
  CONSTRAINT fk_wishlist_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_wishlist_product FOREIGN KEY (product_id) REFERENCES products(product_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS coupons (
  coupon_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  code VARCHAR(40) NOT NULL,
  discount_type ENUM('Percent','Fixed') NOT NULL,
  discount_value DECIMAL(10,2) NOT NULL,
  min_order_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  valid_from DATE NOT NULL,
  valid_to DATE NOT NULL,
  usage_limit INT UNSIGNED NOT NULL,
  PRIMARY KEY (coupon_id),
  CONSTRAINT uq_coupons_code UNIQUE (code),
  CONSTRAINT ck_coupon_value CHECK (discount_value > 0 AND (discount_type <> 'Percent' OR discount_value <= 100)),
  CONSTRAINT ck_coupon_minimum CHECK (min_order_amount >= 0),
  CONSTRAINT ck_coupon_dates CHECK (valid_to >= valid_from),
  CONSTRAINT ck_coupon_limit CHECK (usage_limit > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS orders (
  order_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  customer_id BIGINT UNSIGNED NOT NULL,
  address_no SMALLINT UNSIGNED NOT NULL,
  coupon_id BIGINT UNSIGNED,
  order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  order_status ENUM('Pending','Confirmed','Shipped','Delivered','Cancelled') NOT NULL DEFAULT 'Pending',
  subtotal DECIMAL(12,2) NOT NULL,
  discount_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  shipping_fee DECIMAL(12,2) NOT NULL DEFAULT 0,
  total_amount DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (order_id),
  CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
  CONSTRAINT fk_orders_address FOREIGN KEY (customer_id, address_no) REFERENCES addresses(customer_id, address_no),
  CONSTRAINT fk_orders_coupon FOREIGN KEY (coupon_id) REFERENCES coupons(coupon_id),
  CONSTRAINT ck_order_amounts CHECK (subtotal >= 0 AND discount_amount >= 0 AND shipping_fee >= 0 AND total_amount >= 0 AND discount_amount <= subtotal),
  CONSTRAINT ck_order_total CHECK (total_amount = subtotal - discount_amount + shipping_fee),
  INDEX idx_orders_date (order_date),
  INDEX idx_orders_status (order_status),
  INDEX idx_orders_customer_date (customer_id, order_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS order_items (
  order_id BIGINT UNSIGNED NOT NULL,
  line_no SMALLINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  variant_no SMALLINT UNSIGNED NOT NULL,
  quantity INT NOT NULL,
  unit_price_paid DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (order_id, line_no),
  CONSTRAINT uq_order_variant UNIQUE (order_id, product_id, variant_no),
  CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(order_id),
  CONSTRAINT fk_order_items_variant FOREIGN KEY (product_id, variant_no) REFERENCES product_variants(product_id, variant_no),
  CONSTRAINT ck_order_item_quantity CHECK (quantity > 0),
  CONSTRAINT ck_order_item_price CHECK (unit_price_paid >= 0),
  INDEX idx_order_items_variant (product_id, variant_no)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payments (
  payment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  method ENUM('Card','Wallet','Bank Transfer','Cash on Delivery') NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  pay_status ENUM('Pending','Success','Failed','Refunded') NOT NULL DEFAULT 'Pending',
  transaction_ref VARCHAR(100),
  paid_at DATETIME,
  PRIMARY KEY (payment_id),
  CONSTRAINT uq_payment_reference UNIQUE (transaction_ref),
  CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders(order_id),
  CONSTRAINT ck_payment_amount CHECK (amount > 0),
  INDEX idx_payments_order_status (order_id, pay_status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS couriers (
  courier_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  courier_name VARCHAR(100) NOT NULL,
  phone VARCHAR(25),
  tracking_url VARCHAR(255),
  PRIMARY KEY (courier_id),
  CONSTRAINT uq_couriers_name UNIQUE (courier_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS shipments (
  shipment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  courier_id BIGINT UNSIGNED NOT NULL,
  tracking_no VARCHAR(100) NOT NULL,
  ship_status ENUM('Packed','Shipped','Out for Delivery','Delivered','Failed') NOT NULL DEFAULT 'Packed',
  shipped_at DATETIME,
  delivered_at DATETIME,
  PRIMARY KEY (shipment_id),
  CONSTRAINT uq_shipments_tracking UNIQUE (tracking_no),
  CONSTRAINT fk_shipments_order FOREIGN KEY (order_id) REFERENCES orders(order_id),
  CONSTRAINT fk_shipments_courier FOREIGN KEY (courier_id) REFERENCES couriers(courier_id),
  CONSTRAINT ck_shipment_times CHECK (delivered_at IS NULL OR shipped_at IS NULL OR delivered_at >= shipped_at),
  INDEX idx_shipments_order_status (order_id, ship_status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reviews (
  review_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  line_no SMALLINT UNSIGNED NOT NULL,
  rating TINYINT UNSIGNED NOT NULL,
  title VARCHAR(120),
  comment TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (review_id),
  CONSTRAINT uq_review_order_line UNIQUE (order_id, line_no),
  CONSTRAINT fk_reviews_order_item FOREIGN KEY (order_id, line_no) REFERENCES order_items(order_id, line_no),
  CONSTRAINT ck_review_rating CHECK (rating BETWEEN 1 AND 5)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS return_requests (
  return_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  line_no SMALLINT UNSIGNED NOT NULL,
  quantity INT NOT NULL,
  reason VARCHAR(255) NOT NULL,
  return_status ENUM('Requested','Approved','Rejected','Refunded') NOT NULL DEFAULT 'Requested',
  refund_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (return_id),
  CONSTRAINT fk_returns_order_item FOREIGN KEY (order_id, line_no) REFERENCES order_items(order_id, line_no),
  CONSTRAINT ck_return_quantity CHECK (quantity > 0),
  CONSTRAINT ck_return_refund CHECK (refund_amount >= 0),
  INDEX idx_returns_status (return_status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS seller_payouts (
  payout_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  seller_id BIGINT UNSIGNED NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  gross_sales DECIMAL(14,2) NOT NULL,
  commission_amount DECIMAL(14,2) NOT NULL,
  net_amount DECIMAL(14,2) NOT NULL,
  payout_status ENUM('Pending','Paid') NOT NULL DEFAULT 'Pending',
  paid_at DATETIME,
  PRIMARY KEY (payout_id),
  CONSTRAINT uq_seller_payout_period UNIQUE (seller_id, period_start, period_end),
  CONSTRAINT fk_payouts_seller FOREIGN KEY (seller_id) REFERENCES sellers(seller_id),
  CONSTRAINT ck_payout_period CHECK (period_end >= period_start),
  CONSTRAINT ck_payout_amounts CHECK (gross_sales >= 0 AND commission_amount >= 0 AND commission_amount <= gross_sales AND net_amount = gross_sales - commission_amount),
  INDEX idx_payout_period (period_start, period_end)
) ENGINE=InnoDB;

-- The 18 relations above map directly to the submitted MarketNest ER model.
