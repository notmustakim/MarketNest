-- OPTIONAL TEMPLATE. Execute as a MySQL administrator only after changing the password.
-- Do not use the placeholder password below, and do not bundle a real credential.
USE marketnest;
CREATE ROLE IF NOT EXISTS 'marketnest_app_role';
GRANT SELECT ON marketnest.v_product_catalog TO 'marketnest_app_role';
GRANT SELECT ON marketnest.v_order_summary TO 'marketnest_app_role';
GRANT SELECT ON marketnest.v_seller_monthly_sales TO 'marketnest_app_role';
GRANT SELECT ON marketnest.customers TO 'marketnest_app_role';
GRANT SELECT ON marketnest.addresses TO 'marketnest_app_role';
GRANT SELECT ON marketnest.sellers TO 'marketnest_app_role';
GRANT SELECT ON marketnest.categories TO 'marketnest_app_role';
GRANT SELECT ON marketnest.carts TO 'marketnest_app_role';
GRANT SELECT ON marketnest.orders TO 'marketnest_app_role';
GRANT SELECT ON marketnest.return_requests TO 'marketnest_app_role';
GRANT SELECT, INSERT, UPDATE ON marketnest.products TO 'marketnest_app_role';
GRANT SELECT, INSERT, UPDATE ON marketnest.product_variants TO 'marketnest_app_role';
GRANT SELECT, INSERT, UPDATE, DELETE ON marketnest.cart_items TO 'marketnest_app_role';
GRANT INSERT ON marketnest.orders TO 'marketnest_app_role';
GRANT INSERT ON marketnest.payments TO 'marketnest_app_role';
GRANT EXECUTE ON PROCEDURE marketnest.sp_reserve_order_line TO 'marketnest_app_role';
GRANT EXECUTE ON PROCEDURE marketnest.sp_cancel_order TO 'marketnest_app_role';
GRANT EXECUTE ON PROCEDURE marketnest.sp_generate_seller_payout TO 'marketnest_app_role';
-- Example account creation (replace with a strong local secret):
-- CREATE USER 'marketnest_app'@'localhost' IDENTIFIED BY 'REPLACE_WITH_A_STRONG_PASSWORD';
-- GRANT 'marketnest_app_role' TO 'marketnest_app'@'localhost';
-- SET DEFAULT ROLE 'marketnest_app_role' TO 'marketnest_app'@'localhost';
