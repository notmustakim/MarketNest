import base64, hashlib, secrets
from decimal import Decimal, ROUND_HALF_UP
import mysql.connector
import pandas as pd
import streamlit as st
from db import connect

st.set_page_config(page_title="MarketNest Admin", page_icon="🛍️", layout="wide")
st.markdown("""
<style>
[data-testid="stAppViewContainer"]{background:#f4f6f9;color:#172b3d}
[data-testid="stHeader"]{background:rgba(244,246,249,.88)}
.block-container{max-width:1500px;padding-top:1.35rem;padding-bottom:2rem}
[data-testid="stMetric"]{background:#fff;border:1px solid #e1e7ed;border-radius:12px;padding:14px 16px;box-shadow:0 3px 12px rgba(23,43,61,.04)}
[data-testid="stForm"]{background:#fff;border:1px solid #e1e7ed;border-radius:12px;padding:16px}
[data-testid="stTabs"] button{font-weight:600}
[data-testid="stTab"]{padding-top:1rem}
button[kind="primary"]{background:#1d5e70;border-color:#1d5e70}
h1,h2,h3{color:#17324d}
</style>
""",unsafe_allow_html=True)
head,refresh=st.columns([8,1])
head.title("MarketNest")
head.caption("Marketplace Operations")
if refresh.button("Refresh data",type="primary",use_container_width=True,key="manual_refresh"):
    st.rerun()

def fetch_df(sql,params=()):
    conn=connect()
    try:
        cur=conn.cursor(dictionary=True); cur.execute(sql,params); rows=cur.fetchall(); cur.close()
        return pd.DataFrame(rows)
    finally: conn.close()

def show_table(data):
    try: st.dataframe(data,width="stretch",hide_index=True)
    except TypeError: st.dataframe(data,use_container_width=True,hide_index=True)

def mutate(sql,params=()):
    conn=connect()
    try:
        cur=conn.cursor(); cur.execute(sql,params); result=cur.lastrowid; conn.commit(); cur.close(); return result
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

def notice(message,level="success"):
    if level=="success": st.toast(message)
    else: getattr(st,level)(message)

def make_password_hash():
    secret=secrets.token_bytes(32); salt=secrets.token_hex(16); rounds=210000
    digest=hashlib.pbkdf2_hmac("sha256",secret,salt.encode(),rounds)
    return f"pbkdf2_sha256${rounds}${salt}${base64.b64encode(digest).decode('ascii')}"

def create_customer_record(name,email,phone,label,street,city,postal):
    conn=connect()
    try:
        cur=conn.cursor()
        cur.execute("INSERT INTO customers(full_name,email,phone,password_hash,status) VALUES(%s,%s,%s,%s,'Active')",(name,email,phone or None,make_password_hash()))
        customer_id=cur.lastrowid
        cur.execute("INSERT INTO addresses(customer_id,address_no,label,street_line,city,postal_code,is_default) VALUES(%s,1,%s,%s,%s,%s,1)",(customer_id,label or "Home",street,city,postal or None))
        cur.execute("INSERT INTO carts(customer_id) VALUES(%s)",(customer_id,))
        conn.commit(); cur.close(); return int(customer_id)
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

def transactional_delete(action):
    conn=connect()
    try:
        cur=conn.cursor()
        result=action(cur)
        conn.commit()
        cur.close()
        return result
    except Exception:
        conn.rollback()
        raise
    finally: conn.close()

def delete_product_record(product_id):
    def action(cur):
        cur.execute("SELECT COUNT(*) FROM order_items WHERE product_id=%s",(product_id,))
        if cur.fetchone()[0]: raise ValueError("This product has order history. Hide the listing to preserve past orders.")
        cur.execute("DELETE FROM cart_items WHERE product_id=%s",(product_id,))
        cur.execute("DELETE FROM wishlist_items WHERE product_id=%s",(product_id,))
        cur.execute("DELETE FROM product_variants WHERE product_id=%s",(product_id,))
        cur.execute("DELETE FROM products WHERE product_id=%s",(product_id,))
    return transactional_delete(action)

def delete_variant_record(product_id,variant_no):
    def action(cur):
        cur.execute("SELECT COUNT(*) FROM order_items WHERE product_id=%s AND variant_no=%s",(product_id,variant_no))
        if cur.fetchone()[0]: raise ValueError("This variant appears in order history and cannot be deleted.")
        cur.execute("DELETE FROM cart_items WHERE product_id=%s AND variant_no=%s",(product_id,variant_no))
        cur.execute("DELETE FROM product_variants WHERE product_id=%s AND variant_no=%s",(product_id,variant_no))
    return transactional_delete(action)

def delete_customer_record(customer_id):
    def action(cur):
        cur.execute("SELECT COUNT(*) FROM orders WHERE customer_id=%s",(customer_id,))
        if cur.fetchone()[0]: raise ValueError("This customer has order history. Suspend the account to retain the transaction record.")
        cur.execute("DELETE ci FROM cart_items ci JOIN carts ca ON ca.cart_id=ci.cart_id WHERE ca.customer_id=%s",(customer_id,))
        cur.execute("DELETE FROM carts WHERE customer_id=%s",(customer_id,))
        cur.execute("DELETE FROM wishlist_items WHERE customer_id=%s",(customer_id,))
        cur.execute("DELETE FROM addresses WHERE customer_id=%s",(customer_id,))
        cur.execute("DELETE FROM customers WHERE customer_id=%s",(customer_id,))
    return transactional_delete(action)

def delete_address_record(customer_id,address_no):
    def action(cur):
        cur.execute("SELECT COUNT(*) FROM orders WHERE customer_id=%s AND address_no=%s",(customer_id,address_no))
        if cur.fetchone()[0]: raise ValueError("This address is attached to order history and cannot be deleted.")
        cur.execute("SELECT COUNT(*),MAX(is_default) FROM addresses WHERE customer_id=%s",(customer_id,))
        count,is_default=cur.fetchone()
        if count<=1: raise ValueError("Keep at least one delivery address for this customer.")
        if is_default:
            cur.execute("SELECT address_no FROM addresses WHERE customer_id=%s AND address_no<>%s ORDER BY address_no LIMIT 1",(customer_id,address_no))
            replacement=cur.fetchone()[0]
            cur.execute("UPDATE addresses SET is_default=0 WHERE customer_id=%s AND address_no=%s",(customer_id,address_no))
            cur.execute("UPDATE addresses SET is_default=1 WHERE customer_id=%s AND address_no=%s",(customer_id,replacement))
        cur.execute("DELETE FROM addresses WHERE customer_id=%s AND address_no=%s",(customer_id,address_no))
    return transactional_delete(action)

def delete_seller_record(seller_id):
    def action(cur):
        cur.execute("SELECT COUNT(*) FROM products WHERE seller_id=%s",(seller_id,))
        if cur.fetchone()[0]: raise ValueError("This seller owns product listings. Delete eligible products first, or suspend the seller.")
        cur.execute("DELETE FROM sellers WHERE seller_id=%s",(seller_id,))
    return transactional_delete(action)

def delete_category_record(category_id):
    def action(cur):
        cur.execute("SELECT (SELECT COUNT(*) FROM products WHERE category_id=%s)+(SELECT COUNT(*) FROM categories WHERE parent_category_id=%s)",(category_id,category_id))
        if cur.fetchone()[0]: raise ValueError("This category contains products or subcategories and cannot be deleted.")
        cur.execute("DELETE FROM categories WHERE category_id=%s",(category_id,))
    return transactional_delete(action)

def delete_coupon_record(coupon_id):
    def action(cur):
        cur.execute("SELECT COUNT(*) FROM orders WHERE coupon_id=%s",(coupon_id,))
        if cur.fetchone()[0]: raise ValueError("This coupon is part of order history and cannot be deleted.")
        cur.execute("DELETE FROM coupons WHERE coupon_id=%s",(coupon_id,))
    return transactional_delete(action)

def delete_courier_record(courier_id):
    def action(cur):
        cur.execute("SELECT COUNT(*) FROM shipments WHERE courier_id=%s",(courier_id,))
        if cur.fetchone()[0]: raise ValueError("This courier has shipment history and cannot be deleted.")
        cur.execute("DELETE FROM couriers WHERE courier_id=%s",(courier_id,))
    return transactional_delete(action)

def options(frame,label_fn,value_fn):
    labels=[label_fn(r) for r in frame.itertuples(index=False)]
    return labels,{label_fn(r):value_fn(r) for r in frame.itertuples(index=False)}

