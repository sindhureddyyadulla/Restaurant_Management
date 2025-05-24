import streamlit as st
from db import db_cursor

def login_user(username, password):
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT u.user_id, r.role_name
            FROM User u
            JOIN Role r ON u.role_id = r.role_id
            WHERE u.username = %s AND u.password = %s
        """, (username, password))
        return cursor.fetchone()

def login_screen():
    st.title("Login")
    role_choice = st.radio("Login As", ["Admin", "Manager"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user and user[1].lower() == role_choice.lower():  
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.session_state.role = user[1].lower()  
            st.rerun()
        else:
            st.error("Invalid credentials or role")
