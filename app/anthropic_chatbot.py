"""
anthropic_chatbot.py
---------------------
This is a TEMPORARY stand-in for bedrock_chatbot.py.

Same job, same output shape — the only difference is WHERE the request
goes: instead of AWS Bedrock, this calls Anthropic's own API directly
(api.anthropic.com). This is useful right now because your AWS Bedrock
account has a token quota that hasn't been provisioned yet, and this
lets you keep moving without waiting on AWS.

Once your Bedrock quota is sorted, you can switch main.py back to
import from bedrock_chatbot instead of this file — nothing else in the
app needs to change, since both files return the exact same shape of data.
"""

import json
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from app.orders import get_order_by_id, get_orders_for_user
from app.chatbot import build_order_status_reply
from app.memory_store import get_history, add_turn

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Same instructions as before, PLUS a new rule about using conversation history
SYSTEM_PROMPT = """You are an intent-detection assistant for a customer service chatbot.
You may be shown earlier messages from this same conversation for context.
Read the customer's LATEST message and respond with ONLY a JSON object, nothing else, no markdown fences.

The JSON must have exactly these fields:
{
  "intent": "order_status" or "unknown",
  "order_id": the order ID mentioned in the message (e.g. "ORD1001"), or null if none was mentioned
}

Rules:
- "order_status" = the customer is asking ANYTHING about an existing order: where it is,
  when it will arrive, its status, its tracking number, which carrier is delivering it,
  or wants to track/check on it in any way. Treat all of these as the SAME intent, since
  we already have all of this information together for each order.
- If they mention a number that looks like an order ID (with or without the letters "ORD",
  with or without spaces), normalize it to the format "ORD" followed by digits, e.g. "ORD1001".
- If the customer refers back to something from EARLIER in the conversation (e.g. "that one",
  "the other order", "it", or asks a follow-up like "what's the tracking number?" without
  repeating the order ID), use the conversation history to figure out which order_id they mean.
  If the earlier messages don't make it clear which specific order, leave order_id as null.
- If nothing matches order status, intent is "unknown" and order_id is null.
"""


def build_context_note(history: list[dict]) -> str:
    """
    Turns the stored history into a short 'here's what was discussed
    earlier' summary, written as plain text instructions rather than
    a real back-and-forth conversation. This keeps the AI firmly in
    'always answer with JSON' mode, instead of getting confused by
    seeing its own earlier reply wasn't JSON.
    """
    if not history:
        return ""
    lines = []
    for turn in history:
        speaker = "Customer said" if turn["role"] == "user" else "You (the bot) replied"
        lines.append(f"- {speaker}: {turn['content']}")
    return "\n\nEarlier in this conversation:\n" + "\n".join(lines)


def call_claude_for_intent(message: str, conversation_id: str) -> dict:
    """
    Sends the customer's message to Claude and asks for intent + order ID
    as JSON. If there's earlier conversation history, it's included as a
    short context summary in the system prompt (not as fake conversation
    turns), so the AI can resolve references like "the other one" while
    still reliably replying with pure JSON.
    """
    history = get_history(conversation_id)
    context_note = build_context_note(history)

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=200,
        system=SYSTEM_PROMPT + context_note,
        messages=[{"role": "user", "content": message}],
    )

    # Newer Claude models can sometimes include other block types (like an
    # internal "thinking" block) before the actual text reply. So instead
    # of assuming index [0] is the text, we search through all blocks for
    # the first one that actually has text.
    raw_text = None
    for block in response.content:
        if getattr(block, "text", None):
            raw_text = block.text.strip()
            break

    if not raw_text:
        print("DEBUG: Unexpected Claude response:", response)
        return {"intent": "unknown", "order_id": None}

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print("DEBUG: Claude did not return valid JSON. Raw text was:", repr(raw_text))
        return {"intent": "unknown", "order_id": None}


def handle_message_with_ai(message: str, user_id: str = None, conversation_id: str = None) -> dict:
    """
    Same logic as before, but now conversation-aware:
    1. Look up (or start) this conversation's history
    2. Ask the AI to understand the message, using that history as context
    3. Figure out the reply, same as before
    4. Save both the customer's message and our reply into memory,
       so the NEXT message in this same conversation has context too
    """
    understanding = call_claude_for_intent(message, conversation_id)
    intent = understanding.get("intent", "unknown")
    order_id = understanding.get("order_id")

    if intent == "order_status":
        if order_id:
            order = get_order_by_id(order_id)
            if order:
                reply = build_order_status_reply(order_id, order)
            else:
                reply = (f"I couldn't find any order with ID {order_id}. "
                         f"Could you please double check the order number?")
                order_id = None
        elif user_id:
            user_orders = get_orders_for_user(user_id)
            if len(user_orders) == 1:
                order = user_orders[0]
                order_id = order["order_id"]
                reply = build_order_status_reply(order_id, order)
            elif len(user_orders) > 1:
                order_list = ", ".join(o["order_id"] for o in user_orders)
                reply = (f"You have a few recent orders: {order_list}. "
                         f"Which one would you like to check?")
            else:
                reply = ("I'd be happy to check that for you! Could you share your order ID? "
                          "It usually looks like 'ORD1001'.")
        else:
            reply = ("I'd be happy to check that for you! Could you share your order ID? "
                      "It usually looks like 'ORD1001'.")
    else:
        reply = ("I'm still learning! Right now I can help you check your order status. "
                  "Try asking something like: 'when will my stuff get here?'")

    # Remember this exchange for next time, so follow-up questions have context
    add_turn(conversation_id, "user", message)
    add_turn(conversation_id, "assistant", reply)

    return {"intent": intent, "reply": reply, "order_id": order_id}