try:
    summary=fetch_df("SELECT order_status,COUNT(*) AS order_count,SUM(total_amount) AS order_value FROM orders GROUP BY order_status")
    stock_metric=fetch_df("SELECT COUNT(*) AS n FROM product_variants WHERE stock_qty<=10")
    sales=fetch_df("SELECT DATE_FORMAT(order_date,'%Y-%m') AS month,SUM(total_amount) AS sales FROM orders WHERE order_status='Delivered' GROUP BY DATE_FORMAT(order_date,'%Y-%m') ORDER BY month")
    if not sales.empty: sales["sales"]=sales["sales"].astype(float)
    catalog_metric=fetch_df("SELECT COUNT(*) AS n FROM v_product_catalog")
except mysql.connector.Error as exc:
    st.error("Unable to connect to the MarketNest database. Check the connection settings and confirm MySQL is running.")
    with st.expander("Connection details"):
        st.code(str(exc))
    st.stop()
metrics=st.columns(4)
metrics[0].metric("Catalog variants",int(catalog_metric.iloc[0]["n"]))
metrics[1].metric("Total orders",int(summary["order_count"].sum()) if not summary.empty else 0)
metrics[2].metric("Delivered revenue",f"৳{float(sales['sales'].sum()):,.2f}" if not sales.empty else "৳0.00")
metrics[3].metric("Low-stock items",int(stock_metric.iloc[0]["n"]))
(tab_home,tab_catalog,tab_people,tab_checkout,tab_orders,tab_returns,tab_finance)=st.tabs([
    "Overview","Catalog & sellers","Customers & carts","Checkout","Orders & shipping","Returns & reviews","Payments & reports"])

with tab_home:
    st.subheader("Marketplace overview")
    left,right=st.columns([1.25,1])
    with left:
        st.markdown("**Delivered revenue by month**")
        if not sales.empty: _chart=st.bar_chart(sales.set_index("month"),y="sales",color="#287c86")
        else: st.info("No delivered sales in this period.")
    with right:
        st.markdown("**Orders by status**")
        if not summary.empty:
            _chart=st.bar_chart(summary.set_index("order_status")["order_count"],color="#426b8a")
        else:
            st.info("No orders yet.")
    st.markdown("**Recent orders**")
    recent=fetch_df("SELECT order_id,full_name,order_date,order_status,total_amount FROM v_order_summary ORDER BY order_date DESC LIMIT 8")
    show_table(recent)

