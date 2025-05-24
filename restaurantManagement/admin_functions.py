import streamlit as st
from db import db_cursor
from utils import safe_parse_time
from datetime import (datetime, timedelta, time)

def fix_time(value):
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return time(hour=hours, minute=minutes)
    elif isinstance(value, datetime):
        return value.time()
    elif isinstance(value, time):
        return value
    else:
        return time(0, 0)  # Default if weird


def admin_view_upcoming_events():
    st.header("View Upcoming Events")
    mode = st.radio("View By", ["Single Date", "Date Range"])

    with db_cursor() as cursor:
        if mode == "Single Date":
            date = st.date_input("Select Date")
            cursor.execute("""
                SELECT e.event_name, e.location, e.event_date, e.start_time, e.end_time, c.name, eb.guest_count
                FROM Event e
                JOIN EventBooking eb ON e.event_id = eb.event_id
                JOIN Customer c ON eb.customer_id = c.customer_id
                WHERE e.event_date = %s
            """, (date,))
        else:
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            cursor.execute("""
                SELECT e.event_name, e.location, e.event_date, e.start_time, e.end_time, c.name, eb.guest_count
                FROM Event e
                JOIN EventBooking eb ON e.event_id = eb.event_id
                JOIN Customer c ON eb.customer_id = c.customer_id
                WHERE e.event_date BETWEEN %s AND %s
            """, (start_date, end_date))

        events = cursor.fetchall()

    if events:
        for event in events:
            event_name, location, event_date, start_time, end_time, customer_name, guest_count = event

            # 🛠 Fix time values properly
            start_time = fix_time(start_time)
            end_time = fix_time(end_time)

            st.markdown(f"""
             **{event_date}**
            - **Event:** {event_name}
            - **Location:** {location}
            - **Guests:** {guest_count}
            - **Customer:** {customer_name}
            - **Time:** {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}
            """)
    else:
        st.info("No events found for selected criteria.")

def admin_manage_reservations():
    st.header("Manage Reservations")
    filter_mode = st.radio("Filter By", ["All", "Date", "Date Range"])
    
    with db_cursor() as cursor:
        if filter_mode == "Date":
            date = st.date_input("Select Date")
            cursor.execute("""
                SELECT r.reservation_id, c.name, t.table_number, r.reservation_date, r.time_slot, r.guest_count, r.status
                FROM Reservation r
                JOIN Customer c ON r.customer_id = c.customer_id
                JOIN `Table` t ON r.table_id = t.table_id
                WHERE r.reservation_date = %s
            """, (date,))
        elif filter_mode == "Date Range":
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            cursor.execute("""
                SELECT r.reservation_id, c.name, t.table_number, r.reservation_date, r.time_slot, r.guest_count, r.status
                FROM Reservation r
                JOIN Customer c ON r.customer_id = c.customer_id
                JOIN `Table` t ON r.table_id = t.table_id
                WHERE r.reservation_date BETWEEN %s AND %s
            """, (start_date, end_date))
        else:
            cursor.execute("""
                SELECT r.reservation_id, c.name, t.table_number, r.reservation_date, r.time_slot, r.guest_count, r.status
                FROM Reservation r
                JOIN Customer c ON r.customer_id = c.customer_id
                JOIN `Table` t ON r.table_id = t.table_id
            """)
        
        reservations = cursor.fetchall()

    if reservations:
        reservation_map = {f"#{r[0]} - {r[1]} on {r[3]}": r for r in reservations}
        selected = st.selectbox("Select Reservation", list(reservation_map.keys()))
        r = reservation_map[selected]

        st.write(f"**Reservation ID:** {r[0]} | **Name:** {r[1]} | **Table:** {r[2]} | **Date:** {r[3]} | **Time:** {r[4]} | **Guests:** {r[5]} | **Status:** {r[6]}")

        new_date = st.date_input("New Date", value=r[3])
        
        try:
            start_time, end_time = r[4].split("-")
        except Exception:
            start_time, end_time = "12:00", "13:00"
        
        new_start = st.time_input("Start Time", value=safe_parse_time(start_time))
        new_end = st.time_input("End Time", value=safe_parse_time(end_time))
        new_guest_count = st.number_input("Guest Count", value=r[5], step=1)

        if r[6] != 'Cancelled':  # Only show Update if NOT Cancelled
            if st.button("Update Reservation"):
                with db_cursor() as cursor:
                    new_slot = f"{new_start.strftime('%H:%M')}-{new_end.strftime('%H:%M')}"
                    cursor.execute("""
                        UPDATE Reservation 
                        SET reservation_date = %s, time_slot = %s, guest_count = %s
                        WHERE reservation_id = %s
                    """, (new_date, new_slot, new_guest_count, r[0]))
                    st.success("Reservation updated successfully!")

        if r[6] != 'Cancelled':
            if st.button("Cancel Reservation"):
                with db_cursor() as cursor:
                    cursor.execute("UPDATE Reservation SET status = 'Cancelled' WHERE reservation_id = %s", (r[0],))
                    st.success("Reservation cancelled successfully.")
        else:
            st.info("This reservation is already cancelled. No further updates allowed.")
    else:
        st.info("No reservations found.")


