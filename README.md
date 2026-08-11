# Order Support Chatbot — Proof of Concept (POC)

## 🚀 Live Demo
**Try it now:** https://or-697adaebf85d49179f2552843e06a798.ecs.us-east-1.on.aws

This is a real, working deployment on AWS (ECS Express Mode) — not a local-only demo.
Ask it things like: "where is my order ORD1001", then a follow-up like "when does it arrive?"

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
   Now backed by a real SQLite database (`orders.db`).

2. **`app/anthropic_chatbot.py` — the chef (the logic/brain)**
   Reads what the customer typed, uses real AI to figure out
   "they're asking about order status," pulls out the order ID,
   looks it up, and writes a friendly sentence back — with memory
   of the conversation so far.

3. **`app/main.py` — the waiter (the API)**
   This is the part other things (a website, a mobile app, WhatsApp)
   would actually "talk to." It receives the customer's message and
   sends back the chatbot's reply, as structured data (JSON).

There's also `static/index.html` — a simple chat webpage, so
you can see and test the chatbot with your eyes, not just with
commands in a terminal.

---

## What "request" and "response" actually look like

### Example — with conversation memory

**Request 1:**
```json
POST /chat-ai
{ "message": "where is my order ORD1001" }
```

**Response 1:**
```json
{
  "reply": "Your order ORD1001 (Wireless Mouse) is currently: **Shipped**. Expected delivery date: 2026-08-13. You can track it with BlueDart, tracking ID BD998877.",
  "intent": "order_status",
  "order_id": "ORD1001",
  "conversation_id": "50577128-6b32-418e-8478-ecd84a05d8a3"
}
```

**Request 2 (follow-up, same conversation_id, no order number repeated):**
```json
{
  "message": "when does it arrive?",
  "conversation_id": "50577128-6b32-418e-8478-ecd84a05d8a3"
}
```

**Response 2** — correctly resolves "it" to ORD1001 using conversation history:
```json
{
  "reply": "Your order ORD1001 (Wireless Mouse) is currently: **Shipped**. Expected delivery date: 2026-08-13. You can track it with BlueDart, tracking ID BD998877.",
  "intent": "order_status",
  "order_id": "ORD1001",
  "conversation_id": "50577128-6b32-418e-8478-ecd84a05d8a3"
}
```

---

## How to run it yourself (locally, on your laptop)

1. Install dependencies with `uv`:

## How to run it yourself (locally, on your laptop)

1. Install dependencies with `uv`:

uv sync

2. Create your `.env` file (copy `.env.example` and fill in your real `ANTHROPIC_API_KEY`)
3. Start the server:
4. Open your browser to: `http://localhost:8000/`

---

## How this was actually deployed (ECS Express Mode)

This project is deployed using **Amazon ECS Express Mode** — AWS's simplified
container deployment feature (the successor to App Runner, which stopped
accepting new customers in April 2026). It handles the load balancer,
HTTPS certificate, auto-scaling, and networking automatically — you only
provide a container image.

**To redeploy after making changes:**

1. Build and push a new image to ECR:

**To redeploy after making changes:**

1. Build and push a new image to ECR:

docker build -t order-chatbot .
docker tag order-chatbot:latest 617297630012.dkr.ecr.us-east-1.amazonaws.com/order-chatbot:latest
docker push 617297630012.dkr.ecr.us-east-1.amazonaws.com/order-chatbot:latest


2. In the ECS console, go to your Express service → trigger a new deployment
   (or update the service to pull the `:latest` tag again).

**Environment variables configured on the live service:**
`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `AWS_REGION`, `BEDROCK_MODEL_ID`
(set directly in the ECS Express service configuration — not from a
committed `.env` file, since secrets should never be baked into the image).

---

## Current architecture (updated from the original simple version)

This POC evolved through several stages, each proven working end-to-end:

- **Understanding:** real AI (Claude, via Anthropic's API) instead of keyword
  matching — understands casual, varied phrasing, not just fixed phrases.
  (A Bedrock version also exists in `app/bedrock_chatbot.py`, ready to
  switch back to once AWS Bedrock quota is provisioned — see that file's
  docstring for the one-line import change needed in `main.py`.)
- **Memory:** conversation-aware — follow-up questions like "when does it
  arrive?" or "what's the tracking number?" correctly resolve to the order
  discussed earlier in the same conversation (`app/memory_store.py`).
- **Data:** a real SQLite database (`orders.db`), not a fake dictionary
  (`app/database.py`, `app/orders.py`).
- **Deployment:** live on AWS via Docker + ECS Express Mode (see above).

## What this POC still deliberately leaves out

- User login/authentication (`user_id` is optional and unused unless passed)
- A production-grade database (SQLite is real, but a live AWS deployment's
  storage resets on container restart — AWS RDS would be the next step
  for genuine persistence)
- AI-generated reply text (replies are still template-based for
  predictability — the AI's job is understanding intent, not writing
  the final sentence)

## Natural next steps, if you want to grow this further

- Swap SQLite for AWS RDS (PostgreSQL) for real persistence across restarts
- Add login, so `user_id` is known automatically
- Let the AI generate more tailored final reply text (not just intent detection)
- Switch back to Bedrock once AWS token quota is resolved (see
  `app/bedrock_chatbot.py`)
- Set up CI/CD (e.g. GitHub Actions) so pushing to `main` automatically
  rebuilds and redeploys the ECS service


  2. In the ECS console, go to your Express service → trigger a new deployment
   (or update the service to pull the `:latest` tag again).

**Environment variables configured on the live service:**
`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `AWS_REGION`, `BEDROCK_MODEL_ID`
(set directly in the ECS Express service configuration — not from a
committed `.env` file, since secrets should never be baked into the image).

---

## Current architecture (updated from the original simple version)

This POC evolved through several stages, each proven working end-to-end:

- **Understanding:** real AI (Claude, via Anthropic's API) instead of keyword
  matching — understands casual, varied phrasing, not just fixed phrases.
  (A Bedrock version also exists in `app/bedrock_chatbot.py`, ready to
  switch back to once AWS Bedrock quota is provisioned — see that file's
  docstring for the one-line import change needed in `main.py`.)
- **Memory:** conversation-aware — follow-up questions like "when does it
  arrive?" or "what's the tracking number?" correctly resolve to the order
  discussed earlier in the same conversation (`app/memory_store.py`).
- **Data:** a real SQLite database (`orders.db`), not a fake dictionary
  (`app/database.py`, `app/orders.py`).
- **Deployment:** live on AWS via Docker + ECS Express Mode (see above).

## What this POC still deliberately leaves out

- User login/authentication (`user_id` is optional and unused unless passed)
- A production-grade database (SQLite is real, but a live AWS deployment's
  storage resets on container restart — AWS RDS would be the next step
  for genuine persistence)
- AI-generated reply text (replies are still template-based for
  predictability — the AI's job is understanding intent, not writing
  the final sentence)

## Natural next steps, if you want to grow this further

- Swap SQLite for AWS RDS (PostgreSQL) for real persistence across restarts
- Add login, so `user_id` is known automatically
- Let the AI generate more tailored final reply text (not just intent detection)
- Switch back to Bedrock once AWS token quota is resolved (see
  `app/bedrock_chatbot.py`)
- Set up CI/CD (e.g. GitHub Actions) so pushing to `main` automatically
  rebuilds and redeploys the ECS service