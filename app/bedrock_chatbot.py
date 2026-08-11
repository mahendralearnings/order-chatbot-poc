"""
bedrock_chatbot.py
-------------------
This is the UPGRADED "brain" of the chatbot.

Old version (chatbot.py): looked for fixed phrases like "where is my order".
New version (this file): sends the customer's message to a real AI model
(Claude, running on AWS Bedrock) and asks it to figure out:
  1. what the customer wants (the "intent")
  2. any order ID mentioned, in any format the customer typed it

This means the bot can now understand messages like:
  "hey when's my stuff arriving" or "any update on ORD 1001 pls?"
...without us having to write a keyword rule for every possible phrasing.

The rest of the flow stays IDENTICAL to before: once we know the intent
and order ID, we still look the order up in orders.py the same way.
"""

import json
import os
import boto3
from dotenv import load_dotenv
from app.orders import get_order_by_id, get_orders_for_user
from app.chatbot import build_order_status_reply  # reuse the same reply formatter

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-2-lite-v1:0")

# boto3 automatically finds the credentials you set up with `aws configure`
# We never write access keys directly in our code — that's unsafe.
bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)


# This is the instruction we give the AI model. It tells the AI exactly
# what job to do and what shape of answer we want back (strict JSON),
# so our Python code can read the answer reliably.
SYSTEM_PROMPT = """You are an intent-detection assistant for a customer service chatbot.
Read the customer's message and respond with ONLY a JSON object, nothing else, no markdown fences.

The JSON must have exactly these fields:
{
  "intent": "order_status" or "unknown",
  "order_id": the order ID mentioned in the message (e.g. "ORD1001"), or null if none was mentioned
}

Rules:
- "order_status" = the customer is asking where their order is, when it will arrive,
  or wants to track/check on an order, in ANY wording.
- If they mention a number that looks like an order ID (with or without the letters "ORD",
  with or without spaces), normalize it to the format "ORD" followed by digits, e.g. "ORD1001".
- If nothing matches order status, intent is "unknown" and order_id is null.
"""


def call_bedrock_for_intent(message: str) -> dict:
    """
    Sends the customer's message to whichever model is configured in
    .env and asks it to return the intent + order ID as JSON.

    This uses Bedrock's "Converse" API instead of the older, provider-specific
    invoke_model format. Converse works the SAME way no matter which provider's
    model you point it at (Claude, Amazon Nova, Meta Llama, etc.) — so switching
    models later is just a one-line change to BEDROCK_MODEL_ID in .env, with
    NO code changes needed here.
    """
    response = bedrock_client.converse(
        modelId=MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[
            {"role": "user", "content": [{"text": message}]}
        ],
        inferenceConfig={"maxTokens": 200},
    )

    raw_text = response["output"]["message"]["content"][0]["text"]

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        # If the AI ever replies with something that isn't valid JSON,
        # we fail safely instead of crashing the whole app.
        return {"intent": "unknown", "order_id": None}


def handle_message_with_ai(message: str, user_id: str = None) -> dict:
    """
    This is the new main function — same job as handle_message() in
    chatbot.py, but Step 1 (understanding) now uses real AI instead
    of keyword matching. Steps 2 and 3 (look up order, write reply)
    stay exactly the same as before.
    """
    understanding = call_bedrock_for_intent(message)
    intent = understanding.get("intent", "unknown")
    order_id = understanding.get("order_id")

    if intent == "order_status":
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

        return {
            "intent": intent,
            "reply": "I'd be happy to check that for you! Could you share your order ID? "
                     "It usually looks like 'ORD1001'.",
            "order_id": None,
        }

    return {
        "intent": "unknown",
        "reply": "I'm still learning! Right now I can help you check your order status. "
                 "Try asking something like: 'when will my stuff get here?'",
        "order_id": None,
    }