def admin_table_reservation():
    st.header("Available Tables & Make Reservation")
    with db_cursor() as cursor:
        cursor.execute("SELECT table_id, table_number, seating_capacity FROM `Table` WHERE status = 'Available'")
        tables = cursor.fetchall()

    if tables:
        table_map = {f"Table {num} (Seats: {cap})": tid for tid, num, cap in tables}
        customer_name = st.text_input("Customer Name")
        phone = st.text_input("Phone Number")
        date = st.date_input("Reservation Date")
        
        #  Dropdown for Time Slots instead of free text
        time_slots = [
            "09:00-10:00", "10:00-11:00", "11:00-12:00",
            "12:00-13:00", "13:00-14:00", "14:00-15:00",
            "15:00-16:00", "16:00-17:00", "17:00-18:00",
            "18:00-19:00", "19:00-20:00", "20:00-21:00",
            "21:00-22:00", "22:00-23:00"
        ]
        slot = st.selectbox("Select Time Slot", time_slots)

        guests = st.number_input("Guest Count", min_value=1)
        selected_table = st.selectbox("Select Table", list(table_map.keys()))
        table_id = table_map[selected_table]

        if st.button("Reserve Table"):
            with db_cursor() as cursor:
                cursor.execute("INSERT INTO Customer (name, phone) VALUES (%s, %s)", (customer_name, phone))
                customer_id = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO Reservation (customer_id, table_id, reservation_date, time_slot, guest_count, status)
                    VALUES (%s, %s, %s, %s, %s, 'Reserved')
                """, (customer_id, table_id, date, slot, guests))
                cursor.execute("UPDATE `Table` SET status='Reserved' WHERE table_id=%s", (table_id,))
                st.success("Table reserved successfully!")
    else:
        st.warning("No available tables.")


def admin_event_booking():
    st.header("Event Booking")
    action = st.radio("Action", ["Book New Event", "Update/Delete Events"])

    if action == "Book New Event":
        customer_name = st.text_input("Customer Name (Event)")
        phone = st.text_input("Phone Number")
        event_name = st.text_input("Event Name")
        location = st.text_input("Location")
        event_date = st.date_input("Event Date")
        start_time = st.time_input("Start Time")
        end_time = st.time_input("End Time")
        guest_count = st.number_input("Guest Count", min_value=1)

        if st.button("Book Event"):
            with db_cursor() as cursor:
                # Insert Customer
                cursor.execute("INSERT INTO Customer (name, phone) VALUES (%s, %s)", (customer_name, phone))
                customer_id = cursor.lastrowid

                # Insert Event ( with proper start_time, end_time now)
                staff_id = st.session_state.user_id
                cursor.execute("""
                    INSERT INTO Event (event_name, event_date, start_time, end_time, location, created_by_staff_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (event_name, event_date, start_time.strftime("%H:%M:%S"), end_time.strftime("%H:%M:%S"), location, staff_id))
                event_id = cursor.lastrowid

                # Insert into EventBooking
                cursor.execute("""
                    INSERT INTO EventBooking (event_id, customer_id, booking_date, guest_count)
                    VALUES (%s, %s, CURDATE(), %s)
                """, (event_id, customer_id, guest_count))


                st.success("Event booked successfully!")

    elif action == "Update/Delete Events":
        event_date = st.date_input("Select Event Date")

        with db_cursor() as cursor:
            cursor.execute("""
                SELECT event_id, event_name, location, start_time, end_time
                FROM Event
                WHERE event_date = %s
            """, (event_date,))
            events = cursor.fetchall()

        if events:
            event_map = {f"Event #{eid} - {ename} at {loc}": eid for eid, ename, loc, stime, etime in events}
            selected_event = st.selectbox("Select Event to Update/Delete", list(event_map.keys()))
            selected_id = event_map[selected_event]

            with db_cursor() as cursor:
                cursor.execute("""
                    SELECT event_name, location, start_time, end_time FROM Event WHERE event_id = %s
                """, (selected_id,))
                event_data = cursor.fetchone()

            name, location, start_time, end_time = event_data

            new_name = st.text_input("New Event Name", value=name)
            new_location = st.text_input("New Location", value=location)
            new_start_time = st.time_input("New Start Time", value=safe_parse_time(start_time))
            new_end_time = st.time_input("New End Time", value=safe_parse_time(end_time))


            if st.button("Update Event"):
                with db_cursor() as cursor:
                    cursor.execute("""
                        UPDATE Event
                        SET event_name = %s, location = %s, start_time = %s, end_time = %s
                        WHERE event_id = %s
                    """, (new_name, new_location, new_start_time.strftime("%H:%M:%S"), new_end_time.strftime("%H:%M:%S"), selected_id))
                    st.success("Event updated successfully!")

            if st.button("Delete Event"):
                with db_cursor() as cursor:
                    cursor.execute("DELETE FROM EventBooking WHERE event_id = %s", (selected_id,))
                    cursor.execute("DELETE FROM Event WHERE event_id = %s", (selected_id,))
                    st.success("Event deleted successfully.")

        else:
            st.info("No events found on selected date.")