with tab_catalog:
    listing_tab,variant_tab,seller_tab,category_tab=st.tabs(["Listings","Variants","Sellers","Categories"])
    with listing_tab:
        st.subheader("Product catalog")
        listing=fetch_df("""SELECT p.product_id,p.product_name,p.brand_name,p.status AS product_status,s.store_name,
          s.status AS seller_status,c.category_name,pv.variant_no,pv.sku,pv.color,pv.size,pv.price,pv.stock_qty,
          COALESCE((SELECT AVG(r.rating) FROM order_items oi JOIN reviews r ON r.order_id=oi.order_id AND r.line_no=oi.line_no
                    WHERE oi.product_id=pv.product_id AND oi.variant_no=pv.variant_no),0) AS average_rating
          FROM products p JOIN sellers s ON s.seller_id=p.seller_id JOIN categories c ON c.category_id=p.category_id
          JOIN product_variants pv ON pv.product_id=p.product_id ORDER BY p.product_name,pv.variant_no""")
        if not listing.empty:
            filter_cols=st.columns([1.5,1,1,1.2,1])
            search=filter_cols[0].text_input("Search catalog",placeholder="Name, SKU, color, size",key="catalog_search")
            seller_options=["All sellers"]+sorted(listing["store_name"].dropna().unique().tolist())
            category_options=["All categories"]+sorted(listing["category_name"].dropna().unique().tolist())
            selected_seller=filter_cols[1].selectbox("Seller",seller_options,key="catalog_seller_filter")
            selected_category=filter_cols[2].selectbox("Category",category_options,key="catalog_category_filter")
            low=float(listing["price"].min()); high=float(listing["price"].max()); slider_high=max(high,low+1.0)
            price_range=filter_cols[3].slider("Price range",min_value=low,max_value=slider_high,value=(low,high),step=1.0,key="catalog_price_filter")
            min_rating=filter_cols[4].slider("Min. rating",min_value=0.0,max_value=5.0,value=0.0,step=0.5,key="catalog_rating_filter")
            filtered=listing.copy()
            if search.strip():
                needle=search.strip().casefold()
                searchable=filtered[["product_name","brand_name","store_name","category_name","sku","color","size"]].fillna("").astype(str).agg(" ".join,axis=1).str.casefold()
                filtered=filtered[searchable.str.contains(needle,regex=False)]
            if selected_seller!="All sellers": filtered=filtered[filtered["store_name"]==selected_seller]
            if selected_category!="All categories": filtered=filtered[filtered["category_name"]==selected_category]
            filtered=filtered[(filtered["price"].astype(float)>=price_range[0])&(filtered["price"].astype(float)<=price_range[1])&(filtered["average_rating"].astype(float)>=min_rating)]
            st.caption(f"{len(filtered)} matching variants")
            show_table(filtered)
        else:
            products=fetch_df("SELECT product_id,product_name,status FROM products ORDER BY product_name")
            st.info("No listings match the current catalog.")
        sellers=fetch_df("SELECT seller_id,store_name FROM sellers WHERE status='Active' ORDER BY store_name")
        categories=fetch_df("SELECT category_id,category_name FROM categories ORDER BY category_name")
        with st.expander("Add product",expanded=False):
            if sellers.empty: st.info("Add a seller, then approve it before listing products.")
            elif categories.empty: st.info("Create a category first.")
            else:
                sl,sm=options(sellers,lambda r:f"{r.store_name} (#{r.seller_id})",lambda r:int(r.seller_id))
                cl,cm=options(categories,lambda r:f"{r.category_name} (#{r.category_id})",lambda r:int(r.category_id))
                with st.form("new_product_form"):
                    c1,c2=st.columns(2); seller_label=c1.selectbox("Seller",sl); category_label=c2.selectbox("Category",cl)
                    c1,c2=st.columns(2); name=c1.text_input("Product name"); brand=c2.text_input("Brand")
                    description=st.text_area("Description",height=70)
                    st.markdown("**First variant**")
                    c1,c2,c3,c4=st.columns(4); sku=c1.text_input("Unique SKU"); color=c2.text_input("Color"); size=c3.text_input("Size"); price=c4.number_input("Price",min_value=0.01,step=50.0)
                    c1,c2=st.columns(2); stock=c1.number_input("Initial stock",min_value=0,step=1); status=c2.selectbox("Listing status",["Active","Draft"])
                    create=st.form_submit_button("Create product")
                if create:
                    if not name.strip() or not sku.strip(): st.error("Product name and SKU are required.")
                    else:
                        conn=connect()
                        try:
                            cur=conn.cursor()
                            cur.execute("INSERT INTO products(seller_id,category_id,product_name,description,brand_name,status) VALUES(%s,%s,%s,%s,%s,%s)",(sm[seller_label],cm[category_label],name.strip(),description.strip() or None,brand.strip() or None,status))
                            product_id=cur.lastrowid
                            cur.execute("INSERT INTO product_variants(product_id,variant_no,sku,color,size,price,stock_qty) VALUES(%s,1,%s,%s,%s,%s,%s)",(product_id,sku.strip(),color.strip() or None,size.strip() or None,price,stock))
                            conn.commit(); cur.close(); notice(f"Product #{product_id} created with its first variant.")
                        except Exception as exc: conn.rollback(); st.error(f"Product was not saved: {exc}")
                        finally: conn.close()
        products=fetch_df("SELECT product_id,product_name,status FROM products ORDER BY product_name")
        if not products.empty:
            pl,pm=options(products,lambda r:f"{r.product_name} (#{r.product_id}) · {r.status}",lambda r:int(r.product_id))
            p_label=st.selectbox("Product",pl,key="listing_product_choice")
            current_product_status=products.loc[products["product_id"]==pm[p_label],"status"].iloc[0]
            with st.form("product_status_form"):
                new_status=st.selectbox("Listing status",["Active","Draft","Hidden"],index=["Active","Draft","Hidden"].index(current_product_status)); update=st.form_submit_button("Update listing")
            if update: mutate("UPDATE products SET status=%s WHERE product_id=%s",(new_status,pm[p_label])); notice("Listing status updated.")
            product_records=fetch_df("SELECT product_id,product_name,brand_name,description,category_id FROM products ORDER BY product_name")
            if not categories.empty:
                detail_labels,detail_map=options(product_records,lambda r:f"{r.product_name} (#{r.product_id})",lambda r:int(r.product_id))
                category_labels,category_map=options(categories,lambda r:f"{r.category_name} (#{r.category_id})",lambda r:int(r.category_id))
                with st.expander("Edit product details"):
                    selected_product=st.selectbox("Product record",detail_labels,key="edit_product_choice")
                    product_id=detail_map[selected_product]; product_row=product_records.loc[product_records["product_id"]==product_id].iloc[0]
                    current_category=next(label for label,value in category_map.items() if value==int(product_row.category_id))
                    with st.form("edit_product_form"):
                        c1,c2=st.columns(2); edit_product_name=c1.text_input("Product name",value=product_row.product_name,key=f"product_name_{product_id}"); edit_brand=c2.text_input("Brand",value=product_row.brand_name or "",key=f"product_brand_{product_id}")
                        edit_description=st.text_area("Description",value=product_row.description or "",key=f"product_description_{product_id}")
                        edit_category=st.selectbox("Category",category_labels,index=category_labels.index(current_category),key=f"product_category_{product_id}")
                        save_product=st.form_submit_button("Save product details")
                    if save_product:
                        if not edit_product_name.strip(): st.error("Product name is required.")
                        else:
                            mutate("UPDATE products SET product_name=%s,brand_name=%s,description=%s,category_id=%s WHERE product_id=%s",(edit_product_name.strip(),edit_brand.strip() or None,edit_description.strip() or None,category_map[edit_category],product_id)); notice("Product details updated.")
            with st.expander("Delete product listing"):
                delete_label=st.selectbox("Product to delete",pl,key="delete_product_choice")
                with st.form("delete_product_form"):
                    confirm_delete=st.checkbox("I understand this removes the product, its variants, cart lines, and wishlist entries.")
                    delete=st.form_submit_button("Delete product",type="primary")
                if delete:
                    if not confirm_delete: st.warning("Confirm the deletion to continue.")
                    else:
                        try: delete_product_record(pm[delete_label]); notice("Product deleted.")
                        except Exception as exc: st.error(str(exc))
    with variant_tab:
        st.subheader("Product variants")
        products=fetch_df("SELECT product_id,product_name,status FROM products ORDER BY product_name")
        if products.empty: st.info("Create a product first.")
        else:
            pl,pm=options(products,lambda r:f"{r.product_name} (#{r.product_id})",lambda r:int(r.product_id))
            with st.form("add_variant_form"):
                product_label=st.selectbox("Product",pl); c1,c2,c3=st.columns(3)
                sku=c1.text_input("Unique SKU"); color=c2.text_input("Color"); size=c3.text_input("Size")
                c1,c2=st.columns(2); price=c1.number_input("Price",min_value=0.01,step=50.0); stock=c2.number_input("Initial stock",min_value=0,step=1)
                add=st.form_submit_button("Add variant")
            if add:
                if not sku.strip(): st.error("SKU is required.")
                else:
                    conn=connect()
                    try:
                        cur=conn.cursor(); pid=pm[product_label]
                        cur.execute("SELECT COALESCE(MAX(variant_no),0)+1 FROM product_variants WHERE product_id=%s",(pid,)); vno=int(cur.fetchone()[0])
                        cur.execute("INSERT INTO product_variants(product_id,variant_no,sku,color,size,price,stock_qty) VALUES(%s,%s,%s,%s,%s,%s,%s)",(pid,vno,sku.strip(),color.strip() or None,size.strip() or None,price,stock))
                        conn.commit(); cur.close(); notice(f"Variant {vno} added to product #{pid}.")
                    except Exception as exc: conn.rollback(); st.error(f"Variant was not saved: {exc}")
                    finally: conn.close()
        variants=fetch_df("SELECT pv.product_id,p.product_name,pv.variant_no,pv.sku,pv.color,pv.size,pv.price,pv.stock_qty FROM product_variants pv JOIN products p ON p.product_id=pv.product_id ORDER BY p.product_name,pv.variant_no")
        if not variants.empty:
            vl,vm=options(variants,lambda r:f"{r.product_name} · {r.sku} · {r.color or 'Color n/a'} · {r.size or 'Size n/a'} · stock {r.stock_qty}",lambda r:(int(r.product_id),int(r.variant_no),int(r.stock_qty),float(r.price)))
            stock_label=st.selectbox("Variant to adjust",vl,key="inventory_variant_select")
            stock_pid,stock_vno,current_stock,current_price=vm[stock_label]
            with st.form("inventory_adjustment_form"):
                new_stock=st.number_input("Set available stock",min_value=0,value=current_stock,step=1,key=f"inventory_value_{stock_pid}_{stock_vno}")
                new_price=st.number_input("Set unit price",min_value=0.0,value=current_price,step=50.0,key=f"price_value_{stock_pid}_{stock_vno}")
                adjust=st.form_submit_button("Save changes")
            if adjust:
                mutate("UPDATE product_variants SET stock_qty=%s,price=%s WHERE product_id=%s AND variant_no=%s",(int(new_stock),new_price,stock_pid,stock_vno)); notice("Variant price and inventory updated.")
            with st.expander("Delete product variant"):
                variant_to_delete=st.selectbox("Variant to delete",vl,key="delete_variant_choice")
                with st.form("delete_variant_form"):
                    confirm_variant_delete=st.checkbox("Confirm deletion of this variant")
                    delete_variant=st.form_submit_button("Delete variant",type="primary")
                if delete_variant:
                    if not confirm_variant_delete: st.warning("Confirm the deletion to continue.")
                    else:
                        pid,vno,*_=vm[variant_to_delete]
                        try: delete_variant_record(pid,vno); notice("Variant deleted.")
                        except Exception as exc: st.error(str(exc))
        show_table(variants)

    with seller_tab:
        st.subheader("Seller management")
        sellers=fetch_df("SELECT seller_id,store_name,email,phone,tax_id,commission_rate,status,joined_on FROM sellers ORDER BY seller_id")
        show_table(sellers)
        with st.expander("Add seller"):
            with st.form("new_seller_form"):
                c1,c2=st.columns(2); store=c1.text_input("Store name"); email=c2.text_input("Email")
                c1,c2,c3=st.columns(3); phone=c1.text_input("Phone"); tax_id=c2.text_input("Tax / registration ID"); commission=c3.number_input("Commission %",min_value=0.0,max_value=100.0,value=10.0,step=0.5)
                seller_status=st.selectbox("Account status",["Pending","Active"],index=0,help="Pending sellers require approval before listing products.")
                add_seller=st.form_submit_button("Add seller")
        if add_seller:
            if not store.strip() or not email.strip() or not tax_id.strip(): st.error("Store name, email, and tax ID are required.")
            else:
                try: mutate("INSERT INTO sellers(store_name,email,phone,tax_id,commission_rate,status) VALUES(%s,%s,%s,%s,%s,%s)",(store.strip(),email.strip(),phone.strip() or None,tax_id.strip(),commission,seller_status)); notice(f"Seller added as {seller_status}.")
                except mysql.connector.Error as exc: st.error(f"Seller was not saved: {exc}")
        pending=fetch_df("SELECT seller_id,store_name FROM sellers WHERE status='Pending' ORDER BY store_name")
        if not pending.empty:
            labels,mapping=options(pending,lambda r:f"{r.store_name} (#{r.seller_id})",lambda r:int(r.seller_id))
            with st.form("approve_seller_form"):
                selected=st.selectbox("Pending seller",labels); approve=st.form_submit_button("Approve seller")
            if approve: mutate("UPDATE sellers SET status='Active' WHERE seller_id=%s",(mapping[selected],)); notice("Seller approved and can now list products.")
        all_sellers=fetch_df("SELECT seller_id,store_name,status FROM sellers ORDER BY store_name")
        if not all_sellers.empty:
            all_labels,all_map=options(all_sellers,lambda r:f"{r.store_name} (#{r.seller_id}) · {r.status}",lambda r:int(r.seller_id))
            seller_label=st.selectbox("Seller account",all_labels,key="seller_status_choice")
            current_seller_status=all_sellers.loc[all_sellers["seller_id"]==all_map[seller_label],"status"].iloc[0]
            with st.form("seller_status_form"):
                seller_status_new=st.selectbox("Set account status",["Pending","Active","Suspended"],index=["Pending","Active","Suspended"].index(current_seller_status)); status_save=st.form_submit_button("Save seller status")
            if status_save: mutate("UPDATE sellers SET status=%s WHERE seller_id=%s",(seller_status_new,all_map[seller_label])); notice("Seller status updated.")
            with st.expander("Delete seller"):
                seller_to_delete=st.selectbox("Seller to delete",all_labels,key="delete_seller_choice")
                with st.form("delete_seller_form"):
                    confirm_seller_delete=st.checkbox("Confirm seller deletion")
                    delete_seller=st.form_submit_button("Delete seller",type="primary")
                if delete_seller:
                    if not confirm_seller_delete: st.warning("Confirm the deletion to continue.")
                    else:
                        try: delete_seller_record(all_map[seller_to_delete]); notice("Seller deleted.")
                        except Exception as exc: st.error(str(exc))

    with category_tab:
        st.subheader("Categories")
        cats=fetch_df("SELECT c.category_id,c.category_name,c.parent_category_id,p.category_name AS parent_category FROM categories c LEFT JOIN categories p ON p.category_id=c.parent_category_id ORDER BY c.category_name")
        show_table(cats)
        with st.expander("Add category"):
            with st.form("new_category_form"):
                name=st.text_input("Category name"); labels=["No parent"]+[f"{r.category_name} (#{r.category_id})" for r in cats.itertuples()]
                parents={f"{r.category_name} (#{r.category_id})":int(r.category_id) for r in cats.itertuples()}
                parent=st.selectbox("Parent category",labels); add_category=st.form_submit_button("Add category")
        if add_category:
            if not name.strip(): st.error("Category name is required.")
            else:
                try: mutate("INSERT INTO categories(category_name,parent_category_id) VALUES(%s,%s)",(name.strip(),parents.get(parent))); notice("Category added.")
                except mysql.connector.Error as exc: st.error(f"Category was not saved: {exc}")
        if not cats.empty:
            cat_labels,cat_map=options(cats,lambda r:f"{r.category_name} (#{r.category_id})",lambda r:int(r.category_id))
            with st.expander("Edit category"):
                selected_category=st.selectbox("Category record",cat_labels,key="edit_category_choice")
                category_id=cat_map[selected_category]; category_row=cats.loc[cats["category_id"]==category_id].iloc[0]
                edit_parent_labels=["No parent"]+[label for label in cat_labels if cat_map[label]!=category_id]
                edit_parent_map={"No parent":None}|{label:cat_map[label] for label in cat_labels if cat_map[label]!=category_id}
                current_parent="No parent" if pd.isna(category_row.parent_category_id) else next((label for label,value in edit_parent_map.items() if value==int(category_row.parent_category_id)),"No parent")
                with st.form("edit_category_form"):
                    edit_category_name=st.text_input("Category name",value=category_row.category_name,key=f"category_name_{category_id}")
                    edit_category_parent=st.selectbox("Parent category",edit_parent_labels,index=edit_parent_labels.index(current_parent),key=f"category_parent_{category_id}")
                    save_category=st.form_submit_button("Save category")
                if save_category:
                    if not edit_category_name.strip(): st.error("Category name is required.")
                    else:
                        try: mutate("UPDATE categories SET category_name=%s,parent_category_id=%s WHERE category_id=%s",(edit_category_name.strip(),edit_parent_map[edit_category_parent],category_id)); notice("Category updated.")
                        except mysql.connector.Error as exc: st.error(f"Category was not updated: {exc}")
            with st.expander("Delete unused category"):
                category_to_delete=st.selectbox("Category to delete",cat_labels,key="delete_category_choice")
                with st.form("delete_category_form"):
                    confirm_category_delete=st.checkbox("Confirm category deletion")
                    delete_category=st.form_submit_button("Delete category",type="primary")
                if delete_category:
                    if not confirm_category_delete: st.warning("Confirm the deletion to continue.")
                    else:
                        try: delete_category_record(cat_map[category_to_delete]); notice("Category deleted.")
                        except Exception as exc: st.error(str(exc))

