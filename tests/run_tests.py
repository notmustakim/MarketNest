from __future__ import annotations

import csv
import os
from pathlib import Path
from decimal import Decimal

import mysql.connector
from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(__file__).resolve().parent / "test_results.csv"


def connect(**overrides):
    options = {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "marketnest"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "autocommit": False,
    }
    options.update(overrides)
    return mysql.connector.connect(**options)


def run_case(conn, test_id, description, action):
    try:
        # End any read transaction left open by the previous case before starting this one.
        conn.rollback()
        actual = action(conn)
        return [test_id, description, actual, "PASS"]
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        return [test_id, description, f"FAIL: {type(exc).__name__}: {exc}", "FAIL"]


def rejected(conn, sql, params=()):
    conn.start_transaction()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.rollback()
        raise AssertionError("The invalid operation unexpectedly succeeded")
    except mysql.connector.Error as exc:
        conn.rollback()
        return f"Database rejected invalid input (error {exc.errno})"
    finally:
        cur.close()


def tc01(conn):
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE() AND table_type='BASE TABLE'")
    tables = [row[0] for row in cur.fetchall()]
    if len(tables) != 18:
        raise AssertionError(f"Expected 18 relations, found {len(tables)}")
    counts = {}
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM `{table}`")
        counts[table] = cur.fetchone()[0]
    cur.close()
    if min(counts.values()) < 10:
        raise AssertionError(f"At least one table has fewer than 10 rows: {counts}")
    return f"18 relations checked; minimum row count is {min(counts.values())}"


def tc02(conn):
    return rejected(conn, "UPDATE product_variants SET stock_qty=-1 WHERE product_id=1 AND variant_no=1")


def tc03(conn):
    return rejected(conn, "INSERT INTO customers(full_name,email,password_hash) VALUES('Duplicate','customer01@example.test','test-hash')")


def tc04(conn):
    return rejected(conn, "INSERT INTO cart_items(cart_id,product_id,variant_no,quantity) VALUES(999999,1,1,1)")


def tc05(conn):
    return rejected(conn, "INSERT INTO products(seller_id,category_id,product_name,status) VALUES(999999,1,'Bad foreign key','Active')")


def tc06(conn):
    return rejected(conn, "INSERT INTO orders(customer_id,address_no,order_status,subtotal,discount_amount,shipping_fee,total_amount) VALUES(1,999,'Pending',0,0,0,0)")


def tc07(conn):
    return rejected(conn, "INSERT INTO product_variants(product_id,variant_no,sku,price,stock_qty) VALUES(1,99,'MN-001-01',10,1)")


def tc08(conn):
    return rejected(conn, "INSERT INTO coupons(code,discount_type,discount_value,min_order_amount,valid_from,valid_to,usage_limit) VALUES('BAD150','Percent',150,0,'2026-01-01','2026-12-31',10)")


def tc09(conn):
    return rejected(conn, "INSERT INTO orders(customer_id,address_no,order_status,subtotal,discount_amount,shipping_fee,total_amount) VALUES(1,1,'Pending',100,0,50,120)")


def tc10(conn):
    return rejected(conn, "INSERT INTO reviews(order_id,line_no,rating,title) VALUES(12,1,6,'Invalid rating')")


def tc11(conn):
    return rejected(conn, "INSERT INTO reviews(order_id,line_no,rating,title) VALUES(15,1,5,'Not delivered')")


def tc12(conn):
    return rejected(conn, "INSERT INTO shipments(order_id,courier_id,tracking_no,ship_status) VALUES(1,1,'TRK-0001','Delivered')")


def tc13(conn):
    conn.start_transaction()
    cur = conn.cursor()
    cur.execute("SELECT product_id,variant_no,price,stock_qty FROM product_variants WHERE stock_qty > 1 ORDER BY product_id,variant_no LIMIT 1")
    product_id, variant_no, price, before_stock = cur.fetchone()
    total = float(price) + 80.0
    cur.execute("INSERT INTO orders(customer_id,address_no,order_status,subtotal,discount_amount,shipping_fee,total_amount) VALUES(1,1,'Pending',%s,0,80,%s)", (price, total))
    order_id = cur.lastrowid
    cur.execute("CALL sp_reserve_order_line(%s,1,%s,%s,1,%s)", (order_id, product_id, variant_no, price))
    cur.execute("SELECT stock_qty FROM product_variants WHERE product_id=%s AND variant_no=%s", (product_id, variant_no))
    after_stock = cur.fetchone()[0]
    conn.rollback()
    if after_stock != before_stock - 1:
        raise AssertionError(f"Expected stock {before_stock - 1}, saw {after_stock}")
    return "Stock decreased by one for an inserted order line; transaction rolled back"


