"""
main.py
-------
This file starts a small web server (using FastAPI) that:
1. Shows a simple chat webpage (so you can test with your eyes/hands).
2. Exposes a POST endpoint /chat that any app (website, mobile app,
   WhatsApp bot, etc.) could call to talk to our chatbot.

Think of this as the "front door" of the chatbot. Everything else
(orders.py, chatbot.py) is the logic behind that door.
"""

import uuid
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.chatbot import handle_message

# --- TEMPORARY: using Anthropic direct API instead of Bedrock ---
# Reason: AWS Bedrock account token quota not yet provisioned (as of testing).
# To switch back to Bedrock once that's resolved, change this one import line to:
#   from app.bedrock_chatbot import handle_message_with_ai
from app.anthropic_chatbot import handle_message_with_ai

app = FastAPI(
    title="Customer Service Chatbot - POC",
    description="A simple end-to-end order-status chatbot proof of concept.",
    version="0.1.0",
)


# ---- This defines what a valid REQUEST looks like ----
class ChatRequest(BaseModel):
    message: str          # what the customer typed, e.g. "where is my order ORD1001"
    user_id: str | None = None   # optional: who is asking (if they're logged in)
    conversation_id: str | None = None   # optional: ties messages into one ongoing conversation


# ---- This defines what our RESPONSE looks like ----
class ChatResponse(BaseModel):
    reply: str
    intent: str
    order_id: str | None = None
    conversation_id: str | None = None   # send this back on your NEXT message to keep context


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    The main chatbot endpoint.
    Example request body:
    {
        "message": "where is my order ORD1001"
    }
    """
    result = handle_message(request.message, request.user_id)
    return ChatResponse(**result)


@app.post("/chat-ai", response_model=ChatResponse)
def chat_ai(request: ChatRequest):
    """
    Same as /chat, but understanding is done by a real AI model, AND it
    remembers the last few messages in this conversation.

    First message: leave conversation_id blank, we'll create one for you.
    Every message after that: send back the conversation_id you got in
    the previous response, so the AI has context on what was said before.
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())
    result = handle_message_with_ai(request.message, request.user_id, conversation_id)
    return ChatResponse(**result, conversation_id=conversation_id)


@app.get("/health")
def health():
    """Simple check to confirm the server is alive. Useful for deployment."""
    return {"status": "ok"}


# Serve the simple chat webpage at http://localhost:8000/
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")