with tab_people:
    customer_tab,cart_tab=st.tabs(["Customers & addresses","Cart builder & wishlist"])
    with customer_tab:
        st.subheader("Customers")
        customers=fetch_df("SELECT c.customer_id,c.full_name,c.email,c.phone,c.status,COUNT(DISTINCT a.address_no) AS address_count,COUNT(DISTINCT ci.product_id,ci.variant_no) AS cart_line_count FROM customers c LEFT JOIN addresses a ON a.customer_id=c.customer_id LEFT JOIN carts ca ON ca.customer_id=c.customer_id LEFT JOIN cart_items ci ON ci.cart_id=ca.cart_id GROUP BY c.customer_id,c.full_name,c.email,c.phone,c.status ORDER BY c.full_name")
        show_table(customers)
        if not customers.empty:
            customer_labels,customer_map=options(customers,lambda r:f"{r.full_name} (#{r.customer_id}) · {r.status}",lambda r:int(r.customer_id))
            with st.expander("Update customer profile and status"):
                selected_customer=st.selectbox("Customer record",customer_labels,key="customer_edit_choice")
                selected_id=customer_map[selected_customer]; record=customers.loc[customers["customer_id"]==selected_id].iloc[0]
                with st.form("customer_profile_form"):
                    c1,c2=st.columns(2); edit_name=c1.text_input("Full name",value=record.full_name,key=f"customer_name_{selected_id}"); edit_email=c2.text_input("Email",value=record.email,key=f"customer_email_{selected_id}")
                    c1,c2=st.columns(2); edit_phone=c1.text_input("Phone",value=record.phone or "",key=f"customer_phone_{selected_id}"); edit_status=c2.selectbox("Account status",["Active","Suspended"],index=0 if record.status=="Active" else 1,key=f"customer_status_{selected_id}")
                    update_customer=st.form_submit_button("Save customer")
                if update_customer:
                    if not edit_name.strip() or not edit_email.strip(): st.error("Name and email are required.")
                    else:
                        try: mutate("UPDATE customers SET full_name=%s,email=%s,phone=%s,status=%s WHERE customer_id=%s",(edit_name.strip(),edit_email.strip(),edit_phone.strip() or None,edit_status,selected_id)); notice("Customer updated.")
                        except mysql.connector.Error as exc: st.error(f"Customer was not updated: {exc}")
            with st.expander("Delete customer"):
                delete_customer_label=st.selectbox("Customer to delete",customer_labels,key="delete_customer_choice")
                with st.form("delete_customer_form"):
                    confirm_customer_delete=st.checkbox("Confirm deletion of this customer and their non-order records")
                    delete_customer=st.form_submit_button("Delete customer",type="primary")
                if delete_customer:
                    if not confirm_customer_delete: st.warning("Confirm the deletion to continue.")
                    else:
                        try: delete_customer_record(customer_map[delete_customer_label]); notice("Customer deleted.")
                        except Exception as exc: st.error(str(exc))
        with st.expander("Add customer"):
            with st.form("register_customer_form"):
                c1,c2=st.columns(2); name=c1.text_input("Full name"); email=c2.text_input("Email")
                c1,c2,c3=st.columns(3); phone=c1.text_input("Phone"); city=c2.text_input("City"); postal=c3.text_input("Postal code")
                street=st.text_input("Street address"); address_label=st.text_input("Address label",value="Home")
                create=st.form_submit_button("Create customer")
        if create:
            if not name.strip() or not email.strip() or not city.strip() or not street.strip(): st.error("Name, email, city, and street are required.")
            else:
                try:
                    cid=create_customer_record(name.strip(),email.strip(),phone.strip() or None,address_label.strip() or "Home",street.strip(),city.strip(),postal.strip() or None)
                    notice(f"Customer #{cid} created with an address and an empty cart.")
                except Exception as exc: st.error(f"Customer was not created: {exc}")
        customers=fetch_df("SELECT customer_id,full_name FROM customers ORDER BY full_name")
        if not customers.empty:
            cl,cm=options(customers,lambda r:f"{r.full_name} (#{r.customer_id})",lambda r:int(r.customer_id))
            with st.expander("Add delivery address"):
                with st.form("additional_address_form"):
                    customer_label=st.selectbox("Customer",cl); c1,c2=st.columns(2)
                    label=c1.text_input("Address label",key="address_label_2"); city=c2.text_input("City",key="address_city_2")
                    street=st.text_input("Street address",key="address_street_2"); postal=st.text_input("Postal code",key="address_postal_2")
                    default=st.checkbox("Make default address",key="address_default_2"); save=st.form_submit_button("Add address")
            if save:
                if not city.strip() or not street.strip(): st.error("City and street are required.")
                else:
                    conn=connect()
                    try:
                        cur=conn.cursor(); cid=cm[customer_label]
                        cur.execute("SELECT COALESCE(MAX(address_no),0)+1 FROM addresses WHERE customer_id=%s",(cid,)); no=int(cur.fetchone()[0])
                        if default: cur.execute("UPDATE addresses SET is_default=0 WHERE customer_id=%s",(cid,))
                        cur.execute("INSERT INTO addresses(customer_id,address_no,label,street_line,city,postal_code,is_default) VALUES(%s,%s,%s,%s,%s,%s,%s)",(cid,no,label.strip() or "Other",street.strip(),city.strip(),postal.strip() or None,int(default)))
                        conn.commit(); cur.close(); notice(f"Address #{no} added.")
                    except Exception as exc: conn.rollback(); st.error(f"Address was not saved: {exc}")
                    finally: conn.close()
        address_records=fetch_df("SELECT a.customer_id,a.address_no,c.full_name,a.label,a.street_line,a.city,a.postal_code,a.is_default FROM addresses a JOIN customers c ON c.customer_id=a.customer_id ORDER BY c.full_name,a.address_no")
        if not address_records.empty:
            address_labels,address_map=options(address_records,lambda r:f"{r.full_name} · {r.label} · {r.street_line}, {r.city} (#{r.customer_id}/{r.address_no})",lambda r:(int(r.customer_id),int(r.address_no)))
            with st.expander("Edit delivery address"):
                selected_address=st.selectbox("Address record",address_labels,key="address_edit_choice")
                address_customer,address_no=address_map[selected_address]; address_row=address_records[(address_records["customer_id"]==address_customer)&(address_records["address_no"]==address_no)].iloc[0]
                with st.form("address_edit_form"):
                    c1,c2=st.columns(2); edit_label=c1.text_input("Address label",value=address_row.label,key=f"address_edit_label_{address_customer}_{address_no}"); edit_city=c2.text_input("City",value=address_row.city,key=f"address_edit_city_{address_customer}_{address_no}")
                    edit_street=st.text_input("Street address",value=address_row.street_line,key=f"address_edit_street_{address_customer}_{address_no}"); edit_postal=st.text_input("Postal code",value=address_row.postal_code or "",key=f"address_edit_postal_{address_customer}_{address_no}")
                    edit_default=st.checkbox("Set as default address",value=bool(address_row.is_default),key=f"address_edit_default_{address_customer}_{address_no}"); save_address=st.form_submit_button("Save address")
                if save_address:
                    if not edit_city.strip() or not edit_street.strip(): st.error("City and street are required.")
                    else:
                        conn=connect()
                        try:
                            cur=conn.cursor()
                            if edit_default: cur.execute("UPDATE addresses SET is_default=0 WHERE customer_id=%s",(address_customer,))
                            cur.execute("UPDATE addresses SET label=%s,street_line=%s,city=%s,postal_code=%s,is_default=%s WHERE customer_id=%s AND address_no=%s",(edit_label.strip() or "Other",edit_street.strip(),edit_city.strip(),edit_postal.strip() or None,int(edit_default),address_customer,address_no))
                            conn.commit(); cur.close(); notice("Address updated.")
                        except Exception as exc: conn.rollback(); st.error(f"Address was not updated: {exc}")
                        finally: conn.close()
            with st.expander("Delete delivery address"):
                address_to_delete=st.selectbox("Address to delete",address_labels,key="delete_address_choice")
                with st.form("delete_address_form"):
                    confirm_address_delete=st.checkbox("Confirm deletion of this address")
                    delete_address=st.form_submit_button("Delete address",type="primary")
                if delete_address:
                    if not confirm_address_delete: st.warning("Confirm the deletion to continue.")
                    else:
                        cid,address_no=address_map[address_to_delete]
                        try: delete_address_record(cid,address_no); notice("Address deleted.")
                        except Exception as exc: st.error(str(exc))
    with cart_tab:
        st.subheader("Build a cart")
        customers=fetch_df("SELECT customer_id,full_name FROM customers WHERE status='Active' ORDER BY full_name")
        variants=fetch_df("SELECT p.product_id,p.product_name,pv.variant_no,pv.sku,pv.color,pv.size,pv.price,pv.stock_qty FROM products p JOIN product_variants pv ON pv.product_id=p.product_id WHERE p.status='Active' AND pv.stock_qty>0 ORDER BY p.product_name,pv.variant_no")
        if customers.empty: st.info("Create a customer first.")
        elif variants.empty: st.info("No active in-stock variants are available.")
        else:
            cl,cm=options(customers,lambda r:f"{r.full_name} (#{r.customer_id})",lambda r:int(r.customer_id))
            vl,vm=options(variants,lambda r:f"{r.product_name} · {r.sku} · {r.color or 'Color n/a'} · {r.size or 'Size n/a'} · stock {r.stock_qty}",lambda r:(int(r.product_id),int(r.variant_no),int(r.stock_qty)))
            with st.form("add_cart_item_form"):
                c1,c2=st.columns(2); who=c1.selectbox("Customer",cl); what=c2.selectbox("Product variant",vl)
                qty=st.number_input("Quantity to add",min_value=1,step=1); add_item=st.form_submit_button("Add to cart")
            if add_item:
                cid=cm[who]; pid,vno,stock=vm[what]; conn=connect()
                try:
                    cur=conn.cursor(); cur.execute("SELECT cart_id FROM carts WHERE customer_id=%s",(cid,)); row=cur.fetchone()
                    cart_id=int(row[0]) if row else None
                    if cart_id is None: cur.execute("INSERT INTO carts(customer_id) VALUES(%s)",(cid,)); cart_id=cur.lastrowid
                    cur.execute("SELECT quantity FROM cart_items WHERE cart_id=%s AND product_id=%s AND variant_no=%s",(cart_id,pid,vno)); exists=cur.fetchone()
                    total_qty=(int(exists[0]) if exists else 0)+int(qty)
                    if total_qty>stock: raise ValueError(f"Requested quantity {total_qty} exceeds stock {stock}.")
                    if exists: cur.execute("UPDATE cart_items SET quantity=%s WHERE cart_id=%s AND product_id=%s AND variant_no=%s",(total_qty,cart_id,pid,vno))
                    else: cur.execute("INSERT INTO cart_items(cart_id,product_id,variant_no,quantity) VALUES(%s,%s,%s,%s)",(cart_id,pid,vno,int(qty)))
                    conn.commit(); cur.close(); notice(f"Added {qty} unit(s) to {who}'s cart.")
                except Exception as exc: conn.rollback(); st.error(f"Cart was not updated: {exc}")
                finally: conn.close()
        cart_df=fetch_df("SELECT ci.cart_id,ci.product_id,ci.variant_no,c.customer_id,c.full_name,p.product_name,pv.sku,pv.color,pv.size,pv.price,pv.stock_qty,ci.quantity,pv.price*ci.quantity AS line_total FROM cart_items ci JOIN carts ca ON ca.cart_id=ci.cart_id JOIN customers c ON c.customer_id=ca.customer_id JOIN products p ON p.product_id=ci.product_id JOIN product_variants pv ON pv.product_id=ci.product_id AND pv.variant_no=ci.variant_no ORDER BY c.full_name,p.product_name")
        cart_metrics=st.columns(2); cart_metrics[0].metric("Items in open carts",int(cart_df["quantity"].sum()) if not cart_df.empty else 0); cart_metrics[1].metric("Open cart value",f"৳{float(cart_df['line_total'].sum()):,.2f}" if not cart_df.empty else "৳0.00")
        st.subheader("Cart lines"); show_table(cart_df)
        if not cart_df.empty:
            il,im=options(cart_df,lambda r:f"{r.full_name} · {r.product_name} · {r.sku} (qty {r.quantity})",lambda r:(int(r.cart_id),int(r.product_id),int(r.variant_no),int(r.quantity),int(r.stock_qty)))
            with st.form("update_cart_form"):
                line=st.selectbox("Cart line to update",il); current=im[line][3]; new_qty=st.number_input("New quantity",min_value=1,value=current,step=1)
                update=st.form_submit_button("Update quantity")
            if update:
                cart_id,pid,vno,_,stock=im[line]
                if int(new_qty)>stock: st.error(f"Quantity exceeds available stock ({stock}).")
                else: mutate("UPDATE cart_items SET quantity=%s WHERE cart_id=%s AND product_id=%s AND variant_no=%s",(int(new_qty),cart_id,pid,vno)); notice("Cart quantity updated.")
            with st.form("delete_cart_form"):
                line_to_delete=st.selectbox("Cart line to remove",il,key="remove_cart_line"); remove=st.form_submit_button("Remove item")
            if remove:
                cart_id,pid,vno,*_=im[line_to_delete]; mutate("DELETE FROM cart_items WHERE cart_id=%s AND product_id=%s AND variant_no=%s",(cart_id,pid,vno)); notice("Cart item removed.")
        st.subheader("Wishlist")
        if not customers.empty and not variants.empty:
            with st.form("wishlist_form"):
                c1,c2=st.columns(2); who=c1.selectbox("Customer",cl,key="wishlist_customer"); what=c2.selectbox("Variant",vl,key="wishlist_variant"); add=st.form_submit_button("Add to wishlist")
            if add:
                try: mutate("INSERT INTO wishlist_items(customer_id,product_id) VALUES(%s,%s)",(cm[who],vm[what][0])); notice("Added to wishlist.")
                except mysql.connector.Error as exc: st.error(f"Wishlist was not updated: {exc}")
        wishlist=fetch_df("SELECT w.customer_id,w.product_id,c.full_name,p.product_name,p.brand_name,w.added_at FROM wishlist_items w JOIN customers c ON c.customer_id=w.customer_id JOIN products p ON p.product_id=w.product_id ORDER BY c.full_name,w.added_at DESC")
        show_table(wishlist[["full_name","product_name","brand_name","added_at"]] if not wishlist.empty else wishlist)
        if not wishlist.empty:
            wish_labels,wish_map=options(wishlist,lambda r:f"{r.full_name} · {r.product_name} (#{r.customer_id}/#{r.product_id})",lambda r:(int(r.customer_id),int(r.product_id)))
            with st.form("remove_wishlist_form"):
                wish_to_remove=st.selectbox("Saved item",wish_labels); remove_wish=st.form_submit_button("Remove from wishlist")
            if remove_wish: mutate("DELETE FROM wishlist_items WHERE customer_id=%s AND product_id=%s",wish_map[wish_to_remove]); notice("Wishlist item removed.")

