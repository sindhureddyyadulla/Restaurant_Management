import streamlit as st
import datetime
from db import db_cursor
from db import get_db_connection
from utils import safe_parse_time

def parse_time_correctly(value):
    if isinstance(value, datetime.timedelta):
        return (datetime.datetime.min + value).time()
    elif isinstance(value, datetime.time):
        return value
    elif isinstance(value, str):
        try:
            return datetime.datetime.strptime(value, "%H:%M:%S").time()
        except Exception:
            return datetime.time(0, 0)
    else:
        return datetime.time(0, 0)
    


# ------------------ VIEW EVENTS ------------------
def manager_view_upcoming_events():
    st.header("Upcoming Events (Manager View)")
    view_mode = st.radio("View By", ["Single Date", "Date Range"])

    with db_cursor() as cursor:
        if view_mode == "Single Date":
            selected_date = st.date_input("Select Date")
            cursor.execute("""
                SELECT e.event_name, e.location, e.event_date, eb.guest_count, s.name, c.name
                FROM Event e
                JOIN EventBooking eb ON e.event_id = eb.event_id
                JOIN Customer c ON eb.customer_id = c.customer_id
                JOIN Staff s ON e.created_by_staff_id = s.staff_id
                WHERE e.event_date = %s
            """, (selected_date,))
        else:
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            cursor.execute("""
                SELECT e.event_name, e.location, e.event_date, eb.guest_count, s.name, c.name
                FROM Event e
                JOIN EventBooking eb ON e.event_id = eb.event_id
                JOIN Customer c ON eb.customer_id = c.customer_id
                JOIN Staff s ON e.created_by_staff_id = s.staff_id
                WHERE e.event_date BETWEEN %s AND %s
                ORDER BY e.event_date
            """, (start_date, end_date))

        events = cursor.fetchall()

    if events:
        for event_name, location, event_date, guest_count, created_by, customer_name in events:
            st.write(f"""
                **{event_date}**  
                **Event:** {event_name}  
                **Location:** {location}  
                **Guests:** {guest_count}  
                **Customer:** {customer_name}  
                **Booked By Staff:** {created_by}
            """)
    else:
        st.info("No upcoming events found.")