def admin_place_order():
    st.header("Place Order")
    order_type = st.radio("Order Type", ["Dine-In", "Takeaway"])
    customer_name = st.text_input("Customer Name")
    phone = st.text_input("Phone Number")

    with db_cursor() as cursor:
        cursor.execute("SELECT category_id, category_name FROM MenuCategory")
        categories = cursor.fetchall()
        category_map = {name: cid for cid, name in categories}
        category = st.selectbox("Menu Category", list(category_map.keys()))

        cursor.execute("SELECT menu_item_id, name, price FROM MenuItem WHERE category_id = %s AND is_available = 1", (category_map[category],))
        items = cursor.fetchall()

    st.subheader("Items")
    for item_id, name, price in items:
        qty = st.number_input(f"{name} - Rs.{price}", min_value=0, step=1, key=f"item_{item_id}")
        if qty > 0:
            st.session_state.cart[name] = (item_id, qty, price)
        elif name in st.session_state.cart:
            del st.session_state.cart[name]

    st.subheader("Cart")
    total = 0
    for name, (item_id, qty, price) in st.session_state.cart.items():
        st.write(f"{name} x {qty} = Rs.{qty * price}")
        total += qty * price

    discount_code = st.text_input("Discount Code (or 0 if none)")
    discount_id = None
    if discount_code != "0":
        with db_cursor() as cursor:
            cursor.execute("SELECT discount_id, discount_percentage FROM Discount WHERE discount_code = %s", (discount_code,))
            result = cursor.fetchone()
            if result:
                discount_id, percent = result
                total *= (1 - percent / 100)
                st.success(f"{percent}% discount applied")
            else:
                st.warning("Invalid discount code")

    st.markdown(f"### Total Payable: Rs. {total:.2f}")

    if "order_confirmed" not in st.session_state:
        st.session_state.order_confirmed = False

    if not st.session_state.order_confirmed:
        if st.button("Confirm Order and Proceed to Payment"):
            try:
                with db_cursor() as cursor:
                    # Insert Customer
                    cursor.execute("INSERT INTO Customer (name, phone) VALUES (%s, %s)", (customer_name, phone))
                    customer_id = cursor.lastrowid
                    staff_id = st.session_state.user_id
                    order_time = datetime.now()

                    # Insert into Order ( no table_id)
                    cursor.execute("""
                        INSERT INTO `Order` (staff_id, customer_id, order_time, status)
                        VALUES (%s, %s, %s, 'Placed')
                    """, (staff_id, customer_id, order_time))
                    order_id = cursor.lastrowid

                    # Save order_id in session
                    st.session_state.order_id = order_id

                    # Insert OrderDetails
                    for name, (item_id, qty, price) in st.session_state.cart.items():
                        cursor.execute("""
                            INSERT INTO OrderDetail (order_id, menu_item_id, quantity, price)
                            VALUES (%s, %s, %s, %s)
                        """, (order_id, item_id, qty, price))

                    # Insert Invoice
                    cursor.execute("""
                        INSERT INTO Invoice (order_id, total_amount, discount_id, created_at)
                        VALUES (%s, %s, %s, NOW())
                    """, (order_id, total, discount_id))
                    invoice_id = cursor.lastrowid

                    st.session_state.invoice_id = invoice_id
                    st.session_state.total_amount = total
                    st.session_state.order_confirmed = True
                    st.session_state.payment_stage = True

                    st.success("Order Confirmed! Proceed to Payment.")

            except Exception as e:
                st.error(f"Error processing order: {e}")

    #  New Cancel Button
    if st.session_state.get("order_confirmed", False) and st.session_state.get("payment_stage", False):
        if st.button("Cancel Order"):
            try:
                with db_cursor() as cursor:
                    cursor.execute("""
                        UPDATE `Order`
                        SET status = 'Cancelled'
                        WHERE order_id = %s
                    """, (st.session_state.order_id,))
                st.success("Order Cancelled Successfully.")
                # Reset states
                st.session_state.cart = {}
                st.session_state.order_confirmed = False
                st.session_state.payment_stage = False
            except Exception as e:
                st.error(f"Failed to cancel order: {e}")

    if st.session_state.get("payment_stage", False):
        st.subheader("Payment")
        payment_method = st.radio("Select Payment Method", ["UPI", "Cash"])

        if payment_method == "Cash":
            if st.button("Mark as Paid (Cash)"):
                try:
                    with db_cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO Payment (invoice_id, amount_paid, payment_method, payment_date)
                            VALUES (%s, %s, %s, NOW())
                        """, (st.session_state.invoice_id, st.session_state.total_amount, "Cash"))
                    st.success("Cash Payment Recorded Successfully!")
                    st.session_state.payment_stage = False
                    st.session_state.cart = {}

                    display_invoice()

                except Exception as e:
                    st.error(f"Failed to record cash payment: {e}")

        elif payment_method == "UPI":
            st.image("https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay?pa=restaurant@upi", caption="Scan to Pay UPI", width=200)

            if st.button("Payment Done (UPI)"):
                try:
                    with db_cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO Payment (invoice_id, amount_paid, payment_method, payment_date)
                            VALUES (%s, %s, %s, NOW())
                        """, (st.session_state.invoice_id, st.session_state.total_amount, "UPI"))
                    st.success("UPI Payment Recorded Successfully!")
                    st.session_state.payment_stage = False
                    st.session_state.cart = {}

                    display_invoice()

                except Exception as e:
                    st.error(f"Failed to record UPI payment: {e}")