with tab_checkout:
    st.subheader("Checkout")
    customers=fetch_df("SELECT customer_id,full_name FROM customers WHERE status='Active' ORDER BY full_name")
    with st.expander("Add a new customer",expanded=customers.empty):
        with st.form("checkout_new_customer_form"):
            c1,c2=st.columns(2); new_name=c1.text_input("Full name",key="checkout_new_name"); new_email=c2.text_input("Email",key="checkout_new_email")
            c1,c2=st.columns(2); new_phone=c1.text_input("Phone",key="checkout_new_phone"); new_city=c2.text_input("City",key="checkout_new_city")
            new_street=st.text_input("Street address",key="checkout_new_street"); new_postal=st.text_input("Postal code",key="checkout_new_postal"); new_label=st.text_input("Address label",value="Home",key="checkout_new_label")
            create_for_checkout=st.form_submit_button("Create customer")
        if create_for_checkout:
            if not new_name.strip() or not new_email.strip() or not new_city.strip() or not new_street.strip(): st.error("Name, email, city, and street are required.")
            else:
                try:
                    cid=create_customer_record(new_name.strip(),new_email.strip(),new_phone.strip() or None,new_label.strip() or "Home",new_street.strip(),new_city.strip(),new_postal.strip() or None)
                    notice(f"Customer #{cid} is active and ready for checkout.")
                except Exception as exc: st.error(f"Customer was not created: {exc}")
    if customers.empty: st.info("Register an active customer in Customers & carts first.")
    else:
        cl,cm=options(customers,lambda r:f"{r.full_name} (#{r.customer_id})",lambda r:int(r.customer_id))
        who=st.selectbox("Customer",cl,key="checkout_customer"); cid=cm[who]
        cart=fetch_df("SELECT ci.cart_id,ci.product_id,ci.variant_no,ci.quantity,p.product_name,pv.sku,pv.color,pv.size,pv.price,pv.stock_qty FROM carts ca JOIN cart_items ci ON ci.cart_id=ca.cart_id JOIN products p ON p.product_id=ci.product_id JOIN product_variants pv ON pv.product_id=ci.product_id AND pv.variant_no=ci.variant_no WHERE ca.customer_id=%s AND p.status='Active' ORDER BY p.product_name,pv.variant_no",(cid,))
        addresses=fetch_df("SELECT address_no,label,street_line,city,is_default FROM addresses WHERE customer_id=%s ORDER BY is_default DESC,address_no",(cid,))
        if cart.empty: st.info(f"{who} remains in this list. Their cart is empty; add items from Customers & carts.")
        elif addresses.empty: st.warning("Add a delivery address before checkout.")
        else:
            show_table(cart[["product_name","sku","color","size","quantity","price","stock_qty"]])
            subtotal=sum(Decimal(str(r.price))*int(r.quantity) for r in cart.itertuples()).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
            coupons=fetch_df("SELECT cp.coupon_id,cp.code,cp.discount_type,cp.discount_value,cp.min_order_amount,cp.usage_limit,COUNT(o.order_id) AS used_count FROM coupons cp LEFT JOIN orders o ON o.coupon_id=cp.coupon_id WHERE CURRENT_DATE BETWEEN cp.valid_from AND cp.valid_to GROUP BY cp.coupon_id,cp.code,cp.discount_type,cp.discount_value,cp.min_order_amount,cp.usage_limit HAVING COUNT(o.order_id)<cp.usage_limit ORDER BY cp.code")
            if not coupons.empty: coupons=coupons[coupons["min_order_amount"].apply(lambda x:Decimal(str(x))<=subtotal)]
            coupon_labels=["No coupon"]+[f"{r.code} · {r.discount_type} {r.discount_value}" for r in coupons.itertuples()]
            coupon_map={f"{r.code} · {r.discount_type} {r.discount_value}":r for r in coupons.itertuples()}
            al,am=options(addresses,lambda r:f"{r.label}: {r.street_line}, {r.city} (#{r.address_no})",lambda r:int(r.address_no))
            if st.session_state.get("checkout_address") not in al: st.session_state["checkout_address"]=al[0]
            if st.session_state.get("checkout_coupon") not in coupon_labels: st.session_state["checkout_coupon"]="No coupon"
            c1,c2=st.columns(2)
            address=c1.selectbox("Delivery address",al,key="checkout_address")
            coupon_label=c2.selectbox("Coupon",coupon_labels,key="checkout_coupon")
            coupon_id=None; coupon=None; discount=Decimal("0.00")
            if coupon_label!="No coupon":
                coupon=coupon_map[coupon_label]; coupon_id=int(coupon.coupon_id); value=Decimal(str(coupon.discount_value))
                discount=(subtotal*value/Decimal(100)).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP) if coupon.discount_type=="Percent" else min(value,subtotal)
            shipping=Decimal("80.00"); total=subtotal-discount+shipping
            price=st.columns(4)
            price[0].metric("Subtotal",f"৳{subtotal:,.2f}")
            price[1].metric("Coupon discount",f"−৳{discount:,.2f}")
            price[2].metric("Shipping",f"৳{shipping:,.2f}")
            price[3].metric("Total due",f"৳{total:,.2f}")
            if coupon is not None:
                st.caption(f"{coupon.code} applied. You save ৳{discount:,.2f} on this order.")
            with st.form("checkout_form"):
                method=st.selectbox("Payment method",["Cash on Delivery","Card","Wallet","Bank Transfer"])
                confirm=st.checkbox("Confirm this order and reserve stock"); submit=st.form_submit_button("Place order")
            if any(int(r.quantity)>int(r.stock_qty) for r in cart.itertuples()): st.warning("Cart quantity exceeds current stock; update cart or inventory first.")
            if submit:
                if not confirm: st.warning("Confirm the order before placing it.")
                elif any(int(r.quantity)>int(r.stock_qty) for r in cart.itertuples()): st.error("Cart quantity exceeds current stock.")
                else:
                    conn=connect()
                    try:
                        cur=conn.cursor(); cur.execute("INSERT INTO orders(customer_id,address_no,coupon_id,order_status,subtotal,discount_amount,shipping_fee,total_amount) VALUES(%s,%s,%s,'Pending',%s,%s,%s,%s)",(cid,am[address],coupon_id,subtotal,discount,shipping,total)); order_id=cur.lastrowid
                        for line_no,r in enumerate(cart.itertuples(),1): cur.callproc("sp_reserve_order_line",[order_id,line_no,int(r.product_id),int(r.variant_no),int(r.quantity),r.price])
                        cur.execute("INSERT INTO payments(order_id,method,amount,pay_status) VALUES(%s,%s,%s,'Pending')",(order_id,method,total))
                        for r in cart.itertuples(): cur.execute("DELETE FROM cart_items WHERE cart_id=%s AND product_id=%s AND variant_no=%s",(int(r.cart_id),int(r.product_id),int(r.variant_no)))
                        conn.commit(); cur.close(); notice(f"Order #{order_id} placed. {who} remains available for later orders.")
                    except Exception as exc: conn.rollback(); st.error(f"Checkout rolled back: {exc}")
                    finally: conn.close()