# ------------------ MANAGE STAFF ------------------
def manager_staff_management():
    st.header("Manage Staff")
    search_name = st.text_input("Search Staff by Name")
    role_filter = st.selectbox("Filter by Role", ["All", "Admin", "Manager", "Chef"])

    with db_cursor() as cursor:
        query = """
            SELECT s.staff_id, s.name, s.phone, s.salary, r.role_name
            FROM Staff s
            JOIN Role r ON s.role_id = r.role_id
            WHERE 1=1
        """
        params = []
        if search_name:
            query += " AND s.name LIKE %s"
            params.append(f"%{search_name}%")
        if role_filter != "All":
            query += " AND r.role_name = %s"
            params.append(role_filter)

        cursor.execute(query, tuple(params))
        staff_list = cursor.fetchall()

    if not staff_list:
        st.info("No staff found.")
    else:
        for staff_id, name, phone, salary, role in staff_list:
            with st.expander(f"{name} (Role: {role})"):
                new_name = st.text_input("Name", value=name, key=f"name_{staff_id}")
                new_phone = st.text_input("Phone", value=phone, key=f"phone_{staff_id}")
                new_salary = st.number_input("Salary", value=float(salary), key=f"salary_{staff_id}")
                if st.button("Update", key=f"update_{staff_id}"):
                    with db_cursor() as cursor:
                        cursor.execute("""
                            UPDATE Staff
                            SET name = %s, phone = %s, salary = %s
                            WHERE staff_id = %s
                        """, (new_name, new_phone, new_salary, staff_id))
                        st.success("Staff updated.")

                if st.button("Delete", key=f"delete_{staff_id}"):
                    with db_cursor() as cursor:
                        cursor.execute("DELETE FROM Staff WHERE staff_id = %s", (staff_id,))
                        st.success("Staff deleted.")

    st.markdown("---")
    st.subheader("Add New Staff")

    new_staff_name = st.text_input("Staff Name")
    new_staff_phone = st.text_input("Phone")
    new_staff_salary = st.number_input("Salary", min_value=0.0)
    with db_cursor() as cursor:
        cursor.execute("SELECT role_id, role_name FROM Role")
        roles = cursor.fetchall()
        role_map = {name: rid for rid, name in roles}

    new_role = st.selectbox("Select Role", list(role_map.keys()) + (["Chef"] if "Chef" not in role_map else []))

    if st.button("Add Staff"):
        with db_cursor() as cursor:
            role_id = role_map.get(new_role)
            if not role_id:
                cursor.execute("INSERT INTO Role (role_name) VALUES (%s)", (new_role,))
                role_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO Staff (name, phone, role_id, salary)
                VALUES (%s, %s, %s, %s)
            """, (new_staff_name, new_staff_phone, role_id, new_staff_salary))
            st.success("Staff member added successfully.")



# ------------------ VIEW ORDERS ------------------
def manager_dashboard_view_orders():
    st.header("View Orders and Invoices")
    view_mode = st.radio("Select View Mode", ["Single Date", "Date Range"])

    with db_cursor() as cursor:
        if view_mode == "Single Date":
            selected_date = st.date_input("Select Date")
            cursor.execute("""
                SELECT o.order_id, c.name, o.order_time, o.status, SUM(od.quantity * od.price)
                FROM `Order` o
                JOIN Customer c ON o.customer_id = c.customer_id
                JOIN OrderDetail od ON o.order_id = od.order_id
                WHERE DATE(o.order_time) = %s
                GROUP BY o.order_id
            """, (selected_date,))
        else:
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            cursor.execute("""
                SELECT o.order_id, c.name, o.order_time, o.status, SUM(od.quantity * od.price)
                FROM `Order` o
                JOIN Customer c ON o.customer_id = c.customer_id
                JOIN OrderDetail od ON o.order_id = od.order_id
                WHERE DATE(o.order_time) BETWEEN %s AND %s
                GROUP BY o.order_id
            """, (start_date, end_date))

        orders = cursor.fetchall()

    if orders:
        for oid, cname, otime, status, total in orders:
            with st.expander(f"Order #{oid} - {cname} | {otime.strftime('%d-%m-%Y %H:%M')} | Status: {status} | Rs.{total:.2f}"):
                with db_cursor() as cursor:
                    cursor.execute("""
                        SELECT m.name, od.quantity, od.price
                        FROM OrderDetail od
                        JOIN MenuItem m ON od.menu_item_id = m.menu_item_id
                        WHERE od.order_id = %s
                    """, (oid,))
                    items = cursor.fetchall()
                    for name, qty, price in items:
                        st.write(f"{name} x {qty} = Rs.{qty * price:.2f}")
    else:
        st.info("No orders found.")



# ------------------ MANAGE PURCHASES ------------------
def manager_manage_purchases():
    st.header("Purchase Management")
    conn = get_db_connection()
    cursor = conn.cursor()
    view_mode = st.radio("View", ["Add New", "View By Date"])

    if view_mode == "Add New":
            cursor.execute("SELECT supplier_id, name, category FROM Supplier")
            suppliers = cursor.fetchall()
            supplier_map = {f"{name} ({category})": (sid, category) for sid, name, category in suppliers}
            selected_supplier = st.selectbox("Select Supplier", list(supplier_map.keys()))
            supplier_id, supplier_category = supplier_map[selected_supplier]

            purchase_date = st.date_input("Purchase Date")
            status = st.selectbox("Purchase Status", ["Ordered", "Received", "Cancelled"])

            # ---- Select items from Inventory ----
            cursor.execute("SELECT item_id, item_name FROM InventoryItem WHERE category = %s", (supplier_category,))
            inventory_items = cursor.fetchall()
            item_map = {f"{name} (ID:{iid})": iid for iid, name in inventory_items}
            selected_items = st.multiselect("Select Items to Purchase", list(item_map.keys()))

            items_to_purchase = []

            if selected_items:
                st.subheader("Enter Quantity and Price for Each Selected Item")
                for item_label in selected_items:
                    item_id = item_map[item_label]
                    quantity = st.number_input(f"Quantity for {item_label}", min_value=0.0, step=0.1, key=f"qty_{item_id}")
                    price_per_unit = st.number_input(f"Price per Unit for {item_label}", min_value=0.0, step=0.1, key=f"price_{item_id}")
                    items_to_purchase.append((item_id, quantity, price_per_unit))

            total_amount = sum(qty * price for (_, qty, price) in items_to_purchase)

            st.markdown(f"### Estimated Total Amount: Rs.{total_amount:.2f}")

            if st.button("Record Purchase and Purchase Details"):
                staff_id = st.session_state.user_id
                try:
                    # Insert into Purchase table first
                    cursor.execute("""
                        INSERT INTO Purchase (supplier_id, staff_id, purchase_date, status, total_amount)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (supplier_id, staff_id, purchase_date, status, total_amount))
                    purchase_id = cursor.lastrowid

                    # Insert each item into PurchaseDetail
                    for item_id, qty, price in items_to_purchase:
                        cursor.execute("""
                            INSERT INTO PurchaseDetail (purchase_id, item_id, quantity, price_per_unit)
                            VALUES (%s, %s, %s, %s)
                        """, (purchase_id, item_id, qty, price))

                    conn.commit()
                    st.success("Purchase and purchase details recorded successfully!")

                except Exception as e:
                    conn.rollback()
                    st.error(f"Failed to record purchase: {e}")

    elif view_mode == "View By Date":
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")

            cursor.execute("""
                SELECT p.purchase_id, s.name, p.purchase_date, p.status, p.total_amount
                FROM Purchase p
                JOIN Supplier s ON p.supplier_id = s.supplier_id
                WHERE p.purchase_date BETWEEN %s AND %s
                ORDER BY p.purchase_date
            """, (start_date, end_date))
            purchases = cursor.fetchall()

            if not purchases:
                st.info("No purchases found for the selected dates.")
            else:
                for pid, supname, pdate, status, total in purchases:
                    with st.expander(f"Purchase #{pid} | Supplier: {supname} | Date: {pdate}"):
                        st.write(f"**Status:** {status}")
                        st.write(f"**Total Amount:** Rs.{total:.2f}")

                        cursor.execute("""
                            SELECT ii.item_name, pd.quantity, pd.price_per_unit
                            FROM PurchaseDetail pd
                            JOIN InventoryItem ii ON pd.item_id = ii.item_id
                            WHERE pd.purchase_id = %s
                        """, (pid,))
                        details = cursor.fetchall()
                        for item_name, qty, price_per_unit in details:
                            st.write(f"🛒 {item_name}: {qty} units at Rs.{price_per_unit}/unit")

                        new_status = st.selectbox("Update Status", ["Ordered", "Received", "Cancelled"], index=["Ordered", "Received", "Cancelled"].index(status), key=f"status_{pid}")

                        if new_status != status:
                            if st.button(f"Update Status for Purchase #{pid}", key=f"update_{pid}"):
                                try:
                                    cursor.execute("UPDATE Purchase SET status = %s WHERE purchase_id = %s", (new_status, pid))
                                    conn.commit()
                                    st.success(f"Status updated to {new_status} for Purchase #{pid}")
                                    st.rerun()
                                except Exception as e:
                                    conn.rollback()
                                    st.error(f"Failed to update status: {e}")

            cursor.close()
            conn.close()

            

