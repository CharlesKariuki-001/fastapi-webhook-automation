# FastAPI Webhook Automation

A secure webhook receiver that verifies every request is genuine, rejects
duplicate deliveries, validates payload shape, and forwards clean data
downstream — the core pattern behind reliably connecting tools like
Stripe, Shopify, or a CRM without losing data to spoofed requests,
re-sent events, or silent failures.

## What problem does this solve?

Three separate, expensive failure modes, all handled by this one
service:

1. **Spoofing.** A public webhook URL can be found and hit by anyone.
   Without signature verification, an attacker can fake a
   "payment succeeded" event and trigger real business actions.

2. **Double-processing.** Webhook providers frequently re-send the
   exact same event because of network retries. Without deduplication,
   this can cause duplicate business actions.

3. **Malformed data.** A field renamed or a type changed on the
   provider's end can otherwise cause an unhandled error. Pydantic
   validation ensures invalid payloads fail cleanly.

## Architecture

```text
Provider (Stripe/Shopify/etc.)
        |
        v
  POST /webhook
        |
        v
  HMAC signature check --(invalid)--> 401 Unauthorized
        |
      (valid)
        |
        v
  Pydantic validation --(invalid)--> 422 Unprocessable Content
        |
      (valid)
        |
        v
  Duplicate check (SQLite, WAL mode)
        |
   (seen before) ------------------> 200 duplicate_ignored
        |
       (new)
        |
        v
  Forward downstream + log + mark processed
        |
        v
  200 processed

  The security check runs first and rejects forged requests before payload
validation. This means a request that is both forged and malformed fails
on the signature check with 401, rather than exposing payload validation
details.

Features
FastAPI webhook receiver
HMAC-SHA256 signature verification
Pydantic payload validation
Duplicate event protection
SQLite persistence with WAL mode
Structured error handling
Logging and traceability
Automated test coverage
Dependency-based security checks using FastAPI Depends()
Modern FastAPI lifespan startup
Installation
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

Then edit .env and set a real WEBHOOK_SECRET.

Running it
uvicorn app.main:app --reload

The API will be available at:

http://127.0.0.1:8000
Usage

A genuine request must include a matching HMAC-SHA256 signature of the
raw request body, computed using your WEBHOOK_SECRET, and sent in the
X-Webhook-Signature header.

Example:

curl -X POST http://127.0.0.1:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: <hmac-sha256-of-the-body>" \
  -d '{"event_id": "evt_123", "event_type": "order.created", "data": {"amount": 100}}'
Testing

Run:

pytest -v

The test suite contains 7 tests covering:

Health check
Forged signature rejection
Missing signature rejection
Genuine event processing
Duplicate event detection
Malformed payload rejection
Security ordering: forged + malformed requests must fail on the
signature check before payload validation
Error handling
401 — missing or invalid X-Webhook-Signature
422 — valid signature but invalid payload
200 duplicate_ignored — previously processed event
200 processed — new, valid, genuine event
500 — downstream forwarding failure
Project structure
fastapi-webhook-automation/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   └── security.py
├── tests/
│   └── test_webhook.py
├── docs/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
Limitations

This project uses SQLite with WAL mode and a simulated downstream call.

A production deployment would typically use the client's production
database and target system, plus retry/backoff logic, monitoring, and
possibly a process-safe queue when running multiple server workers.

The HMAC-SHA256 approach is a general webhook security pattern, but
individual providers such as Stripe, Shopify, or GitHub have their own
exact signing formats and headers.

What I learned building this

The most dangerous webhook bugs aren't always crashes. They can be
requests that are trusted when they shouldn't be, or duplicate requests
that are processed more than once.

Both problems can fail silently unless they are deliberately tested.
That is why the security-ordering test — forged and malformed together —
is particularly important.

Need two systems connected?

Send me the two tools you're using and an example payload. I'll map the
simplest reliable integration and provide a fixed price and timeline.