with tab_orders:
    st.subheader("Orders and shipping")
    orders=fetch_df("SELECT * FROM v_order_summary ORDER BY order_date DESC")
    show_table(orders)
    lines=fetch_df("SELECT oi.order_id,oi.line_no,p.product_name,pv.sku,pv.color,pv.size,oi.quantity,oi.unit_price_paid,oi.quantity*oi.unit_price_paid AS line_total FROM order_items oi JOIN products p ON p.product_id=oi.product_id JOIN product_variants pv ON pv.product_id=oi.product_id AND pv.variant_no=oi.variant_no ORDER BY oi.order_id DESC,oi.line_no")
    if not orders.empty:
        ol,om=options(orders,lambda r:f"Order #{r.order_id} · {r.full_name} · {r.order_status}",lambda r:int(r.order_id))
        detail=st.selectbox("Show order lines",ol,key="order_detail"); show_table(lines[lines["order_id"]==om[detail]])
    active=orders[orders["order_status"].isin(["Pending","Confirmed","Shipped"])] if not orders.empty else orders
    couriers=fetch_df("SELECT courier_id,courier_name,phone,tracking_url FROM couriers ORDER BY courier_name")
    if not active.empty:
        al,am=options(active,lambda r:f"Order #{r.order_id} · {r.full_name} · {r.order_status}",lambda r:(int(r.order_id),r.order_status))
        cl,cm=options(couriers,lambda r:f"{r.courier_name} (#{r.courier_id})",lambda r:int(r.courier_id)) if not couriers.empty else ([],{})
        with st.form("order_status_form"):
            selected=st.selectbox("Order to update",al); order_id,current=am[selected]
            allowed={"Pending":["Confirmed","Cancelled"],"Confirmed":["Shipped","Cancelled"],"Shipped":["Delivered"]}[current]
            target=st.selectbox("Next status",allowed)
            courier=st.selectbox("Courier (for shipping)",cl) if cl else None
            tracking=st.text_input("Tracking number (required when shipping)")
            confirm_cancel=st.checkbox("Confirm cancellation (required only for Cancelled status)")
            apply=st.form_submit_button("Apply status")
        if apply:
            if target=="Cancelled" and not confirm_cancel: st.warning("Confirm cancellation first.")
            elif target=="Shipped" and (not courier or not tracking.strip()): st.error("Select a courier and enter a tracking number.")
            else:
                conn=connect()
                try:
                    cur=conn.cursor()
                    if target=="Cancelled": cur.callproc("sp_cancel_order",[order_id])
                    elif target=="Confirmed": cur.execute("UPDATE orders SET order_status='Confirmed' WHERE order_id=%s",(order_id,))
                    elif target=="Shipped":
                        cur.execute("INSERT INTO shipments(order_id,courier_id,tracking_no,ship_status,shipped_at) VALUES(%s,%s,%s,'Shipped',CURRENT_TIMESTAMP)",(order_id,cm[courier],tracking.strip()))
                        cur.execute("UPDATE orders SET order_status='Shipped' WHERE order_id=%s",(order_id,))
                    elif target=="Delivered":
                        cur.execute("UPDATE orders SET order_status='Delivered' WHERE order_id=%s",(order_id,))
                        cur.execute("UPDATE shipments SET ship_status='Delivered',delivered_at=CURRENT_TIMESTAMP WHERE order_id=%s AND ship_status IN ('Shipped','Out for Delivery')",(order_id,))
                        if cur.rowcount<1: raise ValueError("This order has no shipped parcel.")
                    conn.commit(); cur.close(); notice(f"Order #{order_id} moved to {target}.")
                except Exception as exc: conn.rollback(); st.error(f"Order status was not updated: {exc}")
                finally: conn.close()
    else: st.info("No orders are waiting for a status update.")
    with st.expander("Add a courier"):
        with st.form("courier_form"):
            c1,c2=st.columns(2); name=c1.text_input("Courier name"); phone=c2.text_input("Phone"); url=st.text_input("Tracking URL (optional)"); add=st.form_submit_button("Save courier")
        if add:
            if not name.strip(): st.error("Courier name is required.")
            else:
                try: mutate("INSERT INTO couriers(courier_name,phone,tracking_url) VALUES(%s,%s,%s)",(name.strip(),phone.strip() or None,url.strip() or None)); notice("Courier added.")
                except mysql.connector.Error as exc: st.error(f"Courier was not saved: {exc}")
    show_table(couriers)
    if not couriers.empty:
        courier_labels,courier_map=options(couriers,lambda r:f"{r.courier_name} (#{r.courier_id})",lambda r:int(r.courier_id))
        with st.expander("Delete courier"):
            courier_to_delete=st.selectbox("Courier to delete",courier_labels,key="delete_courier_choice")
            with st.form("delete_courier_form"):
                confirm_courier_delete=st.checkbox("Confirm courier deletion")
                delete_courier=st.form_submit_button("Delete courier",type="primary")
            if delete_courier:
                if not confirm_courier_delete: st.warning("Confirm the deletion to continue.")
                else:
                    try: delete_courier_record(courier_map[courier_to_delete]); notice("Courier deleted.")
                    except Exception as exc: st.error(str(exc))

