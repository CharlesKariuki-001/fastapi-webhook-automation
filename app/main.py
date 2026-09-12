"""
Webhook receiver: verifies the request really came from the expected
provider BEFORE looking at its contents, validates the payload shape,
rejects duplicate events, "forwards" valid new events to a downstream
system (simulated here - a real client project would call their
CRM/database/email tool here), and logs every step.

Request lifecycle:
  raw request -> signature check -> schema validation ->
  duplicate check -> forward downstream -> log -> response
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, status, Depends

from app.models import WebhookEvent
from app.database import init_db, is_duplicate, mark_processed
from app.security import verify_signature

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Modern FastAPI replacement for the deprecated @app.on_event("startup").
    # Code before `yield` runs on startup, code after would run on shutdown.
    init_db()
    yield


app = FastAPI(title="Webhook Automation", lifespan=lifespan)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


async def require_valid_signature(request: Request) -> None:
    """
    A FastAPI dependency, not a plain function - this matters. Declaring
    it via `dependencies=[Depends(...)]` on the route means FastAPI runs
    this check as part of resolving the request, before the endpoint
    body even starts executing. Reading the raw body here does not
    "use up" it - Starlette caches the body the first time it's read,
    so the WebhookEvent parameter below reads the identical bytes
    without needing to fetch them again.
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Webhook-Signature")
    if not verify_signature(raw_body, signature, WEBHOOK_SECRET):
        logger.warning("Rejected request with invalid/missing signature")
        raise HTTPException(status_code=401, detail="Invalid or missing webhook signature")


def forward_to_downstream_system(event: WebhookEvent) -> None:
    """
    Simulates sending validated data onward (e.g. to a CRM or database).
    Kept as its own function so a real client project can swap in the
    actual integration call here without touching anything else.
    """
    logger.info("Forwarded event %s (%s) downstream", event.event_id, event.event_type)


@app.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_valid_signature)],
)
async def receive_webhook(event: WebhookEvent):
    # By the time we get here, the signature has already been verified
    # and FastAPI has already validated `event` matches WebhookEvent's
    # shape (returning 422 automatically if it doesn't) - this function
    # only needs to handle business logic.
    if is_duplicate(event.event_id):
        logger.info("Duplicate event ignored: %s", event.event_id)
        return {"status": "duplicate_ignored", "event_id": event.event_id}

    try:
        forward_to_downstream_system(event)
        mark_processed(event.event_id, event.event_type)
    except Exception as exc:
        logger.error("Failed processing event %s: %s", event.event_id, exc)
        raise HTTPException(status_code=500, detail="Processing failed") from exc

    return {"status": "processed", "event_id": event.event_id}


@app.get("/health")
def health_check():
    return {"status": "ok"}
