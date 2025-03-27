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

def get_order_status(order_id: str):
    cursor = connection.cursor()
    cursor.execute("""SELECT status_name FROM order_tracking 
                      JOIN order_status ON order_tracking.status_id = order_status.status_id
                      WHERE order_id = %s""", (order_id,))
    status = cursor.fetchone()
    cursor.close()
    
    return status[0] if status else None