def tc14(conn):
    return rejected(conn, "CALL sp_reserve_order_line(15,99,1,1,999999,1)")


def tc15(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM information_schema.views WHERE table_schema=DATABASE() AND table_name IN ('v_product_catalog','v_order_summary','v_seller_monthly_sales')")
    n = cur.fetchone()[0]
    cur.close()
    if n != 3:
        raise AssertionError(f"Expected three views, found {n}")
    return "All three reporting views are present"


def tc16(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema=DATABASE() AND routine_type='PROCEDURE' AND routine_name IN ('sp_reserve_order_line','sp_cancel_order','sp_generate_seller_payout')")
    procs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE()")
    triggers = cur.fetchone()[0]
    cur.close()
    if procs < 3 or triggers < 13:
        raise AssertionError(f"Found {procs} procedures and {triggers} triggers")
    return f"Found {procs} required procedures and {triggers} triggers"


def tc17(conn):
    conn.start_transaction()
    cur = conn.cursor()
    cur.execute("SET @test_payout_id = NULL")
    cur.execute("CALL sp_generate_seller_payout(1,'2025-01-01','2025-12-31',@test_payout_id)")
    cur.execute("SELECT @test_payout_id")
    payout_id = cur.fetchone()[0]
    conn.rollback()
    cur.close()
    if payout_id is None:
        raise AssertionError("Procedure did not return a payout ID")
    return "Payout procedure created a result inside a rolled-back test transaction"


def tc18(conn):
    conn.start_transaction()
    cur = conn.cursor()
    cur.execute("SELECT stock_qty FROM product_variants WHERE product_id=1 AND variant_no=1")
    before = cur.fetchone()[0]
    cur.execute("UPDATE product_variants SET stock_qty=stock_qty+1 WHERE product_id=1 AND variant_no=1")
    try:
        cur.execute("UPDATE product_variants SET stock_qty=-1 WHERE product_id=1 AND variant_no=1")
    except mysql.connector.Error:
        conn.rollback()
        cur.execute("SELECT stock_qty FROM product_variants WHERE product_id=1 AND variant_no=1")
        after = cur.fetchone()[0]
        cur.close()
        if after != before:
            raise AssertionError(f"Rollback did not restore stock: {before} -> {after}")
        return "Constraint failure was rolled back; original stock remained unchanged"
    conn.rollback()
    cur.close()
    raise AssertionError("Expected CHECK failure did not occur")


def tc19(conn):
    return rejected(conn, "INSERT INTO payments(order_id,method,amount,pay_status,transaction_ref) VALUES(1,'Card',100,'Success','PAY-MN-0001')")


def tc20(conn):
    try:
        bad = connect(user="marketnest_test_invalid_user", password="deliberately-wrong-password")
        bad.close()
        raise AssertionError("Unexpected connection succeeded with invalid credentials")
    except mysql.connector.Error as exc:
        return f"Database rejected the deliberately invalid account (error {exc.errno})"


def tc21(conn):
    return rejected(conn, "INSERT INTO return_requests(order_id,line_no,quantity,reason,return_status,requested_at) SELECT 12,1,quantity+1,'Test quantity limit','Requested',DATE_ADD((SELECT MAX(delivered_at) FROM shipments WHERE order_id=12),INTERVAL 1 DAY) FROM order_items WHERE order_id=12 AND line_no=1")


def tc22(conn):
    return rejected(conn, "INSERT INTO return_requests(order_id,line_no,quantity,reason,return_status,requested_at) SELECT 12,1,1,'Expired window test','Requested',DATE_ADD(MAX(delivered_at),INTERVAL 8 DAY) FROM shipments WHERE order_id=12 AND ship_status='Delivered'")


def tc23(conn):
    return rejected(conn, "INSERT INTO cart_items(cart_id,product_id,variant_no,quantity) VALUES(1,20,1,0)")


def tc24(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM v_product_catalog WHERE stock_qty > 0 AND price >= 0")
    count = cur.fetchone()[0]
    cur.close()
    if count < 1:
        raise AssertionError("Catalog query returned no available products")
    return f"Catalog query returned {count} available variants"


def tc25(conn):
    conn.start_transaction()
    cur = conn.cursor()
    cur.execute("INSERT INTO seller_payouts(seller_id,period_start,period_end,gross_sales,commission_amount,net_amount,payout_status) VALUES(1,'2025-01-01','2025-12-31',0,0,0,'Pending')")
    payout_id = cur.lastrowid
    try:
        cur.execute("UPDATE seller_payouts SET period_start='2026-01-01',period_end='2026-12-31' WHERE payout_id=%s", (payout_id,))
        conn.rollback()
        raise AssertionError("Overlapping payout update unexpectedly succeeded")
    except mysql.connector.Error as exc:
        conn.rollback()
        cur.close()
        return f"Update trigger rejected overlapping payout dates (error {exc.errno})"


def tc26(conn):
    return rejected(conn, "UPDATE return_requests SET quantity=4 WHERE return_id=1")


def tc27(conn):
    return rejected(conn, "INSERT INTO orders(customer_id,address_no,coupon_id,order_status,subtotal,discount_amount,shipping_fee,total_amount) VALUES(1,1,1,'Pending',1000,0,80,1080)")


def tc28(conn):
    return rejected(conn, "INSERT INTO categories(category_id,category_name,parent_category_id) VALUES(1000,'Self-parent test',1000)")


def tc29(conn):
    cur = conn.cursor()
    cur.execute("SELECT price,stock_qty FROM product_variants WHERE product_id=1 AND variant_no=1 FOR UPDATE")
    price, original_stock = cur.fetchone()
    if original_stock < 1:
        cur.close()
        raise AssertionError("Test variant has no available stock")
    shipping = Decimal("80.00")
    total = price + shipping
    cur.execute("INSERT INTO orders(customer_id,address_no,order_status,subtotal,discount_amount,shipping_fee,total_amount) VALUES(1,1,'Confirmed',0,0,%s,%s)", (shipping, shipping))
    order_id = cur.lastrowid
    conn.commit()
    try:
        conn.start_transaction()
        cur.callproc("sp_reserve_order_line", [order_id, 1, 1, 1, 1, price])
        cur.execute("UPDATE orders SET subtotal=%s,total_amount=%s WHERE order_id=%s", (price, total, order_id))
        cur.execute("INSERT INTO payments(order_id,method,amount,pay_status) VALUES(%s,'Cash on Delivery',%s,'Pending')", (order_id, total))
        conn.commit()
        cur.callproc("sp_cancel_order", [order_id])
        conn.commit()
        cur.execute("SELECT o.order_status,p.pay_status,pv.stock_qty FROM orders o JOIN payments p ON p.order_id=o.order_id JOIN product_variants pv ON pv.product_id=1 AND pv.variant_no=1 WHERE o.order_id=%s", (order_id,))
        status, pay_status, restored_stock = cur.fetchone()
        if status != "Cancelled" or pay_status != "Failed" or restored_stock != original_stock:
            raise AssertionError(f"Unexpected cancellation result: {status}, {pay_status}, stock {restored_stock}/{original_stock}")
        result = "Cancellation procedure updated order/payment and restored reserved stock"
    finally:
        conn.rollback()
        cur.execute("DELETE FROM payments WHERE order_id=%s", (order_id,))
        cur.execute("DELETE FROM order_items WHERE order_id=%s", (order_id,))
        cur.execute("DELETE FROM orders WHERE order_id=%s", (order_id,))
        cur.execute("UPDATE product_variants SET stock_qty=%s WHERE product_id=1 AND variant_no=1", (original_stock,))
        conn.commit()
        cur.close()
    return result


def tc30(conn):
    return rejected(conn, "UPDATE orders SET order_status='Pending' WHERE order_id=1")


def tc31(conn):
    return rejected(conn, "INSERT INTO seller_payouts(seller_id,period_start,period_end,gross_sales,commission_amount,net_amount,payout_status) VALUES(1,'2026-06-01','2026-06-30',0,0,0,'Pending')")


def tc32(conn):
    return rejected(conn, "UPDATE categories SET parent_category_id=category_id WHERE category_id=1")


def tc33(conn):
    cur = conn.cursor()
    cur.execute("SELECT rr.quantity,rr.return_status,oi.product_id,oi.variant_no,pv.stock_qty FROM return_requests rr JOIN order_items oi ON oi.order_id=rr.order_id AND oi.line_no=rr.line_no JOIN product_variants pv ON pv.product_id=oi.product_id AND pv.variant_no=oi.variant_no WHERE rr.return_id=4")
    quantity,status,product_id,variant_no,before_stock=cur.fetchone()
    if status != "Approved":
        cur.close()
        raise AssertionError(f"Expected return 4 to be Approved, found {status}")
    cur.execute("UPDATE return_requests rr JOIN order_items oi ON oi.order_id=rr.order_id AND oi.line_no=rr.line_no SET rr.return_status='Refunded',rr.refund_amount=rr.quantity*oi.unit_price_paid WHERE rr.return_id=4")
    cur.execute("SELECT stock_qty FROM product_variants WHERE product_id=%s AND variant_no=%s",(product_id,variant_no))
    after_stock=cur.fetchone()[0]
    conn.rollback()
    cur.close()
    if after_stock != before_stock + quantity:
        raise AssertionError(f"Refund did not restore inventory: {before_stock} -> {after_stock}")
    return "Refund transition restored returned units to inventory; transaction rolled back"


def tc34(conn):
    return rejected(conn, "UPDATE return_requests SET return_status='Approved' WHERE return_id=7")


def main():
    try:
        conn = connect()
    except mysql.connector.Error as exc:
        print(f"Cannot connect to MySQL: {exc}")
        print("Run the three setup SQL files, configure MYSQL_* variables, and retry.")
        raise SystemExit(2)
    cases = [
        ("TC01", "All 18 relations have at least 10 sample rows", tc01),
        ("TC02", "Negative inventory is rejected by a CHECK constraint", tc02),
        ("TC03", "Duplicate customer email is rejected", tc03),
        ("TC04", "Invalid cart foreign key is rejected", tc04),
        ("TC05", "Invalid product seller foreign key is rejected", tc05),
        ("TC06", "Order cannot reference another or missing address", tc06),
        ("TC07", "Duplicate product-variant SKU is rejected", tc07),
        ("TC08", "Percent coupon above 100 is rejected", tc08),
        ("TC09", "Incorrect order total is rejected", tc09),
        ("TC10", "Rating outside the 1-5 boundary is rejected", tc10),
        ("TC11", "Review on a non-delivered order is rejected", tc11),
        ("TC12", "Duplicate shipment tracking number is rejected", tc12),
        ("TC13", "Valid order line reserves stock", tc13),
        ("TC14", "Order-line reservation procedure prevents overselling", tc14),
        ("TC15", "Three reporting views are installed", tc15),
        ("TC16", "Required procedures and triggers are installed", tc16),
        ("TC17", "Seller payout procedure returns a payout ID", tc17),
        ("TC18", "Transaction rollback preserves original inventory", tc18),
        ("TC19", "Duplicate payment transaction reference is rejected", tc19),
        ("TC20", "Invalid database credentials are rejected", tc20),
        ("TC21", "Return quantity cannot exceed purchased units", tc21),
        ("TC22", "Return after seven-day window is rejected", tc22),
        ("TC23", "Zero cart quantity is rejected at the boundary", tc23),
        ("TC24", "Catalog report query returns available variants", tc24),
        ("TC25", "Overlapping payout periods are rejected on update", tc25),
        ("TC26", "Return quantity remains bounded after update", tc26),
        ("TC27", "Coupon discount must match coupon rule", tc27),
        ("TC28", "Category cannot be its own parent", tc28),
        ("TC29", "Cancellation restores order stock and updates payment", tc29),
        ("TC30", "Invalid order status transitions are rejected", tc30),
        ("TC31", "Overlapping payout periods are rejected on insert", tc31),
        ("TC32", "Category cannot be made its own parent by update", tc32),
        ("TC33", "Refunding an approved return restores stock", tc33),
        ("TC34", "Return status transitions are enforced", tc34),
    ]
    results = [run_case(conn, test_id, description, action) for test_id, description, action in cases]
    conn.close()
    with RESULTS.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["Test ID", "Description", "Actual Result", "Status"])
        writer.writerows(results)
    for row in results:
        print(f"{row[0]} {row[3]} - {row[1]}: {row[2]}")
    print(f"\nResults written to {RESULTS}")
    if any(row[3] != "PASS" for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
