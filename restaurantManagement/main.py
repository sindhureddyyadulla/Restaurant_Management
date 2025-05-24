import streamlit as st
from auth import login_screen
from admin_functions import admin_place_order, admin_event_booking, admin_manage_reservations, admin_table_reservation, admin_view_upcoming_events
from utils import initialize_session

from manager_functions import (
    manager_view_upcoming_events,
    manager_staff_management,
    manager_dashboard_view_orders,
    manager_manage_inventory,
    manager_manage_purchases,
    manager_manage_shifts,
    manager_manage_suppliers,
    manager_manage_menu_items
)

# Initialize session
initialize_session()

if not st.session_state.logged_in:
    login_screen()

else:
    st.sidebar.success(f"Logged in as: {st.session_state.role.upper()}")

    if st.session_state.role == "admin":
        action = st.sidebar.selectbox("Admin Actions", [
            "Place Order", "Event Booking", "Manage Reservations", "Reserve Table", "View Events"
        ])
        if action == "Place Order":
            admin_place_order()
        elif action == "Event Booking":
            admin_event_booking()
        elif action == "Manage Reservations":
            admin_manage_reservations()
        elif action == "Reserve Table":
            admin_table_reservation()
        elif action == "View Events":
            admin_view_upcoming_events()

    elif st.session_state.role == "manager":
        action = st.sidebar.selectbox("Manager Actions", [
            "View Orders", "Manage Inventory", "Manage Purchases", "Manage Shifts", "Staff Management", "View Events","Manage Suppliers", "Manage Menu Items"
        ])
        if action == "View Orders":
            manager_dashboard_view_orders()
        elif action == "Manage Inventory":
            manager_manage_inventory()
        elif action == "Manage Purchases":
            manager_manage_purchases()
        elif action == "Manage Shifts":
            manager_manage_shifts()
        elif action == "Staff Management":
            manager_staff_management()
        elif action == "View Events":
            manager_view_upcoming_events()
        elif action == "Manage Suppliers":
            manager_manage_suppliers()
        elif action == "Manage Menu Items":
            manager_manage_menu_items()

