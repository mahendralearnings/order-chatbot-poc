"""
database.py
------------
This sets up a REAL database for our order data, using SQLite.

Why SQLite for a POC: it's a genuine, real SQL database (not a fake
substitute) — but the entire database lives in ONE FILE on your
computer, with no separate server to install or run. This is a real
stepping stone toward something like PostgreSQL on AWS RDS later,
without adding setup complexity at the POC stage.

This file's job: create the table structure, and fill it with the SAME
sample data we had in the old fake dictionary — so nothing else in the
app needs to notice or care that the data source changed underneath it.
"""

import sqlite3
from pathlib import Path
from datetime import date, timedelta

# The database file will be created right in your project folder
DB_PATH = Path(__file__).parent.parent / "orders.db"


def get_connection():
    """Opens a connection to the SQLite database file."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us read columns by name, like a dictionary
    return conn


def init_db():
    """Creates the orders table (if missing) and seeds sample data (if empty)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            status TEXT NOT NULL,
            items TEXT NOT NULL,
            expected_delivery TEXT NOT NULL,
            carrier TEXT,
            tracking_id TEXT
        )
    """)

    # Only seed sample rows if the table is currently empty,
    # so restarting the server doesn't duplicate rows every time.
    cursor.execute("SELECT COUNT(*) FROM orders")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_orders = [
            ("ORD1001", "customer_1", "Shipped", "Wireless Mouse",
             (date.today() + timedelta(days=2)).isoformat(), "BlueDart", "BD998877"),
            ("ORD1002", "customer_1", "Out for Delivery", "Office Chair",
             date.today().isoformat(), "Delhivery", "DL556611"),
            ("ORD1003", "customer_2", "Processing", "Laptop Stand, USB-C Cable",
             (date.today() + timedelta(days=5)).isoformat(), "Not assigned yet", None),
        ]
        cursor.executemany(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)",
            sample_orders
        )
        conn.commit()

    conn.close()