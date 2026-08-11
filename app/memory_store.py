"""
memory_store.py
----------------
This gives the chatbot short-term memory of a conversation.

In plain English: every time you chat, we tag the conversation with an
ID (like a ticket number). Each new message gets added to that ID's
history. When we ask the AI to understand a new message, we also hand
it the last few messages from that same conversation, so it can
understand things like "the OTHER order" or "that one" by looking back
at what was already said.

For this POC, history lives in memory (a Python dictionary) — it's
reset if the server restarts. A real production system would use
something like Redis or a database table instead, so memory survives
restarts and works across multiple server instances.
"""

# key = conversation_id, value = list of {"role": ..., "content": ...} turns
_conversation_history: dict[str, list[dict]] = {}

# How many past turns (user + assistant messages combined) to keep per
# conversation. Keeping this small keeps costs down and avoids confusing
# the AI with too much old context.
MAX_TURNS = 6


def get_history(conversation_id: str) -> list[dict]:
    """Returns the stored conversation so far, or an empty list if new."""
    return _conversation_history.get(conversation_id, [])


def add_turn(conversation_id: str, role: str, content: str) -> None:
    """
    Adds one message to a conversation's history.
    role is either "user" (the customer) or "assistant" (the chatbot's reply).
    """
    history = _conversation_history.setdefault(conversation_id, [])
    history.append({"role": role, "content": content})

    # Keep only the most recent MAX_TURNS messages so memory doesn't grow forever
    if len(history) > MAX_TURNS:
        _conversation_history[conversation_id] = history[-MAX_TURNS:]