import streamlit as st
import mysql.connector
import base64
import pandas as pd
from datetime import datetime

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="3306",
        database="car"
    )

def set_background(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    css = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpg;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Set wallpaper with relative path
set_background("car.jpg")


def authenticate_user(username, password, role):
    conn = connect_db()
    cursor = conn.cursor()

    if role == 'Admin':
        cursor.execute(
            "SELECT * FROM admin WHERE username=%s AND password=%s",
            (username, password)
        )
    elif role == 'Customer':
        cursor.execute(
            "SELECT * FROM customer WHERE username=%s AND password=%s",
            (username, password)
        )
    else:
        conn.close()
        return None

    result = cursor.fetchone()
    conn.close()
    return result

def admin_dashboard():
    st.header("Admin Dashboard")

    if st.button("Sign Out", key="sign_out_btn"):
        st.session_state.clear()
        st.session_state.page = "login"
        st.rerun()

    if st.button("Back", key="back_btn"):
        st.session_state.page = "login"
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["Manage Cars", "Update Car Info", "Remove Car", "View Bookings"])

    # Tab 1: Add new cars
    with tab1:
        st.subheader("Add New Car")
        car_id = st.text_input("Car ID", key="add_car_id")
        model = st.text_input("Car Model", key="add_model")
        brand = st.text_input("Brand", key="add_brand")
        year = st.number_input("Year", min_value=1900, max_value=2100, step=1, key="add_year")
        status = st.selectbox("Status", ["Available", "Unavailable"], key="add_status")

        if st.button("Add Car", key="add_car_btn"):
            if car_id and model and brand:
                conn = connect_db()
                cursor = conn.cursor()
                # Check duplicate car_id
                cursor.execute("SELECT * FROM available_cars WHERE car_id = %s", (car_id,))
                existing_car = cursor.fetchone()

                if existing_car:
                    st.warning(f"Car ID '{car_id}' already exists. Please use a unique Car ID.")
                else:
                    cursor.execute(
                        "INSERT INTO available_cars (car_id, model, brand, year, status) VALUES (%s, %s, %s, %s, %s)",
                        (car_id, model, brand, year, status)
                    )
                    conn.commit()
                    st.success("Car added successfully!")
                conn.close()
            else:
                st.warning("Please fill in all required fields.")

    # Tab 2: Update car info (only available cars)
    with tab2:
        st.subheader("Update Car Information")
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT car_id, model, brand, year, status FROM available_cars WHERE status='Available'")
        cars = cursor.fetchall()
        conn.close()

        if cars:
            cars_display = [f"{car[1]} ({car[2]}) - ID: {car[0]}" for car in cars]
            selected_car_update = st.selectbox("Select a car to update", options=cars_display, key="update_car_selectbox")

            car_id_to_update = selected_car_update.split("ID: ")[1].strip()
            car_to_edit = next((car for car in cars if str(car[0]) == car_id_to_update), None)

            if car_to_edit:
                new_model = st.text_input("Model", value=car_to_edit[1], key="update_model")
                new_brand = st.text_input("Brand", value=car_to_edit[2], key="update_brand")
                new_year = st.number_input("Year", min_value=1900, max_value=2100, step=1, value=car_to_edit[3], key="update_year")
                new_status = st.selectbox("Status", ["Available", "Unavailable"],
                                          index=0 if car_to_edit[4] == "Available" else 1,
                                          key="update_status")

                if st.button("Update Car Info", key="update_car_btn"):
                    conn = connect_db()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE available_cars
                        SET model=%s, brand=%s, year=%s, status=%s
                        WHERE car_id=%s
                    """, (new_model, new_brand, new_year, new_status, car_id_to_update))
                    conn.commit()
                    conn.close()
                    st.success(f"Car ID {car_id_to_update} updated successfully!")
                    st.rerun()
        else:
            st.info("No available cars to update.")

    # Tab 3: Remove car (only available cars)
    with tab3:
        st.subheader("Remove Car")
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT car_id, model, brand FROM available_cars WHERE status='Available'")
        cars = cursor.fetchall()
        conn.close()

        if cars:
            cars_display = [f"{car[1]} ({car[2]}) - ID: {car[0]}" for car in cars]
            selected_car_remove = st.selectbox("Select a car to remove", options=cars_display, key="remove_car_selectbox")

            car_id_to_remove = selected_car_remove.split("ID: ")[1].strip()

            if st.button("Remove Car", key="remove_car_btn"):
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM available_cars WHERE car_id=%s", (car_id_to_remove,))
                conn.commit()
                conn.close()
                st.success(f"Car ID {car_id_to_remove} removed successfully!")
                st.rerun()
        else:
            st.info("No available cars to remove.")

    # Tab 4: View bookings
    with tab4:
        st.subheader("Bookings")
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rented_cars")
        bookings = cursor.fetchall()
        conn.close()

        columns = ["ID", "Username", "Car_ID", "Duration", "Date"]
        df_bookings = pd.DataFrame(bookings, columns=columns)
        st.table(df_bookings)

def customer_dashboard(username):
    st.header(f"Welcome, {username}")

    if st.button("Back"):
        st.session_state.page = "login"
        st.rerun()

    tab1, tab2 = st.tabs(["Browse Cars", "My Bookings"])

    with tab1:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM available_cars WHERE status = 'Available'")
        cars = cursor.fetchall()
        conn.close()

        columns = ["Car_ID", "Model", "Brand", "Year", "Status"]
        df_cars = pd.DataFrame(cars, columns=columns)

        st.dataframe(df_cars.drop(columns=["Status"]))

        if not df_cars.empty:
            car_ids = df_cars["Car_ID"].tolist()
            car_models = df_cars["Model"].tolist()

            if "selected_car" not in st.session_state:
                selected_car = st.selectbox("Select a car to rent", options=car_models)
                if st.button(f"Rent {selected_car}"):
                    st.session_state.selected_car = selected_car
                    st.session_state.selected_car_id = car_ids[car_models.index(selected_car)]
                    st.rerun()
            else:
                st.write(f"Selected car to rent: **{st.session_state.selected_car}**")
                duration = st.number_input("Enter rental duration (days):", min_value=1, max_value=365, step=1)
                if st.button("Confirm Rental"):
                    conn = connect_db()
                    cursor = conn.cursor()
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute(
                        "INSERT INTO rented_cars (username, car_id, duration, date) VALUES (%s, %s, %s, %s)",
                        (username, st.session_state.selected_car_id, duration, current_date)
                    )
                    cursor.execute(
                        "UPDATE available_cars SET status='Unavailable' WHERE car_id=%s",
                        (st.session_state.selected_car_id,)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"{st.session_state.selected_car} rented for {duration} days successfully!")
                    del st.session_state.selected_car
                    del st.session_state.selected_car_id
                    st.rerun()
        else:
            st.info("No cars available for rent at the moment.")

    with tab2:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rented_cars WHERE username=%s", (username,))
        bookings = cursor.fetchall()
        conn.close()

        columns = ["id", "username", "car_id", "duration", "date"]
        df_bookings = pd.DataFrame(bookings, columns=columns)
        st.table(df_bookings)

def login_page():
    st.title("🚗 Car Rental Management System")

    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Admin", "Customer"])

        if st.button("Login"):
            user = authenticate_user(username, password, role)
            if user:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = username
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Invalid credentials")

    elif choice == "Register":
        st.subheader("Register")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")
        role = st.selectbox("Role", ["Admin", "Customer"])

        if st.button("Register"):
            if not new_user or not new_pass:
                st.warning("Please enter username and password.")
            else:
                conn = connect_db()
                cursor = conn.cursor()
                # Check for existing username
                if role == "Admin":
                    cursor.execute("SELECT * FROM admin WHERE username=%s", (new_user,))
                else:
                    cursor.execute("SELECT * FROM customer WHERE username=%s", (new_user,))

                if cursor.fetchone():
                    st.warning(f"Username '{new_user}' already exists. Please choose a different username.")
                else:
                    try:
                        if role == "Admin":
                            cursor.execute(
                                "INSERT INTO admin (username, password) VALUES (%s, %s)",
                                (new_user, new_pass)
                            )
                        elif role == "Customer":
                            cursor.execute(
                                "INSERT INTO customer (username, password) VALUES (%s, %s)",
                                (new_user, new_pass)
                            )
                        conn.commit()
                        st.success(f"{role} registered successfully.")
                    except Exception as e:
                        st.error(f"Error: {e}")
                conn.close()

def main():
    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.page = "login"

    if st.session_state.logged_in and st.session_state.page == "dashboard":
        if st.session_state.role == "Admin":
            admin_dashboard()
        elif st.session_state.role == "Customer":
            customer_dashboard(st.session_state.username)
    else:
        login_page()

if __name__ == "__main__":
    main()
