import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database connection details from environment variables
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# Connect to the PostgreSQL database
connection = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

def get_next_order_id():
    cursor = connection.cursor()
    cursor.execute("""SELECT MAX(order_id) from orders;""")
    next_order_id = cursor.fetchone()
    cursor.close()
    
    return next_order_id[0]+1 if next_order_id else 1

def get_order_status(order_id: str):
    cursor = connection.cursor()
    cursor.execute("""SELECT status_name FROM order_tracking 
                      JOIN order_status ON order_tracking.status_id = order_status.status_id
                      WHERE order_id = %s""", (order_id,))
    status = cursor.fetchone()
    cursor.close()
    
    return status[0] if status else None


def save_order_details(order: dict):
    order_id = get_next_order_id()
    return_code = insert_order_items(order_id,order)

    if return_code != -1:
        order_total = get_order_total(order_id)
        status_id = get_status_id("In progress")
        insert_order_tracking(order_id,status_id)
        return f"Awesome!! Order place with order id #{order_id}. Your order total is {order_total}." 
    else:
        return "Sorry, I couldn't process your order due to backend error. Please place a new order"

def get_item_details(order):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT item_id, price, name FROM food_items WHERE name IN %s", (tuple(order.keys()),))
        item_data =cursor.fetchall()
        cursor.close()
        return item_data if item_data else None

    except Exception as e:
        return None

def insert_order_items(order_id,order):
    try:
        item_data = get_item_details(order)

        if not item_data:
            return -1
        
        order_items = []
        for item_id,price,name in item_data:
            quantity = order[name]
            total_price = price * quantity
            order_items.append((order_id,item_id,quantity,total_price))
        

        cursor = connection.cursor()
        cursor.executemany(
                "INSERT INTO orders (order_id, item_id, quantity, total_price) VALUES (%s, %s, %s, %s)",
                order_items
            )  
        connection.commit()
        cursor.close()
        
    except:
        return -1

def get_order_total(order_id):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT SUM(total_price) FROM orders WHERE order_id = %s", (order_id,))
        total_price = cursor.fetchone()[0] 
        cursor.close()
        return total_price if total_price else None
    except:
        return None

def get_status_id(status_name):
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT status_id FROM order_status WHERE status_name = %s", (status_name,))
        status_id = cursor.fetchone()
        cursor.close()
        return status_id
    except: 
        return None

def insert_order_tracking(order_id,status_id):
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO order_tracking (order_id, status_id) VALUES (%s, %s)", (order_id, status_id))
        connection.commit()
        cursor.close()
    except: 
        return -1