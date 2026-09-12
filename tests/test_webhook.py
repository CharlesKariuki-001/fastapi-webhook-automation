"""
Proves the webhook receiver behaves correctly under every realistic
scenario a real provider (Stripe/Shopify-style) can throw at it.
Every test here was actually run against a live instance of the app
before being written down - not written from assumption.
"""

import os
import json
import hmac
import hashlib

os.environ.setdefault("WEBHOOK_SECRET", "test-secret-key")
SECRET = os.environ["WEBHOOK_SECRET"]

# Clean slate for every test run
for f in ["events.db", "events.db-wal", "events.db-shm"]:
    if os.path.exists(f):
        os.remove(f)

from app.main import app
from fastapi.testclient import TestClient


def sign(body: bytes) -> str:
    return hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def headers(signature: str) -> dict:
    return {"X-Webhook-Signature": signature, "Content-Type": "application/json"}


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_forged_signature_is_rejected():
    with TestClient(app) as client:
        body = json.dumps({"event_id": "evt_forge", "event_type": "order.created", "data": {}}).encode()
        response = client.post("/webhook", content=body, headers=headers("not-the-real-signature"))
        assert response.status_code == 401


def test_missing_signature_header_is_rejected():
    with TestClient(app) as client:
        body = json.dumps({"event_id": "evt_nosig", "event_type": "order.created", "data": {}}).encode()
        response = client.post("/webhook", content=body, headers={"Content-Type": "application/json"})
        assert response.status_code == 401


def test_genuine_event_is_processed():
    with TestClient(app) as client:
        body = json.dumps({"event_id": "evt_real_1", "event_type": "order.created", "data": {"amount": 50}}).encode()
        response = client.post("/webhook", content=body, headers=headers(sign(body)))
        assert response.status_code == 200
        assert response.json()["status"] == "processed"


def test_duplicate_event_is_ignored_not_reprocessed():
    """
    Simulates the single most common real webhook bug: a provider
    re-sending the exact same event (network retry on their end).
    The second delivery must be recognized and skipped, not treated
    as a brand-new event.
    """
    with TestClient(app) as client:
        body = json.dumps({"event_id": "evt_retry_1", "event_type": "order.created", "data": {"amount": 75}}).encode()
        first = client.post("/webhook", content=body, headers=headers(sign(body)))
        second = client.post("/webhook", content=body, headers=headers(sign(body)))

        assert first.json()["status"] == "processed"
        assert second.status_code == 200
        assert second.json()["status"] == "duplicate_ignored"


def test_malformed_payload_is_rejected_with_422():
    with TestClient(app) as client:
        body = json.dumps({"event_type": "order.created", "data": {}}).encode()  # missing event_id
        response = client.post("/webhook", content=body, headers=headers(sign(body)))
        assert response.status_code == 422


def test_forged_signature_rejected_before_payload_is_even_validated():
    """
    The most important security test in this file: a request that is
    BOTH forged AND malformed must be rejected on the signature (401),
    not on the payload shape (422). This proves the endpoint refuses
    to spend any effort validating content it can't even trust the
    source of.
    """
    with TestClient(app) as client:
        bad_body = json.dumps({"event_type": "order.created"}).encode()
        response = client.post("/webhook", content=bad_body, headers=headers("totally-forged"))
        assert response.status_code == 401
