# 🍽️ Restaurant Management System

A complete **Restaurant Management System** built using **Python**, **Streamlit**, and **MySQL**.  
This system supports role-based login for **Admin** and **Manager**, allowing them to perform all core restaurant operations including order placement, inventory management, staff scheduling, event booking, and more.


 ----🚀 Features----

👨‍💼 Admin Features

- 🔐 **Login** with role-based access
- 🧾 **Place Orders**
   - Dine-In and Takeaway options
   - Search and select menu items by category
   - Add items to cart and manage quantities
   - Apply available discounts
   - Generate Invoice with payment details
- 🪑 **Table Reservations**
   - Add new reservations for customers
   - View, update, and delete reservations
- 🎉 **Event Booking**
   - Book events on behalf of customers
   - Record event name, date, time, location, guest count
- 📋 **Customer Management**
   - Create new customer records during order or reservation
- 📄 **Invoice Generation**
   - Create invoice for each order
   - Link to applied discounts
- 💳 **Payments**
   - Capture payment method (Cash/UPI)
   - Track payment time and amount

----------------------------------------

 🧑‍🔧 Manager Features

- 🔐 **Login** with role-based access
- 📦 **Inventory Management**
   - View current inventory items
   - Update stock levels
- 🛒 **Supplier Purchases**
   - View and manage suppliers
   - Create, update, and cancel purchase orders
- 🕒 **Shift Scheduling**
   - Assign shifts to staff (admin, manager, chief)
   - Update and view shift schedules
- 📆 **View Events**
   - Monitor all upcoming booked events

-----------------------------------------

🛠️ Tech Stack

| Layer         | Technology                 |
|---------------|--------------------------  |
| Frontend      | Streamlit (Python-based UI)|
| Backend       | Python                     |
| Database      | MySQL                      |


**Run the application:**

  streamlit run app.py