# ------------------ MANAGE SHIFTS ------------------
def manager_manage_shifts():
    st.header("Shift Schedule Management")
    mode = st.radio("Select Mode", ["View Shifts", "Manage Shifts"])

    conn = get_db_connection()
    cursor = conn.cursor()

    if mode == "View Shifts":
            view_mode = st.radio("View Shifts By", ["Single Date", "Date Range", "Staff Name/ID"])

            cursor.execute("SELECT DISTINCT r.role_name FROM Role r JOIN Staff s ON r.role_id = s.role_id")
            roles = [r[0] for r in cursor.fetchall()]
            roles.insert(0, "All")  # Add "All" option
            selected_role = st.selectbox("Select Role", roles,key="view_shifts_role")

            if view_mode == "Single Date":
                date = st.date_input("Select Shift Date")

                if selected_role == "All":
                    cursor.execute("""
                        SELECT s.name, r.role_name, ss.start_time, ss.end_time
                        FROM ShiftSchedule ss
                        JOIN Staff s ON ss.staff_id = s.staff_id
                        JOIN Role r ON s.role_id = r.role_id
                        WHERE ss.shift_date = %s
                    """, (date,))
                else:
                    cursor.execute("""
                        SELECT s.name, r.role_name, ss.start_time, ss.end_time
                        FROM ShiftSchedule ss
                        JOIN Staff s ON ss.staff_id = s.staff_id
                        JOIN Role r ON s.role_id = r.role_id
                        WHERE ss.shift_date = %s AND r.role_name = %s
                    """, (date, selected_role))

                shifts = cursor.fetchall()
                if shifts:
                    for name, role, start, end in shifts:
                        st.write(f"👤 {name} ({role}) : {start} to {end}")
                else:
                    st.info("No shifts found for selected criteria.")

            elif view_mode == "Date Range":
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")

                if selected_role == "All":
                    cursor.execute("""
                        SELECT s.name, r.role_name, ss.shift_date, ss.start_time, ss.end_time
                        FROM ShiftSchedule ss
                        JOIN Staff s ON ss.staff_id = s.staff_id
                        JOIN Role r ON s.role_id = r.role_id
                        WHERE ss.shift_date BETWEEN %s AND %s
                        ORDER BY ss.shift_date
                    """, (start_date, end_date))
                else:
                    cursor.execute("""
                        SELECT s.name, r.role_name, ss.shift_date, ss.start_time, ss.end_time
                        FROM ShiftSchedule ss
                        JOIN Staff s ON ss.staff_id = s.staff_id
                        JOIN Role r ON s.role_id = r.role_id
                        WHERE ss.shift_date BETWEEN %s AND %s
                        AND r.role_name = %s
                        ORDER BY ss.shift_date
                    """, (start_date, end_date, selected_role))

                shifts = cursor.fetchall()
                if shifts:
                    for name, role, shift_date, start, end in shifts:
                        st.write(f" {shift_date} - {name} ({role}): {start} to {end}")
                else:
                    st.info("No shifts found for selected criteria.")

            

            elif view_mode == "Staff Name/ID":
                if selected_role == "All":
                    cursor.execute("""
                        SELECT staff_id, name
                        FROM Staff
                    """)
                else:
                    cursor.execute("""
                        SELECT s.staff_id, s.name
                        FROM Staff s
                        JOIN Role r ON s.role_id = r.role_id
                        WHERE r.role_name = %s
                    """, (selected_role,))
                staff_list = cursor.fetchall()

                if not staff_list:
                    st.info("No staff found for selected role.")
                else:
                    staff_map = {f"{name} (ID: {sid})": sid for sid, name in staff_list}
                    selected_staff = st.selectbox("Select Staff", list(staff_map.keys()))
                    staff_id = staff_map[selected_staff]

                    cursor.execute("""
                        SELECT ss.shift_date, ss.start_time, ss.end_time 
                        FROM ShiftSchedule ss
                        WHERE ss.staff_id = %s
                        ORDER BY ss.shift_date
                    """, (staff_id,))
                    shifts = cursor.fetchall()

                    if shifts:
                        for s in shifts:
                            st.write(f" {s[0]}: {s[1]} to {s[2]}")
                    else:
                        st.info("No shifts for selected staff.")


    elif mode == "Manage Shifts":
        st.subheader("Manage Shifts")

        date = st.date_input("Select Date for Managing Shifts")

        with db_cursor() as cursor:
            cursor.execute("SELECT staff_id, name FROM Staff")
            staff_data = cursor.fetchall()

            cursor.execute("""
                SELECT s.name, ss.shift_id, ss.staff_id, ss.start_time, ss.end_time
                FROM ShiftSchedule ss
                JOIN Staff s ON ss.staff_id = s.staff_id
                WHERE ss.shift_date = %s
            """, (date,))
            shifts = cursor.fetchall()

        st.subheader(f"Shifts on {date}")

        # ------------------ Existing Shifts ------------------
        for name, shift_id, sid, start, end in shifts:
            try:
                start_time_obj = parse_time_correctly(start)
                end_time_obj = parse_time_correctly(end)
            except Exception as e:
                st.error(f"Error parsing shift times: {e}")
                continue

            with st.expander(f"{name} | {start_time_obj.strftime('%H:%M')} - {end_time_obj.strftime('%H:%M')}"):
                new_start = st.time_input("Start Time", value=start_time_obj, key=f"start_{shift_id}")
                new_end = st.time_input("End Time", value=end_time_obj, key=f"end_{shift_id}")

                if st.button("Update Shift", key=f"update_shift_{shift_id}"):
                    try:
                        with db_cursor() as cursor:
                            cursor.execute(
                                "UPDATE ShiftSchedule SET start_time = %s, end_time = %s WHERE shift_id = %s",
                                (new_start.strftime("%H:%M:%S"), new_end.strftime("%H:%M:%S"), shift_id)
                            )
                        st.success(f"Shift for {name} updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating shift: {e}")

                if st.button("Delete Shift", key=f"delete_shift_{shift_id}"):
                    try:
                        with db_cursor() as cursor:
                            cursor.execute("DELETE FROM ShiftSchedule WHERE shift_id = %s", (shift_id,))
                        st.success(f"Shift for {name} deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting shift: {e}")

        # ------------------ Add New Shift ------------------
        st.markdown("---")
        st.header("Add New Shift")

        staff_map = {f"{name} (ID: {sid})": sid for sid, name in staff_data}
        selected_staff = st.selectbox("Select Staff to Add Shift", list(staff_map.keys()))
        staff_id = staff_map[selected_staff]

        start_time_new = st.time_input("Start Time (New)", key="start_new")
        end_time_new = st.time_input("End Time (New)", key="end_new")

        if st.button("Add New Shift"):
            try:
                with db_cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO ShiftSchedule (staff_id, shift_date, start_time, end_time) VALUES (%s, %s, %s, %s)",
                        (staff_id, date, start_time_new.strftime("%H:%M:%S"), end_time_new.strftime("%H:%M:%S"))
                    )
                st.success("New shift added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding new shift: {e}")


