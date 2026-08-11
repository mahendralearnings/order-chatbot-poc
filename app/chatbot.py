"""
chatbot.py
----------
This is the "brain" of the chatbot.

It does 3 simple jobs, in plain English:
1. UNDERSTAND: figure out what the customer is asking about (we call
   this "intent" — meaning "what does the user want?").
2. FIND INFO: if they're asking about an order, find that order's data.
3. REPLY: turn that data into a friendly sentence.

For this POC we use simple keyword matching instead of a big AI model,
so it is fast, free, and 100% predictable. Later, you can swap the
"understand" step with a real LLM (like Claude on Bedrock) for smarter
understanding, without changing anything else in the app.
"""

import re
from app.orders import get_order_by_id, get_orders_for_user

# Words that suggest the customer is asking about order status/tracking
ORDER_STATUS_KEYWORDS = [
    "where is my order",
    "track my order",
    "order status",
    "when will my order",
    "order arrive",
    "delivery status",
    "where's my order",
    "track order",
]

# Pattern to catch an order ID typed by the user, e.g. "ORD1001"
ORDER_ID_PATTERN = re.compile(r"\bORD\d+\b", re.IGNORECASE)


def detect_intent(message: str) -> str:
    """
    Figures out what the user wants.
    Returns a simple label like 'order_status' or 'unknown'.
    """
    text = message.lower()
    for phrase in ORDER_STATUS_KEYWORDS:
        if phrase in text:
            return "order_status"
    return "unknown"


def extract_order_id(message: str):
    """Looks for something like 'ORD1001' inside the user's message."""
    match = ORDER_ID_PATTERN.search(message)
    return match.group(0).upper() if match else None


def build_order_status_reply(order_id: str, order: dict) -> str:
    """Turns raw order data into a friendly, human sentence."""
    items = ", ".join(order["items"])
    reply = (
        f"Your order {order_id} ({items}) is currently: **{order['status']}**. "
        f"Expected delivery date: {order['expected_delivery']}."
    )
    if order["tracking_id"]:
        reply += f" You can track it with {order['carrier']}, tracking ID {order['tracking_id']}."
    return reply


def handle_message(message: str, user_id: str = None) -> dict:
    """
    This is the main function the API calls.
    Input: the raw text the user typed (and optionally who they are).
    Output: a dictionary with the chatbot's reply and any extra data.
    """
    intent = detect_intent(message)

    if intent == "order_status":
        order_id = extract_order_id(message)

        # Case 1: user gave a specific order ID, e.g. "where is ORD1001"
        if order_id:
            order = get_order_by_id(order_id)
            if order:
                return {
                    "intent": intent,
                    "reply": build_order_status_reply(order_id, order),
                    "order_id": order_id,
                }
            else:
                return {
                    "intent": intent,
                    "reply": f"I couldn't find any order with ID {order_id}. "
                             f"Could you please double check the order number?",
                    "order_id": None,
                }

        # Case 2: no order ID given, but we know who the user is
        if user_id:
            user_orders = get_orders_for_user(user_id)
            if len(user_orders) == 1:
                order = user_orders[0]
                return {
                    "intent": intent,
                    "reply": build_order_status_reply(order["order_id"], order),
                    "order_id": order["order_id"],
                }
            elif len(user_orders) > 1:
                order_list = ", ".join(o["order_id"] for o in user_orders)
                return {
                    "intent": intent,
                    "reply": f"You have a few recent orders: {order_list}. "
                             f"Which one would you like to check?",
                    "order_id": None,
                }

        # Case 3: no order ID and no known user
        return {
            "intent": intent,
            "reply": "I'd be happy to check that for you! Could you share your order ID? "
                     "It usually looks like 'ORD1001'.",
            "order_id": None,
        }

    # Fallback for anything the bot doesn't understand yet
    return {
        "intent": "unknown",
        "reply": "I'm still learning! Right now I can help you check your order status. "
                 "Try asking something like: 'Where is my order ORD1001?'",
        "order_id": None,
    }