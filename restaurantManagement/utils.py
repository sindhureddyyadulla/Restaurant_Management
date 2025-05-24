import datetime
import streamlit as st

def safe_parse_time(value):
    if value is None:
        return datetime.time(0, 0)
    if isinstance(value, datetime.time):
        return value
    if isinstance(value, datetime.datetime):
        return value.time()
    if isinstance(value, str):
        value = value.strip()
        if value.isdigit():
            value = value.zfill(2) + ":00"
        if len(value) == 5:
            return datetime.datetime.strptime(value, "%H:%M").time()
        elif len(value) == 8:
            return datetime.datetime.strptime(value, "%H:%M:%S").time()
    return datetime.time(0, 0)

def initialize_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.cart = {}