# ------------------ MANAGE INVENTORY ------------------
def manager_manage_inventory():
    st.header("Manage Inventory Items")
    with db_cursor() as cursor:
        cursor.execute("SELECT DISTINCT category FROM InventoryItem")
        categories = [row[0] for row in cursor.fetchall()]
        selected_category = st.selectbox("Select Category", categories)

        cursor.execute("""
            SELECT item_id, item_name, unit, current_quantity 
            FROM InventoryItem 
            WHERE category = %s
        """, (selected_category,))
        items = cursor.fetchall()

    if items:
        for item_id, name, unit, qty in items:
            with st.expander(f"{name} ({qty} {unit})"):
                new_name = st.text_input("Item Name", value=name, key=f"invname_{item_id}")
                new_unit = st.text_input("Unit", value=unit, key=f"invunit_{item_id}")
                new_qty = st.number_input("Quantity", value=float(qty), min_value=0.0, step=0.1, key=f"invqty_{item_id}")
                if st.button("Update Item", key=f"update_item_{item_id}"):
                    with db_cursor() as cursor:
                        cursor.execute("""
                            UPDATE InventoryItem 
                            SET item_name = %s, unit = %s, current_quantity = %s 
                            WHERE item_id = %s
                        """, (new_name, new_unit, new_qty, item_id))
                        st.success("Inventory item updated.")

                if st.button("Delete Item", key=f"delete_item_{item_id}"):
                    with db_cursor() as cursor:
                        cursor.execute("DELETE FROM InventoryItem WHERE item_id = %s", (item_id,))
                        st.success("Inventory item deleted.")
    else:
        st.info("No items found in selected category.")

    st.markdown("---")
    st.subheader("Add New Inventory Item")
    new_item_name = st.text_input("New Item Name")
    new_item_unit = st.text_input("New Unit")
    new_item_qty = st.number_input("New Quantity", min_value=0.0, step=0.1)
    new_item_category = st.text_input("New Category")

    if st.button("Add New Item"):
        with db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO InventoryItem (item_name, unit, current_quantity, category)
                VALUES (%s, %s, %s, %s)
            """, (new_item_name, new_item_unit, new_item_qty, new_item_category))
            st.success("New inventory item added.")


# ------------------ MANAGE SUPPLIERS ------------------
def manager_manage_suppliers():
    st.header("Manage Suppliers")

    with db_cursor() as cursor:
        cursor.execute("SELECT supplier_id, name, phone, category FROM Supplier")
        suppliers = cursor.fetchall()

    if suppliers:
        for supplier_id, name, phone, category in suppliers:
            with st.expander(f"{name} ({category})"):
                new_name = st.text_input("Supplier Name", value=name, key=f"sup_name_{supplier_id}")
                new_phone = st.text_input("Phone", value=phone, key=f"sup_phone_{supplier_id}")
                new_category = st.text_input("Category", value=category, key=f"sup_category_{supplier_id}")

                if st.button("Update Supplier", key=f"update_sup_{supplier_id}"):
                    try:
                        with db_cursor() as cursor:
                            cursor.execute("""
                                UPDATE Supplier
                                SET name = %s, phone = %s, category = %s
                                WHERE supplier_id = %s
                            """, (new_name, new_phone, new_category, supplier_id))
                        st.success("Supplier updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update supplier: {e}")
    else:
        st.info("No suppliers found.")

    st.markdown("---")
    st.subheader("Add New Supplier")

    new_sup_name = st.text_input("New Supplier Name")
    new_sup_phone = st.text_input("New Supplier Phone")
    new_sup_category = st.text_input("New Supplier Category")

    if st.button("Add Supplier"):
        if new_sup_name and new_sup_category:
            try:
                with db_cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO Supplier (name, phone, category)
                        VALUES (%s, %s, %s)
                    """, (new_sup_name, new_sup_phone, new_sup_category))
                st.success("New supplier added successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add supplier: {e}")
        else:
            st.warning("Please fill in all required fields (Name and Category).")