with tab_returns:
    request_tab,manage_tab,review_tab=st.tabs(["Request return","Manage returns","Reviews"])
    with request_tab:
        st.subheader("Request a return for a recent delivery")
        eligible=fetch_df("""SELECT o.order_id,oi.line_no,p.product_name,pv.sku,oi.quantity AS purchased_qty,
          oi.unit_price_paid,MAX(sh.delivered_at) AS delivered_at,
          COALESCE(SUM(CASE WHEN rr.return_status<>'Rejected' THEN rr.quantity ELSE 0 END),0) AS returned_qty
          FROM orders o JOIN order_items oi ON oi.order_id=o.order_id JOIN products p ON p.product_id=oi.product_id
          JOIN product_variants pv ON pv.product_id=oi.product_id AND pv.variant_no=oi.variant_no
          JOIN shipments sh ON sh.order_id=o.order_id AND sh.ship_status='Delivered'
          LEFT JOIN return_requests rr ON rr.order_id=oi.order_id AND rr.line_no=oi.line_no
          WHERE o.order_status='Delivered' AND sh.delivered_at>=DATE_SUB(CURRENT_TIMESTAMP,INTERVAL 7 DAY)
          GROUP BY o.order_id,oi.line_no,p.product_name,pv.sku,oi.quantity,oi.unit_price_paid
          ORDER BY delivered_at DESC,o.order_id,oi.line_no""")
        if not eligible.empty:
            eligible["remaining_qty"]=eligible["purchased_qty"]-eligible["returned_qty"]
            eligible=eligible[eligible["remaining_qty"]>0].reset_index(drop=True)
        if eligible.empty: st.info("No delivered order is currently within the return window.")
        else:
            rl,rm=options(eligible,lambda r:f"Order #{r.order_id} · {r.product_name} · {r.sku} · {r.remaining_qty} returnable",lambda r:r)
            with st.form("return_request_form"):
                line=st.selectbox("Delivered item",rl); row=rm[line]
                qty=st.number_input("Quantity to return",min_value=1,max_value=int(row.remaining_qty),step=1); reason=st.text_input("Reason")
                submit=st.form_submit_button("Submit return")
            if submit:
                if not reason.strip(): st.error("Enter a reason.")
                else:
                    try: mutate("INSERT INTO return_requests(order_id,line_no,quantity,reason,return_status,refund_amount,requested_at) VALUES(%s,%s,%s,%s,'Requested',0,CURRENT_TIMESTAMP)",(int(row.order_id),int(row.line_no),int(qty),reason.strip())); notice("Return submitted to the admin queue.")
                    except mysql.connector.Error as exc: st.error(f"Return was not saved: {exc}")
    with manage_tab:
        st.subheader("Return review queue")
        returns=fetch_df("SELECT rr.return_id,rr.order_id,rr.line_no,c.full_name,p.product_name,pv.sku,rr.quantity,rr.reason,rr.return_status,rr.refund_amount,rr.requested_at FROM return_requests rr JOIN orders o ON o.order_id=rr.order_id JOIN customers c ON c.customer_id=o.customer_id JOIN order_items oi ON oi.order_id=rr.order_id AND oi.line_no=rr.line_no JOIN products p ON p.product_id=oi.product_id JOIN product_variants pv ON pv.product_id=oi.product_id AND pv.variant_no=oi.variant_no ORDER BY rr.requested_at DESC,rr.return_id DESC")
        show_table(returns)
        actionable=returns[returns["return_status"].isin(["Requested","Approved"])] if not returns.empty else returns
        if not actionable.empty:
            rl,rm=options(actionable,lambda r:f"Return #{r.return_id} · Order #{r.order_id} · {r.product_name} · {r.return_status}",lambda r:(int(r.return_id),r.return_status))
            with st.form("return_status_form"):
                selected=st.selectbox("Return request",rl); return_id,current=rm[selected]
                choices=["Approved","Rejected"] if current=="Requested" else ["Refunded"]
                status=st.selectbox("Next status",choices); apply=st.form_submit_button("Apply return status")
            if apply:
                try:
                    if status=="Refunded": mutate("UPDATE return_requests rr JOIN order_items oi ON oi.order_id=rr.order_id AND oi.line_no=rr.line_no SET rr.return_status='Refunded',rr.refund_amount=rr.quantity*oi.unit_price_paid WHERE rr.return_id=%s",(return_id,))
                    else: mutate("UPDATE return_requests SET return_status=%s WHERE return_id=%s",(status,return_id))
                    notice(f"Return #{return_id} moved to {status}.")
                except mysql.connector.Error as exc: st.error(f"Return was not updated: {exc}")
        else: st.info("No return requests are waiting for review or refund.")
    with review_tab:
        st.subheader("Review a delivered purchase")
        reviewable=fetch_df("SELECT o.order_id,oi.line_no,p.product_name,pv.sku FROM orders o JOIN order_items oi ON oi.order_id=o.order_id JOIN products p ON p.product_id=oi.product_id JOIN product_variants pv ON pv.product_id=oi.product_id AND pv.variant_no=oi.variant_no LEFT JOIN reviews r ON r.order_id=oi.order_id AND r.line_no=oi.line_no WHERE o.order_status='Delivered' AND r.review_id IS NULL ORDER BY o.order_date DESC,o.order_id,oi.line_no")
        if reviewable.empty: st.info("Every delivered order line already has a review.")
        else:
            rl,rm=options(reviewable,lambda r:f"Order #{r.order_id} · {r.product_name} · {r.sku}",lambda r:(int(r.order_id),int(r.line_no)))
            with st.form("review_form"):
                selected=st.selectbox("Delivered item",rl); rating=st.select_slider("Rating",options=[1,2,3,4,5],value=5)
                title=st.text_input("Review title"); comment=st.text_area("Comment",height=80); submit=st.form_submit_button("Save review")
            if submit:
                try: mutate("INSERT INTO reviews(order_id,line_no,rating,title,comment) VALUES(%s,%s,%s,%s,%s)",(*rm[selected],int(rating),title.strip() or None,comment.strip() or None)); notice("Review saved.")
                except mysql.connector.Error as exc: st.error(f"Review was not saved: {exc}")
        st.subheader("Recent reviews")
        show_table(fetch_df("SELECT c.full_name,p.product_name,r.rating,r.title,r.comment,r.created_at FROM reviews r JOIN orders o ON o.order_id=r.order_id JOIN customers c ON c.customer_id=o.customer_id JOIN order_items oi ON oi.order_id=r.order_id AND oi.line_no=r.line_no JOIN products p ON p.product_id=oi.product_id ORDER BY r.created_at DESC"))

