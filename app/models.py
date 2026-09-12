"""
Defines what a valid incoming webhook event looks like.

Mirrors the shape real providers use (Stripe/Shopify-style): every
event has a unique ID (used for deduplication), a type, and a data
payload. Pydantic rejects anything that doesn't match this shape
BEFORE it reaches business logic - so a malformed payload fails with
a clean 422 error, not a raw KeyError deep inside the app.
"""

from pydantic import BaseModel, Field


class WebhookEvent(BaseModel):
    event_id: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    data: dict