# ------------------ MANAGE MENU ITEMS ------------------
def manager_manage_menu_items():
    st.header("Manage Menu Items")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch existing menu items
        cursor.execute("SELECT menu_item_id, name, price, is_available FROM MenuItem")
        menu_items = cursor.fetchall()

        if menu_items:
            for item_id, name, price, available in menu_items:
                with st.expander(f"{name} (Rs.{price:.2f}) - {'Available' if available else 'Unavailable'}"):
                    new_name = st.text_input("New Name", value=name, key=f"menuname_{item_id}")
                    new_price = st.number_input("New Price", min_value=0.0, value=float(price), key=f"menuprice_{item_id}")
                    new_availability = st.checkbox("Available", value=bool(available), key=f"menuavail_{item_id}")

                    if st.button("Update Menu Item", key=f"update_menu_{item_id}"):
                        try:
                            cursor.execute("""
                                UPDATE MenuItem
                                SET name = %s, price = %s, is_available = %s
                                WHERE menu_item_id = %s
                            """, (new_name, new_price, int(new_availability), item_id))
                            conn.commit()
                            st.success(f"Menu item '{new_name}' updated successfully!")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Failed to update menu item: {e}")
        else:
            st.info("No menu items found.")

        st.markdown("---")
        st.subheader("Add New Menu Item")

        # Fetch categories for new item
        cursor.execute("SELECT category_id, category_name FROM MenuCategory")
        categories = cursor.fetchall()
        category_map = {name: cid for cid, name in categories}

        new_item_name = st.text_input("Item Name")
        new_item_price = st.number_input("Price", min_value=0.0)
        new_item_category = st.selectbox("Category", list(category_map.keys()))

        if st.button("Add Menu Item"):
            if new_item_name and new_item_category:
                try:
                    cursor.execute("""
                        INSERT INTO MenuItem (name, price, category_id, is_available)
                        VALUES (%s, %s, %s, 1)
                    """, (new_item_name, new_item_price, category_map[new_item_category]))
                    conn.commit()
                    st.success(f"Menu item '{new_item_name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Failed to add new menu item: {e}")
            else:
                st.warning("Please fill all fields before adding a menu item.")

    except Exception as e:
        st.error(f"An error occurred while managing menu items: {e}")
    finally:
        cursor.close()
        conn.close()

# ------------------ MANAGER DASHBOARD ------------------
def manager_dashboard():
    st.sidebar.title("Manager Dashboard")
    choice = st.sidebar.selectbox("Select Option", [
        "View Orders", "Manage Inventory", "Manage Purchases", "Manage Shifts", "Manage Staff", "View Events", "Manage Suppliers", "Manage Menu Items" 
    ])

    if choice == "View Orders":
        manager_dashboard_view_orders()
    elif choice == "Manage Inventory":
        manager_manage_inventory()
    elif choice == "Manage Purchases":
        manager_manage_purchases()
    elif choice == "Manage Shifts":
        manager_manage_shifts()
    elif choice == "Manage Staff":
        manager_staff_management()
    elif choice == "View Events":
        manager_view_upcoming_events()
    elif choice == "Manage Suppliers":
        manager_manage_suppliers()   
    elif choice == "Manage Menu Items":
        manager_manage_menu_items()

