# FastAPI Webhook Automation

A lightweight backend service that receives, validates, and forwards data between systems the kind of small, focused integration that replaces manual copy paste work or an expensive no-code subscription.

## The Problem

Many small businesses have two or more tools that should talk to each other automatically but don't a payment happens in one system, and someone has to manually update a spreadsheet or CRM. This project demonstrates a clean way to close that gap: a webhook receiver that validates incoming data, processes it safely, and forwards it to where it needs to go.

## Who This Is For

Anyone who needs to:
- Receive webhook events from a service (e.g. a payment or order notification)
- Validate incoming data before acting on it
- Prevent duplicate processing of the same event
- Forward or store the result automatically (database, another API, a notification)

## Features

- **FastAPI webhook receiver** — fast, well-documented, production-style structure
- **Payload validation** — using Pydantic, so malformed or incomplete data is rejected cleanly, not silently accepted
- **Duplicate event protection** — stores event IDs so the same webhook firing twice doesn't cause double-processing
- **Database storage** — validated events are saved (SQLite for local demo, easily swapped for Postgres in production)
- **Logging** — every event, success, and failure is logged for traceability
- **Error handling** — clear, correct HTTP status codes for valid, invalid, and failed requests

## Architecture
External Service

↓ (webhook fires)

FastAPI endpoint

↓

Validate payload (Pydantic)

↓

Check for duplicate event ID

↓

Process (store in DB / forward to another system)

↓

Log outcome

↓

Return response (200 / 4xx / 5xx)

## Installation

```bash
git clone https://github.com/CharlesKariuki-001/fastapi-webhook-automation.git
cd fastapi-webhook-automation
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running Locally

```bash
uvicorn src.main:app --reload
```

Then send a test webhook:

```bash
curl -X POST http://127.0.0.1:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"event_id": "evt_001", "type": "payment.success", "amount": 49.99}'
```

Sending the same `event_id` twice will be detected and rejected as a duplicate  this is intentional, and demonstrates the duplicate-protection logic.

## Testing

```bash
pytest
```

Tests cover: valid requests, invalid/missing fields, duplicate events, and simulated downstream failures.

## Limitations

This is a demonstration architecture using SQLite and a single endpoint for clarity. A production deployment would typically add: authentication/signature verification on incoming webhooks, a production-grade database, retry/backoff logic for downstream calls, and monitoring/alerting  all of which I scope based on the client's actual systems.

## What I Learned

The tricky part of webhook handling usually isn't the "happy path"  it's the edge cases: what happens when the same event arrives twice, what happens when the downstream system is briefly unavailable, and how you make failures visible instead of silent.

## Need Two Systems Connected?

If you have two tools that should sync automatically but currently require manual work, send me the two systems and a sample payload I'll map out the simplest reliable integration and give you a fixed price and timeline.

📬 [LinkedIn](https://ke.linkedin.com/in/charles-mburu-838965382) · [X](https://x.com/KariukiBuilds__)
