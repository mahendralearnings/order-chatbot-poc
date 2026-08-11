# Order Support Chatbot — Proof of Concept (POC)

## What this is (in plain English)

This is a very small, working chatbot. A customer can type something
like **"where is my order ORD1001"**, and the chatbot replies with the
real status of that order, just like a customer support agent would.

It is a **proof of concept**, which means: it's not fancy or
production-ready yet, but it proves the *idea* works, end to end —
from typing a question, to getting a correct answer, to it being
something you could actually run on a server.

---

## How it's built (the 3 layers)

Think of it like a restaurant:

1. **`app/orders.py` — the kitchen storage (data)**
   A fake list of orders, like a mini database. In real life, this
   would be swapped for a real database (like PostgreSQL).

2. **`app/chatbot.py` — the chef (the logic/brain)**
   This reads what the customer typed, figures out "they're asking
   about order status," pulls out the order ID if they gave one, looks
   it up in the storage, and writes a friendly sentence back.

3. **`app/main.py` — the waiter (the API)**
   This is the part other things (a website, a mobile app, WhatsApp)
   would actually "talk to." It receives the customer's message and
   sends back the chatbot's reply, as structured data (JSON).

There's also `static/index.html` — a simple chat webpage, just so
you can see and test the chatbot with your eyes, not just with
commands in a terminal.

---

## What "request" and "response" actually look like

This is the core of the POC — proof that asking "where is my order"
gets the right answer.

### Example 1 — customer gives an order ID

**Request** (what the app/website sends to our chatbot):
```json
POST /chat
{
  "message": "where is my order ORD1001"
}
```

**Response** (what the chatbot sends back):
```json
{
  "reply": "Your order ORD1001 (Wireless Mouse) is currently: **Shipped**. Expected delivery date: 2026-08-10. You can track it with BlueDart, tracking ID BD998877.",
  "intent": "order_status",
  "order_id": "ORD1001"
}
```

### Example 2 — customer doesn't give an order ID

**Request:**
```json
{ "message": "where is my order" }
```

**Response:**
```json
{
  "reply": "I'd be happy to check that for you! Could you share your order ID? It usually looks like 'ORD1001'.",
  "intent": "order_status",
  "order_id": null
}
```

### Example 3 — order ID doesn't exist

**Request:**
```json
{ "message": "where is my order ORD9999" }
```

**Response:**
```json
{
  "reply": "I couldn't find any order with ID ORD9999. Could you please double check the order number?",
  "intent": "order_status",
  "order_id": null
}
```

### Example 4 — something unrelated

**Request:**
```json
{ "message": "what is your refund policy" }
```

**Response:**
```json
{
  "reply": "I'm still learning! Right now I can help you check your order status. Try asking something like: 'Where is my order ORD1001?'",
  "intent": "unknown",
  "order_id": null
}
```

I ran all 4 of these for real while building this — they are actual
tested outputs, not made up.

---

## How to run it yourself (locally, on your laptop)

1. Install the requirements:
   ```
   pip install -r requirements.txt
   ```
2. Start the server:
   ```
   uvicorn app.main:app --reload
   ```
3. Open your browser to: `http://localhost:8000/`
   You'll see the little chat webpage. Type: `where is my order ORD1001`

You can also test it directly with curl (a terminal tool for sending
web requests):
```
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"where is my order ORD1001\"}"
```

---

## How to deploy it (make it live on the internet)

This project includes a `Dockerfile`. Docker is a way to "package"
your app with everything it needs, so it runs the same way anywhere.

**Step 1 — Build the package:**
```
docker build -t order-chatbot .
```

**Step 2 — Run it:**
```
docker run -p 8000:8000 order-chatbot
```

**Step 3 — Put it on the internet.**
Since this Docker image is standard, you can deploy it to any of
these (you already know AWS, so these are the natural fits):
- **AWS App Runner** — easiest option, just point it at your Docker image
- **AWS ECS (Fargate)** — more control, still no servers to manage
- **AWS Elastic Beanstalk** — simple if you want a "just works" option

For a true POC/demo, App Runner is the fastest path: you push your
Docker image, and within a few minutes you get a public URL like
`https://xxxx.us-east-1.awsapprunner.com` that anyone can chat with.

---

## What this POC deliberately leaves out (on purpose, for now)

To keep this focused and easy to understand, we did NOT include:
- A real database (we used a fake Python dictionary instead)
- User login/authentication (so `user_id` is optional and unused unless passed)
- A real AI/LLM understanding the message (we used simple keyword matching)
- Conversation memory (each message is handled fresh, with no history)

## Natural next steps, if you want to grow this later

- Swap `orders.py` to query a real database
- Add login, so `user_id` is known automatically and the bot can say
  "you have 2 orders, which one?" without the customer typing an ID
- Swap the simple keyword-matching in `chatbot.py` for a real LLM call
  (e.g., AWS Bedrock) so it understands messages written in more
  natural, varied ways — not just fixed keyword phrases
- Add conversation memory so it can handle follow-up questions like
  "and what about my other one?"
