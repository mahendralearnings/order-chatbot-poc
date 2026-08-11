"""
orders.py
----------
This now does a REAL database lookup, using SQLite (see database.py).

Same function names and same return shape as the old fake-dictionary
version — get_order_by_id() and get_orders_for_user() work exactly the
same from the outside. This means chatbot.py and anthropic_chatbot.py
did NOT need to change at all to use this. That's the benefit of
keeping "how we answer the customer" separate from "where the data
actually lives" — you can swap the data source without touching the
logic that uses it.
"""

from app.database import get_connection, init_db

# Make sure the database file, table, and sample data all exist
# the moment this module is first loaded by the app.
init_db()


def _row_to_order_dict(row) -> dict:
    """Converts one raw database row into the same shape our chatbot code expects."""
    return {
        "user_id": row["user_id"],
        "status": row["status"],
        "items": row["items"].split(", "),
        "expected_delivery": row["expected_delivery"],
        "carrier": row["carrier"],
        "tracking_id": row["tracking_id"],
    }


def get_order_by_id(order_id: str):
    """Look up one order by its ID using a real SQL query. Returns None if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id.upper(),))
    row = cursor.fetchone()
    conn.close()
    return _row_to_order_dict(row) if row else None


def get_orders_for_user(user_id: str):
    """Find all orders that belong to a given user (customer), using a real SQL query."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"order_id": row["order_id"], **_row_to_order_dict(row)} for row in rows]