with tab_finance:
    sales_tab,payment_tab,payout_tab,coupon_tab=st.tabs(["Sales & stock","Payments","Seller payouts","Coupons"])
    with sales_tab:
        st.subheader("Marketplace reports")
        if not sales.empty: _chart=st.bar_chart(sales.set_index("month"),y="sales")
        performance=fetch_df("SELECT store_name,SUM(gross_sales) AS gross_sales,SUM(commission_amount) AS commission_amount,SUM(net_sales) AS net_sales FROM v_seller_monthly_sales GROUP BY store_name ORDER BY gross_sales DESC")
        c1,c2=st.columns(2)
        with c1: st.write("Seller performance"); show_table(performance)
        with c2: st.write("Low stock"); show_table(fetch_df("SELECT p.product_name,pv.sku,pv.color,pv.size,pv.stock_qty FROM product_variants pv JOIN products p ON p.product_id=pv.product_id WHERE pv.stock_qty<=10 ORDER BY pv.stock_qty,p.product_name"))
        st.write("Returns by status"); show_table(fetch_df("SELECT return_status,COUNT(*) AS requests,SUM(refund_amount) AS refunds FROM return_requests GROUP BY return_status ORDER BY requests DESC"))
    with payment_tab:
        st.subheader("Payment attempts")
        payments=fetch_df("SELECT p.payment_id,p.order_id,c.full_name,p.method,p.amount,p.pay_status,p.transaction_ref,p.paid_at FROM payments p JOIN orders o ON o.order_id=p.order_id JOIN customers c ON c.customer_id=o.customer_id ORDER BY p.payment_id DESC")
        show_table(payments)
        pending=payments[payments["pay_status"]=="Pending"] if not payments.empty else payments
        if not pending.empty:
            pl,pm=options(pending,lambda r:f"Payment #{r.payment_id} · Order #{r.order_id} · {r.full_name} · ৳{r.amount}",lambda r:int(r.payment_id))
            with st.form("payment_result_form"):
                selected=st.selectbox("Pending payment",pl); result=st.selectbox("Payment outcome",["Success","Failed"]); save=st.form_submit_button("Record payment outcome")
            if save:
                try: mutate("UPDATE payments SET pay_status=%s,paid_at=CASE WHEN %s='Success' THEN CURRENT_TIMESTAMP ELSE NULL END WHERE payment_id=%s",(result,result,pm[selected])); notice("Payment outcome recorded.")
                except mysql.connector.Error as exc: st.error(f"Payment was not updated: {exc}")
        st.caption("No external payment gateway is connected.")
    with payout_tab:
        st.subheader("Generate a seller payout")
        sellers=fetch_df("SELECT seller_id,store_name FROM sellers WHERE status='Active' ORDER BY store_name")
        if not sellers.empty:
            sl,sm=options(sellers,lambda r:f"{r.store_name} (#{r.seller_id})",lambda r:int(r.seller_id))
            with st.form("payout_form"):
                seller=st.selectbox("Seller",sl); c1,c2=st.columns(2)
                start=c1.date_input("Period start",value=pd.Timestamp("2027-01-01").date()); end=c2.date_input("Period end",value=pd.Timestamp("2027-12-31").date())
                make=st.form_submit_button("Generate payout")
            if make:
                if end<start: st.error("End date must be on or after start date.")
                else:
                    conn=connect()
                    try:
                        cur=conn.cursor(); cur.execute("SET @new_payout_id=NULL"); cur.execute("CALL sp_generate_seller_payout(%s,%s,%s,@new_payout_id)",(sm[seller],start,end)); cur.execute("SELECT @new_payout_id"); payout_id=cur.fetchone()[0]
                        conn.commit(); cur.close(); notice(f"Payout #{payout_id} generated.")
                    except Exception as exc: conn.rollback(); st.error(f"Payout was not generated: {exc}. Select a range that does not overlap an existing payout.")
                    finally: conn.close()
        show_table(fetch_df("SELECT payout_id,seller_id,period_start,period_end,gross_sales,commission_amount,net_amount,payout_status,paid_at FROM seller_payouts ORDER BY period_start DESC,seller_id"))
    with coupon_tab:
        st.subheader("Coupon management")
        coupon_records=fetch_df("SELECT coupon_id,code,discount_type,discount_value,min_order_amount,valid_from,valid_to,usage_limit FROM coupons ORDER BY valid_from DESC,code")
        show_table(coupon_records)
        with st.expander("Add coupon"):
            with st.form("new_coupon_form"):
                c1,c2,c3=st.columns(3); code=c1.text_input("Coupon code"); kind=c2.selectbox("Type",["Percent","Fixed"]); value=c3.number_input("Value",min_value=0.01,step=1.0)
                c1,c2,c3=st.columns(3); minimum=c1.number_input("Minimum order",min_value=0.0,step=100.0); start=c2.date_input("Valid from",value=pd.Timestamp.today().date()); end=c3.date_input("Valid to",value=pd.Timestamp.today().date())
                limit=st.number_input("Usage limit",min_value=1,value=100,step=1); create=st.form_submit_button("Create coupon")
        if create:
            if not code.strip(): st.error("Coupon code is required.")
            elif kind=="Percent" and value>100: st.error("Percent discount cannot exceed 100%.")
            elif end<start: st.error("End date must be on or after start date.")
            else:
                try: mutate("INSERT INTO coupons(code,discount_type,discount_value,min_order_amount,valid_from,valid_to,usage_limit) VALUES(%s,%s,%s,%s,%s,%s,%s)",(code.strip().upper(),kind,value,minimum,start,end,int(limit))); notice("Coupon created for eligible checkouts.")
                except mysql.connector.Error as exc: st.error(f"Coupon was not saved: {exc}")
        if not coupon_records.empty:
            coupon_labels,coupon_map=options(coupon_records,lambda r:f"{r.code} (#{r.coupon_id})",lambda r:int(r.coupon_id))
            with st.expander("Delete unused coupon"):
                coupon_to_delete=st.selectbox("Coupon to delete",coupon_labels,key="delete_coupon_choice")
                with st.form("delete_coupon_form"):
                    confirm_coupon_delete=st.checkbox("Confirm coupon deletion")
                    delete_coupon=st.form_submit_button("Delete coupon",type="primary")
                if delete_coupon:
                    if not confirm_coupon_delete: st.warning("Confirm the deletion to continue.")
                    else:
                        try: delete_coupon_record(coupon_map[coupon_to_delete]); notice("Coupon deleted.")
                        except Exception as exc: st.error(str(exc))

st.caption("MarketNest | Marketplace Operations")