# Show Invoice
def display_invoice():
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT o.order_id, c.name, o.order_time
            FROM `Order` o
            JOIN Invoice i ON o.order_id = i.order_id
            JOIN Customer c ON o.customer_id = c.customer_id
            WHERE i.invoice_id = %s
        """, (st.session_state.invoice_id,))
        order_info = cursor.fetchone()

        cursor.execute("""
            SELECT m.name, od.quantity, od.price
            FROM OrderDetail od
            JOIN MenuItem m ON od.menu_item_id = m.menu_item_id
            JOIN `Order` o ON od.order_id = o.order_id
            JOIN Invoice i ON o.order_id = i.order_id
            WHERE i.invoice_id = %s
        """, (st.session_state.invoice_id,))
        items = cursor.fetchall()

    if order_info:
        order_id, customer_name, order_time = order_info
        st.markdown("---")
        st.success(f"Invoice for Order #{order_id}")
        st.write(f"**Customer:** {customer_name}")
        st.write(f"**Order Time:** {order_time.strftime('%d-%m-%Y %H:%M')}")

        st.subheader("Ordered Items")
        for item_name, qty, price in items:
            st.write(f"- {item_name} x {qty} = Rs.{qty * price:.2f}")

        st.markdown(f"### **Total Paid: Rs.{st.session_state.total_amount:.2f}**")
